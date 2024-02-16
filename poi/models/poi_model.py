from django.db import models


class PointOfInterest(models.Model):
    """
    A point of interest with imported coordinates and average rating.

    external_id is the generated primary key; internal_id is the ID from the
    source file, which is not unique because repeat imports append rows.
    """

    external_id = models.AutoField(primary_key=True)
    internal_id = models.CharField(max_length=100)
    name = models.CharField(max_length=255)
    category = models.CharField(max_length=100)
    latitude = models.FloatField()
    longitude = models.FloatField()
    ratings = models.FloatField()

    def __str__(self):
        return f'{self.name} ({self.internal_id})'
