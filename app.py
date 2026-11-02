
import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import datetime, timezone
import uuid

st.set_page_config(
    page_title="Revenue Recovery Prototype 0.3.3",
    page_icon="📈",
    layout="wide"
)

DATA = Path(__file__).with_name("fictional_scenarios.csv")
LOCAL_FEEDBACK = Path(__file__).with_name("feedback_log_v033.csv")
df = pd.read_csv(DATA).sort_values("model_rank")

def save_feedback(records):
    """
    Production path:
      If Streamlit secrets include SUPABASE_URL and SUPABASE_KEY,
      save to Supabase table reviewer_feedback.
    Local-test fallback:
      Save to feedback_log_v033.csv.
    """
    try:
        supabase_url = st.secrets.get("SUPABASE_URL", "")
        supabase_key = st.secrets.get("SUPABASE_KEY", "")
    except Exception:
        supabase_url = ""
        supabase_key = ""

    if supabase_url and supabase_key:
        from supabase import create_client
        client = create_client(supabase_url, supabase_key)
        client.table("reviewer_feedback").insert(records).execute()
        return "supabase"

    out = pd.DataFrame(records)
    out.to_csv(
        LOCAL_FEEDBACK,
        mode="a",
        header=not LOCAL_FEEDBACK.exists(),
        index=False
    )
    return "local"

st.title("Revenue Recovery Prototype 0.3.3")
st.subheader("External Reviewer Validation Edition")

with st.expander("ℹ️ Quick Instructions", expanded=True):
    st.markdown("""
- **Goal:** Test whether the model's priority ranking aligns with real-world business judgment.
- **Task:** Review 8 fictional situations. **#1 = handle first; #8 = handle last.**
- **Your input:** Mark each rank **About right**, **Too high**, or **Too low**.
- Takes about **3–5 minutes**.
""")

st.caption("All scenarios are fictional. Please do not enter confidential customer or company information.")

with st.sidebar:
    st.header("Reviewer Background")

    name_company = st.text_input("Name / Company (Optional)")

    role = st.selectbox(
        "Primary Role",
        [
            "Select Role...",
            "Business Owner",
            "Office Manager / Dispatcher",
            "Sales / Estimator",
            "Technician",
            "Bookkeeper / Accounting",
            "Operations Manager",
            "Other"
        ]
    )

    industry = st.selectbox(
        "Industry / Trade",
        [
            "Select Industry...",
            "HVAC",
            "Plumbing",
            "Electrical",
            "Roofing / Exterior",
            "Cleaning / Landscaping",
            "General Contracting",
            "Other"
        ]
    )

    experience = st.selectbox(
        "Years of Industry Experience",
        [
            "Select experience...",
            "<1 year",
            "1–2 years",
            "3–5 years",
            "6–10 years",
            "11–20 years",
            "20+ years"
        ]
    )

    confidence = st.selectbox(
        "Confidence in Domain Judgment",
        [
            "Select confidence...",
            "Low",
            "Medium",
            "High"
        ]
    )

    st.markdown("---")
    consent = st.checkbox(
        "I agree that my anonymous feedback may be used to improve this research prototype."
    )

st.header("📋 The Model's Proposed Priority Order")
st.dataframe(
    df[["model_rank","id","type","value","status","description"]].rename(columns={
        "model_rank":"Rank",
        "id":"ID",
        "type":"Type",
        "value":"Value ($)",
        "status":"Status",
        "description":"Description"
    }),
    use_container_width=True,
    hide_index=True
)

st.divider()
st.header("🔍 Item-by-Item Review")

responses = []

for _, r in df.iterrows():
    with st.container(border=True):
        st.markdown(
            f"### Model Rank: #{int(r.model_rank)} of 8 — "
            f"[{r.id}] {r.type} (${r.value:,.2f})"
        )
        st.caption(f"Details: {r.description} | Status: {r.status}")

        left, right = st.columns([1, 1])

        with left:
            judgment = st.radio(
                f"Does rank #{int(r.model_rank)} make sense for {r.id}?",
                [
                    "Select judgment...",
                    "About right",
                    "Too high (should be lower priority)",
                    "Too low (should be higher priority)"
                ],
                key=f"judgment_{r.id}"
            )

            preferred_rank = None
            if judgment.startswith("Too high") or judgment.startswith("Too low"):
                preferred_rank = st.selectbox(
                    "Where would you rank it instead?",
                    ["Select replacement rank..."] + [str(i) for i in range(1,9)],
                    key=f"preferred_{r.id}"
                )

        with right:
            note = st.text_input(
                f"Optional Notes / Reasoning for {r.id}",
                key=f"note_{r.id}"
            )

        responses.append((r, judgment, preferred_rank, note))

general = st.text_area(
    "Optional: What important information is missing from these scenarios?",
    placeholder="Examples: customer history, profit margin, urgency, payment dispute, seasonality..."
)

if st.button("🚀 Submit All Reviewer Feedback", type="primary"):
    background_missing = (
        role == "Select Role..."
        or industry == "Select Industry..."
        or experience == "Select experience..."
        or confidence == "Select confidence..."
    )

    unanswered = [
        r.id for r, judgment, _, _ in responses
        if judgment == "Select judgment..."
    ]

    replacement_missing = [
        r.id for r, judgment, preferred_rank, _ in responses
        if (judgment.startswith("Too high") or judgment.startswith("Too low"))
        and preferred_rank == "Select replacement rank..."
    ]

    if background_missing:
        st.error("Please complete all required reviewer background fields.")
    elif not consent:
        st.error("Please check the consent box before submitting.")
    elif unanswered:
        st.error("Please review all 8 items before submitting.")
    elif replacement_missing:
        st.error(
            "For every item marked Too high or Too low, "
            "please choose the rank you would use instead."
        )
    else:
        reviewer_id = str(uuid.uuid4())
        submitted_at = datetime.now(timezone.utc).isoformat()
        records = []

        for r, judgment, preferred_rank, note in responses:
            if judgment == "About right":
                normalized_judgment = "About right"
                final_rank = int(r.model_rank)
            elif judgment.startswith("Too high"):
                normalized_judgment = "Too high"
                final_rank = int(preferred_rank)
            else:
                normalized_judgment = "Too low"
                final_rank = int(preferred_rank)

            records.append({
                "reviewer_id": reviewer_id,
                "submitted_at": submitted_at,
                "name_or_company": name_company or None,
                "role": role,
                "industry": industry,
                "years_experience": experience,
                "confidence": confidence,
                "opportunity_id": r.id,
                "opportunity_type": r.type,
                "model_rank": int(r.model_rank),
                "judgment": normalized_judgment,
                "preferred_rank": final_rank,
                "rank_difference": final_rank - int(r.model_rank),
                "notes": note or None,
                "general_missing_variables": general or None,
                "prototype_version": "0.3.3"
            })

        try:
            destination = save_feedback(records)
            if destination == "supabase":
                st.success("Thank you — your review was submitted successfully.")
            else:
                st.success(
                    "Thank you — your review was saved locally for testing. "
                    "Persistent cloud storage is not configured yet."
                )
        except Exception:
            st.error(
                "Your responses could not be saved. "
                "Please do not close the page and contact the researcher."
            )

st.caption(
    "Research purpose: compare a fixed model priority ranking with "
    "independent judgments from people with relevant business experience."
)
