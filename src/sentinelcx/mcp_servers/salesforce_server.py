"""Salesforce MCP server exposing customer data tools."""

import logging

from fastmcp import FastMCP

from sentinelcx.clients.salesforce_client import SalesforceClient
from sentinelcx.config import SalesforceSettings

_log_file = "/tmp/sentinelcx_mcp.log"
logger = logging.getLogger("mcp.salesforce")
logger.setLevel(logging.INFO)
_fh = logging.FileHandler(_log_file)
_fh.setFormatter(logging.Formatter("%(asctime)s %(name)s %(message)s"))
logger.addHandler(_fh)

salesforce_mcp = FastMCP("salesforce", instructions="Salesforce CRM data access")

_client: SalesforceClient | None = None


def init_client(settings: SalesforceSettings) -> None:
    global _client
    _client = SalesforceClient(settings)


def _get_client() -> SalesforceClient:
    if _client is None:
        raise RuntimeError("Salesforce client not initialized. Call init_client() first.")
    return _client


@salesforce_mcp.tool()
def get_customer_record(customer_name: str) -> dict:
    """Look up a customer in Salesforce by their full name (e.g. "Sarah Johnson").

    Searches the Contact object by first/last name, then returns the parent Account
    with all contacts, industry, tier (in Description), and the Salesforce account_id.
    Use the returned account_id for subsequent calls to get_case_history,
    get_purchase_history, and get_account_health.
    """
    logger.info("get_customer_record CALLED — customer_name=%s", customer_name)
    result = _get_client().get_customer_by_name(customer_name)
    logger.info(
        "get_customer_record RESULT — found=%s, account_id=%s",
        bool(result),
        result.get("Id", "N/A"),
    )
    return result


@salesforce_mcp.tool()
def get_case_history(account_id: str) -> list[dict]:
    """Fetch case/ticket history for a customer account.

    Requires the Salesforce account_id (returned by get_customer_record).
    Returns up to 50 most recent cases with subject, status, priority, and resolution.
    """
    logger.info("get_case_history CALLED — account_id=%s", account_id)
    return _get_client().get_case_history(account_id)


@salesforce_mcp.tool()
def get_purchase_history(account_id: str) -> list[dict]:
    """Fetch purchase history (closed-won opportunities) for a customer account.

    Requires the Salesforce account_id (returned by get_customer_record).
    Returns up to 50 most recent purchases with amount, stage, and close date.
    """
    logger.info("get_purchase_history CALLED — account_id=%s", account_id)
    return _get_client().get_purchase_history(account_id)


@salesforce_mcp.tool()
def get_account_health(account_id: str) -> dict:
    """Get account health score and churn risk assessment.

    Requires the Salesforce account_id (returned by get_customer_record).
    Computes a 0-100 health score based on case resolution rate and lifetime value.
    Returns score, churn_risk (low/medium/high), lifetime_value, and resolution_rate.
    """
    logger.info("get_account_health CALLED — account_id=%s", account_id)
    return _get_client().get_account_health(account_id)


if __name__ == "__main__":
    init_client(SalesforceSettings())
    salesforce_mcp.run()
