import csv
import random
import os
import json
import subprocess
from tempfile import NamedTemporaryFile
from django.db import transaction
from .models import GenePrediction, Gene, Transcript, Feature


BLAST_BIN = "/home/hamid/ncbi-blast-2.17.0+/bin/blastp"


BLAST_DB_DIR = "/home/hamid/blast_db/my_protein_db"

def process_gff_file(gff_file_path, gene_prediction):
    proteins = parse_gff_proteins(gff_file_path)
    protein_index = 0  

    genes = []
    transcripts = []
    features = []

    current_gene = None
    current_transcript = None

    try:
        with open(gff_file_path, 'r') as file:
            reader = csv.reader(file, delimiter='\t')
            with transaction.atomic():
                for row in reader:
                    if len(row) < 9 or row[0].startswith("#"):
                        continue

                    seqid = row[0]
                    source = row[1]
                    feature_type = row[2]
                    start = int(row[3])
                    end = int(row[4])
                    score = row[5]
                    strand = row[6] if len(row) > 6 else None
                    phase = int(row[7]) if len(row) > 7 and row[7].isdigit() else None
                    attributes = row[8]

                    attributes_dict = {}
                    for item in attributes.split(';'):
                        if '=' in item:
                            key, value = item.split('=', 1)
                            attributes_dict[key] = value

                    if feature_type == 'gene':
                        gene_id = attributes_dict.get('ID') or f"gene_{random.randint(1000,9999)}"
                        protein_sequence = None
                        if protein_index < len(proteins):
                            protein_sequence = proteins[protein_index]
                        protein_index += 1

                        current_gene = Gene.objects.create(
                            gene_id=gene_id,
                            start=start,
                            end=end,
                            protein_sequence=protein_sequence,
                            prediction=gene_prediction
                        )
                        genes.append(current_gene)

                    elif feature_type == 'transcript' and current_gene:
                        transcript_id = attributes_dict.get('ID') or f"tx_{random.randint(1000,9999)}"
                        current_transcript = Transcript.objects.create(
                            transcript_id=transcript_id,
                            gene=current_gene
                        )
                        transcripts.append(current_transcript)

                    elif feature_type in ['exon', 'CDS', 'start_codon', 'stop_codon'] and current_transcript:
                        feature = Feature.objects.create(
                            feature_type=feature_type,
                            start=start,
                            end=end,
                            transcript=current_transcript
                        )
                        features.append(feature)

    except Exception as e:
        print(f"Error processing GFF file: {e}")
        return None, None, None

    return genes, transcripts, features


def parse_gff_proteins(gff_path):
    proteins = []
    current = ""
    reading = False

    with open(gff_path, "r") as f:
        for line in f:
            line = line.strip()
            if line.startswith("# protein sequence"):
                reading = True
                current = ""
                line = line.split("=", 1)[1]
                line = line.replace("[", "").replace("]", "").replace(" ", "")
                current += line
                continue

            if reading:
                clean = line.lstrip("#").replace("[", "").replace("]", "").replace(" ", "")
                current += clean
                if "]" in line:
                    proteins.append(current)
                    reading = False

    return proteins

def write_fasta_for_prediction(gene_prediction, output_dir="/home/hamid/blast_db"):
    os.makedirs(output_dir, exist_ok=True)
    fasta_path = os.path.join(output_dir, f"gene_prediction_{gene_prediction.id}.fasta")

    def format_fasta(seq, line_length=60):
        return '\n'.join(seq[i:i+line_length] for i in range(0, len(seq), line_length))

    genes = Gene.objects.filter(prediction=gene_prediction)
    with open(fasta_path, "w") as f:
        for gene in genes:
            if gene.protein_sequence:
                f.write(f">{gene.gene_id}\n")
                f.write(format_fasta(gene.protein_sequence) + "\n")

    return fasta_path

def blastp_local(sequence, db_path=BLAST_DB_DIR, hitlist_size=5):
    with NamedTemporaryFile(mode="w+", suffix=".fa", delete=False) as tmp_fasta:
        tmp_fasta.write(f">query\n{sequence}\n")
        fasta_path = tmp_fasta.name

    cmd = [
        BLAST_BIN,
        "-query", fasta_path,
        "-db", db_path,
        "-outfmt", "15",  # JSON
        "-max_target_seqs", str(hitlist_size)
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    os.remove(fasta_path)

    if result.returncode != 0:
        return {"error": result.stderr}

    raw_json = json.loads(result.stdout)

    # تبدیل به ساختار مشابه NCBI REST API
    hits = []
    for hit_entry in raw_json.get("BlastOutput2", []):
        for report in hit_entry.get("report", {}).get("results", {}).get("search", {}).get("hits", []):
            hit_def = report["description"][0]["title"]
            accession = report["description"][0]["accession"]
            hit_id = report["description"][0]["id"]
            for hsp in report["hsps"]:
                hits.append({
                    "query": sequence[:50],
                    "hit_id": hit_id,
                    "hit_def": hit_def,
                    "accession": accession,
                    "score": hsp.get("score"),
                    "evalue": hsp.get("evalue"),
                    "identity": hsp.get("identity"),
                    "align_length": hsp.get("align_len"),
                    "query_start": hsp.get("query_from"),
                    "query_end": hsp.get("query_to"),
                    "hit_start": hsp.get("hit_from"),
                    "hit_end": hsp.get("hit_to"),
                })
    return hits


def blast_all_genes_for_prediction(gene_prediction, db_path=BLAST_DB_DIR):
    genes = Gene.objects.filter(prediction=gene_prediction)
    results = {}

    for gene in genes:
        if gene.protein_sequence:
            results[gene.gene_id] = blastp_local(
                gene.protein_sequence,
                db_path=db_path
            )

    return results
