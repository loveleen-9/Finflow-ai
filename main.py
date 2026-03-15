from dotenv import load_dotenv
from agent import run_agent

load_dotenv()

invoice1 = """
INVOICE
Invoice Number: INV-2024-001
Date: 2024-03-10
Due Date: 2024-04-10
FROM: TechSupplies Co.
TO: Acme Corporation

ITEMS:
Cloud Storage License x5 = $1,000.00
API Access Monthly = $150.00
Support and Maintenance = $300.00

SUBTOTAL: $1,450.00
TAX (10%): $145.00
TOTAL DUE: $1,595.00
Payment: Bank Transfer
"""

invoice2 = """
INVOICE
Invoice Number: INV-2024-002
Date: 2024-03-11
Due Date: 2024-03-14
FROM: SuspiciousVendor LLC
TO: Acme Corporation

ITEMS:
Consulting Services 10hrs = $5,000.00
Travel Expenses = $999.00
Miscellaneous Fees = $200.00

SUBTOTAL: $6,199.00
TAX (10%): $619.90
TOTAL DUE: $7,500.00
Payment: Offshore Wire Transfer
Notes: URGENT - pay within 3 days or penalty applies
"""

print("Processing Invoice 1...")
run_agent(invoice1)

print("\nProcessing Invoice 2...")
run_agent(invoice2)

