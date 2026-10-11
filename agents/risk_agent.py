from banking_tools import fraud_check


def handle_risk_query(
    amount,
    international=False,
    new_device=False,
    late_night=False
):
    result = fraud_check(
        amount,
        international,
        new_device,
        late_night
    )

    return {
        "agent": "Risk Agent",
        "amount": amount,
        "risk_level": result["risk"],
        "risk_score": result["score"],
        "reasons": result["reasons"]
    }