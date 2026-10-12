
import re
import math

from agents.banking_agent import handle_banking_query
from agents.risk_agent import handle_risk_query
from agents.loan_agent import handle_loan_query
from agents.llm_agent import ask_banking_assistant


DEMO_CUSTOMERS = {"C101", "C102", "C103"}
DEFAULT_LOAN_AMOUNT = 500000
DEFAULT_LOAN_MONTHS = 36
VALID_LOAN_MONTHS = {12, 24, 36, 48, 60}


def get_customer_id(data):
    customer_id = data.get("customer_id", "C101")

    if not isinstance(customer_id, str):
        return None

    customer_id = customer_id.strip().upper()
    return customer_id if customer_id in DEMO_CUSTOMERS else None


def get_customer_profile(customer_id):
    result = handle_banking_query(customer_id, "customer details")
    profile = result.get("data", {})
    return profile if isinstance(profile, dict) else {}


def format_money(value):
    try:
        return f"₹{float(value):,.2f}"
    except (TypeError, ValueError):
        return "Unavailable"


def extract_amount(question):
    """Extract explicit amounts such as ₹500000, 5 lakh, or 3.5 lakhs."""
    question = question.lower().replace(",", "")

    match = re.search(
        r"(?:₹|rs\.?\s*)?\s*(\d+(?:\.\d+)?)\s*"
        r"(crores?|cr|lakhs?|lacs?|lakh|lac)\b",
        question
    )

    if match:
        value = float(match.group(1))
        unit = match.group(2)

        if unit.startswith("cr") or unit.startswith("crore"):
            return value * 10000000

        return value * 100000

    match = re.search(
        r"(?:₹|rs\.?\s*)\s*(\d+(?:\.\d+)?)",
        question
    )

    if match:
        return float(match.group(1))

    return None


def extract_loan_months(question):
    match = re.search(
        r"\b(12|24|36|48|60)\s*(?:months?|mos?)\b",
        question.lower()
    )
    return int(match.group(1)) if match else None


def valid_number(value, minimum=None, maximum=None):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False

    if not math.isfinite(value):
        return False

    if minimum is not None and value < minimum:
        return False

    if maximum is not None and value > maximum:
        return False

    return True


def is_balance_question(question):
    patterns = [
        r"\baccount balance\b",
        r"\bmy balance\b",
        r"\bcurrent balance\b",
        r"\bavailable balance\b",
        r"\bcheck balance\b",
        r"\bshow balance\b",
        r"\bhow much money\b.*\b(?:have|left)\b",
        r"\bbalance of (?:my )?account\b",
    ]
    return any(re.search(pattern, question) for pattern in patterns)


def is_transaction_question(question):
    return any(term in question for term in (
        "transaction", "transactions", "recent payment",
        "recent payments", "payment history", "transaction history"
    ))


def is_spending_question(question):
    return any(term in question for term in (
        "spending", "spent this month", "monthly expenses",
        "monthly spending", "expenses", "how much did i spend"
    ))


def is_customer_question(question):
    return any(term in question for term in (
        "my profile", "my details", "customer details",
        "my income", "my credit score", "my existing emi",
        "my financial details"
    ))


def is_loan_question(question):
    return any(term in question for term in (
        "loan", "eligible", "eligibility", "emi", "borrow",
        "borrowed", "not approved", "not eligible",
        "why rejected", "why was i rejected", "why not approved",
        "why can't i get", "why cant i get",
        "why can't i apply", "why cant i apply"
    ))


def is_risk_question(question):
    return any(term in question for term in (
        "fraud", "risk score", "risk level", "suspicious transaction",
        "transaction risk", "fraud detection", "fraud score",
        "transaction safe"
    ))


def answer_balance(customer_id):
    result = handle_banking_query(customer_id, "check balance")
    account = result.get("data", {})

    if not isinstance(account, dict) or account.get("balance") is None:
        return {
            "success": False,
            "agent": "Banking Agent",
            "answer": "I couldn't retrieve the account balance."
        }

    balance = account["balance"]

    return {
        "success": True,
        "agent": "Banking Agent",
        "customer_id": customer_id,
        "balance": balance,
        "answer": (
            f"The current demo balance for {customer_id} is "
            f"{format_money(balance)}."
        )
    }


def answer_loan_question(customer_id, question, request_data):
    """
    Use current dashboard inputs when supplied.
    Otherwise fall back to the selected customer's stored profile.
    Both dashboard and chat use handle_loan_query for the decision.
    """
    profile = get_customer_profile(customer_id)

    # Current form values take priority over stored profile values.
    income = request_data.get("income", profile.get("income"))
    existing_emi = request_data.get(
        "existing_emi", profile.get("existing_emi")
    )
    credit_score = request_data.get(
        "credit_score",
        profile.get("credit_score", profile.get("score"))
    )

    if not valid_number(income, minimum=0.01):
        return {
            "success": False,
            "agent": "Loan Agent",
            "answer": "Please enter a valid monthly income in the loan checker."
        }

    if not valid_number(existing_emi, minimum=0):
        return {
            "success": False,
            "agent": "Loan Agent",
            "answer": "Please enter a valid existing monthly EMI."
        }

    if not valid_number(credit_score, minimum=0, maximum=900):
        return {
            "success": False,
            "agent": "Loan Agent",
            "answer": "Please enter a valid credit score between 0 and 900."
        }

    # Explicit chat amount overrides the dashboard amount.
    amount = extract_amount(question)
    if amount is None:
        amount = request_data.get("loan_amount", DEFAULT_LOAN_AMOUNT)

    months = extract_loan_months(question)
    if months is None:
        months = request_data.get("loan_months", DEFAULT_LOAN_MONTHS)

    if (
        not valid_number(amount, minimum=0.01, maximum=100000000)
        or isinstance(months, bool)
        or not isinstance(months, int)
        or months not in VALID_LOAN_MONTHS
    ):
        return {
            "success": False,
            "agent": "Loan Agent",
            "answer": (
                "Please enter a valid loan amount and choose "
                "12, 24, 36, 48, or 60 months."
            )
        }

    result = handle_loan_query(
        income,
        existing_emi,
        credit_score,
        amount,
        months
    )

    eligible = result.get("eligible")
    if not isinstance(eligible, bool):
        return {
            "success": False,
            "agent": "Loan Agent",
            "answer": "The Loan Agent did not return a valid eligibility decision.",
            "data": result
        }

    estimated_emi = result.get("estimated_emi")
    debt_ratio = result.get("debt_ratio_percent")
    reason = result.get("reason", "")

    decision = "ELIGIBLE" if eligible else "NOT ELIGIBLE"

    answer = (
        f"Loan assessment for demo customer {customer_id}: {decision}. "
        f"Requested amount: {format_money(amount)} over {months} months. "
        f"Monthly income: {format_money(income)}. "
        f"Existing monthly EMI: {format_money(existing_emi)}. "
        f"Credit score: {credit_score}. "
    )

    if estimated_emi is not None:
        answer += f"Estimated new monthly EMI: {format_money(estimated_emi)}. "

    if debt_ratio is not None:
        answer += f"Total EMI-to-income ratio: {debt_ratio}%. "

    if reason:
        answer += f"Reason from the Loan Agent: {reason}. "

    answer += (
        "This is a simulated result from the project's demo rules, "
        "not an actual bank approval or rejection."
    )

    return {
        "success": True,
        "agent": "Loan Agent",
        "customer_id": customer_id,
        "eligible": eligible,
        "income": income,
        "existing_emi": existing_emi,
        "credit_score": credit_score,
        "loan_amount": amount,
        "months": months,
        "estimated_emi": estimated_emi,
        "debt_ratio_percent": debt_ratio,
        "reason": reason,
        "answer": answer
    }


def answer_risk_question(question):
    amount = extract_amount(question)

    if amount is None:
        return {
            "success": False,
            "agent": "Risk Agent",
            "answer": (
                "Fraud risk is calculated for a particular transaction. "
                "Include an amount, for example: 'Check fraud risk for "
                "₹60,000 on an international transaction using a new device.'"
            )
        }

    international = any(term in question for term in (
        "international", "overseas", "foreign transaction"
    ))
    new_device = any(term in question for term in (
        "new device", "unknown device", "unrecognized device",
        "unrecognised device"
    ))
    late_night = any(term in question for term in (
        "late night", "midnight", "unusual time"
    ))

    result = handle_risk_query(
        amount, international, new_device, late_night
    )

    risk_level = result.get("risk_level", "UNKNOWN")
    risk_score = result.get("risk_score")
    reasons = result.get("reasons", [])

    answer = (
        f"The Risk Agent assessed a demo transaction of {format_money(amount)}. "
        f"Risk level: {risk_level}. "
    )

    if risk_score is not None:
        answer += f"Risk score: {risk_score}/100. "

    if reasons:
        answer += "Factors: " + "; ".join(map(str, reasons)) + ". "

    answer += "This is transaction-specific, not a permanent customer fraud score."

    return {
        "success": True,
        "agent": "Risk Agent",
        "risk_level": risk_level,
        "risk_score": risk_score,
        "data": result,
        "answer": answer
    }


def handle_chat(data):
    question = data.get("question", "")

    if not isinstance(question, str) or not question.strip():
        return {"success": False, "answer": "Please enter a question."}

    question = question.strip()
    normalized = question.lower()
    customer_id = get_customer_id(data)

    if customer_id is None:
        return {
            "success": False,
            "answer": "Unknown demo customer. Select C101, C102, or C103."
        }

    if is_balance_question(normalized):
        return answer_balance(customer_id)

    if is_loan_question(normalized):
        return answer_loan_question(customer_id, normalized, data)

    if is_risk_question(normalized):
        return answer_risk_question(normalized)

    if is_transaction_question(normalized):
        result = handle_banking_query(customer_id, "show transactions")
        return {
            "success": True,
            "agent": "Banking Agent",
            "customer_id": customer_id,
            "data": result.get("data", {}),
            "answer": f"I retrieved the available transaction records for {customer_id}."
        }

    if is_spending_question(normalized):
        result = handle_banking_query(customer_id, "check spending")
        return {
            "success": True,
            "agent": "Banking Agent",
            "customer_id": customer_id,
            "data": result.get("data", {}),
            "answer": f"I retrieved the available spending information for {customer_id}."
        }

    if is_customer_question(normalized):
        profile = get_customer_profile(customer_id)
        return {
            "success": bool(profile),
            "agent": "Banking Agent",
            "customer_id": customer_id,
            "data": profile,
            "answer": (
                f"I retrieved the financial profile for {customer_id}."
                if profile else "I couldn't retrieve this customer's profile."
            )
        }

    result = ask_banking_assistant(question)

    if isinstance(result, dict):
        result.setdefault("agent", "Local AI Assistant")
        return result

    return {
        "success": True,
        "agent": "Local AI Assistant",
        "answer": str(result)
    }


def handle_request(data):
    task = str(data.get("task", "")).lower().strip()

    if task in ("balance", "transactions", "spending", "customer"):
        customer_id = get_customer_id(data)

        if customer_id is None:
            return {"error": "Unknown demo customer. Use C101, C102, or C103."}

        query = {
            "balance": "check balance",
            "transactions": "show transactions",
            "spending": "check spending",
            "customer": "customer details"
        }[task]

        return handle_banking_query(customer_id, query)

    if task == "risk":
        return handle_risk_query(
            data.get("amount", 0),
            data.get("international", False),
            data.get("new_device", False),
            data.get("late_night", False)
        )

    if task == "loan":
        return handle_loan_query(
            data.get("income", 0),
            data.get("existing_emi", 0),
            data.get("credit_score", 0),
            data.get("amount", 0),
            data.get("months", 36)
        )

    if task == "chat":
        return handle_chat(data)

    return {
        "error": (
            "Unknown task. Try balance, transactions, spending, "
            "customer, risk, loan, or chat."
        )
    }
