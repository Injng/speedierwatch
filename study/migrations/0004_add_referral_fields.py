from django.db import migrations, models
import uuid


def generate_referral_codes(apps, schema_editor):
    """
    Generate unique referral codes for all existing participants
    """
    Participant = apps.get_model("study", "Participant")
    for participant in Participant.objects.all():
        participant.referral_code = str(uuid.uuid4())
        participant.save()


class Migration(migrations.Migration):
    dependencies = [
        ("study", "0003_quizresponse_raffle_tickets"),
    ]

    operations = [
        # First add fields with blank=True and null=True
        migrations.AddField(
            model_name="participant",
            name="referral_code",
            field=models.CharField(blank=True, max_length=36, null=True),
        ),
        migrations.AddField(
            model_name="participant",
            name="referred_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=models.deletion.SET_NULL,
                related_name="referrals",
                to="study.participant",
            ),
        ),
        # Run data migration to generate referral codes
        migrations.RunPython(generate_referral_codes),
        # Then make referral_code unique and non-nullable
        migrations.AlterField(
            model_name="participant",
            name="referral_code",
            field=models.CharField(blank=True, max_length=36, unique=True),
        ),
    ]
