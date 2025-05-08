from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Participant, QuizResponse, Question
from .forms import ParticipantForm, QuizForm
import random


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


def quiz(request):
    participant_id = request.session.get("participant_id")
    if not participant_id:
        messages.error(request, "Please register first.")
        return redirect("study:home")

    participant = Participant.objects.get(id=participant_id)

    if request.method == "POST":
        form = QuizForm(Question.objects.all(), request.POST)
        if form.is_valid():
            score = 0
            for i, question in enumerate(Question.objects.all()):
                if form.cleaned_data[f"question_{i}"] == question.correct_answer:
                    score += 1

            QuizResponse.objects.create(participant=participant, score=score)
            return redirect("study:results")
    else:
        form = QuizForm(Question.objects.all())

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
