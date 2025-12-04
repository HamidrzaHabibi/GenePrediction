from django.contrib import admin
from .models import User,GenePrediction,Chromosome,Species


# Register your models here.
admin.site.register(GenePrediction)
admin.site.register(Species)
admin.site.register(Chromosome)
