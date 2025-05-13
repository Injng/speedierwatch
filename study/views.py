from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Participant, QuizResponse
from .forms import ParticipantForm, QuizForm
from pathlib import Path
import random
import json
from decimal import Decimal


def home(request):
    referral_code = request.GET.get("ref")
    referred_by = None

    if referral_code:
        try:
            referred_by = Participant.objects.get(referral_code=referral_code)
            request.session["referral_code"] = referral_code
        except Participant.DoesNotExist:
            pass

    if request.method == "POST":
        form = ParticipantForm(request.POST)
        if form.is_valid():
            participant = form.save(commit=False)
            participant.treatment_group = random.randint(1, 2)

            # Set referrer if available
            if "referral_code" in request.session:
                try:
                    referring_participant = Participant.objects.get(
                        referral_code=request.session["referral_code"]
                    )
                    participant.referred_by = referring_participant
                except Participant.DoesNotExist:
                    pass

            participant.save()
            request.session["participant_id"] = participant.id
            return redirect("study:video")
    else:
        form = ParticipantForm()

    # Check if there's a referral bonus notification to show
    referred_bonus_earned = None
    if "referred_bonus_earned" in request.session:
        referred_bonus_earned = request.session["referred_bonus_earned"]
        del request.session["referred_bonus_earned"]  # Clear after showing

    context = {
        "form": form,
        "referred_by": referred_by,
        "referred_bonus_earned": referred_bonus_earned,
        "referral_success": True if referred_by else False,
        "referral_source": referred_by.name if referred_by else None,
    }
    return render(request, "study/home.html", context)


def video(request):
    participant_id = request.session.get("participant_id")
    if not participant_id:
        messages.error(request, "Please register first.")
        return redirect("study:home")

    participant = Participant.objects.get(id=participant_id)
    return render(
        request,
        "study/video.html",
        {
            "participant": participant,
            "video_speed": "1" if participant.treatment_group == 1 else "2",
        },
    )


def invalidate_participant(request):
    participant_id = request.session.get("participant_id")
    if participant_id:
        try:
            # Delete all related data
            participant = Participant.objects.get(id=participant_id)
            QuizResponse.objects.filter(participant=participant).delete()
            participant.delete()
        except Participant.DoesNotExist:
            pass
        finally:
            # Clear session
            request.session.flush()

    return render(request, "study/invalidated.html")


def quiz(request):
    participant_id = request.session.get("participant_id")
    if not participant_id:
        messages.error(request, "Please register first.")
        return redirect("study:home")

    participant = Participant.objects.get(id=participant_id)

    json_path = Path(__file__).parent / "data" / "questions.json"
    with open(json_path) as f:
        questions_data = json.load(f)["questions"]

    random.shuffle(questions_data)
    request.session["shuffled_questions"] = questions_data

    if request.method == "POST":
        form = QuizForm(
            request.POST,
            questions_to_display=request.session.get("shuffled_questions", []),
        )
        if form.is_valid():
            score = 0
            shuffled_questions_from_session = request.session.get(
                "shuffled_questions", []
            )

            for i, question_data in enumerate(shuffled_questions_from_session):
                user_answer_key = form.cleaned_data.get(f"question_{i}")

                original_correct_answer_letter = question_data["correct_answer"]

                if user_answer_key == original_correct_answer_letter:
                    score += 1

            # Calculate raffle tickets: 2 times the score (as decimal)
            raffle_tickets = Decimal("2") * score
            QuizResponse.objects.create(
                participant=participant, score=score, raffle_tickets=raffle_tickets
            )
            del request.session["shuffled_questions"]
            return redirect("study:results")
    else:
        form = QuizForm(questions_to_display=questions_data)

    return render(
        request, "study/quiz.html", {"form": form, "participant": participant}
    )


def results(request):
    participant_id = request.session.get("participant_id")
    if not participant_id:
        messages.error(request, "Please register first.")
        return redirect("study:home")

    participant = Participant.objects.get(id=participant_id)
    quiz_response = QuizResponse.objects.get(participant=participant)

    # Check if this completion was through a referral and process cascading rewards
    if participant.referred_by:
        # Apply cascading referral rewards - each level gets 20% of the tickets from their referral
        current_referral = participant.referred_by
        current_bonus = quiz_response.raffle_tickets
        referral_level = 1

        while current_referral and referral_level <= 5:  # Limit to 5 levels deep
            try:
                referring_quiz_response = QuizResponse.objects.get(
                    participant=current_referral
                )
                # Calculate bonus for this level (20% of previous level's tickets)
                level_bonus = current_bonus * Decimal("0.2")

                # Update referrer's tickets
                referring_quiz_response.raffle_tickets += level_bonus
                referring_quiz_response.save()

                # Store info for the direct referrer only
                if referral_level == 1:
                    request.session["referred_bonus_earned"] = str(level_bonus)

                # Set up for next level in the chain
                current_bonus = level_bonus
                current_referral = current_referral.referred_by
                referral_level += 1
            except QuizResponse.DoesNotExist:
                break

    # Generate site URL for referral link
    site_url = request.build_absolute_uri("/").rstrip("/")
    referral_url = f"{site_url}?ref={participant.referral_code}"

    # Check if a referral was used
    referral_success = participant.referred_by is not None
    referral_source = participant.referred_by.name if participant.referred_by else None

    # Ensure referred_bonus_earned is properly formatted for template
    if "referred_bonus_earned" in request.session:
        # Store as string to avoid serialization issues
        if not isinstance(request.session["referred_bonus_earned"], str):
            request.session["referred_bonus_earned"] = str(
                request.session["referred_bonus_earned"]
            )

    return render(
        request,
        "study/results.html",
        {
            "participant": participant,
            "quiz_response": quiz_response,
            "referral_url": referral_url,
            "referral_success": referral_success,
            "referral_source": referral_source,
        },
    )


def leaderboard(request):
    """
    Display a leaderboard of participants and their raffle tickets
    """
    # Get all participants who have completed the quiz
    participants_with_quiz = (
        QuizResponse.objects.select_related("participant")
        .all()
        .order_by("-raffle_tickets")
    )

    # Generate referral URLs for each participant
    site_url = request.build_absolute_uri("/").rstrip("/")
    participants_data = []

    for quiz_response in participants_with_quiz:
        participant = quiz_response.participant
        referral_url = f"{site_url}?ref={participant.referral_code}"

        # Count the number of referrals this participant has made
        referral_count = Participant.objects.filter(referred_by=participant).count()

        participants_data.append(
            {
                "name": participant.name,
                "score": quiz_response.score,
                "tickets": float(
                    quiz_response.raffle_tickets
                ),  # Convert Decimal to float for template
                "referral_url": referral_url,
                "referral_count": referral_count,
            }
        )

    return render(
        request,
        "study/leaderboard.html",
        {
            "participants": participants_data,
            "total_participants": len(participants_data),
            "total_tickets": float(sum(p["tickets"] for p in participants_data)),
        },
    )
