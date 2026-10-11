
from banking_tools import loan_check


def handle_loan_query(income, existing_emi, credit_score, amount, months=36):
    result = loan_check(
        income,
        existing_emi,
        credit_score,
        amount,
        months
    )

    return {
        "agent": "Loan Agent",
        "loan_amount": amount,
        "eligible": result["eligible"],
        "estimated_emi": result["estimated_emi"],
        "debt_ratio_percent": result["debt_ratio_percent"],
        "reason": result["reason"]
    }
