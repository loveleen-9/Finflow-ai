def validate_invoice(data, past_invoices):
    print("\n[STEP 2] Validating invoice...")
    errors = []
    warnings = []

    for field in ["invoice_number", "vendor_name", "total_due"]:
        if not data.get(field):
            errors.append(f"Missing: {field}")

    try:
        expected = round(float(data.get("subtotal", 0)) + float(data.get("tax", 0)), 2)
        actual = float(data.get("total_due", 0))
        if abs(expected - actual) > 0.10:
            errors.append(f"Math error: {expected} != {actual}")
        else:
            print("  Math check passed")
    except:
        errors.append("Could not check math")

    if data.get("invoice_number") in past_invoices:
        errors.append("DUPLICATE invoice!")
    else:
        print("  No duplicate found")

    if "urgent" in str(data.get("notes", "")).lower():
        warnings.append("Urgent payment pressure detected")

    result = {"is_valid": len(errors) == 0, "errors": errors, "warnings": warnings}
    print(f"  Valid: {result['is_valid']} | Errors: {len(errors)} | Warnings: {len(warnings)}")
    return result