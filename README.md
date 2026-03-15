# FinFlow AI — Invoice Fraud Detection

An AI-powered invoice fraud detection web app built with **Flask** and the **Anthropic Claude API**. Upload invoices in any format, and three AI agents automatically extract, validate, and analyze them for fraud risk in real time.

---

## Features

- **Auto-analysis** — click a sample, upload a file, or paste text and agents run instantly
- **Real-time streaming** — live agent log output via Server-Sent Events (SSE)
- **Multi-format upload** — PDF, Excel, CSV, JPG, PNG
- **Vision OCR fallback** — scanned/image-based PDFs are processed via Claude's vision
- **20+ currencies** — auto-detected from invoice symbols (₹, €, £, د.إ, S$, ¥, …)
- **Bulk upload** — process multiple invoices at once with per-file card results
- **History tab** — all results persisted in localStorage, filterable by date range
- **Manual override** — Pass / Fail buttons for MANUAL_REVIEW decisions
- **Email vendor** — pre-filled rejection email compose on REJECT decisions
- **Math validation** — subtotal + tax + fees = total check built in

---

## AI Pipeline

| Step | Model | Task |
|------|-------|------|
| 1 — Extract | `claude-haiku-4-5` | Parse invoice fields → structured JSON |
| 2 — Validate | Rule-based | Math check, missing fields, urgency flags |
| 3 — Analyze | `claude-sonnet-4-6` | Fraud risk score, flags, recommendation |

**Decisions:** `AUTO_APPROVE` · `MANUAL_REVIEW` · `REJECT`

---

## Tech Stack

- **Backend** — Python, Flask, Anthropic Python SDK
- **Frontend** — Vanilla JS, Inter font, CSS custom properties
- **PDF** — PyMuPDF (`fitz`) with Vision OCR fallback
- **Excel/CSV** — pandas
- **Streaming** — Server-Sent Events (SSE)
- **Storage** — localStorage (client-side history)

---

## Getting Started

### Prerequisites

- Python 3.10+
- An [Anthropic API key](https://console.anthropic.com/)

### Installation

```bash
git clone https://github.com/loveleen-username/finflow-ai.git
cd finflow-ai
pip install flask anthropic python-dotenv pymupdf pandas openpyxl
```

### Configuration

Create a `.env` file in the root directory:

```env
ANTHROPIC_API_KEY=your_api_key_here
```

### Run

```bash
python app.py
```

Open **http://localhost:5000** in your browser.

---

## Project Structure

```
finflow-ai/
├── app.py              # Flask routes, SSE streaming, AI pipeline
├── file_reader.py      # PDF, Excel, CSV, image parsing + Vision OCR
├── validator.py        # Standalone validation logic (CLI reference)
├── templates/
│   └── dashboard.html  # Single-page UI (HTML + CSS + JS)
├── bulk_test/          # Sample invoices in 6 currencies for testing
│   ├── inv_INR_clean.pdf
│   ├── inv_EUR_clean.pdf
│   ├── inv_GBP_review.pdf
│   ├── inv_AED_suspicious.pdf
│   ├── inv_SGD_clean.pdf
│   └── inv_JPY_clean.pdf
├── uploads/            # Temp upload folder (auto-cleaned)
└── .env                # API key (not committed)
```

---

## Usage

### Single Invoice
1. Click a **sample card** — or —
2. **Upload** a file (drag & drop or browse) — or —
3. **Paste** invoice text into the textarea (auto-runs after 1.5 s)

The agent streams its progress live, then shows a result panel with risk score, flags, and decision.

### Bulk Upload
Click **"Select multiple invoices"** in the sidebar, pick several files. Each invoice is processed sequentially with a card showing decision, risk bar, flags, and reasoning. Click any card to view full details.

### History
Switch to the **History** tab to see all past analyses. Use the **date range picker** (max 1 month) and **search bar** to filter. Click any entry to reopen its full result.

### Manual Override
When the agent returns **MANUAL REVIEW**, Pass / Fail buttons let you override the decision manually.

### Email Vendor
When the agent returns **REJECT**, an email compose panel appears pre-filled with the vendor name, invoice number, amount, and rejection reasons. Click **Open in Email App** or **Copy Message**.

---

## Sample Invoices

The `bulk_test/` folder contains 6 test PDFs:

| File | Currency | Expected Decision |
|------|----------|-------------------|
| `inv_INR_clean.pdf` | INR ₹88,500 | AUTO_APPROVE |
| `inv_EUR_clean.pdf` | EUR €8,996 | AUTO_APPROVE |
| `inv_GBP_review.pdf` | GBP £11,530 | MANUAL_REVIEW |
| `inv_AED_suspicious.pdf` | AED 30,000 | REJECT |
| `inv_SGD_clean.pdf` | SGD S$10,900 | AUTO_APPROVE |
| `inv_JPY_clean.pdf` | JPY ¥1,375,000 | AUTO_APPROVE |

---

## Environment Variables

| Variable | Description |
|----------|-------------|
| `ANTHROPIC_API_KEY` | Your Anthropic API key (required) |

---

## License

MIT
