from django.contrib import admin
from .models import Participant, QuizResponse


@admin.register(Participant)
class ParticipantAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "treatment_group", "created_at")
    list_filter = ("treatment_group",)
    search_fields = ("name", "email")


@admin.register(QuizResponse)
class QuizResponseAdmin(admin.ModelAdmin):
    list_display = ("participant", "score", "submitted_at")
    list_filter = ("score", "submitted_at")
    search_fields = ("participant__name", "participant__email")
