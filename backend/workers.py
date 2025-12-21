import json
from .utils import (
    calculate_final_interest_rate,
    compute_emi,
    calculate_foir,
    generate_sanction_pdf
)



with open("backend/mock_crm.json") as f:
    CRM = json.load(f)

# ---------------- SALES AGENT ----------------
import random

FIELD_LABELS = {
    "loan_amount": "loan amount",
    "tenure_months": "loan tenure",
    "purpose": "loan purpose",
    "salary": "monthly salary",
    "phone": "phone number",
    "pan": "PAN number"
}

FIELD_ORDER = [
    "loan_amount",
    "tenure_months",
    "purpose",
    "salary",
    "salary_slip_uploaded",
    "phone",
    "pan"
]

ACK_MESSAGES = {
    "loan_amount": [
        "Got it 👍 Loan amount noted.",
        "Thanks, I’ve noted the loan amount.",
    ],
    "tenure_months": [
        "Perfect, tenure noted.",
        "Great, I’ve captured the loan duration.",
    ],
    "purpose": [
        "Understood. Loan purpose noted.",
        "Thanks for sharing the purpose.",
    ],
    "salary": [
        "Thanks 👍 Salary details noted.",
        "Got it, income recorded.",
    ],
    "salary_slip_uploaded" :[
        "Thanks, salary slip received.",
        "Salary slip uploaded successfully."
    ],
    "phone": [
        "Phone number noted.",
        "Thanks, I’ve saved your contact number.",
    ],
    "pan": [
        "PAN received. Thanks!",
        "Great, PAN noted successfully.",
    ]
}


ASK_MESSAGES = {
    "loan_amount": [
        "May I know how much loan amount you’re looking for?",
        "What loan amount should I consider for you?"
    ],
    "tenure_months": [
        "For how many months would you like to take this loan?",
        "What repayment duration are you comfortable with?"
    ],
    "purpose": [
        "What will you be using this loan for?",
        "Could you tell me the purpose of the loan?"
    ],
    "salary": [
        "To proceed, I’ll need your monthly salary.",
        "May I know your monthly income?"
    ],
    "salary_slip_uploaded" : [
        "Please upload your salary slip to continue.",
        "I’ll need your salary slip for verification. Kindly upload it."
    ],
    "phone": [
        "Please share your registered mobile number.",
        "Could you provide your phone number?"
    ],
    "pan": [
        "Lastly, may I have your PAN number?",
        "Please share your PAN to complete verification."
    ]
}


APPROVAL_MESSAGES = [
    (
        "🎉 That’s great news!\n\n"
        "I’ve carefully reviewed your details, and I’m happy to let you know that your loan has been approved. "
        "Your profile meets all our eligibility criteria, and everything looks good from our side. "
        "You can now go ahead and download your sanction letter below."
    ),
    (
        "✅ Congratulations!\n\n"
        "Based on your income, credit profile, and loan requirements, we’re pleased to approve your loan. "
        "This decision ensures a comfortable repayment plan while keeping your finances balanced. "
        "Please find your official sanction letter attached."
    ),
    (
        "🎊 Good news!\n\n"
        "Your loan application has been successfully approved after a thorough evaluation. "
        "We’ve ensured that the EMI fits well within your income, so repayments stay stress-free. "
        "You can download your sanction letter and proceed with confidence."
    ),
    (
        "😊 Happy to share an update!\n\n"
        "Everything checks out perfectly, and your loan is now approved. "
        "It was a pleasure assisting you through this process. "
        "Your sanction letter is ready for download below."
    )
]

async def sales_agent(session: dict):
    last_asked = session.get("last_asked_field")

    # ✅ Acknowledge ONLY the last asked field
    acknowledgement = ""
    if last_asked and session.get(last_asked):
        acknowledgement = random.choice(ACK_MESSAGES[last_asked])

    # ✅ Find next missing field
    for field in FIELD_ORDER:
        if not session.get(field):
            session["last_asked_field"] = field

            ask = random.choice(ASK_MESSAGES[field])

            if acknowledgement:
                return {
                    "reply": f"{acknowledgement}\n\n{ask}"
                }

            return {"reply": ask}

    # Nothing missing
    return {"reply": None}

# ---------------- KYC AGENT ----------------
async def verification_agent(session):
    for c in CRM:
        if c["phone"] == session["phone"] and c["pan"] == session["pan"]:
            return {
    "verified": True,
    "mock_score": c["mock_score"],
    "customer_profile": c
}

    return {
    "verified": False,
    "reason": (
        f"I couldn’t find a matching record for the phone number **{session['phone']}** "
        f"with PAN **{session['pan']}** in our system. "
        "Please double-check the details and try again."
    )
}

# ---------------- SALARY SLIP AGENT ----------------
import random

INVALID_SLIP_MESSAGES = [
    "I’m sorry 😕 — we couldn’t verify your salary slip.",
    "The uploaded salary slip doesn’t meet our verification requirements.",
    "We’re unable to validate the income document you shared."
]

async def salary_slip_agent(session):
    # Already verified → continue
    if session.get("salary_slip_verified"):
        return {"verified": True}

    # Explicit invalid slip case
    if session.get("salary_slip_status") == "invalid":
        return {
            "verified": False,
            "final_reject": True,
            "reason": random.choice(INVALID_SLIP_MESSAGES)
        }

    # Ask for upload
    session["last_asked_field"] = "salary"
    return {
        "verified": False,
        "final_reject": False,
        "reason": "I’ll need your salary slip for verification. Kindly upload it."
    }




# ---------------- UNDERWRITING ----------------
async def underwriting_agent(session):
    score = session["mock_score"]

    if score < 700:
        return {
            "decision": "rejected",
            "reason": (
                "I checked your credit profile carefully. "
                "At the moment, your credit score is below our minimum eligibility criteria. "
                "Improving your score can significantly increase approval chances in the future."
            )
        }



    rate = calculate_final_interest_rate(session["purpose"], score)

    emi = compute_emi(
        session["loan_amount"],
        session["tenure_months"],
        rate
    )

    foir = calculate_foir(emi, session["salary"])

    if foir > 0.20:
     return {
        "decision": "rejected",
        "reason": (
            "I checked your income details carefully. "
            "At the moment, the monthly EMI comes to more than 20% of your salary, "
            "which could make repayments stressful. "
            "To keep things comfortable for you, I won’t be able to approve this loan right now."
        )
    }

    return {
        "decision": "approved",
        "emi": emi,
        "interest_rate": rate
    }

# ---------------- SANCTION ----------------
async def sanction_agent(session, session_id):
    return {"pdf_path": generate_sanction_pdf(session_id, session)}
