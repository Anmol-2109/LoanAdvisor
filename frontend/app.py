import streamlit as st
import requests
import uuid
import time

API_CHAT = "http://127.0.0.1:8000/api/message"
API_UPLOAD = "http://127.0.0.1:8000/api/upload-salary-slip"

st.set_page_config(page_title="FinBot", page_icon="💬", layout="centered")

# ---------------- SESSION INIT ----------------
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state.messages = []

# 🔑 IMPORTANT FLAGS (prevent loops)
if "salary_slip_verified" not in st.session_state:
    st.session_state.salary_slip_verified = False

if "salary_slip_attempted" not in st.session_state:
    st.session_state.salary_slip_attempted = False


# ---------------- HEADER ----------------
st.markdown("## 💬 FinBot – Smart Loan Advisor")
st.caption("Instant, intelligent NBFC loan assistance")

# ---------------- CHAT HISTORY ----------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["text"])


# ---------------- CHAT INPUT ----------------
user_msg = st.chat_input("Type your message...")

if user_msg:
    # store user message
    st.session_state.messages.append({
        "role": "user",
        "text": user_msg
    })

    # assistant thinking bubble
    with st.chat_message("assistant"):
        box = st.empty()
        box.markdown("🤖 *FinBot is thinking…*")

        time.sleep(0.6)

        res = requests.post(API_CHAT, json={
            "text": user_msg,
            "session_id": st.session_state.session_id
        })

        try:
            data = res.json()
        except Exception:
            box.markdown("⚠️ Server error. Please try again.")
            st.stop()

        reply = data.get("reply", "")
        box.markdown(reply)

    st.session_state.messages.append({
        "role": "assistant",
        "text": reply
    })

    st.rerun()


# =====================================================
# 📎 SALARY SLIP UPLOAD — FIXED & LOOP-SAFE
# =====================================================
if st.session_state.messages and not st.session_state.salary_slip_verified:
    last_bot_msg = st.session_state.messages[-1]["text"].lower()

    if "salary slip" in last_bot_msg and not st.session_state.salary_slip_attempted:
        st.markdown("---")

        st.markdown(
            """
            <div style="
                background:#f1f7ff;
                border-left:6px solid #4f8cff;
                padding:14px;
                border-radius:10px;
                margin-top:10px;
            ">
            📎 <b>Upload Salary Slip</b><br>
            <span style="color:#444;">
            Please upload your salary slip (PDF / Image) to continue.
            </span>
            </div>
            """,
            unsafe_allow_html=True
        )

        uploaded = st.file_uploader(
            "Upload salary slip",
            type=["pdf", "png", "jpg", "jpeg"],
            label_visibility="collapsed"
        )

        if uploaded:
            st.session_state.salary_slip_attempted = True

            with st.spinner("Verifying salary slip..."):
                time.sleep(1)

                res = requests.post(
                    API_UPLOAD,
                    params={"session_id": st.session_state.session_id}
                )

                result = res.json()

            # ✅ VERIFIED CASE
            if result["status"] == "verified":
                st.session_state.salary_slip_verified = True

                st.session_state.messages.append({
                    "role": "assistant",
                    "text": "✅ Salary slip verified successfully. Thanks! Let’s continue."
                })

                st.rerun()

            # ❌ INVALID CASE
            else:
                st.session_state.messages.append({
                    "role": "assistant",
                    "text": (
                        "❌ We couldn’t verify your salary slip.\n\n"
                        "Without a valid income document, "
                        "we’re unable to proceed with this loan application."
                    )
                })

                st.rerun()
