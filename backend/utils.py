from math import pow
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
import os

def calculate_final_interest_rate(purpose, score):
    base = {
        "home": 0.075,
        "education": 0.085,
        "business": 0.10
    }

    if score < 600:
        return None

    rate = base.get(purpose, 0.10)

    if score >= 750:
        rate -= 0.01
    elif score < 650:
        rate += 0.015

    return round(rate, 4)

def compute_emi(principal, months, annual_rate):
    r = annual_rate / 12
    emi = principal * r * pow(1 + r, months) / (pow(1 + r, months) - 1)
    return round(emi, 2)

def calculate_foir(emi, salary):
    return round(emi / salary, 2)

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from datetime import datetime
import os

BASE_DIR = os.path.dirname(__file__)
PDF_DIR = os.path.join(BASE_DIR, "static_pdfs")
os.makedirs(PDF_DIR, exist_ok=True)


def generate_sanction_pdf(session_id: str, session: dict):
    file_name = f"sanction_{session_id}.pdf"
    file_path = os.path.join(PDF_DIR, file_name)

    c = canvas.Canvas(file_path, pagesize=A4)
    width, height = A4

    y = height - 50

    # ---------------- HEADER ----------------
    c.setFont("Helvetica-Bold", 18)
    c.drawString(50, y, "Loan Sanction Letter")

    y -= 30
    c.setFont("Helvetica", 10)
    c.drawString(50, y, f"Sanction Reference ID: {session_id}")
    y -= 15
    c.drawString(50, y, f"Date: {datetime.now().strftime('%d %B %Y')}")

    # ---------------- CUSTOMER DETAILS ----------------
    y -= 40
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y, "Customer Details")

    y -= 20
    c.setFont("Helvetica", 11)
    c.drawString(50, y, f"Name: {session['customer_profile']['name']}")
    y -= 15
    c.drawString(50, y, f"Phone: {session['customer_profile']['phone']}")
    y -= 15
    c.drawString(50, y, f"PAN: {session['customer_profile']['pan']}")

    # ---------------- LOAN DETAILS ----------------
    y -= 35
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y, "Loan Details")

    y -= 20
    c.setFont("Helvetica", 11)
    c.drawString(50, y, f"Loan Amount: ₹{session['loan_amount']}")
    y -= 15
    c.drawString(50, y, f"Tenure: {session['tenure_months']} months")
    y -= 15
    c.drawString(
        50,
        y,
        f"Interest Rate: {round(session['interest_rate'] * 100, 2)}% per annum"
    )
    y -= 15
    c.drawString(50, y, f"Monthly EMI: ₹{round(session['emi'], 2)}")

    # ---------------- FOOTER ----------------
    y -= 40
    c.setFont("Helvetica", 10)
    c.drawString(
        50,
        y,
        "This is a system-generated sanction letter issued by FinBot NBFC."
    )

    y -= 15
    c.drawString(
        50,
        y,
        "The loan is subject to terms and conditions of the lending institution."
    )

    c.showPage()
    c.save()

    return file_path

