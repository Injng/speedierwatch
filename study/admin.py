from django.contrib import admin
from .models import Participant, QuizResponse, Question

@admin.register(Participant)
class ParticipantAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'treatment_group', 'created_at')
    list_filter = ('treatment_group', 'created_at')
    search_fields = ('name', 'email')

@admin.register(QuizResponse)
class QuizResponseAdmin(admin.ModelAdmin):
    list_display = ('participant', 'score', 'submitted_at')
    list_filter = ('score', 'submitted_at')
    search_fields = ('participant__name', 'participant__email')

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text', 'correct_answer')
    search_fields = ('text',)
