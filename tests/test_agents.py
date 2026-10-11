
import unittest

from banking_tools import fraud_check, loan_check
from agents.banking_agent import handle_banking_query
from agents.risk_agent import handle_risk_query
from agents.loan_agent import handle_loan_query
from agents.supervisor import handle_request


class TestAgentBank(unittest.TestCase):

    def test_customer_balance(self):
        result = handle_banking_query("C101", "check balance")

        self.assertEqual(result["type"], "balance")
        self.assertEqual(result["data"]["balance"], 85000.0)

    def test_high_fraud_risk(self):
        result = fraud_check(60000, True, True)

        self.assertEqual(result["risk"], "HIGH")
        self.assertEqual(result["score"], 90)

    def test_low_fraud_risk(self):
        result = fraud_check(1000)

        self.assertEqual(result["risk"], "LOW")
        self.assertEqual(result["score"], 0)

    def test_eligible_loan(self):
        result = loan_check(90000, 12000, 760, 500000)

        self.assertTrue(result["eligible"])
        self.assertAlmostEqual(
            result["estimated_emi"], 16607.15, places=2
        )

    def test_ineligible_loan(self):
        result = loan_check(45000, 19000, 620, 500000)

        self.assertFalse(result["eligible"])

    def test_supervisor_balance_routing(self):
        result = handle_request({
            "task": "balance",
            "customer_id": "C101"
        })

        self.assertEqual(result["data"]["balance"], 85000.0)

    def test_supervisor_risk_routing(self):
        result = handle_request({
            "task": "risk",
            "amount": 60000,
            "international": True,
            "new_device": True
        })

        self.assertEqual(result["risk_level"], "HIGH")
        self.assertEqual(result["risk_score"], 90)

    def test_unknown_task(self):
        result = handle_request({"task": "unknown"})

        self.assertIn("error", result)


if __name__ == "__main__":
    unittest.main()
