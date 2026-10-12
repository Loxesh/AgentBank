
"""Supervisor Agent for the AgentBank demo."""

import math
import re

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
    profile = result.get("data", {}) if isinstance(result, dict) else {}
    return profile if isinstance(profile, dict) else {}


def format_money(value):
    try:
        return f"₹{float(value):,.2f}"
    except (TypeError, ValueError):
        return "Unavailable"


def extract_amount(question):
    """Extract amounts such as ₹500000, Rs. 500000, or 5 lakh."""
    question = question.lower().replace(",", "")

    match = re.search(
        r"(?:₹|rs\.?\s*)?\s*(\d+(?:\.\d+)?)\s*"
        r"(crores?|cr|lakhs?|lacs?|lakh|lac)\b",
        question,
    )

    if match:
        value = float(match.group(1))
        unit = match.group(2)

        if unit.startswith("cr"):
            return value * 10_000_000

        return value * 100_000

    match = re.search(
        r"(?:₹|rs\.?\s*)\s*(\d+(?:\.\d+)?)",
        question,
    )

    if match:
        return float(match.group(1))

    return None


def extract_loan_months(question):
    match = re.search(
        r"\b(12|24|36|48|60)\s*(?:months?|mos?)\b",
        question.lower(),
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
    patterns = (
        r"\baccount balance\b",
        r"\bmy balance\b",
        r"\bcurrent balance\b",
        r"\bavailable balance\b",
        r"\bcheck balance\b",
        r"\bshow balance\b",
        r"\bbalance of (?:my )?account\b",
        r"\bhow much money do i have\b",
        r"\bhow much money is left\b",
    )

    return any(re.search(pattern, question) for pattern in patterns)


def is_transaction_question(question):
    terms = (
        "transaction",
        "transactions",
        "recent payment",
        "recent payments",
        "payment history",
        "transaction history",
        "latest payment",
        "last payment",
        "highest amount",
        "largest transaction",
        "biggest transaction",
        "lowest amount",
        "smallest transaction",
        "average transaction",
        "average amount",
        "highest transaction",
        "lowest transaction",
        "most expensive transaction",
        "least expensive transaction",
        "last five",
        "last 5",
        "previous transaction",
        "latest debit",
        "latest credit",
        "last debit",
        "last credit",
    )

    return any(term in question for term in terms)


def is_spending_question(question):
    return any(
        term in question
        for term in (
            "spending",
            "spent this month",
            "monthly expenses",
            "monthly spending",
            "expenses",
            "how much did i spend",
            "total spending",
            "total spent",
        )
    )


def is_customer_question(question):
    return any(
        term in question
        for term in (
            "my profile",
            "my details",
            "customer details",
            "my income",
            "my credit score",
            "my existing emi",
            "my financial details",
        )
    )


def is_loan_calculation_question(question):
    """Detect direct loan calculations, not general loan explanations."""
    direct_requests = (
        "am i eligible",
        "am i eligible for",
        "check my loan",
        "check loan eligibility",
        "check my eligibility",
        "calculate my emi",
        "calculate emi",
        "calculate the emi",
        "estimate my emi",
        "estimate emi",
        "loan checker",
        "loan assessment",
        "assess my loan",
        "can i get a loan",
        "can i get this loan",
        "can i borrow",
        "would i qualify",
        "will i qualify",
        "check if i qualify",
        "check if i am eligible",
        "check whether i am eligible",
        "loan eligibility for me",
        "evaluate my loan",
    )

    if any(phrase in question for phrase in direct_requests):
        return True

    asks_for_result = any(
        phrase in question
        for phrase in (
            "eligible or not",
            "eligible for this amount",
            "monthly emi for",
            "emi for a loan",
            "emi for loan",
            "loan of ₹",
            "loan of rs",
            "borrow ₹",
            "borrow rs",
        )
    )

    asks_for_explanation = any(
        phrase in question
        for phrase in (
            "explain",
            "what affects",
            "what factors",
            "factors that affect",
            "factors affecting",
            "how does",
            "how do",
            "why does",
            "what is",
            "what are",
            "tell me about",
            "difference between",
        )
    )

    return asks_for_result and not asks_for_explanation


def is_risk_assessment_question(question):
    direct_requests = (
        "check fraud risk",
        "check the fraud risk",
        "assess fraud risk",
        "assess the risk",
        "check transaction risk",
        "is this transaction suspicious",
        "is this transaction safe",
        "check if this transaction",
        "evaluate this transaction",
        "fraud risk for",
        "risk score for transaction",
    )

    return any(phrase in question for phrase in direct_requests)


def is_customer_transaction_risk_question(question):
    """Detect fraud-risk questions about a customer's stored transactions."""
    question = question.lower()

    risk_terms = (
        "suspicious",
        "fraudulent",
        "fraud risk",
        "transaction risk",
        "safe",
    )

    transaction_terms = (
        "transaction",
        "payment",
        "travel",
        "fuel",
        "groceries",
        "salary",
        "online store",
        "book store",
        "cafe",
    )

    reference_terms = (
        "my",
        "latest",
        "last",
        "this",
        "the",
        "travel",
        "fuel",
        "groceries",
        "salary",
        "online store",
        "book store",
        "cafe",
    )

    return (
        any(term in question for term in risk_terms)
        and any(term in question for term in transaction_terms)
        and any(term in question for term in reference_terms)
    )


def answer_balance(customer_id):
    result = handle_banking_query(customer_id, "check balance")
    account = result.get("data", {}) if isinstance(result, dict) else {}

    if not isinstance(account, dict) or account.get("balance") is None:
        return {
            "success": False,
            "agent": "Banking Agent",
            "answer": "I couldn't retrieve the account balance.",
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
        ),
    }


def answer_loan_question(customer_id, question, request_data):
    """Use dashboard values when supplied, otherwise use the customer profile."""
    profile = get_customer_profile(customer_id)

    income = request_data.get("income", profile.get("income"))
    existing_emi = request_data.get(
        "existing_emi",
        profile.get("existing_emi"),
    )
    credit_score = request_data.get(
        "credit_score",
        profile.get("credit_score", profile.get("score")),
    )

    if not valid_number(income, minimum=0.01):
        return {
            "success": False,
            "agent": "Loan Agent",
            "answer": "Please enter a valid monthly income in the loan checker.",
        }

    if not valid_number(existing_emi, minimum=0):
        return {
            "success": False,
            "agent": "Loan Agent",
            "answer": "Please enter a valid existing monthly EMI.",
        }

    if not valid_number(credit_score, minimum=0, maximum=900):
        return {
            "success": False,
            "agent": "Loan Agent",
            "answer": "Please enter a valid credit score between 0 and 900.",
        }

    amount = extract_amount(question)

    if amount is None:
        amount = request_data.get(
            "loan_amount",
            request_data.get("amount", DEFAULT_LOAN_AMOUNT),
        )

    months = extract_loan_months(question)

    if months is None:
        months = request_data.get(
            "loan_months",
            request_data.get("months", DEFAULT_LOAN_MONTHS),
        )

    if (
        not valid_number(amount, minimum=0.01, maximum=100_000_000)
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
            ),
        }

    result = handle_loan_query(
        income,
        existing_emi,
        credit_score,
        amount,
        months,
    )

    eligible = result.get("eligible")

    if not isinstance(eligible, bool):
        return {
            "success": False,
            "agent": "Loan Agent",
            "answer": (
                "The Loan Agent did not return a valid eligibility decision."
            ),
            "data": result,
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
        "answer": answer,
        "data": result,
    }


def answer_risk_question(question):
    amount = extract_amount(question)

    if amount is None:
        return {
            "success": False,
            "agent": "Risk Agent",
            "answer": (
                "For a simulated transaction risk check, include an amount "
                "and any known context. For example: 'Check fraud risk for "
                "₹60,000 on an international transaction using a new device.'"
            ),
        }

    international = any(
        term in question
        for term in ("international", "overseas", "foreign transaction")
    )

    new_device = any(
        term in question
        for term in (
            "new device",
            "unknown device",
            "unrecognized device",
            "unrecognised device",
        )
    )

    late_night = any(
        term in question
        for term in ("late night", "midnight", "unusual time")
    )

    result = handle_risk_query(
        amount,
        international,
        new_device,
        late_night,
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

    answer += (
        "This is a simulated transaction-specific assessment, "
        "not a guarantee that a transaction is safe or fraudulent."
    )

    return {
        "success": True,
        "agent": "Risk Agent",
        "risk_level": risk_level,
        "risk_score": risk_score,
        "data": result,
        "answer": answer,
    }


def extract_transaction_rows(result):
    """Extract transaction rows from the Banking Agent response."""
    if not isinstance(result, dict):
        return []

    data = result.get("data", [])

    if isinstance(data, list):
        return [row for row in data if isinstance(row, dict)]

    if isinstance(data, dict):
        for key in ("transactions", "items", "records", "rows"):
            rows = data.get(key)
            if isinstance(rows, list):
                return [row for row in rows if isinstance(row, dict)]

    return []


def transaction_sort_key(transaction):
    """Sort by timestamp, then by transaction ID when available."""
    created_at = str(
        transaction.get("created_at", transaction.get("date", ""))
    )

    try:
        numeric_id = int(transaction.get("id", 0))
    except (TypeError, ValueError):
        numeric_id = 0

    return created_at, numeric_id


def transaction_kind(transaction):
    return str(
        transaction.get("kind", transaction.get("type", ""))
    ).lower()


def transaction_amount(transaction):
    try:
        return float(transaction.get("amount"))
    except (TypeError, ValueError):
        return None


def format_transaction(transaction):
    merchant = transaction.get("merchant", "Unknown merchant")
    amount = transaction_amount(transaction)
    kind = transaction_kind(transaction).upper() or "UNKNOWN"
    created_at = transaction.get("created_at", "Date unavailable")

    amount_text = (
        format_money(amount) if amount is not None else "Unavailable"
    )

    return (
        f"{merchant}: {amount_text} ({kind}), "
        f"date/time: {created_at}"
    )


def answer_transaction_question(customer_id, question):
    """Retrieve and summarize the selected customer's demo transactions."""
    result = handle_banking_query(customer_id, "show transactions")
    transactions = extract_transaction_rows(result)

    if not transactions:
        return {
            "success": False,
            "agent": "Banking Agent",
            "customer_id": customer_id,
            "answer": (
                f"I couldn't retrieve transaction records for {customer_id}. "
                "The database may contain no transactions or the Banking "
                "Agent did not return transaction rows."
            ),
            "data": (
                result.get("data", {})
                if isinstance(result, dict)
                else {}
            ),
        }

    ordered = sorted(
        transactions,
        key=transaction_sort_key,
        reverse=True,
    )
    normalized = question.lower()

    if any(
        term in normalized
        for term in ("highest", "largest", "biggest", "most expensive")
    ):
        available = [
            row for row in transactions
            if transaction_amount(row) is not None
        ]
        chosen = max(available, key=transaction_amount) if available else None
        description = "highest-amount transaction"

    elif any(
        term in normalized
        for term in ("lowest", "smallest", "least expensive")
    ):
        available = [
            row for row in transactions
            if transaction_amount(row) is not None
        ]
        chosen = min(available, key=transaction_amount) if available else None
        description = "lowest-amount transaction"

    elif "average" in normalized or "mean transaction" in normalized:
        amounts = [
            transaction_amount(row)
            for row in transactions
            if transaction_amount(row) is not None
        ]

        if not amounts:
            chosen = None
            description = "average transaction"
        else:
            average = sum(amounts) / len(amounts)

            return {
                "success": True,
                "agent": "Banking Agent",
                "customer_id": customer_id,
                "data": {
                    "transactions": ordered,
                    "average_amount": average,
                },
                "answer": (
                    f"For demo customer {customer_id}, the average amount "
                    f"across {len(amounts)} available transaction records "
                    f"is {format_money(average)}. This is based only on the "
                    "records returned by the demo database."
                ),
            }

    elif "oldest" in normalized or "first transaction" in normalized:
        chosen = ordered[-1]
        description = "oldest available transaction"

    elif "credit" in normalized or "incoming" in normalized:
        credits = [
            row for row in ordered
            if transaction_kind(row) == "credit"
        ]
        chosen = credits[0] if credits else None
        description = "latest incoming credit"

    elif "debit" in normalized or "outgoing" in normalized:
        debits = [
            row for row in ordered
            if transaction_kind(row) == "debit"
        ]
        chosen = debits[0] if debits else None
        description = "latest outgoing debit"

    elif any(
        term in normalized
        for term in (
            "last five",
            "last 5",
            "five transactions",
            "5 transactions",
        )
    ):
        chosen = None
        description = "last five transactions"

    elif any(
        term in normalized
        for term in (
            "previous",
            "before that",
            "second latest",
            "second last",
        )
    ):
        chosen = ordered[1] if len(ordered) > 1 else None
        description = "previous transaction"

    else:
        chosen = ordered[0]
        description = "latest transaction"

    if description == "last five transactions":
        selected = ordered[:5]

        if selected:
            answer = (
                f"Here are the latest {len(selected)} available transactions "
                f"for demo customer {customer_id}:\n"
                + "\n".join(
                    f"{index}. {format_transaction(row)}"
                    for index, row in enumerate(selected, start=1)
                )
            )
        else:
            answer = f"No transactions were found for {customer_id}."

    elif chosen is None:
        answer = (
            f"I couldn't find a matching {description} for demo customer "
            f"{customer_id} in the available transaction records."
        )
        selected = []

    else:
        answer = (
            f"The {description} for demo customer {customer_id} is: "
            f"{format_transaction(chosen)}."
        )
        selected = [chosen]

    return {
        "success": True,
        "agent": "Banking Agent",
        "customer_id": customer_id,
        "data": {
            "transactions": ordered,
            "selected_transactions": selected,
        },
        "answer": answer,
    }


def answer_spending_question(customer_id):
    result = handle_banking_query(customer_id, "check spending")

    if not isinstance(result, dict):
        return {
            "success": False,
            "agent": "Banking Agent",
            "answer": "I couldn't retrieve spending information.",
        }

    return {
        "success": True,
        "agent": "Banking Agent",
        "customer_id": customer_id,
        "data": result.get("data", {}),
        "answer": (
            "I retrieved the available spending information for "
            f"demo customer {customer_id}."
        ),
    }


def answer_customer_transaction_risk(customer_id, question):
    """Assess a stored transaction using its actual database indicators."""
    result = handle_banking_query(customer_id, "show transactions")
    rows = extract_transaction_rows(result)

    if not rows:
        return {
            "success": False,
            "agent": "Risk Agent",
            "customer_id": customer_id,
            "answer": f"I couldn't retrieve transactions for {customer_id}.",
        }

    ordered = sorted(
        rows,
        key=transaction_sort_key,
        reverse=True,
    )
    question_lower = question.lower()

    merchant_terms = (
        "travel",
        "fuel",
        "groceries",
        "salary",
        "online store",
        "book store",
        "cafe",
    )

    merchant = next(
        (
            term for term in merchant_terms
            if re.search(r"\b" + re.escape(term) + r"\b", question_lower)
        ),
        None,
    )

    if merchant:
        matches = [
            row for row in ordered
            if merchant in str(row.get("merchant", "")).lower()
        ]
        transaction = matches[0] if matches else None
    else:
        # Latest means the latest transaction of any kind, credit or debit.
        transaction = ordered[0]

    if transaction is None:
        return {
            "success": False,
            "agent": "Risk Agent",
            "customer_id": customer_id,
            "answer": (
                f"I couldn't find a matching transaction for {customer_id}."
            ),
        }

    amount = transaction_amount(transaction)

    if amount is None:
        return {
            "success": False,
            "agent": "Risk Agent",
            "customer_id": customer_id,
            "answer": (
                "The transaction amount is unavailable for risk assessment."
            ),
        }

    # Use the actual indicator values stored in the database.
    international = bool(transaction.get("international", 0))
    new_device = bool(transaction.get("new_device", 0))
    late_night = bool(transaction.get("late_night", 0))

    risk = handle_risk_query(
        amount,
        international,
        new_device,
        late_night,
    )

    risk_level = risk.get("risk_level", "UNKNOWN")
    risk_score = risk.get("risk_score", "Unavailable")
    reasons = risk.get("reasons", [])

    answer = (
        f"For demo customer {customer_id}, the transaction is "
        f"{format_transaction(transaction)}. "
        f"The simulated Risk Agent classified it as {risk_level} risk "
        f"with a score of {risk_score}/100. "
    )

    if reasons:
        answer += (
            "Contributing factors: "
            + "; ".join(map(str, reasons))
            + ". "
        )
    else:
        answer += (
            "No risk indicators were triggered by the recorded demo rules. "
        )

    answer += (
        "This is a rule-based simulation, not proof that a transaction "
        "is fraudulent or guaranteed to be safe."
    )

    return {
        "success": True,
        "agent": "Risk Agent",
        "customer_id": customer_id,
        "data": {
            "transaction": transaction,
            "risk": risk,
        },
        "answer": answer,
    }


def handle_chat(data):
    question = data.get("question", "")

    if not isinstance(question, str) or not question.strip():
        return {
            "success": False,
            "answer": "Please enter a question.",
        }

    question = question.strip()
    normalized = question.lower()
    customer_id = get_customer_id(data)

    if customer_id is None:
        return {
            "success": False,
            "answer": "Unknown demo customer. Select C101, C102, or C103.",
        }

    # Handle transaction-specific fraud questions before general routing.
    if is_customer_transaction_risk_question(normalized):
        return answer_customer_transaction_risk(
            customer_id,
            normalized,
        )

    if is_balance_question(normalized):
        return answer_balance(customer_id)

    if is_transaction_question(normalized):
        return answer_transaction_question(customer_id, normalized)

    if is_spending_question(normalized):
        return answer_spending_question(customer_id)

    if is_customer_question(normalized):
        profile = get_customer_profile(customer_id)

        return {
            "success": bool(profile),
            "agent": "Banking Agent",
            "customer_id": customer_id,
            "data": profile,
            "answer": (
                f"Here is the available financial profile for "
                f"{customer_id}: {profile}"
                if profile
                else "I couldn't retrieve this customer's profile."
            ),
        }

    if is_loan_calculation_question(normalized):
        return answer_loan_question(
            customer_id,
            normalized,
            data,
        )

    if is_risk_assessment_question(normalized):
        return answer_risk_question(normalized)

    # General banking questions go to the local LLM.
    # Verified customer context is attached when relevant.
    context = None

    asks_about_customer = any(
        term in normalized
        for term in (
            "my ",
            "myself",
            "this customer",
            "selected customer",
            "customer's",
            "customer ",
            "account",
            "transaction",
            "transactions",
            "balance",
            "spending",
            "credit score",
            "existing emi",
        )
    )

    if asks_about_customer:
        profile = get_customer_profile(customer_id)

        transaction_result = handle_banking_query(
            customer_id,
            "show transactions",
        )
        transaction_rows = extract_transaction_rows(transaction_result)

        context = {
            "customer_id": customer_id,
            "profile": profile,
            "transactions": transaction_rows,
        }

        if is_balance_question(normalized):
            balance_result = handle_banking_query(
                customer_id,
                "check balance",
            )
            context["balance"] = (
                balance_result.get("data", {})
                if isinstance(balance_result, dict)
                else {}
            )

    result = ask_banking_assistant(
        question,
        banking_context=context,
    )

    if isinstance(result, dict):
        result.setdefault("agent", "Local AI Assistant")
        return result

    return {
        "success": True,
        "agent": "Local AI Assistant",
        "answer": str(result),
    }


def handle_request(data):
    task = str(data.get("task", "")).lower().strip()

    if task in ("balance", "transactions", "spending", "customer"):
        customer_id = get_customer_id(data)

        if customer_id is None:
            return {
                "error": "Unknown demo customer. Use C101, C102, or C103."
            }

        query = {
            "balance": "check balance",
            "transactions": "show transactions",
            "spending": "check spending",
            "customer": "customer details",
        }[task]

        return handle_banking_query(customer_id, query)

    if task == "risk":
        return handle_risk_query(
            data.get("amount", 0),
            data.get("international", False),
            data.get("new_device", False),
            data.get("late_night", False),
        )

    if task == "loan":
        return handle_loan_query(
            data.get("income", 0),
            data.get("existing_emi", 0),
            data.get("credit_score", 0),
            data.get("amount", 0),
            data.get("months", 36),
        )

    if task == "chat":
        return handle_chat(data)

    return {
        "error": (
            "Unknown task. Try balance, transactions, spending, "
            "customer, risk, loan, or chat."
        )
    }
