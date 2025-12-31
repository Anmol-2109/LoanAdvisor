# import re

# def extract_intent(text: str) -> dict:
#     t = text.lower()

#     result = {
#         "loan_amount": None,
#         "tenure_months": None,
#         "purpose": None,
#         "phone": None,
#         "pan": None,
#         "salary": None
#     }

#     # Phone
#     m = re.search(r"\b[6-9]\d{9}\b", text)
#     if m:
#         result["phone"] = m.group()

#     # PAN
#     m = re.search(r"\b[A-Z]{5}\d{4}[A-Z]\b", text.upper())
#     if m:
#         result["pan"] = m.group()

#     # Salary
#     m = re.search(r"(salary|income)\s*(is|:)?\s*(\d{4,7})", t)
#     if m:
#         result["salary"] = int(m.group(3))

#     # Loan amount
#     if "lakh" in t:
#         m = re.search(r"(\d+)\s*lakh", t)
#         if m:
#             result["loan_amount"] = int(m.group(1)) * 100000
#     else:
#         m = re.search(r"loan.*?(\d{4,7})", t)
#         if m:
#             result["loan_amount"] = int(m.group(1))

#     # Tenure
#     m = re.search(r"(\d+)\s*(month|months)", t)
#     if m:
#         result["tenure_months"] = int(m.group(1))

#     # Purpose
#     if "home" in t:
#         result["purpose"] = "home"
#     elif "education" in t:
#         result["purpose"] = "education"
#     elif "business" in t:
#         result["purpose"] = "business"

#     return result

import os
import json
import google.generativeai as genai

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model = genai.GenerativeModel("gemini-1.5-flash")

INTENT_SCHEMA = {
    "loan_amount": "number or null",
    "tenure_months": "number or null",
    "purpose": "home | education | business | null",
    "salary": "number or null",
    "phone": "string or null",
    "pan": "string or null"
}

def extract_intent(text: str) -> dict:
    prompt = f"""
You are an intent extraction engine for a loan chatbot.

Extract the following fields from the user message.
Return STRICT JSON only. No explanation.

Schema:
{json.dumps(INTENT_SCHEMA, indent=2)}

User message:
{text}
"""

    response = model.generate_content(prompt)
    raw = response.text.strip()

    try:
        return json.loads(raw)
    except Exception:
        # Safe fallback
        return {k: None for k in INTENT_SCHEMA}
