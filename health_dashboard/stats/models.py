from django.db import models

class UserSteps(models.Model):
    user_id = models.CharField(max_length=255)  # Unique ID to identify each user
    date = models.DateField()  # Date of the steps
    steps = models.IntegerField()  # Number of steps completed

    class Meta:
        unique_together = ('user_id', 'date')  # Enforce uniqueness of (user_id, date)

    def __str__(self):
        return f"{self.user_id} - {self.date}: {self.steps} steps"


class ManualData(models.Model):
    """
    Stores manual entries in a table named 'manual' (via Meta.db_table).
    Columns: date, metric, value.
    """
    date = models.DateField()
    metric = models.CharField(max_length=100)
    value = models.FloatField()

    class Meta:
        db_table = 'manual'  # ensure the actual table name is 'manual'

    def __str__(self):
        return f"{self.date} | {self.metric} | {self.value}"


class UserHR(models.Model):
    """
    Stores average daily heart rate values fetched from Google Fit.
    """
    user_id = models.CharField(max_length=255)
    date = models.DateField()
    average_hr = models.FloatField()  # Store average heart rate

    class Meta:
        unique_together = ('user_id', 'date')

    def __str__(self):
        return f"{self.user_id} - {self.date}: {self.average_hr} bpm"


class UserCalories(models.Model):
    """
    Stores total daily calories expended fetched from Google Fit.
    """
    user_id = models.CharField(max_length=255)
    date = models.DateField()
    calories = models.FloatField()  # Store total daily calories expended

    class Meta:
        unique_together = ('user_id', 'date')

    def __str__(self):
        return f"{self.user_id} - {self.date}: {self.calories} kcal"


class UserSleep(models.Model):
    """
    Stores total daily sleep (in minutes) fetched from Google Fit.
    """
    user_id = models.CharField(max_length=255)
    date = models.DateField()
    sleep_minutes = models.IntegerField()  # Store total minutes slept in a day

    class Meta:
        unique_together = ('user_id', 'date')

    def __str__(self):
        return f"{self.user_id} - {self.date}: {self.sleep_minutes} min slept"
