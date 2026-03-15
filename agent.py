from extractor import extract_invoice
from validator import validate_invoice
from analyzer import analyze_invoice

processed = []

def run_agent(invoice_text):
    print("\n" + "="*50)
    print("   FINFLOW AI AGENT — Processing Invoice")
    print("="*50)

    data = extract_invoice(invoice_text)
    if "error" in data:
        print("STOPPED: Extraction failed")
        return

    validation = validate_invoice(data, processed)

    if any("DUPLICATE" in e or "Math" in e for e in validation["errors"]):
        print("\n  Critical error found - skipping AI analysis")
        analysis = {"risk_level": "HIGH", "risk_score": 95,
                    "flags": validation["errors"],
                    "recommendation": "REJECT",
                    "reasoning": "Critical validation errors"}
    else:
        analysis = analyze_invoice(data, validation)

    decision = analysis.get("recommendation", "MANUAL_REVIEW")
    if decision == "AUTO_APPROVE" and float(data.get("total_due", 0)) > 5000:
        decision = "MANUAL_REVIEW"
        print("\n  Amount over $5000 - escalating to manual review")

    print("\n" + "-"*50)
    print(f"  Invoice : {data.get('invoice_number')}")
    print(f"  Vendor  : {data.get('vendor_name')}")
    print(f"  Amount  : ${data.get('total_due')}")
    print(f"  Risk    : {analysis.get('risk_level')} ({analysis.get('risk_score')}/100)")
    print(f"  DECISION: {decision}")
    if analysis.get("flags"):
        print(f"  Flags   :")
        for f in analysis["flags"]:
            print(f"    - {f}")
    print("="*50)

    processed.append(data.get("invoice_number"))
    return decision
    