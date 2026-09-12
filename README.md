# 🎬 Movie Review Analyzer

A movie-review sentiment analyzer built with Python, NLTK VADER, movie-specific sentiment rules, and Gradio.

## Features

- Overall movie rating out of 10
- Positive / Mixed / Negative verdict
- Watch recommendation
- Seven movie aspects:
  - Acting
  - Story
  - Direction
  - Pacing
  - Music
  - Cinematography
  - Climax
- Automatic review summary
- Simple Gradio interface
- No external AI API required

## Run locally

```bash
pip install -r requirements.txt
python app.py
```

The application will provide a local Gradio URL.

## Technology

- Python
- NLTK VADER
- Rule-based movie aspect analysis
- Gradio

## Project Status

The analyzer was developed and tested in Google Colab before being packaged as a standalone Gradio application.
