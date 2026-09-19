from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import SchoolEmailVerificationCode, SchoolVerification, User

admin.site.register(User, UserAdmin)
admin.site.register(SchoolVerification)
admin.site.register(SchoolEmailVerificationCode)