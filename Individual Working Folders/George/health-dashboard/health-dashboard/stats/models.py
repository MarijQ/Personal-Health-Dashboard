from django.db import models

# Create your models here.

class BloodPressure(models.Model):
    blood_pressure = models.IntegerField()