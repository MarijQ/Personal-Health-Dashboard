from django.db import models

class UserSteps(models.Model):
    user_id = models.CharField(max_length=255)  # Unique ID to identify each user
    date = models.DateField()  # Date of the steps
    steps = models.IntegerField()  # Number of steps completed

    class Meta:
        unique_together = ('user_id', 'date')  # Enforce uniqueness of (user_id, date)

    def __str__(self):
        return f"{self.user_id} - {self.date}: {self.steps} steps"
