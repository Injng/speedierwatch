def update_raffle_tickets(apps, schema_editor):
    """
    Update raffle tickets for existing entries to be 2 times their score
    """
    QuizResponse = apps.get_model("study", "QuizResponse")

    # Get all existing quiz responses
    for response in QuizResponse.objects.all():
        # Update raffle tickets to be 2 times the score
        response.raffle_tickets = 2 * response.score
        response.save()


def reverse_update_raffle_tickets(apps, schema_editor):
    """
    Reverse operation - revert to original raffle tickets (which was 2^score)
    """
    QuizResponse = apps.get_model("study", "QuizResponse")

    # Get all existing quiz responses
    for response in QuizResponse.objects.all():
        # Revert to original formula (2^score)
        response.raffle_tickets = 2**response.score if response.score > 0 else 0
        response.save()
