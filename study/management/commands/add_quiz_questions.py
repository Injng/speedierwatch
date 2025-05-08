from django.core.management.base import BaseCommand
from study.models import Question


class Command(BaseCommand):
    help = "Adds the quiz questions for the Chrono-Mapping study"

    def handle(self, *args, **kwargs):
        questions = [
            {
                "text": 'What is "Chrono-Mapping" described as?',
                "correct_answer": "B",
                "option_a": "A method for predicting future geographical changes.",
                "option_b": "A theoretical cartographic technique from the late 19th century.",
                "option_c": "A way to measure the physical distance between historical events.",
                "option_d": "A system for navigating using star charts and temporal anomalies.",
            },
            {
                "text": "According to Professor Eldrin Kai, what do geographical locations possess in addition to spatial coordinates?",
                "correct_answer": "C",
                "option_a": "Magnetic field variations",
                "option_b": "Unique atmospheric pressures",
                "option_c": "Temporal resonance signatures",
                "option_d": "Undiscovered elemental compositions",
            },
            {
                "text": 'What is the primary purpose of the "Resonance Inductor" in Chrono-Mapping?',
                "correct_answer": "B",
                "option_a": "To generate energy for historical reenactments.",
                "option_b": "To detect and chart temporal signatures.",
                "option_c": "To alter the flow of time in a localized area.",
                "option_d": "To communicate with past civilizations.",
            },
            {
                "text": 'What do "temporal resonance signatures" represent according to Kai\'s manuscripts?',
                "correct_answer": "C",
                "option_a": "The sounds of past events.",
                "option_b": "The collective memories of people who lived in a location.",
                "option_c": "Subtle energy imprints from significant historical events or prolonged human activity.",
                "option_d": "Echoes of future possibilities for a specific area.",
            },
            {
                "text": "How was the Resonance Inductor theorized to operate?",
                "correct_answer": "C",
                "option_a": "Using steam power and intricate clockwork mechanisms.",
                "option_b": "By harnessing solar energy and reflecting it onto geographical charts.",
                "option_c": "Through a combination of finely tuned crystalline structures and minute electrical currents.",
                "option_d": "By analyzing the gravitational pull of celestial bodies on specific locations.",
            },
            {
                "text": "Where were the specialized crystals for the Resonance Inductor supposedly sourced from?",
                "correct_answer": "B",
                "option_a": "The Amazon rainforest",
                "option_b": "A unique geological formation in the Ural Mountains",
                "option_c": "Deep-sea volcanic vents",
                "option_d": "Meteorite impact craters in Antarctica",
            },
            {
                "text": "How did the Resonance Inductor visually represent temporal signatures?",
                "correct_answer": "D",
                "option_a": "As a written report detailing historical data.",
                "option_b": "Through a series of audible tones and frequencies.",
                "option_c": "As a holographic projection of past events.",
                "option_d": "As a series of concentric, color-coded rings on a map.",
            },
            {
                "text": "In the visual representation of Chrono-Mapping, what would vibrant, tight rings indicate?",
                "correct_answer": "C",
                "option_a": "A very old and weak temporal resonance.",
                "option_b": "An event of minor historical significance.",
                "option_c": "A powerful, more recent event.",
                "option_d": "An area with no detectable temporal resonance.",
            },
            {
                "text": "What characteristic of the color-coded rings would suggest an older, less impactful temporal occurrence?",
                "correct_answer": "C",
                "option_a": "Dark, narrow rings",
                "option_b": "Bright, pulsating rings",
                "option_c": "Fainter, wider rings",
                "option_d": "Spiraling, multi-colored rings",
            },
            {
                "text": "What was believed to cause the crystals in the Resonance Inductor to vibrate?",
                "correct_answer": "B",
                "option_a": "Changes in atmospheric temperature.",
                "option_b": "Exposure to residual temporal energies.",
                "option_c": "The Earth's magnetic field.",
                "option_d": "Direct physical contact with historical artifacts.",
            },
        ]

        # Clear existing questions
        Question.objects.all().delete()

        # Add new questions
        for q in questions:
            Question.objects.create(**q)

        self.stdout.write(self.style.SUCCESS("Successfully added quiz questions"))
