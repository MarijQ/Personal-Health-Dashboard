from django.contrib import admin
from .models import UserSteps, ManualData, UserHR, UserCalories, UserSleep

admin.site.register(UserSteps)
admin.site.register(ManualData)
admin.site.register(UserHR)
admin.site.register(UserCalories)
admin.site.register(UserSleep)
