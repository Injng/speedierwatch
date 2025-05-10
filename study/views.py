from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Participant, QuizResponse
from .forms import ParticipantForm, QuizForm
import random
import json
import os
from pathlib import Path
from django.conf import settings


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

    if request.method == "POST":
        form = QuizForm(request.POST)
        if form.is_valid():
            # Load questions from JSON
            json_path = Path(__file__).parent / "data" / "questions.json"
            with open(json_path) as f:
                questions_data = json.load(f)
            
            # Calculate score
            score = 0
            for i, question in enumerate(questions_data["questions"]):
                if form.cleaned_data[f"question_{i}"] == question["correct_answer"]:
                    score += 1

            QuizResponse.objects.create(participant=participant, score=score)
            return redirect("study:results")
    else:
        form = QuizForm()

    return render(request, "study/quiz.html", {"form": form})


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
