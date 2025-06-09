from django.contrib import admin
from .models import SiteUser, MoodleUser, UserMoodleLink

# Register your models here.
admin.site.register(SiteUser)
admin.site.register(MoodleUser)
admin.site.register(UserMoodleLink)