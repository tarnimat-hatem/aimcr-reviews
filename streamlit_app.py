import streamlit as st
import os
import json
import time
import threading
from datetime import date, datetime
from pathlib import Path
from typing import List, Literal

from pydantic import BaseModel, Field, EmailStr, validator
from git import Repo, Actor
from dotenv import load_dotenv

# ==============================
# Load .env
# ==============================
load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN",)
REPO_OWNER   = os.getenv("REPO_OWNER")
REPO_NAME    = os.getenv("REPO_NAME")

if not GITHUB_TOKEN:
    st.error("GITHUB_TOKEN missing in .env file")
    st.stop()
if not REPO_OWNER:
    st.error("REPO_OWNER missing in .env file")
    st.stop()
# Show you exactly what the app is using (very helpful!)
st.sidebar.caption(f"Repo: {REPO_OWNER}/{REPO_NAME}")

CACHE_DIR = Path(".cache_git_repo")
DRAFT_PATH_IN_REPO = "drafts/current_draft.json"

def get_repo():
    if CACHE_DIR.exists():
        try:
            repo = Repo(CACHE_DIR)
            repo.remotes.origin.pull(rebase=True)
            return repo
        except Exception as e:
            st.sidebar.error(f"Pull failed: {e}")
            CACHE_DIR.unlink(missing_ok=True)  # force fresh clone

    # Fresh clone with clear error message
    repo_url = f"https://{GITHUB_TOKEN}@github.com/{REPO_OWNER}/{REPO_NAME}.git"
    try:
        repo = Repo.clone_from(repo_url, CACHE_DIR, depth=1)
        st.sidebar.success("Cloned repo successfully")
        return repo
    except Exception as e:
        st.error(f"Cannot clone repo. Check:")
        st.error(f"• Token has 'repo' scope?")
        st.error(f"• Repo {REPO_OWNER}/{REPO_NAME} exists and is private?")
        st.code(str(e))
        st.stop()

# ==============================
# Pydantic Models – NOW USING MAX SCORE
# ==============================
class CheckItem(BaseModel):
    description: str = ""
    score: Literal[1, 2, 3, 4, 5] = 1
    notes: str = ""

class ThirdPartySoftware(BaseModel):
    checks: List[CheckItem] = Field(default_factory=list)
    cumulative_score: int = 0

    @validator("cumulative_score", always=True)
    def calc_max(cls, v, values):
        checks = values.get("checks", [])
        return max([item.score for item in checks], default=0) if checks else 0

class SourceCode(BaseModel):
    checks: List[CheckItem] = Field(default_factory=list)
    cumulative_score: int = 0
    repository_url: str = ""

    @validator("cumulative_score", always=True)
    def calc_max(cls, v, values):
        checks = values.get("checks", [])
        return max([item.score for item in checks], default=0) if checks else 0

class Datasets(BaseModel):
    checks: List[CheckItem] = Field(default_factory=list)
    cumulative_score: int = 0
    sample_guideline: str = ""

    @validator("cumulative_score", always=True)
    def calc_max(cls, v, values):
        checks = values.get("checks", [])
        return max([item.score for item in checks], default=0) if checks else 0

class Models(BaseModel):
    checks: List[CheckItem] = Field(default_factory=list)
    cumulative_score: int = 0
    model_name: str = ""
    training_flops: str = ""
    estimated_shaheen_flops: str = ""
    exceeds_1e27: bool = False

    @validator("cumulative_score", always=True)
    def calc_max(cls, v, values):
        checks = values.get("checks", [])
        return max([item.score for item in checks], default=0) if checks else 0

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
# GitHub Draft Sync (cross-computer)
# ==============================
def get_repo():
    if CACHE_DIR.exists():
        try:
            repo = Repo(CACHE_DIR)
            repo.remotes.origin.pull(rebase=True)
            return repo
        except:
            pass  # keep trying fresh clone below

    # Fresh clone
    url = f"https://{GITHUB_TOKEN}@github.com/{REPO_OWNER}/{REPO_NAME}.git"
    try:
        Repo.clone_from(url, CACHE_DIR, depth=1)
        st.sidebar.success("Repo cloned")
        return Repo(CACHE_DIR)
    except Exception as e:
        st.error("Cannot access GitHub repo")
        st.code(str(e))
        st.stop()

def load_draft():
    try:
        repo = get_repo()
        if any(e.path == DRAFT_PATH_IN_REPO for e in repo.tree()):
            content = repo.git.show(f"HEAD:{DRAFT_PATH_IN_REPO}")
            data = json.loads(content)
            st.session_state.form_data = data.get("data", {})
            st.sidebar.success(f"Draft loaded – {data.get('saved_at', '?')}")
    except:
        pass

def save_draft():
    if "form_data" not in st.session_state:
        return
    draft = {"saved_at": datetime.now().strftime("%Y-%m-%d %H:%M"), "data": st.session_state.form_data}
    try:
        repo = get_repo()
        f = CACHE_DIR / DRAFT_PATH_IN_REPO
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(json.dumps(draft, indent=2))
        repo.git.add(DRAFT_PATH_IN_REPO)
        if repo.is_dirty(untracked_files=True):
            repo.index.commit("Auto-save draft", author=Actor("AIMCR", "aimcr@kaust.edu.sa"))
            repo.remotes.origin.push()
    except:
        pass

if "draft_saver" not in st.session_state:
    threading.Thread(target=lambda: [time.sleep(10) or save_draft() for _ in iter(int, 1)], daemon=True).start()
    st.session_state.draft_saver = True
    load_draft()

if "form_data" not in st.session_state:
    st.session_state.form_data = {}

def val(key, default=""):
    return st.session_state.form_data.get(key, default)

# ==============================
# MAIN UI – DYNAMIC ENTRIES + MAX SCORE
# ==============================
st.set_page_config(page_title="KAUST AIMCR", layout="centered")
st.title("KAUST Supercomputing Lab – AIMCR Form")
st.markdown("### AI Model Control Review")

# Initialize counts if missing
for prefix in ["tp", "sc", "ds", "md"]:
    if f"{prefix}_entries" not in st.session_state:
        st.session_state[f"{prefix}_entries"] = []

# Add new entry buttons (outside form → allowed)
col1, col2, col3, col4 = st.columns(4)
if col1.button("Add Library → Third-Party Software"):
    st.session_state.tp_entries.append({})
    st.rerun()
if col2.button("Add Item → Source Code Checks"):
    st.session_state.sc_entries.append({})
    st.rerun()
if col3.button("Add Item → Datasets Checks"):
    st.session_state.ds_entries.append({})
    st.rerun()
if col4.button("Add Item → Models Checks"):
    st.session_state.md_entries.append({})
    st.rerun()

with st.form("aimcr_form", clear_on_submit=False):
    st.subheader("Reviewer & Project Information")
    c1, c2 = st.columns(2)
    with c1:
        st.text_input("Reviewer Name *", value=val("reviewer_name", "Mohsin Ahmed Shaikh"), key="reviewer_name")
        st.text_input("Reviewer Email *", value=val("reviewer_email", "mohsin.shaikh@kaust.edu.sa"), key="reviewer_email")
    with c2:
        st.text_input("Project Name *", value=val("project_name"), key="project_name")
        st.text_input("Project ID *", value=val("project_id"), key="project_id")

    # Generic section renderer
    def render_section(title: str, entries_list: list, prefix: str):
        st.subheader(title)
        checks = []
        for idx, _ in enumerate(entries_list):
            with st.expander(f"Entry {idx+1}", expanded=True):
                desc = st.text_input("Description", value=val(f"{prefix}_desc_{idx}"), key=f"{prefix}_desc_{idx}")
                score = st.selectbox("Risk Level", [1,2,3,4,5],
                                    index=val(f"{prefix}_score_{idx}", 0),
                                    key=f"{prefix}_score_{idx}")
                notes = st.text_area("Notes", value=val(f"{prefix}_notes_{idx}"), height=100, key=f"{prefix}_notes_{idx}")
                checks.append(CheckItem(description=desc, score=score, notes=notes))

        if checks:
            max_score = max(c.score for c in checks)
            st.info(f"**Highest Risk in this section: {max_score}**")
            if max_score >= 4:
                st.warning("High individual risk detected")
            elif max_score >= 3:
                st.info("Moderate risk")
        else:
            st.info("No entries yet – click the button above to add one")

        return checks

    tp_checks = render_section("Third-Party Software Screening", st.session_state.tp_entries, "tp")
    sc_checks = render_section("Source Code Screening", st.session_state.sc_entries, "sc")
    repo_url = st.text_input("Repository URL (if public)", value=val("repo_url"), key="repo_url")

    ds_checks = render_section("Datasets & User Files Screening", st.session_state.ds_entries, "ds")
    sample_guide = st.text_input("Sampling guideline", value=val("sample_guide"), key="sample_guide")
    uploaded = st.file_uploader("Supporting files (optional)", accept_multiple_files=True)

    md_checks = render_section("Models Screening", st.session_state.md_entries, "md")
    c1, c2 = st.columns(2)
    with c1:
        st.text_input("Model name", value=val("model_name"), key="model_name")
        st.text_input("Training FLOPs", value=val("training_flops"), key="training_flops")
    with c2:
        st.text_input("Est. Shaheen FLOPs", value=val("est_flops"), key="est_flops")
        st.checkbox("Total > 10²⁷ FLOPs", value=val("exceeds", False), key="exceeds")

    decision = st.selectbox("Final Decision", ["Approved", "Approved with Monitoring", "Escalated", "Rejected"],
                            index=["Approved", "Approved with Monitoring", "Escalated", "Rejected"].index(val("decision", "Approved")),
                            key="decision")
    st.text_area("Final notes", value=val("final_notes"), key="final_notes")

    col1, col2 = st.columns(2)
    submitted = col1.form_submit_button("Submit Review → Save to GitHub", type="primary")
    if col2.form_submit_button("Start New Review (clear draft)"):
        try:
            repo = get_repo()
            repo.git.rm("--cached", DRAFT_PATH_IN_REPO, ignore_unmatch=True)
            repo.index.commit("Clear draft")
            repo.remotes.origin.push()
        except: pass
        st.session_state.clear()
        st.rerun()

    if submitted:
        if not all([st.session_state.get(k) for k in ["reviewer_name", "reviewer_email", "project_name", "project_id"]]):
            st.error("Fill required fields")
        else:
            review = AIMCRReview(
                reviewer_name=st.session_state.reviewer_name,
                reviewer_email=st.session_state.reviewer_email,
                project_name=st.session_state.project_name,
                project_id=st.session_state.project_id,
                third_party_software=ThirdPartySoftware(checks=tp_checks),
                source_code=SourceCode(checks=sc_checks, repository_url=repo_url),
                datasets=Datasets(checks=ds_checks, sample_guideline=sample_guide),
                models=Models(checks=md_checks,
                              model_name=st.session_state.model_name,
                              training_flops=st.session_state.training_flops,
                              estimated_shaheen_flops=st.session_state.est_flops,
                              exceeds_1e27=st.session_state.exceeds),
                final_decision=decision,
                final_notes=st.session_state.final_notes
            )

            folder = f"{date.today()}__{st.session_state.project_id.replace('/', '-')}"
            try:
                repo = get_repo()
                dir_path = Path(repo.working_dir) / folder
                dir_path.mkdir(exist_ok=True)
                (dir_path / "review.json").write_text(review.json(indent=2))

                if uploaded:
                    up = dir_path / "uploaded_files"
                    up.mkdir(exist_ok=True)
                    for f in uploaded:
                        (up / f.name).write_bytes(f.getbuffer())

                repo.git.add(all=True)
                repo.index.commit(f"AIMCR: {st.session_state.project_name}")
                repo.remotes.origin.push()

                st.balloons()
                st.success(f"Submitted! → https://github.com/{REPO_OWNER}/{REPO_NAME}/tree/main/{folder}")

                # Clear draft
                repo.git.rm("--cached", DRAFT_PATH_IN_REPO, ignore_unmatch=True)
                repo.index.commit("Clear after submit")
                repo.remotes.origin.push()

            except Exception as e:
                st.error("Failed to submit")
                st.exception(e)

st.sidebar.caption(f"Auto-saving → {REPO_NAME}/drafts/current_draft.json")
if st.sidebar.button("Save draft now"):
    save_draft()
    st.sidebar.success("Saved!")