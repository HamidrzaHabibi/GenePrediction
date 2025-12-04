from django.db import models
import uuid
from django.contrib.auth.models import User


class GenePrediction(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="gene_predictions")
    name = models.CharField(max_length=200, blank=True)
    description = models.TextField(max_length=5000, blank=True, null=True)
    status = models.CharField(max_length=50, default="pending")
    result = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    def __str__(self):
        return self.name


class Gene(models.Model):
    gene_id = models.CharField(max_length=100, unique=True)
    start = models.IntegerField()
    end = models.IntegerField()
    protein_sequence = models.TextField(null=True, blank=True)  
    prediction = models.ForeignKey(GenePrediction, related_name="genes", on_delete=models.CASCADE)

    def __str__(self):
        return self.gene_id


class Transcript(models.Model):
    transcript_id = models.CharField(max_length=100, unique=True)
    gene = models.ForeignKey(Gene, related_name="transcripts", on_delete=models.CASCADE)

    def __str__(self):
        return self.transcript_id


class Feature(models.Model):
    feature_type = models.CharField(max_length=50)
    start = models.IntegerField()
    end = models.IntegerField()
    transcript = models.ForeignKey(Transcript, related_name="features", on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.feature_type} - {self.start}-{self.end}"



class Species(models.Model):
    name = models.CharField(max_length=100)        
    code = models.CharField(max_length=100)        
    genome_version = models.CharField(max_length=50) 

    def __str__(self):
        return f"{self.name} ({self.genome_version})"


class Chromosome(models.Model):
    species = models.ForeignKey(Species, on_delete=models.CASCADE, related_name="chromosomes")
    name = models.CharField(max_length=50)     
    fasta_path = models.CharField(max_length=255)  
    class Meta:
        unique_together = ("species", "name")

    def __str__(self):
        return f"{self.species.code} chr{self.name}"                                                                