from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.parsers import BaseParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.contrib.auth.models import User
from bio.models import GenePrediction, Gene
from .serializer import GenePredictionSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from bio.utils import process_gff_file, blastp_local, write_fasta_for_prediction
import tempfile
import random
import os
import subprocess

# --- ROUTES ---
@api_view(['GET'])
def getRoutes(request):
    routes = [
        {'GET': '/api/laboratories/'},
        {'GET': '/api/laboratories/id'},
        {'POST': '/api/users/token'},
        {'POST': '/api/users/token/refresh'},
    ]
    return Response(routes)



@api_view(["POST"])
def register(request):
    username = request.data.get('username')
    password = request.data.get('password')
    if not username or not password:
        return Response({"message": "fill all fields"}, status=400)
    if User.objects.filter(username=username).exists():
        return Response({"message": "User already exists"}, status=400)

    user = User.objects.create_user(username=username, password=password)
    refresh = RefreshToken.for_user(user)
   
    return Response({
        "message": "User created successfully",
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }, status=201) 


OUTPUT_DIR = "augustus_outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

class PlainTextParser(BaseParser):
    media_type = "text/plain"

    def parse(self, stream, media_type=None, parser_context=None):
        return stream.read().decode("utf-8")



@api_view(['POST'])
@permission_classes([AllowAny])
@parser_classes([PlainTextParser])
def predict_gene(request):
    sequence = request.data.strip()
    if not sequence:
        return Response({"error": "No sequence provided"}, status=400)

    if sequence.startswith(">"):
        fasta_text = sequence
    else:
        fasta_text = f">{random.randint(1000, 9999)}\n{sequence}"

    with tempfile.NamedTemporaryFile(mode="w+", suffix=".fa", delete=False) as fasta_file:
        fasta_file.write(fasta_text)
        fasta_path = fasta_file.name

    output_file = os.path.join(OUTPUT_DIR, f"prediction_{os.path.basename(fasta_path)}.gff")

    try:
        subprocess.run([
            "augustus",
            "--species={data.species}",
            fasta_path,
            f"--outfile={output_file}"
        ], check=True)
    finally:
        os.remove(fasta_path)

    try:
        gene_prediction = GenePrediction.objects.create(
            owner=request.user,
            name="Gene Prediction",
            status="done"
        )
        process_gff_file(output_file, gene_prediction)
        fasta_path = write_fasta_for_prediction(gene_prediction)
    except Exception as e:
        return Response({"error": f"Error processing GFF file: {str(e)}"}, status=500)

    return Response({
        "message": "Prediction done successfully.",
        "id": gene_prediction.id,   
        "output_file": output_file
    })



@api_view(["GET"])
def blast_gene(request, gene_id):
    try:
        gene = Gene.objects.get(gene_id=gene_id)
    except Gene.DoesNotExist:
        return Response({"error": "Gene not found"}, status=404)

    if not gene.protein_sequence:
        return Response({"error": "No protein sequence found"}, status=400)


    db_path = "/home/hamid/blast_db/my_protein_db"
    blast_results = blastp_local(gene.protein_sequence, db_path=db_path)

    return Response({
        "gene_id": gene_id,
        "protein_length": len(gene.protein_sequence),
        "blast_results": blast_results
    })



@api_view(['GET'])
def get_gene_prediction_result(request, pk):
    try:
        gene_prediction = GenePrediction.objects.get(id=pk)
        serializer = GenePredictionSerializer(gene_prediction)
        return Response(serializer.data)
    except GenePrediction.DoesNotExist:
        return Response({"error": "Gene prediction not found"}, status=404)
