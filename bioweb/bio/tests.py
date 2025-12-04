from django.test import TestCase

# Create your tests here.
from Bio import Entrez
import requests


Entrez.email="orangefox044@gmail.com"
Entrez.api_key='1ce277f2d5be98953e742228095a910f9708'





accession = "NC_045512.2"
api_key = "YOUR_API_KEY"
url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

params = {
    "db": "nucleotide",
    "id": accession,
    "rettype": "fasta",  # توالی FASTA
    "retmode": "text",
    "api_key": api_key
}

res = requests.get(url, params=params)
dna_seq = res.text

# ذخیره فایل FASTA
with open("genome.fa", "w") as f:
    f.write(dna_seq)