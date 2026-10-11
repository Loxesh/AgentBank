
from banking_tools import (
    customer_details,
    account_balance,
    recent_transactions,
    monthly_spending
)


def handle_banking_query(customer_id, query):
    query = query.lower()

    if "balance" in query:
        return {
            "type": "balance",
            "data": account_balance(customer_id)
        }

    elif "transaction" in query:
        return {
            "type": "transactions",
            "data": recent_transactions(customer_id)
        }

    elif "spending" in query:
        return {
            "type": "spending",
            "data": monthly_spending(customer_id)
        }

    else:
        return {
            "type": "customer",
            "data": customer_details(customer_id)
        }
