from django.db import migrations
from study.migrations.operations.update_raffle_tickets import (
    update_raffle_tickets,
    reverse_update_raffle_tickets,
)


class Migration(migrations.Migration):
    dependencies = [
        ("study", "0004_add_referral_fields"),
    ]

    operations = [
        migrations.RunPython(update_raffle_tickets, reverse_update_raffle_tickets),
    ]
