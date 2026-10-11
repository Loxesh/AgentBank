
from flask import Flask, request, jsonify, render_template
from database import setup_database
from agents.supervisor import handle_request
import math

app = Flask(__name__)

VALID_TASKS = {
    "balance",
    "transactions",
    "spending",
    "customer",
    "risk",
    "loan",
    "chat"
}

DEMO_CUSTOMERS = {"C101", "C102", "C103"}


def error_response(message, status=400):
    return jsonify({
        "success": False,
        "error": message
    }), status


def valid_number(value, minimum=None, maximum=None):
    if isinstance(value, bool):
        return False

    if not isinstance(value, (int, float)):
        return False

    if not math.isfinite(value):
        return False

    if minimum is not None and value < minimum:
        return False

    if maximum is not None and value > maximum:
        return False

    return True


@app.get("/")
def home():
    return render_template("index.html")


@app.get("/api/health")
def health():
    return jsonify({
        "status": "ok",
        "application": "AgentBank",
        "environment": "demo"
    })


@app.post("/api/agent")
def agent_api():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return error_response(
            "Send a valid JSON object in the request body."
        )

    task = data.get("task")

    if not isinstance(task, str) or not task.strip():
        return error_response("A task is required.")

    task = task.strip().lower()
    data["task"] = task

    if task not in VALID_TASKS:
        return error_response(
            "Unknown task. Choose balance, transactions, spending, "
            "customer, risk, loan, or chat."
        )

    if task in {"balance", "transactions", "spending", "customer"}:
        customer_id = data.get("customer_id", "C101")

        if not isinstance(customer_id, str):
            return error_response("Customer ID must be text.")

        if customer_id not in DEMO_CUSTOMERS:
            return error_response(
                "Unknown demo customer. Use C101, C102, or C103."
            )

    elif task == "risk":
        amount = data.get("amount")

        if not valid_number(amount, minimum=0.01):
            return error_response(
                "Transaction amount must be a positive number."
            )

        for key in ("international", "new_device", "late_night"):
            if key in data and not isinstance(data[key], bool):
                return error_response(
                    f"{key} must be true or false."
                )

    elif task == "loan":
        income = data.get("income")
        existing_emi = data.get("existing_emi")
        credit_score = data.get("credit_score")
        amount = data.get("amount")
        months = data.get("months", 36)

        if not valid_number(income, minimum=0.01):
            return error_response(
                "Monthly income must be greater than zero."
            )

        if not valid_number(existing_emi, minimum=0):
            return error_response(
                "Existing EMI must be zero or greater."
            )

        if not valid_number(credit_score, minimum=0, maximum=900):
            return error_response(
                "Credit score must be between 0 and 900."
            )

        if not valid_number(amount, minimum=0.01):
            return error_response(
                "Loan amount must be greater than zero."
            )

        if (
            isinstance(months, bool)
            or not isinstance(months, int)
            or months not in {12, 24, 36, 48, 60}
        ):
            return error_response(
                "Loan duration must be 12, 24, 36, 48, or 60 months."
            )

    elif task == "chat":
        question = data.get("question")

        if not isinstance(question, str) or not question.strip():
            return error_response("Please enter a question.")

        if len(question) > 1000:
            return error_response(
                "Your question must be 1000 characters or fewer."
            )

    try:
        result = handle_request(data)

        if isinstance(result, dict) and "error" in result:
            return jsonify(result), 400

        return jsonify(result), 200

    except Exception:
        app.logger.exception("AgentBank request failed")
        return error_response(
            "An internal error occurred. Check the Flask terminal.",
            500
        )


if __name__ == "__main__":
    setup_database()
    app.run(debug=True)
