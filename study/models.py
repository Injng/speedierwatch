from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

# Create your models here.


class Participant(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    created_at = models.DateTimeField(auto_now_add=True)
    treatment_group = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(2)],
        help_text="1 for 1x speed, 2 for 2x speed",
    )

    def __str__(self):
        return f"{self.name} - Group {self.treatment_group}"


class QuizResponse(models.Model):
    participant = models.OneToOneField(Participant, on_delete=models.CASCADE)
    score = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        help_text="Score out of 10",
    )
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.participant.name}'s Quiz - Score: {self.score}/10"


class Question(models.Model):
    text = models.TextField()
    correct_answer = models.CharField(max_length=200)
    option_a = models.CharField(max_length=200)
    option_b = models.CharField(max_length=200)
    option_c = models.CharField(max_length=200)
    option_d = models.CharField(max_length=200)

    def __str__(self):
        return self.text[:50] + "..."
