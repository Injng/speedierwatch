from django.urls import path
from . import views

app_name = "study"

urlpatterns = [
    path("", views.home, name="home"),
    path("video/", views.video, name="video"),
    path("quiz/", views.quiz, name="quiz"),
    path("results/", views.results, name="results"),
    path("invalidated/", views.invalidate_participant, name="invalidated"),
    path("leaderboard/", views.leaderboard, name="leaderboard"),
]
