from django.contrib import admin
from .models import UserRegistrationModel, PredictionHistory


# =========================
# USER REGISTRATION ADMIN
# =========================
@admin.register(UserRegistrationModel)
class UserRegistrationAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'loginid',
        'mobile',
        'email',
        'city',
        'state',
        'status',
    )
    search_fields = ('name', 'loginid', 'email', 'mobile', 'city', 'state')
    list_filter = ('status', 'state', 'city')


# =========================
# PREDICTION HISTORY ADMIN
# =========================
@admin.register(PredictionHistory)
class PredictionHistoryAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'loginid',
        'username',
        'predicted_class',
        'confidence',
        'source',
        'created_at',
    )
    search_fields = ('loginid', 'username', 'predicted_class', 'source')
    list_filter = ('predicted_class', 'source', 'created_at')
    readonly_fields = ('created_at',)