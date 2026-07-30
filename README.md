# Overview

A small Flask-based web UI that evaluates supervisor interview transcripts against a performance rubric using a locally-hosted LLM. The frontend is static HTML templates and the backend is Python (Flask). The app calls a local Ollama API (http://localhost:11434/api/generate) to run the model and then parses the model's JSON output into an audit view.

> Important: This project expects Ollama (local LLM runtime) to be running and serving the model referenced in app.py (model name: "llama3.2"). See "Running the LLM (Ollama)" below.

## Table of contents
- [What’s in this repo](#whats-in-this-repo)
- [Prerequisites](#prerequisites)
- [Install & run (quick)](#install--run-quick)
- [Running the LLM (Ollama)](#running-the-llm-ollama)
- [How it works (runtime flow)](#how-it-works-runtime-flow)
- [Key files and structure](#key-files-and-structure)
- [Testing / sample data](#testing--sample-data)
- [Notes & troubleshooting](#notes--troubleshooting)
- [Contributing](#contributing)
- [License](#license)
- [Contact](#contact)

## What’s in this repo
- A Flask web app that accepts a supervisor transcript and other metadata, calls a local LLM, and renders an audit report.
- The app expects the LLM to return a specific flat JSON schema which is parsed and displayed.

## Prerequisites
- Python 3.8+
- pip
- (Recommended) python -m venv .venv
- Ollama installed and able to serve a local model (see below)
- Network access to localhost ports used by Ollama (default 11434) and Flask (default 5000)

## Install & run (quick)
1. Clone:
   git clone https://github.com/sayantanpal9/deepthought.git
   cd deepthought

2. Create & activate a venv (optional but recommended):
   python -m venv .venv
   source .venv/bin/activate   # macOS / Linux
   .\.venv\Scripts\Activate.ps1  # Windows PowerShell

3. Install Python dependencies:
   pip install Flask requests

4. Start Ollama and the model (see next section).

5. Run the Flask app:
   python app.py

6. Open the app:
   http://127.0.0.1:5000/home

## Running the LLM (Ollama)
This project posts generation requests to http://localhost:11434/api/generate. The included code uses:
- model: "llama3.2"
- endpoint: POST http://localhost:11434/api/generate with JSON body { model, prompt, stream, format, ... }

Suggested Ollama workflow (replace model name if you use a different one):

- Install Ollama (see https://ollama.com for the official installer).
- Pull the model you want to use (example):
  ollama pull llama3.2

- Start the Ollama API server:
  ollama serve

  By default, ollama serve exposes the HTTP API at http://localhost:11434.

- Confirm the server is reachable:
  curl -X POST "http://localhost:11434/api/generate" -H "Content-Type: application/json" -d '{"model":"llama3.2","prompt":"hello","stream":false,"format":"text"}'

Notes:
- The code in app.py expects the model to return a JSON under the key "response" (response.json().get('response')) and that the model output contains a JSON object for parsing. If you change the Ollama model or the output format, update app.py accordingly.
- If you use a different model name (e.g., llama3 or a custom local model name), change the 'model' parameter in app.py's requests.post call.

## How it works (runtime flow)
1. User opens /home and fills the form (fellow, company, transcript).
2. Flask handler (/home POST) flattens the context and constructs a prompt that includes rubric.json content.
3. The app sends the prompt to the local Ollama API at /api/generate and requests JSON output.
4. The app extracts the first {...} JSON block from the model text, parses it, applies minimal safety defaults, and renders templates/res.html with the parsed data.

Key modules: app.py (Flask routes + LLM request/response handling), templates/home.html (form), templates/res.html (result view), rubric.json (scoring rubric), sample-transcripts.json (example transcripts).

## Key files and structure
Top-level (most relevant):
- app.py — Flask app, form handling, LLM request to Ollama, JSON extraction and rendering
- rubric.json — The evaluation rubric included in prompts (used by the LLM to produce the structured audit)
- sample-transcripts.json — Example transcripts and expected scoring notes for testing
- templates/
  - home.html — Input form (fellow, company, transcript)
  - res.html — Rendered audit result (score, evidence, KPI mapping, follow-up questions)

