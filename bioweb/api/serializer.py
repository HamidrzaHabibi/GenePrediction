from rest_framework import serializers 
from bio.models import GenePrediction
from django.contrib.auth.models import User
from bio.models import GenePrediction, Gene, Transcript, Feature

class FeatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feature
        fields = ['feature_type', 'start', 'end']


class TranscriptSerializer(serializers.ModelSerializer):
    features = FeatureSerializer(many=True, read_only=True)

    class Meta:
        model = Transcript
        fields = ['transcript_id', 'features']


class GeneSerializer(serializers.ModelSerializer):
    transcripts = TranscriptSerializer(many=True, read_only=True)

    class Meta:
        model = Gene
        fields = ['gene_id', 'start', 'end', 'transcripts','protein_sequence']


class GenePredictionSerializer(serializers.ModelSerializer):
    genes = GeneSerializer(many=True, read_only=True)

    class Meta:
        model = GenePrediction
        fields = ['name', 'description', 'status', 'genes', 'result', 'created_at']

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model=User
        fields= "__all__"
        
        

