from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid

# Create your models here.


class Participant(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    created_at = models.DateTimeField(auto_now_add=True)
    treatment_group = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(2)],
        help_text="1 for 1x speed, 2 for 2x speed",
    )
    referral_code = models.CharField(max_length=36, unique=True, blank=True)
    referred_by = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="referrals",
    )

    def save(self, *args, **kwargs):
        if not self.referral_code:
            self.referral_code = str(uuid.uuid4())
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} - Group {self.treatment_group}"


class QuizResponse(models.Model):
    participant = models.OneToOneField(Participant, on_delete=models.CASCADE)
    score = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        help_text="Score out of 10",
    )
    raffle_tickets = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Number of raffle tickets earned based on score and referrals",
    )
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.participant.name}'s Quiz - Score: {self.score}/10, Tickets: {self.raffle_tickets:.2f}"
