# SpeedWatcher - Educational Video Study

This is a Django-based web application for conducting a study on the impact of video playback speed on learning outcomes.

## Setup

1. Install uv:
```bash
pip install uv
```

2. Create and activate a virtual environment:
```bash
uv venv
source .venv/bin/activate  # On Linux/Mac
# or
.venv\Scripts\activate  # On Windows
```

3. Install dependencies:
```bash
uv pip install -r requirements.txt
```

4. Run migrations:
```bash
python manage.py migrate
```

5. Create a superuser (optional):
```bash
python manage.py createsuperuser
```

6. Run the development server:
```bash
python manage.py runserver
```

## Features

- Random assignment of participants to 1x or 2x video speed groups
- Educational video playback with controlled speed
- Multiple-choice quiz assessment
- Data collection and analysis capabilities
- Admin interface for managing participants and results

## Project Structure

- `speedwatcher/` - Main project directory
- `study/` - Main application for the study
- `templates/` - HTML templates
- `static/` - Static files (CSS, JS, images)
- `media/` - User-uploaded files (videos) 