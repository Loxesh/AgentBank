
"""Trusted banking tools for the AgentBank demo."""

from datetime import datetime, timezone
from database import query_one, query_all, add_demo_transaction


def customer_details(customer_id):
    return query_one(
        "SELECT * FROM customers WHERE id = ?",
        (customer_id,)
    )


def account_balance(customer_id):
    return query_one(
        "SELECT * FROM accounts WHERE customer_id = ?",
        (customer_id,)
    )


def recent_transactions(customer_id, limit=5):
    return query_all(
        """SELECT * FROM transactions
           WHERE customer_id = ?
           ORDER BY id DESC LIMIT ?""",
        (customer_id, limit)
    )


def monthly_spending(customer_id):
    month = datetime.now(timezone.utc).strftime("%Y-%m")

    result = query_one(
        """SELECT COALESCE(SUM(amount), 0) AS total
           FROM transactions
           WHERE customer_id = ? AND kind = 'debit'
           AND substr(created_at, 1, 7) = ?""",
        (customer_id, month)
    )

    return round(result["total"], 2)


def fraud_check(
    amount, international=False, new_device=False, late_night=False
):
    """Apply fictional, explainable demo fraud rules."""

    score = 0
    reasons = []

    if amount >= 50000:
        score += 35
        reasons.append("Amount is at least Rs 50,000")
    elif amount >= 20000:
        score += 20
        reasons.append("Amount is at least Rs 20,000")

    if international:
        score += 30
        reasons.append("International transaction")

    if new_device:
        score += 25
        reasons.append("New device")

    if late_night:
        score += 20
        reasons.append("Unusual transaction hour")

    risk = (
        "HIGH" if score >= 60
        else "MEDIUM" if score >= 30
        else "LOW"
    )

    return {
        "score": min(score, 100),
        "risk": risk,
        "reasons": reasons
    }


def loan_check(income, existing_emi, credit_score, amount, months=36):
    """Calculate EMI using fictional demo eligibility rules."""

    monthly_rate = 0.12 / 12
    power = (1 + monthly_rate) ** months

    loan_emi = amount * monthly_rate * power / (power - 1)
    total_emi = existing_emi + loan_emi
    ratio = total_emi / income if income > 0 else 1.0

    eligible = credit_score >= 650 and ratio <= 0.40

    return {
        "eligible": eligible,
        "estimated_emi": round(loan_emi, 2),
        "debt_ratio_percent": round(ratio * 100, 1),
        "credit_score": credit_score,
        "reason": (
            "Meets the example rules"
            if eligible
            else "Credit score is low or total EMI exceeds 40% of income"
        )
    }


def simulate_debit(
    customer_id, amount, merchant,
    international=False, new_device=False, late_night=False
):
    transaction_id = add_demo_transaction(
        customer_id, amount, merchant,
        international, new_device, late_night
    )

    if transaction_id is None:
        return None

    return {
        "id": transaction_id,
        "fraud": fraud_check(
            amount, international, new_device, late_night
        )
    }
