from django import forms
from .models import Participant
import json
from pathlib import Path


class ParticipantForm(forms.ModelForm):
    class Meta:
        model = Participant
        fields = ["name", "email"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
        }


class QuizForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Load questions from JSON file
        json_path = Path(__file__).parent / "data" / "questions.json"
        with open(json_path) as f:
            questions_data = json.load(f)

        # Create form fields for each question
        for i, question in enumerate(questions_data["questions"]):
            self.fields[f"question_{i}"] = forms.ChoiceField(
                label=question["text"],
                choices=[
                    ("A", question["option_a"]),
                    ("B", question["option_b"]),
                    ("C", question["option_c"]),
                    ("D", question["option_d"]),
                ],
                widget=forms.RadioSelect(attrs={"class": "form-check-input"}),
            )
