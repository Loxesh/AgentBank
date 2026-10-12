
# AgentBank — Multi-Agent Banking Automation

AgentBank is an educational banking simulation built using Flask, SQLite, specialized agents, and a locally hosted language model.

The application demonstrates how a Supervisor Agent routes requests to Banking, Risk, and Loan Agents, while a web dashboard provides an interface for interacting with the system.

> **Disclaimer:** AgentBank is a demo application using fictional customer data and simulated banking rules. It is not connected to a real bank and does not perform real financial transactions or loan applications.

## Features

- **Multi-agent orchestration:** Routes requests to the appropriate specialist agent.
- **Banking operations:** Retrieves customer profiles, account balances, recent transactions, and spending information.
- **Fraud-risk analysis:** Evaluates simulated transaction risk using transaction amounts and risk indicators.
- **Loan eligibility estimation:** Estimates eligibility based on income, existing EMI, credit score, loan amount, and repayment duration.
- **Local AI assistant:** Uses Ollama with `llama3.2:3b` for general banking questions.
- **Interactive dashboard:** A responsive web interface for selecting customers and using banking features.
- **Input validation:** Validates supported API requests and financial inputs.
- **Unit tests:** Tests key agent operations and Supervisor routing.

## Technology Stack

- Python 3.12
- Flask
- SQLite
- HTML, CSS, and JavaScript
- Ollama
- `llama3.2:3b`
- Python `unittest`

## Project Structure

```text
AgentBank_Flask_Beginner_MVP/
├── agents/
│   ├── __init__.py
│   ├── banking_agent.py
│   ├── llm_agent.py
│   ├── loan_agent.py
│   ├── risk_agent.py
│   └── supervisor.py
├── templates/
│   └── index.html
├── tests/
│   └── test_agents.py
├── app.py
├── banking_tools.py
├── database.py
├── requirements.txt
├── README.md
└── .gitignore
```

The SQLite database is created locally when the application initializes.

## Architecture

1. The dashboard sends requests to the Flask API.
2. The Flask backend validates supported requests.
3. The Supervisor Agent routes each request.
4. The Banking Agent retrieves customer and account information.
5. The Risk Agent evaluates simulated transaction risk.
6. The Loan Agent calculates loan eligibility and repayment metrics.
7. The local Ollama model handles general conversational questions.
8. The backend returns JSON results for display in the dashboard.

## Prerequisites

- Python 3.12 recommended
- Git
- Ollama installed locally
- The `llama3.2:3b` model downloaded through Ollama

## Installation and Setup

### 1. Clone the repository

Replace `YOUR_USERNAME` with your GitHub username.

```bash
git clone https://github.com/YOUR_USERNAME/AgentBank.git
cd AgentBank
```

### 2. Create a virtual environment

Windows PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Install and prepare Ollama

Install Ollama from:

https://ollama.com/download

Download the required model:

```bash
ollama pull llama3.2:3b
```

Ensure Ollama is running locally before using the AI chat feature.

### 5. Run the application

From the project root, with the virtual environment activated:

```bash
python app.py
```

Open this URL in your browser:

http://127.0.0.1:5000

The application initializes its demo database when started directly through `app.py`.

## Demo Customers

The application includes fictional demo customers.

| Customer ID | Customer | Monthly Income | Existing EMI | Credit Score | Balance |
|---|---|---:|---:|---:|---:|
| C101 | Asha Kumar | ₹90,000 | ₹12,000 | 760 | ₹85,000 |
| C102 | Ravi Shah | ₹45,000 | ₹19,000 | 620 | ₹32,000 |
| C103 | Maya Iyer | ₹1,25,000 | ₹18,000 | 720 | ₹1,80,000 |

These values are synthetic and intended only for demonstration.

## API Endpoints

### Health Check

`GET /api/health`

Checks whether the application is responding.

### Dashboard

`GET /`

Serves the AgentBank web interface.

### Agent API

`POST /api/agent`

Accepts JSON requests for supported tasks.

Example balance request:

```json
{
  "task": "balance",
  "customer_id": "C101"
}
```

Example loan eligibility request:

```json
{
  "task": "loan",
  "income": 90000,
  "existing_emi": 12000,
  "credit_score": 760,
  "amount": 500000,
  "months": 36
}
```

Example fraud-risk request:

```json
{
  "task": "risk",
  "amount": 60000,
  "international": true,
  "new_device": true,
  "late_night": false
}
```

Example AI chat request:

```json
{
  "task": "chat",
  "question": "What is my account balance?",
  "customer_id": "C101"
}
```

## Running Tests

From the project root, run:

```bash
python -m unittest discover -s tests -v
```

The existing test suite covers core agent behavior and Supervisor routing.

## Limitations

- Customer records and transactions are fictional.
- Fraud detection uses simplified demonstration rules.
- Loan eligibility is an estimate, not a real bank decision.
- The local language model can produce inaccurate answers to general questions.
- The application does not connect to banking networks or payment systems.
- The application is not intended for real financial decisions or sensitive personal data.

## Future Improvements

- More robust natural-language intent classification.
- Expanded API and integration tests.
- More detailed explanations for loan decisions.
- Improved audit logging and production security.
- Evaluation of fraud-risk and loan-eligibility rules.

## Author

Developed as an educational multi-agent banking architecture demonstration project.
