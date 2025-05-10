from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Participant, QuizResponse
from .forms import ParticipantForm, QuizForm
from pathlib import Path
import random
import json


def home(request):
    if request.method == "POST":
        form = ParticipantForm(request.POST)
        if form.is_valid():
            participant = form.save(commit=False)
            participant.treatment_group = random.randint(1, 2)
            participant.save()
            request.session["participant_id"] = participant.id
            return redirect("study:video")
    else:
        form = ParticipantForm()
    return render(request, "study/home.html", {"form": form})


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

            QuizResponse.objects.create(participant=participant, score=score)
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

    return render(
        request,
        "study/results.html",
        {"participant": participant, "quiz_response": quiz_response},
    )
