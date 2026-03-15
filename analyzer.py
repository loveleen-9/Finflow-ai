import anthropic
import json
import re
import os

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

def analyze_invoice(data, validation):
    print("\n[STEP 3] Running AI fraud analysis...")

    prompt = f"""You are a fraud detection expert.
Analyze this invoice and return ONLY valid JSON:
{{
  "risk_level": "LOW or MEDIUM or HIGH",
  "risk_score": 0,
  "flags": [],
  "recommendation": "AUTO_APPROVE or MANUAL_REVIEW or REJECT",
  "reasoning": ""
}}

INVOICE: {json.dumps(data)}
VALIDATION: {json.dumps(validation)}"""

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=800,
        messages=[{"role": "user", "content": prompt}]
    )

    raw = re.sub(r"```json|```", "", message.content[0].text).strip()

    try:
        result = json.loads(raw)
        print(f"  Risk: {result.get('risk_level')} ({result.get('risk_score')}/100)")
        print(f"  Decision: {result.get('recommendation')}")
        return result
    except:
        return {"risk_level": "MEDIUM", "risk_score": 50,
                "flags": ["Analysis failed"], "recommendation": "MANUAL_REVIEW", "reasoning": ""}