from django import forms
from .models import Participant
import random


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
        questions_to_display = kwargs.pop("questions_to_display", [])
        super().__init__(*args, **kwargs)
        self.ordered_correct_answers = []

        for i, question_data in enumerate(questions_to_display):
            field_name = f"question_{i}"

            options = [
                ("A", question_data["option_a"]),
                ("B", question_data["option_b"]),
                ("C", question_data["option_c"]),
                ("D", question_data["option_d"]),
            ]
            random.shuffle(options)

            self.fields[field_name] = forms.ChoiceField(
                label=question_data["text"],
                choices=options,
                widget=forms.RadioSelect(attrs={"class": "form-check-input"}),
                required=True,
            )
            self.ordered_correct_answers.append(question_data["correct_answer"])
