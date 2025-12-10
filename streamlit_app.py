import streamlit as st
from pydantic import BaseModel, Field, EmailStr, validator
from datetime import date
from typing import List, Literal
import git
import os
import base64
import json
from pathlib import Path

# ==============================
# Pydantic model = your JSON schema
# ==============================
class CheckItem(BaseModel):
    description: str = Field(..., description="What was checked")
    score: Literal[1, 2, 3, 4, 5] = 1
    notes: str = ""

class ThirdPartySoftware(BaseModel):
    checks: List[CheckItem] = Field(..., min_items=5)
    cumulative_score: int = Field(default=0, ge=0, le=25)

    @validator("cumulative_score", always=True)
    def calc_score(cls, v, values):
        if "checks" in values:
            return sum(item.score for item in values["checks"])
        return v

class SourceCode(BaseModel):
    checks: List[CheckItem] = Field(..., min_items=5)
    cumulative_score: int = 0
    repository_url: str = ""

class Datasets(BaseModel):
    checks: List[CheckItem] = Field(..., min_items=5)
    cumulative_score: int = 0
    sample_guideline: str = ""
    uploaded_files: List[str] = []  # filenames only for now

class Models(BaseModel):
    checks: List[CheckItem] = Field(..., min_items=5)
    cumulative_score: int = 0
    model_name: str = ""
    training_flops: str = ""
    estimated_shaheen_flops: str = ""
    exceeds_1e27: bool = False

class AIMCRReview(BaseModel):
    reviewer_name: str
    reviewer_email: EmailStr
    project_name: str
    project_id: str
    review_date: date = Field(default_factory=date.today)

    third_party_software: ThirdPartySoftware
    source_code: SourceCode
    datasets: Datasets
    models: Models

    final_decision: Literal["Approved", "Approved with Monitoring", "Escalated", "Rejected"]
    final_notes: str = ""

# ==============================
# Streamlit UI
# ==============================
st.set_page_config(page_title="KAUST AIMCR Review", layout="centered")
st.title("KAUST Supercomputing Lab – AIMCR Form")
st.markdown("### AI Model Control Review – Shaheen III Access")

with st.form("aimcr_form"):
    st.subheader("Reviewer & Project Information")
    col1, col2 = st.columns(2)
    with col1:
        reviewer_name = st.text_input("Reviewer Name *", value="Mohsin Ahmed Shaikh")
        reviewer_email = st.text_input("Reviewer Email *", value="mohsin.shaikh@kaust.edu.sa")
    with col2:
        project_name = st.text_input("Project Name *")
        project_id = st.text_input("Project ID *")

    # ——————————————————————
    # Reusable function for check sections
    # ——————————————————————
    def risk_check_section(title: str, key_prefix: str, min_checks=5):
        st.subheader(title)
        checks = []
        for i in range(max(st.session_state.get(f"{key_prefix}_count", min_checks), min_checks)):
            with st.expander(f"Check {i+1}", expanded=True):
                desc = st.text_input("Description", key=f"{key_prefix}_desc_{i}")
                score = st.selectbox("Risk Level", [1,2,3,4,5], index=0, key=f"{key_prefix}_score_{i}")
                notes = st.text_area("Notes", key=f"{key_prefix}_notes_{i}", height=100)
                checks.append(CheckItem(description=desc, score=score, notes=notes))
        cumulative = sum(c.score for c in checks)
        st.info(f"Cumulative score: **{cumulative}** / 25")
        if cumulative > 21:
            st.error("High Risk → candidate for rejection")
        return checks, cumulative

    # Third-Party Software
    tp_checks, tp_score = risk_check_section("Third-Party Software Screening", "tp")

    # Source Code
    sc_checks, sc_score = risk_check_section("Source Code Screening", "sc")
    repo_url = st.text_input("Source code repository URL (if public)")

    # Datasets
    ds_checks, ds_score = risk_check_section("Datasets & User Files Screening", "ds")
    sample_guide = st.text_input("Sampling guideline used (e.g., 0.01% of 1M samples)")
    uploaded = st.file_uploader("Upload supporting files (optional)", accept_multiple_files=True)

    # Models
    md_checks, md_score = risk_check_section("Models Screening", "md")
    col1, col2 = st.columns(2)
    with col1:
        model_name = st.text_input("Model name")
        training_flops = st.text_input("Training FLOPs (e.g., 6e25)")
    with col2:
        est_flops = st.text_input("Estimated FLOPs on Shaheen III")
        exceeds = st.checkbox("Total (training + Shaheen) > 10²⁷ FLOPs → escalate")

    st.subheader("Final Decision")
    decision = st.selectbox("Decision", ["Approved", "Approved with Monitoring", "Escalated", "Rejected"])
    final_notes = st.text_area("Final notes / justification")

    submitted = st.form_submit_button("Submit Review → Create JSON in Git Repo")

    if submitted:
        if not all([reviewer_name, reviewer_email, project_name, project_id]):
            st.error("Please fill all required fields")
        else:
            # Build the review object
            review = AIMCRReview(
                reviewer_name=reviewer_name,
                reviewer_email=reviewer_email,
                project_name=project_name,
                project_id=project_id,
                third_party_software=ThirdPartySoftware(checks=tp_checks),
                source_code=SourceCode(checks=sc_checks, repository_url=repo_url),
                datasets=Datasets(checks=ds_checks, sample_guideline=sample_guide),
                models=Models(
                    checks=md_checks,
                    model_name=model_name,
                    training_flops=training_flops,
                    estimated_shaheen_flops=est_flops,
                    exceeds_1e27=exceeds
                ),
                final_decision=decision,
                final_notes=final_notes
            )

            # Generate folder name
            timestamp = date.today().isoformat() + "T" + "__import__('datetime').datetime.now().strftime('%H-%M-%SZ')"
            folder_name = f"{review.review_date}__{review.project_id.replace('/', '-')}"
            json_content = review.json(indent=2)

            # Save to GitHub using GitPython
            token = st.secrets["GITHUB_TOKEN"]
            owner = st.secrets["REPO_OWNER"]
            repo_name = st.secrets["REPO_NAME"]

            try:
                # Temporary local clone (Streamlit Cloud gives us /tmp)
                repo_path = f"/tmp/{repo_name}"
                if os.path.exists(repo_path):
                    repo = git.Repo.Repo(repo_path)
                    repo.remotes.origin.pull()
                else:
                    repo = git.Repo.clone_from(f"https://{token}@github.com/{owner}/{repo_name}.git", repo_path)

                review_dir = os.Path(repo_path) / folder_name
                review_dir.mkdir(exist_ok=True)

                # Write JSON
                with open(review_dir / "review.json", "w") as f:
                    f.write(json_content)

                # Save uploaded files (if any)
                if uploaded:
                    upload_dir = review_dir / "uploaded_files"
                    upload_dir.mkdir()
                    for file in uploaded:
                        with open(upload_dir / file.name, "wb") as f:
                            f.write(file.getbuffer())

                # Commit & push
                repo.git.add(all=True)
                repo.index.commit(f"New AIMCR review: {project_name} ({project_id})")
                origin = repo.remote(name='origin')
                origin.push()

                st.balloons()
                st.success(f"Submitted! View at:")
                st.code(f"https://github.com/{owner}/{repo_name}/tree/main/{folder_name}")
                st.json(review.dict(), expanded=False)

            except Exception as e:
                st.error("Failed to push to GitHub. Check your token permissions.")
                st.exception(e)
