# Local AI Browser Agent

A local browser automation agent that accepts plain English instructions, converts them into a structured plan with a local Ollama model, and executes the plan in a browser using Playwright.

## Project structure

```
project-root/
│── backend/
│   ├── main.py
│   ├── agent.py
│   ├── browser_controller.py
│   ├── llm_interface.py
│   ├── vision_module.py
│   └── utils.py
│
│── frontend/
│   ├── index.html
│   ├── script.js
│   └── styles.css
│
│── requirements.txt
│── README.md
```

## Setup

1. Install Ollama and start the service locally.
2. Pull a model such as `mistral`:

```bash
tool install ollama
ollama pull mistral
```

3. Install Python dependencies:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

4. Install Playwright browser binaries:

```bash
python -m playwright install chromium
```

## Run the backend

From the project root:

```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

## Open the frontend

Open `frontend/index.html` in your browser, or serve it from a local static server.

## How to use

Enter a command such as:

- `Search YouTube for Python tutorials`
- `Go to Amazon and search for headphones`
- `Open Wikipedia and search Artificial Intelligence`

Then click **Run Task**.

## Features

- Natural language task input
- Local Ollama LLM planning
- Async Playwright browser automation
- Optional vision fallback via Ollama vision model
- Logs and recent history shown in UI

## Notes

- Ensure Ollama is running at `http://127.0.0.1:11434`.
- The backend assumes the model name `mistral` by default.
- For vision support, use a compatible Ollama image model such as `llava-mini` and update `backend/vision_module.py` if needed.
