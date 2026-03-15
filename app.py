from flask import Flask, render_template, request, jsonify, Response
import uuid
from file_reader import read_file
import anthropic
import json
import re
import os
import queue
import threading
from dotenv import load_dotenv

load_dotenv(override=True)

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Remove any 0-byte temp files left from interrupted requests
for _f in os.listdir(UPLOAD_FOLDER):
    _p = os.path.join(UPLOAD_FOLDER, _f)
    if os.path.getsize(_p) == 0:
        os.remove(_p)

SAMPLE_INVOICES = {
    "clean": """
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
""",
    "suspicious": """
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
}

def get_client():
    api_key = os.getenv("ANTHROPIC_API_KEY")
    return anthropic.Anthropic(api_key=api_key)

def extract_invoice(invoice_text, log):
    log("🔍 Tool 1: Extracting invoice fields with AI...")
    client = get_client()
    prompt = f"""Extract fields from this invoice. Return ONLY valid JSON:
{{
  "invoice_number": "",
  "vendor_name": "",
  "date": "",
  "due_date": "",
  "currency": "USD",
  "subtotal": 0.0,
  "tax": 0.0,
  "other_fees": 0.0,
  "total_due": 0.0,
  "notes": ""
}}
For "currency" use the 3-letter ISO code. Detect it from any symbol or label in the invoice:
- ₹, Rs., Rs, INR, Rupees, Rupee → INR
- $, USD, US$ → USD
- €, EUR → EUR
- £, GBP → GBP
- د.إ, AED, Dirham → AED
- ¥, JPY, CNY → JPY or CNY based on context
- S$, SGD → SGD
- If no currency is found, infer from vendor country or invoice origin. Only default to USD if truly no indication exists.
Always return "date" and "due_date" in YYYY-MM-DD format. Convert any format (e.g. 10/03/2026, March 10 2026, 10-Mar-26) to YYYY-MM-DD.
Use "other_fees" for any additional charges beyond subtotal and tax (e.g. shipping, handling, discounts, surcharges). Use a negative value for discounts.
INVOICE:
{invoice_text}"""
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=400,
        messages=[{"role": "user", "content": prompt}]
    )
    raw = re.sub(r"```json|```", "", message.content[0].text).strip()
    try:
        data = json.loads(raw)
        log(f"✅ Extracted: {data.get('invoice_number')} from {data.get('vendor_name')} [{data.get('currency','USD')}]")
        return data
    except:
        log("❌ Extraction failed")
        return {"error": "failed"}

def validate_invoice(data, log):
    log("🔎 Tool 2: Validating invoice data...")
    errors = []
    warnings = []
    for field in ["invoice_number", "vendor_name", "date", "subtotal", "total_due"]:
        if not data.get(field):
            errors.append(f"Missing field: {field}")
    try:
        expected = round(
            float(data.get("subtotal", 0)) +
            float(data.get("tax", 0)) +
            float(data.get("other_fees", 0)), 2)
        actual = float(data.get("total_due", 0))
        if abs(expected - actual) > 0.10:
            errors.append(f"Math error: {expected} != {actual}")
            log(f"❌ Math error detected: {expected} ≠ {actual}")
        else:
            log("✅ Math check passed")
    except:
        errors.append("Could not verify math")
    if "urgent" in str(data.get("notes", "")).lower():
        warnings.append("Urgent payment pressure detected")
        log("⚠️  Urgency pressure found in notes")
    result = {"is_valid": len(errors) == 0, "errors": errors, "warnings": warnings}
    log(f"✅ Validation done — {len(errors)} error(s), {len(warnings)} warning(s)")
    return result

def analyze_invoice(data, validation, log):
    log("🤖 Tool 3: Running AI fraud analysis...")
    client = get_client()
    from datetime import date
    today = date.today().isoformat()
    prompt = f"""You are a fraud detection expert. Today's date is {today}.
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
        log(f"🔍 Risk Score: {result.get('risk_score')}/100 — {result.get('risk_level')}")
        return result
    except:
        return {"risk_level": "MEDIUM", "risk_score": 50, "flags": [], "recommendation": "MANUAL_REVIEW", "reasoning": ""}

@app.route("/upload", methods=["POST"])
def upload():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400
    ext = os.path.splitext(file.filename)[1].lower()
    allowed = [".pdf", ".xlsx", ".xls", ".csv", ".jpg", ".jpeg", ".png"]
    if ext not in allowed:
        return jsonify({"error": f"File type {ext} not supported"}), 400
    filename = str(uuid.uuid4()) + ext
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)
    text, error = read_file(filepath)
    os.remove(filepath)
    if error:
        return jsonify({"error": error}), 500
    return jsonify({"text": text, "filename": file.filename})
@app.route("/")
def index():
    return render_template("dashboard.html")

@app.route("/health")
def health():
    key = os.getenv("ANTHROPIC_API_KEY", "")
    return jsonify({
        "status": "ok",
        "api_key_set": bool(key),
        "api_key_prefix": key[:12] + "..." if key else "NOT SET"
    })

@app.route("/process", methods=["POST"])
def process():
    data = request.json
    invoice_type = data.get("invoice_type")
    custom_text = data.get("custom_text", "").strip()

    if custom_text:
        invoice_text = custom_text
        source = "uploaded file / custom text"
    elif invoice_type and invoice_type in SAMPLE_INVOICES:
        invoice_text = SAMPLE_INVOICES[invoice_type]
        source = f"sample invoice ({invoice_type})"
    else:
        invoice_text = SAMPLE_INVOICES["clean"]
        source = "sample invoice (clean)"

    def generate():
        def log(msg):
            yield f"data: {json.dumps({'type': 'log', 'message': msg})}\n\n"

        logs = []
        def logger(msg):
            logs.append(msg)

        try:
            yield f"data: {json.dumps({'type': 'start'})}\n\n"
            yield f"data: {json.dumps({'type': 'log', 'message': f'📄 Source: {source}'})}\n\n"

            invoice_data = extract_invoice(invoice_text, logger)
            for l in logs: yield f"data: {json.dumps({'type': 'log', 'message': l})}\n\n"
            logs.clear()

            if "error" in invoice_data:
                yield f"data: {json.dumps({'type': 'error', 'message': 'Extraction failed'})}\n\n"
                return

            validation = validate_invoice(invoice_data, logger)
            for l in logs: yield f"data: {json.dumps({'type': 'log', 'message': l})}\n\n"
            logs.clear()

            if any("Math" in e or "DUPLICATE" in e for e in validation["errors"]):
                logger("⚠️  Critical error — skipping AI analysis")
                analysis = {"risk_level": "HIGH", "risk_score": 95, "flags": validation["errors"], "recommendation": "REJECT", "reasoning": "Critical validation errors found"}
            else:
                analysis = analyze_invoice(invoice_data, validation, logger)

            for l in logs: yield f"data: {json.dumps({'type': 'log', 'message': l})}\n\n"
            logs.clear()

            decision = analysis.get("recommendation", "MANUAL_REVIEW")
            if decision == "AUTO_APPROVE" and float(invoice_data.get("total_due", 0)) > 5000:
                decision = "MANUAL_REVIEW"
                logger("⚠️  Amount over $5,000 — escalating to manual review")

            for l in logs: yield f"data: {json.dumps({'type': 'log', 'message': l})}\n\n"

            result = {
                "type": "result",
                "invoice_number": invoice_data.get("invoice_number"),
                "vendor": invoice_data.get("vendor_name"),
                "currency": invoice_data.get("currency", "USD"),
                "total": invoice_data.get("total_due"),
                "risk_level": analysis.get("risk_level"),
                "risk_score": analysis.get("risk_score"),
                "decision": decision,
                "flags": analysis.get("flags", []),
                "warnings": validation.get("warnings", []),
                "reasoning": analysis.get("reasoning", "")
            }
            yield f"data: {json.dumps(result)}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return Response(generate(), mimetype="text/event-stream")

@app.route("/bulk-process", methods=["POST"])
def bulk_process():
    files = request.files.getlist("files")
    if not files:
        return jsonify({"error": "No files uploaded"}), 400
    allowed = [".pdf", ".xlsx", ".xls", ".csv", ".jpg", ".jpeg", ".png"]

    # Save all files to disk before streaming starts —
    # file streams are unavailable once Flask leaves the request context
    saved = []
    for file in files:
        filename = file.filename
        ext = os.path.splitext(filename)[1].lower()
        if ext not in allowed:
            saved.append({"filename": filename, "error": f"Unsupported type {ext}", "path": None})
        else:
            tmp_path = os.path.join(UPLOAD_FOLDER, str(uuid.uuid4()) + ext)
            file.save(tmp_path)
            saved.append({"filename": filename, "path": tmp_path})

    def generate():
        total = len(saved)
        yield f"data: {json.dumps({'type': 'bulk_start', 'total': total})}\n\n"

        for i, sf in enumerate(saved):
            filename = sf["filename"]
            if sf.get("error"):
                yield f"data: {json.dumps({'type': 'bulk_item', 'index': i, 'filename': filename, 'error': sf['error']})}\n\n"
                continue

            tmp_path = sf["path"]
            try:
                text, err = read_file(tmp_path)
                os.remove(tmp_path)

                if err or not (text or "").strip():
                    yield f"data: {json.dumps({'type': 'bulk_item', 'index': i, 'filename': filename, 'error': err or 'No text extracted'})}\n\n"
                    continue

                logs = []
                def logger(msg, _l=logs): _l.append(msg)

                invoice_data = extract_invoice(text, logger)
                if "error" in invoice_data:
                    yield f"data: {json.dumps({'type': 'bulk_item', 'index': i, 'filename': filename, 'error': 'Extraction failed'})}\n\n"
                    continue

                validation = validate_invoice(invoice_data, logger)

                if any("Math" in e or "DUPLICATE" in e for e in validation["errors"]):
                    analysis = {"risk_level": "HIGH", "risk_score": 95, "flags": validation["errors"], "recommendation": "REJECT", "reasoning": "Critical validation errors found"}
                else:
                    analysis = analyze_invoice(invoice_data, validation, logger)

                decision = analysis.get("recommendation", "MANUAL_REVIEW")
                if decision == "AUTO_APPROVE" and float(invoice_data.get("total_due", 0) or 0) > 5000:
                    decision = "MANUAL_REVIEW"

                yield f"data: {json.dumps({'type': 'bulk_item', 'index': i, 'filename': filename, 'invoice_number': invoice_data.get('invoice_number'), 'vendor': invoice_data.get('vendor_name'), 'currency': invoice_data.get('currency', 'USD'), 'total': invoice_data.get('total_due'), 'date': invoice_data.get('date'), 'risk_score': analysis.get('risk_score'), 'decision': decision, 'flags': analysis.get('flags', []), 'warnings': validation.get('warnings', []), 'reasoning': analysis.get('reasoning', '')})}\n\n"

            except Exception as e:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
                yield f"data: {json.dumps({'type': 'bulk_item', 'index': i, 'filename': filename, 'error': str(e)})}\n\n"

        yield f"data: {json.dumps({'type': 'bulk_done', 'total': total})}\n\n"

    return Response(generate(), mimetype="text/event-stream")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host="0.0.0.0", port=port)
