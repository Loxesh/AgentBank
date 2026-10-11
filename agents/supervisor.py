
from agents.banking_agent import handle_banking_query
from agents.risk_agent import handle_risk_query
from agents.loan_agent import handle_loan_query
from agents.llm_agent import ask_banking_assistant


def handle_request(data):
    task = str(data.get("task", "")).lower().strip()

    if task in ("balance", "transactions", "spending", "customer"):
        customer_id = data.get("customer_id", "C101")

        query = {
            "balance": "check balance",
            "transactions": "show transactions",
            "spending": "check spending",
            "customer": "customer details"
        }[task]

        return handle_banking_query(customer_id, query)

    elif task == "risk":
        return handle_risk_query(
            data.get("amount", 0),
            data.get("international", False),
            data.get("new_device", False),
            data.get("late_night", False)
        )

    elif task == "loan":
        return handle_loan_query(
            data.get("income", 0),
            data.get("existing_emi", 0),
            data.get("credit_score", 0),
            data.get("amount", 0),
            data.get("months", 36)
        )

    elif task == "chat":
        question = data.get("question", "")
        return ask_banking_assistant(question)

    return {
        "error": (
            "Unknown task. Try balance, transactions, spending, "
            "customer, risk, loan, or chat."
        )
    }
