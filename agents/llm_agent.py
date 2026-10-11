
"""Local LLM assistant for the AgentBank demo."""

import json
import urllib.request
import urllib.error
import socket


OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3.2:3b"


def ask_banking_assistant(question):
    """Generate a banking-related answer using local Ollama."""

    question = str(question).strip()

    if not question:
        return {
            "success": False,
            "answer": "Please enter a question."
        }

    prompt = f"""
You are AgentBank Assistant, the AI assistant for a student banking
simulation project.

IMPORTANT RULES:
1. Only describe features that are explicitly listed below.
2. Never invent menus, pages, buttons, services, or application workflows.
3. AgentBank currently supports:
   - Viewing balances for three fictional demo customers.
   - Simulating transaction fraud risk with demo rules.
   - Estimating loan eligibility and monthly EMI using demo rules.
   - Answering general banking questions using this local AI model.
4. AgentBank does NOT support real loan applications, real money transfers,
   real bank accounts, or actual financial approvals.
5. If asked whether someone can apply for a loan through AgentBank,
   explain that the current demo only estimates eligibility; it does not
   submit loan applications.
6. Be honest when you do not know something.
7. Keep answers friendly, accurate, and concise.
8. Do not ask for passwords, PINs, or sensitive banking information.

User question:
{question}

Answer:
"""

    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.2
        }
    }

    req = urllib.request.Request(
        OLLAMA_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as response:
            result = json.loads(response.read().decode("utf-8"))

        answer = result.get("response", "").strip()

        if not answer:
            return {
                "success": False,
                "answer": "The local AI returned an empty response."
            }

        return {
            "success": True,
            "answer": answer,
            "model": MODEL_NAME
        }

    except (urllib.error.URLError, socket.timeout, TimeoutError):
        return {
            "success": False,
            "answer": (
                "Cannot connect to Ollama. Please check that Ollama "
                "is running on this computer."
            )
        }

    except (json.JSONDecodeError, KeyError, ValueError):
        return {
            "success": False,
            "answer": "Could not read the response from the local AI."
        }
