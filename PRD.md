# FinFlow AI — Product Requirements Document

## 1. Overview

**Product Name:** FinFlow AI
**Type:** Web Application
**Stack:** Python / Flask / Anthropic Claude API
**Version:** 1.0

FinFlow AI is an AI-powered invoice fraud detection tool. It accepts invoices in multiple formats, runs them through a three-step AI pipeline (extract → validate → analyze), and returns a risk score, flags, and an actionable decision in real time.

---

## 2. Problem Statement

Finance and accounts-payable teams manually review hundreds of invoices. Fraudulent or erroneous invoices — duplicate submissions, math errors, inflated amounts, suspicious vendors — slip through due to volume and human fatigue. FinFlow AI automates the initial triage layer, surfacing high-risk invoices instantly so reviewers focus only on what matters.

---

## 3. Goals

| Goal | Metric |
|------|--------|
| Reduce manual review time | Auto-approve low-risk invoices without human touch |
| Catch fraud signals early | Flag math errors, urgency language, overdue dates, anomalous amounts |
| Support diverse invoice formats | PDF, Excel, CSV, JPG, PNG all processed correctly |
| Give reviewers full context | Risk score + flags + reasoning visible on every result |
| Enable audit trail | All analyses persisted in History tab |

---

## 4. Users

**Primary:** Accounts-payable clerks and finance managers who process vendor invoices.
**Secondary:** Finance directors who need an audit trail and override capability.

---

## 5. Features

### 5.1 Invoice Input

| Method | Description |
|--------|-------------|
| Sample cards | One-click pre-loaded invoices (clean, suspicious, etc.) |
| File upload | Drag-and-drop or browse — PDF, Excel, CSV, JPG, PNG |
| Text paste | Paste raw invoice text; auto-runs after 1.5 s idle |
| Bulk upload | Select multiple files; each processed sequentially |

### 5.2 AI Pipeline

**Step 1 — Extract** (`claude-haiku-4-5`)
- Parses invoice text into structured JSON
- Fields: invoice number, vendor name, total due, subtotal, tax, due date, notes

**Step 2 — Validate** (rule-based)
- Math check: subtotal + tax = total (tolerance ±$0.10)
- Missing required fields check
- Urgency keyword detection (e.g. "immediate", "overdue", "final notice")
- Date sanity: past-due detection, future-dated invoices

**Step 3 — Analyze** (`claude-sonnet-4-6`)
- Fraud risk score: 0–100
- Risk level: LOW / MEDIUM / HIGH
- Flags list: specific anomalies found
- Recommendation reasoning: plain-English explanation
- Decision: `AUTO_APPROVE` / `MANUAL_REVIEW` / `REJECT`

### 5.3 Real-Time Streaming

- Pipeline progress streamed via Server-Sent Events (SSE)
- Live agent log visible while processing
- No page reload required

### 5.4 Result Panel

- Decision badge (color-coded: green / amber / red)
- Risk score bar (animated fill)
- Flags list
- Full reasoning text
- Manual override buttons (MANUAL_REVIEW only): **Pass** / **Fail**
- Email vendor panel (REJECT only): pre-filled rejection email

### 5.5 Bulk Upload

- Multi-file picker in sidebar
- Per-file result cards with: decision badge, vendor, amount, risk bar, flags, reasoning snippet
- Pass/Fail or Email button per card
- Cards rendered as processing completes (not all at end)

### 5.6 History Tab

- All analyses auto-saved to `localStorage` (key: `finflow_history`, max 500 entries)
- Grouped display with date range filter
- From / To date inputs with max 1-month range enforced
- Search/filter by vendor or invoice number
- Click any entry to reopen full result
- Clear history button
- Badge on tab showing total count

### 5.7 Email Vendor (on REJECT)

- Pre-filled fields: To (vendor email if available), Subject, Body
- Body includes: vendor name, invoice number, amount, rejection flags as bullet points
- **Open in Email App** — opens `mailto:` URL in default email client
- **Copy Message** — copies full email text to clipboard

### 5.8 Manual Override (on MANUAL_REVIEW)

- **Pass** — marks invoice as approved
- **Fail** — marks invoice as rejected
- Override recorded in history entry

### 5.9 Multi-Currency Support

20+ currencies auto-detected from invoice symbols:

`$` `€` `£` `₹` `¥` `د.إ` `S$` `CHF` `kr` `₩` `฿` `₺` `R$` `zł` `Kč` `HK$` `MX$` `A$` `C$` `NZ$`

---

## 6. UI / UX Requirements

- **Theme:** White and blue (`#1a56db` accent, `#eef3fb` background)
- **Font:** Inter (Google Fonts), minimum 12px body text
- **Layout:** 360px fixed sidebar + fluid content area
- **Responsive:** Sidebar collapses on narrow viewports
- **Accessibility:** Sufficient contrast on all text, focus states on interactive elements
- **Loading states:** Spinner during processing, disabled buttons while streaming

---

## 7. Technical Requirements

| Area | Requirement |
|------|-------------|
| Backend | Python 3.10+, Flask |
| AI | Anthropic Python SDK, `claude-haiku-4-5-20251001` + `claude-sonnet-4-6` |
| PDF parsing | PyMuPDF (`fitz`); Vision OCR fallback for scanned PDFs |
| Excel / CSV | pandas + openpyxl |
| Streaming | Flask `Response` with `text/event-stream` content type |
| Storage | Browser `localStorage` (no server-side DB required) |
| Secrets | `ANTHROPIC_API_KEY` via `.env` (never committed) |
| Uploads | Temp folder auto-cleaned; `.gitkeep` tracks folder in git |

---

## 8. Decision Logic

| Condition | Decision |
|-----------|----------|
| Risk score ≤ 40, no critical flags | `AUTO_APPROVE` |
| Risk score 41–69, or minor flags | `MANUAL_REVIEW` |
| Risk score ≥ 70, or math error / critical flag | `REJECT` |

---

## 9. Sample Test Invoices

| File | Currency | Amount | Expected Decision |
|------|----------|--------|-------------------|
| `inv_INR_clean.pdf` | INR | ₹88,500 | AUTO_APPROVE |
| `inv_EUR_clean.pdf` | EUR | €8,996 | AUTO_APPROVE |
| `inv_GBP_review.pdf` | GBP | £11,530 | MANUAL_REVIEW |
| `inv_AED_suspicious.pdf` | AED | 30,000 | REJECT |
| `inv_SGD_clean.pdf` | SGD | S$10,900 | AUTO_APPROVE |
| `inv_JPY_clean.pdf` | JPY | ¥1,375,000 | AUTO_APPROVE |

---

## 10. Out of Scope (v1.0)

- User authentication / multi-tenant accounts
- Server-side database (history is client-only)
- ERP / accounting software integration (QuickBooks, SAP, etc.)
- Automated email sending (compose only, no SMTP)
- Mobile app
- Batch scheduling / cron jobs
- Custom rule configuration UI

---

## 11. Future Enhancements (v2.0 Candidates)

- Deploy to Railway / Render for public access
- PostgreSQL backend for shared history across users
- Configurable risk threshold slider
- Export history to CSV / Excel
- Dashboard summary: approval rate, total value flagged, top risky vendors
- Webhook integration to notify Slack / Teams on REJECT
- Side-by-side duplicate invoice detection
