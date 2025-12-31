from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
import uuid, os

import random
from .workers import APPROVAL_MESSAGES
import asyncio

from .workers import salary_slip_agent


from .intent_llm import extract_intent
from .workers import (
    sales_agent,
    verification_agent,
    underwriting_agent,
    sanction_agent
)

app = FastAPI(title="FinBot")
SESSIONS = {}

class ChatRequest(BaseModel):
    text: str
    session_id: str | None = None

@app.post("/api/message")
async def chat(req: ChatRequest):
    session_id = req.session_id or str(uuid.uuid4())
    session = SESSIONS.setdefault(session_id, {})

    # ---------------- Extract intent ----------------
    # ---------------- Extract intent ----------------
    if req.text != "__continue__":
       extracted = extract_intent(req.text)
       session.update({k: v for k, v in extracted.items() if v is not None})


    # ---------------- SALES AGENT ----------------
    sales = await sales_agent(session)
    if sales.get("reply"):
        await asyncio.sleep(0.8)
        return {
            "reply": sales["reply"],
            "session_id": session_id
        }

    # =====================================================
    # 🔽 ADD THIS BLOCK EXACTLY HERE
    # ---------------- SALARY SLIP (ALWAYS REQUIRED) ----------------
    salary_slip = await salary_slip_agent(session)

    if not salary_slip["verified"]:

    # 🚫 FINAL REJECTION CASE
        if salary_slip.get("final_reject"):
           return {
            "reply": (
                f"{salary_slip['reason']}\n\n"
                "Without a valid salary slip, we won’t be able to proceed with this loan application.\n\n"
                "You can reapply anytime with a valid income document."
            ),
            "session_id": session_id
        }

    # ⏳ Ask for upload
        return {
        "reply": salary_slip["reason"],
        "need_salary_slip": True,
        "session_id": session_id
    }

    # =====================================================

    # ---------------- KYC ----------------
    ver = await verification_agent(session)
    if not ver["verified"]:
        await asyncio.sleep(0.8)
        return {
            "reply": ver["reason"],
            "session_id": session_id
        }

    session["mock_score"] = ver["mock_score"]
    session["customer_profile"] = ver["customer_profile"]

    # ---------------- UNDERWRITING ----------------
    uw = await underwriting_agent(session)
    if uw["decision"] == "rejected":
        await asyncio.sleep(0.8)
        return {
            "reply": uw["reason"],
            "session_id": session_id
        }

    session.update(uw)

    # ---------------- SANCTION ----------------
    sanction = await sanction_agent(session, session_id)
    await asyncio.sleep(0.8)

    return {
        "reply": random.choice(APPROVAL_MESSAGES),
        "emi": session["emi"],
        "interest_rate": session["interest_rate"],
        "pdf": f"/api/pdf/{os.path.basename(sanction['pdf_path'])}",
        "session_id": session_id
    }



@app.post("/api/upload-salary-slip")
async def upload_salary_slip(session_id: str):
    if session_id not in SESSIONS:
        raise HTTPException(400, "Invalid session")

    session = SESSIONS[session_id]

    session["salary_slip_uploaded"] = True
    session["salary_slip_verified"] = False
    session["salary_slip_invalid"] = True   # MATCH AGENT

    return {
        "status": "invalid",
        "reason": "Salary slip could not be verified"
    }



@app.get("/api/pdf/{file}")
async def pdf(file: str):
    path = f"backend/static_pdfs/{file}"
    if not os.path.exists(path):
        raise HTTPException(404, "PDF not found")
    return FileResponse(path, media_type="application/pdf")
