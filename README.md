# Revenue Recovery Prototype 0.3.3 — Deployment-Ready External Reviewer Edition

## What changed
- Replaced the years-of-experience slider with a required dropdown.
- Kept role, industry, experience, and confidence as active reviewer selections.
- Preserved the fixed 8-item ranking for clean external validation.
- Kept prior feedback invisible to reviewers.
- Kept replacement-rank capture for Too high / Too low judgments.
- Added persistent Supabase storage support.
- Kept local CSV as a testing fallback only.

## Local test
```bash
pip install -r requirements.txt
streamlit run app.py
```

Without Supabase secrets, test responses are saved to:
`feedback_log_v033.csv`

## Persistent storage setup
1. Create a free Supabase project.
2. Open the SQL Editor.
3. Run `supabase_setup.sql`.
4. Copy `secrets.example.toml` to `.streamlit/secrets.toml`.
5. Add your real `SUPABASE_URL` and secret key.
6. Do not commit `.streamlit/secrets.toml` to GitHub.
7. When deploying to Streamlit Community Cloud, add the same two values under App Settings > Secrets.

## Privacy
Use only fictional scenarios.
Do not ask reviewers to enter confidential customer or company information.
Name/company remains optional.

## Experiment rule
Do not change the ranking/scenarios during the initial validation batch.
