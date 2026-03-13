from django.contrib import admin
from .models import CustomUser, Session, ActionLog

admin.site.register(CustomUser)
admin.site.register(Session)
admin.site.register(ActionLog)