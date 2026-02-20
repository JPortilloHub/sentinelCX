"""Salesforce API client wrapper using simple-salesforce."""

from simple_salesforce import Salesforce

from sentinelcx.config import SalesforceSettings


class SalesforceClient:
    def __init__(self, settings: SalesforceSettings) -> None:
        self._sf = Salesforce(
            username=settings.username,
            password=settings.password,
            security_token=settings.security_token,
            domain=settings.domain,
        )

    def get_customer(self, account_id: str) -> dict:
        """Fetch customer Account and related Contact info by account ID."""
        result = self._sf.query(
            f"SELECT Id, Name, Industry, Type, Phone, Website, Description "
            f"FROM Account WHERE Id = '{account_id}'"
        )
        if not result["records"]:
            return {}
        account = result["records"][0]
        contacts = self._sf.query(
            f"SELECT Id, Name, Email, Phone, Title FROM Contact WHERE AccountId = '{account_id}'"
        )
        account["contacts"] = contacts.get("records", [])
        return account

    def get_customer_by_name(self, customer_name: str) -> dict:
        """Search for a customer by contact name and return Account + Contact info.

        Searches the Contact object by FirstName and LastName, then fetches the
        parent Account. Returns empty dict if no match found.
        """
        parts = customer_name.strip().split()
        if len(parts) < 2:
            return {}
        first_name = parts[0].replace("'", "\\'")
        last_name = " ".join(parts[1:]).replace("'", "\\'")

        contacts = self._sf.query(
            f"SELECT Id, AccountId, Name, Email, Phone, Title "
            f"FROM Contact "
            f"WHERE FirstName = '{first_name}' AND LastName = '{last_name}' "
            f"LIMIT 1"
        )
        if not contacts["records"]:
            return {}

        contact = contacts["records"][0]
        account_id = contact.get("AccountId")
        if not account_id:
            return {"contact": contact}

        account = self.get_customer(account_id)
        account["matched_contact"] = contact
        return account

    def get_case_history(self, account_id: str) -> list[dict]:
        """Fetch case/ticket history for a customer account."""
        result = self._sf.query(
            f"SELECT Id, CaseNumber, Subject, Status, Priority, CreatedDate, ClosedDate, "
            f"Description, Resolution__c "
            f"FROM Case WHERE AccountId = '{account_id}' ORDER BY CreatedDate DESC LIMIT 50"
        )
        return result.get("records", [])

    def get_purchase_history(self, account_id: str) -> list[dict]:
        """Fetch purchase/opportunity history for a customer account."""
        result = self._sf.query(
            f"SELECT Id, Name, Amount, StageName, CloseDate, Description "
            f"FROM Opportunity WHERE AccountId = '{account_id}' "
            f"AND StageName = 'Closed Won' ORDER BY CloseDate DESC LIMIT 50"
        )
        return result.get("records", [])

    def get_account_health(self, account_id: str) -> dict:
        """Compute account health score from case and opportunity data."""
        cases = self.get_case_history(account_id)
        purchases = self.get_purchase_history(account_id)

        total_cases = len(cases)
        closed_cases = sum(1 for c in cases if c.get("Status") == "Closed")
        resolution_rate = closed_cases / total_cases if total_cases > 0 else 1.0
        total_spent = sum(p.get("Amount", 0) or 0 for p in purchases)

        # Simple health score: weighted combination
        score = min(100.0, (resolution_rate * 50) + min(total_spent / 1000, 50))
        churn_risk = "high" if score < 30 else "medium" if score < 60 else "low"

        return {
            "score": round(score, 1),
            "churn_risk": churn_risk,
            "lifetime_value": total_spent,
            "total_cases": total_cases,
            "resolution_rate": round(resolution_rate, 2),
        }
