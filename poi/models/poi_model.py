'''
This file contains the models for point of Interest Data
'''
from django.db import models


class PointOfInterest(models.Model):
    '''
    Model hold the data entries for point of sale
    '''
    external_id = models.AutoField(primary_key=True)
    internal_id = models.CharField(max_length=100)
    name = models.CharField(max_length=255)
    category = models.CharField(max_length=100)
    latitude = models.FloatField()
    longitude = models.FloatField()
    ratings = models.FloatField()
