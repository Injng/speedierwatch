from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    path('', views.statistics_view, name='statistics'),
]
