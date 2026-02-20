"""CLI script to seed all external services with test data.

Usage:
    python -m seed_data.seed                  # Seed everything
    python -m seed_data.seed --knowledge-only # Only generate knowledge base docs
    python -m seed_data.seed --eval-only      # Only generate evaluation data
    python -m seed_data.seed --salesforce-only # Only seed Salesforce
    python -m seed_data.seed --chatwoot-only   # Only seed Chatwoot
"""

import argparse
import asyncio
import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def seed_knowledge_base() -> None:
    """Generate knowledge base markdown docs."""
    from seed_data.knowledge_base_content import generate_knowledge_base

    logger.info("Generating knowledge base content...")
    stats = generate_knowledge_base()
    logger.info(
        "Knowledge base: %d files created across %d categories",
        stats["files_created"],
        len(stats["categories"]),
    )
    for cat in stats["categories"]:
        logger.info("  - %s: %d documents", cat["name"], cat["documents"])


def seed_evaluation_data() -> None:
    """Generate evaluation datasets (labeled tickets + routing ground truth)."""
    from seed_data.generator import write_evaluation_data

    logger.info("Generating evaluation data...")
    stats = write_evaluation_data()
    logger.info(
        "Evaluation data: %d tickets, %d routing entries",
        stats["tickets_generated"],
        stats["routing_entries"],
    )
    logger.info("  - Tickets file: %s", stats["tickets_file"])
    logger.info("  - Routing file: %s", stats["routing_file"])


def seed_salesforce() -> None:
    """Create customer records in Salesforce."""
    from seed_data.generator import generate_customers

    try:
        from sentinelcx.config import SalesforceSettings  # noqa: F401
    except ImportError:
        logger.error("sentinelcx package not installed. Run: pip install -e .")
        return

    settings = SalesforceSettings()
    if not settings.username:
        logger.warning("Salesforce credentials not configured. Skipping.")
        return

    from simple_salesforce import Salesforce
    from simple_salesforce.exceptions import SalesforceMalformedRequest

    sf = Salesforce(
        username=settings.username,
        password=settings.password,
        security_token=settings.security_token,
        domain=settings.domain,
    )

    # Clean existing data first
    logger.info("Deleting existing Salesforce Contacts and Accounts...")
    existing_contacts = sf.query("SELECT Id FROM Contact")
    for record in existing_contacts.get("records", []):
        try:
            sf.Contact.delete(record["Id"])
        except Exception:
            pass
    logger.info("  Deleted %d contacts", len(existing_contacts.get("records", [])))

    existing_accounts = sf.query("SELECT Id FROM Account")
    for record in existing_accounts.get("records", []):
        try:
            sf.Account.delete(record["Id"])
        except Exception:
            pass
    logger.info("  Deleted %d accounts", len(existing_accounts.get("records", [])))

    customers = generate_customers()
    logger.info("Seeding %d customers into Salesforce...", len(customers))

    for customer in customers:
        try:
            # Create Account (use customer name so it matches Chatwoot contacts)
            account = sf.Account.create(
                {
                    "Name": customer["name"],
                    "Industry": "Technology",
                    "Type": "Customer",
                    "Description": f"Tier: {customer['tier']} | Company: {customer['company']}",
                }
            )
            account_id = account["id"]

            # Create Contact
            name_parts = customer["name"].split()
            try:
                sf.Contact.create(
                    {
                        "AccountId": account_id,
                        "FirstName": name_parts[0],
                        "LastName": name_parts[1] if len(name_parts) > 1 else "",
                        "Email": customer["email"],
                    }
                )
            except SalesforceMalformedRequest as dup_err:
                if "DUPLICATES_DETECTED" in str(dup_err):
                    logger.info("  Contact %s already exists, skipping duplicate", customer["name"])
                else:
                    raise

            logger.info("  Created: %s (%s) - %s", customer["name"], customer["tier"], account_id)
        except Exception as e:
            logger.error("  Failed to create %s: %s", customer["name"], e)


async def seed_chatwoot() -> None:
    """Create conversations in Chatwoot."""
    from seed_data.generator import generate_tickets

    try:
        from sentinelcx.clients.chatwoot_client import ChatwootClient
        from sentinelcx.config import ChatwootSettings
    except ImportError:
        logger.error("sentinelcx package not installed. Run: pip install -e .")
        return

    settings = ChatwootSettings()
    if not settings.api_token:
        logger.warning("Chatwoot credentials not configured. Skipping.")
        return

    client = ChatwootClient(settings)
    tickets = generate_tickets(50)  # Seed 50 conversations
    logger.info("Seeding %d conversations into Chatwoot...", len(tickets))

    import httpx

    base_url = f"{settings.base_url.rstrip('/')}/api/v1/accounts/{settings.account_id}"
    headers = {"api_access_token": settings.api_token}

    async with httpx.AsyncClient(base_url=base_url, headers=headers, timeout=30.0) as http:
        # Get the first available inbox
        inbox_resp = await http.get("/inboxes")
        if inbox_resp.status_code != 200:
            logger.error("Failed to fetch inboxes. Create an inbox in Chatwoot first.")
            return
        inboxes = inbox_resp.json().get("payload", [])
        if not inboxes:
            logger.error("No inboxes found. Create an API inbox in Chatwoot Settings -> Inboxes.")
            return
        inbox_id = inboxes[0]["id"]
        logger.info("Using inbox: %s (id=%s)", inboxes[0].get("name", "unknown"), inbox_id)

        for ticket in tickets:
            try:
                # Create or find existing contact
                email = f"test.{ticket['id'].lower()}@example.com"
                contact_resp = await http.post(
                    "/contacts",
                    json={
                        "name": ticket["customer_name"],
                        "email": email,
                    },
                )
                if contact_resp.status_code in (200, 201):
                    contact_data = contact_resp.json()
                    contact_id = contact_data.get("payload", {}).get("contact", {}).get("id")
                elif contact_resp.status_code == 422:
                    # Contact already exists, search for it
                    search_resp = await http.get("/contacts/search", params={"q": email})
                    if search_resp.status_code == 200:
                        contacts = search_resp.json().get("payload", [])
                        if contacts:
                            contact_id = contacts[0]["id"]
                        else:
                            logger.warning("  Contact exists but search failed for %s", ticket["id"])
                            continue
                    else:
                        logger.warning("  Could not find existing contact for %s", ticket["id"])
                        continue
                else:
                    logger.warning("  Failed to create contact for %s", ticket["id"])
                    continue

                # Create conversation
                conv_resp = await http.post(
                    "/conversations",
                    json={
                        "contact_id": contact_id,
                        "inbox_id": inbox_id,
                        "message": {"content": f"Subject: {ticket['subject']}\n\n{ticket['body']}"},
                    },
                )
                if conv_resp.status_code in (200, 201):
                    conv_data = conv_resp.json()
                    conv_id = conv_data.get("id")
                    logger.info("  Created conversation %s for ticket %s", conv_id, ticket["id"])
                else:
                    logger.warning("  Failed to create conversation for %s", ticket["id"])
            except Exception as e:
                logger.error("  Error seeding ticket %s: %s", ticket["id"], e)

    await client.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed sentinelCX with test data")
    parser.add_argument(
        "--knowledge-only", action="store_true", help="Only generate knowledge base"
    )
    parser.add_argument("--eval-only", action="store_true", help="Only generate evaluation data")
    parser.add_argument("--salesforce-only", action="store_true", help="Only seed Salesforce")
    parser.add_argument("--chatwoot-only", action="store_true", help="Only seed Chatwoot")
    args = parser.parse_args()

    specific = args.knowledge_only or args.eval_only or args.salesforce_only or args.chatwoot_only

    if not specific or args.knowledge_only:
        seed_knowledge_base()

    if not specific or args.eval_only:
        seed_evaluation_data()

    if not specific or args.salesforce_only:
        seed_salesforce()

    if not specific or args.chatwoot_only:
        asyncio.run(seed_chatwoot())

    logger.info("Seeding complete!")


if __name__ == "__main__":
    main()
