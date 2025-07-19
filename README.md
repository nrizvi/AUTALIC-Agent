# AUTALIC Agent

This project implements a chatbot powered by a local Large Language Model (LLM) using Ollama. The agent is designed to detect anti-autistic hate speech based on the AUTALIC dataset.

The agent, "AUTALIC Agent", was created by Naba Rizvi.

## Features

- **ReAct Agent Architecture**: The agent uses a Reason-Act loop to analyze user input, use tools, and provide a final answer.
- **Local LLM**: Powered by Ollama and the `qwen3:14b` model, running entirely on your local machine.
- **Custom Tool**: A tool to retrieve examples of annotated sentences from the `AUTALIC.csv` dataset.
- **Web Interface**: A user-friendly chat interface with a pink-themed design.

## Project Structure

```
AUTALIC-Agent/
├── AUTALIC.csv
├── agent/
│   ├── __init__.py
│   └── agent.py
├── static/
│   ├── script.js
│   └── style.css
├── templates/
│   └── index.html
├── .env.example
├── main.py
├── README.md
└── requirements.txt
```

## Getting Started

### Prerequisites

- [Python 3.8+](https://www.python.org/downloads/)
- [Ollama](https://ollama.com/)

### 1. Setup Ollama

First, you need to have Ollama installed and running.

**Install Ollama:**

Follow the instructions on the [Ollama website](https://ollama.com/).

**Pull the model:**

This project uses the `qwen3:14b` model, which supports tool calling. You can pull it by running:

```bash
ollama pull qwen3:14b
```

**Run Ollama on a specific port:**

To avoid conflicts with other instances of Ollama, you can run it on a different host and port. Open a new terminal and run the following command. The application will connect to this instance.

```bash
OLLAMA_HOST=127.0.0.1:11435 ollama serve
```

Keep this terminal window open.

### 2. Setup the Project

**Clone the repository and navigate to the project directory:**

*(This step is already done if you are reading this)*

**Create a virtual environment:**

```bash
python3 -m venv venv
source venv/bin/activate
# On Windows, use: venv\Scripts\activate
```

**Install dependencies:**

Make sure you have deactivated any other virtual environments. Then, in the project root, run:

```bash
pip install -r requirements.txt
```

**Configure environment variables:**

Create a `.env` file in the root of the project. You can do this by running `touch .env` in your terminal.

Then, open the `.env` file and add the following line:

```
OLLAMA_HOST=127.0.0.1:11435
```

This should match the host and port where you are running the `ollama serve` command.

### 3. Run the Application

Start the FastAPI server:

```bash
uvicorn main:app --reload
```

Open your web browser and navigate to [http://127.0.0.1:8000](http://127.0.0.1:8000).

You can now start chatting with the AUTALIC Agent! 