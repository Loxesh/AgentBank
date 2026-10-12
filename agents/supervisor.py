
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

MERCHANTS = (
    "online store",
    "book store",
    "groceries",
    "travel",
    "fuel",
    "salary",
    "cafe",
)


def get_customer_id(data):
    customer_id = data.get("customer_id", "C101")
    if not isinstance(customer_id, str):
        return None
    customer_id = customer_id.strip().upper()
    return customer_id if customer_id in DEMO_CUSTOMERS else None


def format_money(value):
    try:
        return f"₹{float(value):,.2f}"
    except (TypeError, ValueError):
        return "Unavailable"


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
    return float(match.group(1)) if match else None


def extract_loan_months(question):
    match = re.search(
        r"\b(12|24|36|48|60)\s*(?:months?|mos?)\b",
        question.lower(),
    )
    return int(match.group(1)) if match else None


def get_customer_profile(customer_id):
    result = handle_banking_query(customer_id, "customer details")
    profile = result.get("data", {}) if isinstance(result, dict) else {}
    return profile if isinstance(profile, dict) else {}


def is_balance_question(question):
    patterns = (
        r"\bbalance\b",
        r"\bhow much money do i have\b",
        r"\bhow much money is left\b",
        r"\baccount funds\b",
    )
    return any(re.search(pattern, question) for pattern in patterns)


def is_customer_question(question):
    return any(term in question for term in (
        "my profile", "my details", "customer details", "my income",
        "my credit score", "my existing emi", "my financial details",
    ))


def is_loan_calculation_question(question):
    direct_requests = (
        "am i eligible", "eligible for a loan", "check my loan",
        "check loan eligibility", "check my eligibility", "calculate my emi",
        "calculate emi", "estimate my emi", "estimate emi", "loan checker",
        "loan assessment", "assess my loan", "can i get a loan",
        "can i get this loan", "can i borrow", "would i qualify",
        "will i qualify", "check if i qualify", "check if i am eligible",
        "check whether i am eligible", "loan eligibility for me",
        "evaluate my loan",
    )
    if any(term in question for term in direct_requests):
        return True

    asks_for_result = any(term in question for term in (
        "eligible or not", "eligible for this amount", "monthly emi for",
        "emi for a loan", "emi for loan", "loan of ₹", "loan of rs",
        "borrow ₹", "borrow rs",
    ))
    asks_for_explanation = any(term in question for term in (
        "explain", "what affects", "what factors", "factors that affect",
        "factors affecting", "how does", "how do", "why does", "what is",
        "what are", "tell me about", "difference between",
    ))
    return asks_for_result and not asks_for_explanation


def is_risk_assessment_question(question):
    return any(term in question for term in (
        "check fraud risk", "assess fraud risk", "assess the risk",
        "check transaction risk", "suspicious", "fraudulent",
        "is this transaction safe", "check if this transaction",
        "evaluate this transaction", "fraud risk for",
        "risk score for transaction",
    ))


def extract_transaction_rows(result):
    """Extract transaction dictionaries from the Banking Agent response."""
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


def get_transactions(customer_id):
    result = handle_banking_query(customer_id, "show transactions")
    rows = extract_transaction_rows(result)

    # Most recent first. The database query already returns newest IDs first;
    # sorting also supports timestamps when they are available.
    def sort_key(row):
        created_at = str(row.get("created_at", row.get("date", "")))
        try:
            row_id = int(row.get("id", 0))
        except (TypeError, ValueError):
            row_id = 0
        return created_at, row_id

    return sorted(rows, key=sort_key, reverse=True)


def transaction_amount(transaction):
    try:
        amount = float(transaction.get("amount"))
        return amount if math.isfinite(amount) else None
    except (TypeError, ValueError):
        return None


def transaction_kind(transaction):
    return str(
        transaction.get("kind", transaction.get("type", ""))
    ).strip().lower()


def format_transaction(transaction):
    merchant = transaction.get("merchant", "Unknown merchant")
    amount = transaction_amount(transaction)
    kind = transaction_kind(transaction).upper() or "UNKNOWN"
    created_at = transaction.get(
        "created_at", transaction.get("date", "Date unavailable")
    )
    return (
        f"{merchant}: {format_money(amount)} ({kind}), "
        f"date/time: {created_at}"
    )


def find_merchant(question):
    """Find a known merchant mentioned in a question."""
    question = question.lower()
    for merchant in MERCHANTS:
        if re.search(r"\b" + re.escape(merchant) + r"\b", question):
            return merchant
    return None


def is_transaction_question(question):
    """Identify questions that require transaction records."""
    terms = (
        "transaction", "transactions", "payment history",
        "transaction history", "recent payment", "recent payments",
        "latest payment", "last payment", "highest amount",
        "largest transaction", "biggest transaction", "highest transaction",
        "lowest amount", "smallest transaction", "lowest transaction",
        "least transaction", "least expensive", "most expensive",
        "highest", "lowest", "largest", "smallest",
        "average transaction", "average amount", "mean transaction",
        "last five", "last 5", "previous transaction",
        "latest debit", "latest credit", "last debit", "last credit",
        "oldest transaction", "first transaction",
    )

    if any(term in question for term in terms):
        return True

    # Merchant-specific questions such as "How much did I spend on Fuel?"
    merchant = find_merchant(question)
    spending_language = any(term in question for term in (
        "spent", "spend", "paid", "payment", "transaction",
        "cost", "amount", "purchase",
    ))
    return bool(merchant and spending_language)


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
    profile = get_customer_profile(customer_id)

    income = request_data.get("income", profile.get("income"))
    existing_emi = request_data.get(
        "existing_emi", profile.get("existing_emi")
    )
    credit_score = request_data.get(
        "credit_score", profile.get("credit_score", profile.get("score"))
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
            "loan_amount", request_data.get("amount", DEFAULT_LOAN_AMOUNT)
        )

    months = extract_loan_months(question)
    if months is None:
        months = request_data.get(
            "loan_months", request_data.get("months", DEFAULT_LOAN_MONTHS)
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
        income, existing_emi, credit_score, amount, months
    )
    eligible = result.get("eligible")

    if not isinstance(eligible, bool):
        return {
            "success": False,
            "agent": "Loan Agent",
            "answer": "The Loan Agent did not return a valid eligibility decision.",
            "data": result,
        }

    decision = "ELIGIBLE" if eligible else "NOT ELIGIBLE"
    answer = (
        f"Loan assessment for demo customer {customer_id}: {decision}. "
        f"Requested amount: {format_money(amount)} over {months} months. "
        f"Monthly income: {format_money(income)}. "
        f"Existing monthly EMI: {format_money(existing_emi)}. "
        f"Credit score: {credit_score}. "
    )

    if result.get("estimated_emi") is not None:
        answer += (
            f"Estimated new monthly EMI: "
            f"{format_money(result['estimated_emi'])}. "
        )

    if result.get("debt_ratio_percent") is not None:
        answer += (
            f"Total EMI-to-income ratio: "
            f"{result['debt_ratio_percent']}%. "
        )

    if result.get("reason"):
        answer += f"Reason from the Loan Agent: {result['reason']}. "

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
        "estimated_emi": result.get("estimated_emi"),
        "debt_ratio_percent": result.get("debt_ratio_percent"),
        "reason": result.get("reason", ""),
        "answer": answer,
        "data": result,
    }


def answer_transaction_question(customer_id, question):
    transactions = get_transactions(customer_id)

    if not transactions:
        return {
            "success": False,
            "agent": "Banking Agent",
            "customer_id": customer_id,
            "answer": (
                f"I couldn't retrieve transaction records for {customer_id}. "
                "Check whether the Banking Agent returned transaction rows."
            ),
        }

    normalized = question.lower()
    merchant = find_merchant(normalized)

    # Merchant-specific queries should filter first, before calculating
    # highest/lowest/latest or spending amounts.
    if merchant:
        matching = [
            row for row in transactions
            if merchant in str(row.get("merchant", "")).lower()
        ]

        if not matching:
            return {
                "success": False,
                "agent": "Banking Agent",
                "customer_id": customer_id,
                "answer": (
                    f"I couldn't find a {merchant.title()} transaction "
                    f"for demo customer {customer_id}."
                ),
            }

        # Asking how much was spent on a merchant means summing matching
        # debit records, rather than returning the latest transaction.
        if any(term in normalized for term in (
            "how much did i spend", "how much have i spent",
            "total spent", "total spending", "spent on", "spend on",
            "how much was spent",
        )):
            debit_rows = [
                row for row in matching
                if transaction_kind(row) == "debit"
            ]
            total = sum(transaction_amount(row) or 0 for row in debit_rows)

            return {
                "success": True,
                "agent": "Banking Agent",
                "customer_id": customer_id,
                "data": {
                    "merchant": merchant.title(),
                    "transactions": debit_rows,
                    "total_spent": total,
                },
                "answer": (
                    f"Demo customer {customer_id} spent "
                    f"{format_money(total)} on {merchant.title()} across "
                    f"{len(debit_rows)} recorded debit transaction(s). "
                    "This total uses the available transaction records."
                ),
            }

        transactions = matching

    # Highest/lowest comparisons are made against the relevant records.
    amounts_available = [
        row for row in transactions
        if transaction_amount(row) is not None
    ]

    if any(term in normalized for term in (
        "highest", "largest", "biggest", "most expensive", "maximum",
    )):
        chosen = max(
            amounts_available, key=transaction_amount, default=None
        )
        description = "highest-amount transaction"

    elif any(term in normalized for term in (
        "lowest", "smallest", "least expensive", "least transaction",
        "minimum", "cheapest",
    )):
        chosen = min(
            amounts_available, key=transaction_amount, default=None
        )
        description = "lowest-amount transaction"

    elif "average" in normalized or "mean transaction" in normalized:
        amounts = [transaction_amount(row) for row in amounts_available]
        average = sum(amounts) / len(amounts) if amounts else None

        if average is None:
            answer = "There are no numeric transaction amounts to average."
        else:
            answer = (
                f"The average transaction amount for demo customer "
                f"{customer_id} is {format_money(average)}, based on "
                f"{len(amounts)} available record(s)."
            )

        return {
            "success": average is not None,
            "agent": "Banking Agent",
            "customer_id": customer_id,
            "data": {"average_amount": average, "transactions": transactions},
            "answer": answer,
        }

    elif "oldest" in normalized or "first transaction" in normalized:
        chosen = transactions[-1] if transactions else None
        description = "oldest available transaction"

    elif any(term in normalized for term in (
        "last five", "last 5", "five transactions", "5 transactions",
    )):
        selected = transactions[:5]
        answer = (
            f"Latest {len(selected)} transaction(s) for demo customer "
            f"{customer_id}:\n"
            + "\n".join(
                f"{index}. {format_transaction(row)}"
                for index, row in enumerate(selected, start=1)
            )
        )
        return {
            "success": True,
            "agent": "Banking Agent",
            "customer_id": customer_id,
            "data": {"transactions": selected},
            "answer": answer,
        }

    elif any(term in normalized for term in (
        "previous", "before that", "second latest", "second last",
    )):
        chosen = transactions[1] if len(transactions) > 1 else None
        description = "previous transaction"

    elif "credit" in normalized or "incoming" in normalized:
        chosen = next(
            (row for row in transactions if transaction_kind(row) == "credit"),
            None,
        )
        description = "latest incoming credit"

    elif "debit" in normalized or "outgoing" in normalized:
        chosen = next(
            (row for row in transactions if transaction_kind(row) == "debit"),
            None,
        )
        description = "latest outgoing debit"

    else:
        # Latest transaction is the default only when the question doesn't
        # request a specific amount comparison or transaction position.
        chosen = transactions[0] if transactions else None
        description = "latest transaction"

    if chosen is None:
        answer = (
            f"I couldn't find a {description} for demo customer "
            f"{customer_id} in the available transaction records."
        )
    else:
        answer = (
            f"The {description} for demo customer {customer_id} is: "
            f"{format_transaction(chosen)}."
        )

    return {
        "success": chosen is not None,
        "agent": "Banking Agent",
        "customer_id": customer_id,
        "data": {
            "transactions": transactions,
            "selected_transaction": chosen,
        },
        "answer": answer,
    }


def answer_spending_question(customer_id, question=""):
    # Merchant-specific spending is calculated from matching debit records.
    if find_merchant(question):
        return answer_transaction_question(customer_id, question)

    result = handle_banking_query(customer_id, "check spending")
    if not isinstance(result, dict):
        return {
            "success": False,
            "agent": "Banking Agent",
            "answer": "I couldn't retrieve spending information.",
        }

    data = result.get("data", {})
    if isinstance(data, dict):
        # Use the amount returned by the Banking Agent where available.
        for key in ("monthly_spending", "total_spending", "total_spent", "spending"):
            if data.get(key) is not None:
                return {
                    "success": True,
                    "agent": "Banking Agent",
                    "customer_id": customer_id,
                    "data": data,
                    "answer": (
                        f"Available spending information for demo customer "
                        f"{customer_id}: {format_money(data[key])} "
                        "for the period calculated by the Banking Agent."
                    ),
                }

    return {
        "success": True,
        "agent": "Banking Agent",
        "customer_id": customer_id,
        "data": data,
        "answer": (
            f"The Banking Agent returned spending information for "
            f"demo customer {customer_id}: {data}. "
            "The exact total depends on the spending data returned."
        ),
    }


def is_customer_transaction_risk_question(question):
    risk_terms = (
        "suspicious", "fraudulent", "fraud risk", "transaction risk",
    )
    mentions_transaction = any(term in question for term in (
        "transaction", "payment", *MERCHANTS,
    ))
    return (
        any(term in question for term in risk_terms)
        and mentions_transaction
    )


def answer_customer_transaction_risk(customer_id, question):
    transactions = get_transactions(customer_id)

    if not transactions:
        return {
            "success": False,
            "agent": "Risk Agent",
            "customer_id": customer_id,
            "answer": f"I couldn't retrieve transactions for {customer_id}.",
        }

    merchant = find_merchant(question)
    if merchant:
        matches = [
            row for row in transactions
            if merchant in str(row.get("merchant", "")).lower()
        ]
        transaction = matches[0] if matches else None
    else:
        transaction = transactions[0]

    if transaction is None:
        return {
            "success": False,
            "agent": "Risk Agent",
            "customer_id": customer_id,
            "answer": f"I couldn't find the requested transaction for {customer_id}.",
        }

    amount = transaction_amount(transaction)
    if amount is None:
        return {
            "success": False,
            "agent": "Risk Agent",
            "answer": "The transaction amount is unavailable for risk assessment.",
        }

    risk = handle_risk_query(
        amount,
        bool(transaction.get("international", 0)),
        bool(transaction.get("new_device", 0)),
        bool(transaction.get("late_night", 0)),
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
        answer += "Contributing factors: " + "; ".join(map(str, reasons)) + ". "
    else:
        answer += "No risk indicators were triggered by the recorded demo rules. "

    answer += (
        "This is a rule-based simulation, not proof that a transaction "
        "is fraudulent or guaranteed to be safe."
    )

    return {
        "success": True,
        "agent": "Risk Agent",
        "customer_id": customer_id,
        "data": {"transaction": transaction, "risk": risk},
        "answer": answer,
    }


def is_spending_question(question):
    return any(term in question for term in (
        "spending", "spent this month", "monthly expenses",
        "monthly spending", "expenses", "how much did i spend",
        "how much have i spent", "total spending", "total spent",
        "spend on", "spent on",
    ))


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
            "answer": "Unknown demo customer. Select C101, C102, or C103.",
        }

    # Specific stored-transaction risk questions must run before general chat.
    if is_customer_transaction_risk_question(normalized):
        return answer_customer_transaction_risk(customer_id, normalized)

    if is_balance_question(normalized):
        return answer_balance(customer_id)

    # Route merchant-specific spending and transaction comparisons directly
    # to database-backed logic instead of the LLM.
    if is_transaction_question(normalized):
        return answer_transaction_question(customer_id, normalized)

    if is_spending_question(normalized):
        return answer_spending_question(customer_id, normalized)

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
                if profile else "I couldn't retrieve this customer's profile."
            ),
        }

    if is_loan_calculation_question(normalized):
        return answer_loan_question(customer_id, normalized, data)

    if is_risk_assessment_question(normalized):
        amount = extract_amount(normalized)
        if amount is None:
            return {
                "success": False,
                "agent": "Risk Agent",
                "answer": (
                    "Include an amount for a simulated risk check, for example: "
                    "'Check fraud risk for ₹60,000 on an international "
                    "transaction using a new device.'"
                ),
            }

        international = any(term in normalized for term in (
            "international", "overseas", "foreign transaction",
        ))
        new_device = any(term in normalized for term in (
            "new device", "unknown device", "unrecognized device",
            "unrecognised device",
        ))
        late_night = any(term in normalized for term in (
            "late night", "midnight", "unusual time",
        ))

        result = handle_risk_query(
            amount, international, new_device, late_night
        )
        risk_level = result.get("risk_level", "UNKNOWN")
        score = result.get("risk_score", "Unavailable")
        reasons = result.get("reasons", [])

        answer = (
            f"The Risk Agent assessed a demo transaction of {format_money(amount)}. "
            f"Risk level: {risk_level}. Risk score: {score}/100. "
        )
        if reasons:
            answer += "Factors: " + "; ".join(map(str, reasons)) + ". "
        answer += (
            "This is a simulated assessment, not a guarantee that a transaction "
            "is safe or fraudulent."
        )

        return {
            "success": True,
            "agent": "Risk Agent",
            "risk_level": risk_level,
            "risk_score": score,
            "data": result,
            "answer": answer,
        }

    # General questions continue to use the existing local Ollama model.
    context = None
    asks_about_customer = any(term in normalized for term in (
        "my ", "myself", "this customer", "selected customer",
        "customer's", "customer ", "account", "transaction",
        "transactions", "balance", "spending", "credit score",
        "existing emi",
    ))

    if asks_about_customer:
        profile = get_customer_profile(customer_id)
        transactions = get_transactions(customer_id)
        context = {
            "customer_id": customer_id,
            "profile": profile,
            "transactions": transactions,
        }

    result = ask_banking_assistant(question, banking_context=context)
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
