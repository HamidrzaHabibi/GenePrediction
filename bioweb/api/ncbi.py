import requests
from django.conf import settings

API_KEY = settings.NCBI_API_KEY

def fetch_dna_sequence(accession):
    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
    params = {
        "db": "nucleotide",
        "id": accession,
        "rettype": "fasta",
        "retmode": "text",
        "api_key": API_KEY,
    }

    response = requests.get(url, params=params)
    if response.status_code == 200 and response.text:
        return response.text
    else:
        raise ValueError(f"unable to fetch DNA sequence for accession {accession}")
