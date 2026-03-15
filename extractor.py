import anthropic
import json
import re
import os

def extract_invoice(invoice_text):
    print("\n[STEP 1] Extracting invoice fields with AI...")
    
    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

    prompt = f"""Extract fields from this invoice. Return ONLY valid JSON:
{{
  "invoice_number": "",
  "vendor_name": "",
  "total_due": 0.0,
  "subtotal": 0.0,
  "tax": 0.0,
  "due_date": "",
  "notes": ""
}}

INVOICE:
{invoice_text}"""

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}]
    )

    raw = re.sub(r"```json|```", "", message.content[0].text).strip()

    try:
        data = json.loads(raw)
        print(f"  Extracted: {data.get('invoice_number')} from {data.get('vendor_name')}")
        return data
    except:
        print("  ERROR: Could not extract invoice data")
        return {"error": "failed"}