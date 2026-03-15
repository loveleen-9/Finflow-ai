import os
import fitz
import pandas as pd
import anthropic

def read_file(filepath):
    ext = os.path.splitext(filepath)[1].lower()
    print(f"\n[FILE READER] Reading {ext} file...")
    if ext == ".pdf":
        return read_pdf(filepath)
    elif ext in [".xlsx", ".xls", ".csv"]:
        return read_excel(filepath)
    elif ext in [".jpg", ".jpeg", ".png"]:
        return read_image(filepath)
    else:
        return None, "Unsupported file type"

def read_pdf(filepath):
    try:
        doc = fitz.open(filepath)
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        print(f"  Extracted {len(text)} characters from PDF")

        # If little/no text found, the PDF is likely image-based — use Vision OCR
        if len(text.strip()) < 80:
            print("  Low text yield — trying Vision OCR on PDF pages...")
            return read_pdf_as_image(filepath)

        return text, None
    except Exception as e:
        return None, str(e)

def read_pdf_as_image(filepath):
    try:
        import base64
        client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        doc = fitz.open(filepath)
        all_text = []
        for page in doc:
            pix = page.get_pixmap(dpi=150)
            img_bytes = pix.tobytes("png")
            image_data = base64.standard_b64encode(img_bytes).decode("utf-8")
            message = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=500,
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": image_data}},
                        {"type": "text", "text": "Extract all invoice text from this image. Return the raw text only."}
                    ]
                }]
            )
            all_text.append(message.content[0].text)
        doc.close()
        result = "\n".join(all_text)
        print(f"  Vision OCR extracted {len(result)} characters")
        return result, None
    except Exception as e:
        return None, str(e)

def read_excel(filepath):
    try:
        ext = os.path.splitext(filepath)[1].lower()
        if ext == ".csv":
            df = pd.read_csv(filepath)
        else:
            df = pd.read_excel(filepath)
        text = df.to_string(index=False)
        print(f"  Extracted {len(df)} rows from spreadsheet")
        return text, None
    except Exception as e:
        return None, str(e)

def read_image(filepath):
    try:
        import base64
        client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        with open(filepath, "rb") as f:
            image_data = base64.standard_b64encode(f.read()).decode("utf-8")
        ext = os.path.splitext(filepath)[1].lower().replace(".", "")
        media_type = "image/jpeg" if ext in ["jpg","jpeg"] else "image/png"
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=500,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": image_data}},
                    {"type": "text", "text": "Extract all invoice text from this image. Return the raw text only."}
                ]
            }]
        )
        text = message.content[0].text
        print(f"  Extracted text from image using AI vision")
        return text, None
    except Exception as e:
        return None, str(e)