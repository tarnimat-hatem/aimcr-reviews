import streamlit as st
import json
import os
from datetime import datetime
from pathlib import Path
import subprocess
import shutil
from helper_functions import (calculate_section_risk,
                              create_folder_structure,
                              get_risk_color,
                              load_draft, delete_draft,
                              get_draft_files, save_draft, 
                              save_final_submission,
                              save_to_json, 
                              setup_local_workspace, 
                              push_to_github)

# Page configuration
st.set_page_config(
    page_title="AI Model Control Review (AIMCR)",
    page_icon="🔍",
    layout="wide"
)

# GitHub Configuration
GITHUB_REPO = "mshaikh786/aimcr-reviews"
GITHUB_REPO_URL = f"https://github.com/{GITHUB_REPO}.git"
LOCAL_REPO_PATH = Path.cwd() / ".aimcr_workspace"

# Initialize workspace on startup
if 'workspace_initialized' not in st.session_state:
    with st.spinner("Initializing workspace and syncing with GitHub..."):
        success, message = setup_local_workspace(LOCAL_REPO_PATH, GITHUB_REPO_URL)
        if success:
            st.session_state.workspace_initialized = True
        else:
            st.error(f"⚠️ Could not sync with GitHub: {message}")
            st.info("You can still use the application locally. Drafts will be saved locally only.")
            LOCAL_REPO_PATH.mkdir(parents=True, exist_ok=True)
            st.session_state.workspace_initialized = True

# Initialize session state
if 'data' not in st.session_state:
    st.session_state.data = {
        'metadata': {
            'proposal_title': '',
            'principal_investigator': '',
            'proposal_date': '',
            'reviewer_name': '',
            'reviewer_id': '',
            'aimcr_date': '',
            'project_id': ''
        },
        'third_party_software': [],
        'source_code': [],
        'datasets_user_files': [],
        'models': [],
        'observations': '',
        'recommendation': ''
    }

if 'current_section' not in st.session_state:
    st.session_state.current_section = 'metadata'

if 'edit_index' not in st.session_state:
    st.session_state.edit_index = {}

# Risk scoring configuration
RISK_LEVELS = {
    1: "No Risk",
    2: "Low Risk",
    3: "Medium Risk",
    4: "High Risk",
    5: "Critical Risk"
}

# Section configurations
SECTION_CHECKS = {
    'third_party_software': [
        'Project & Usage Alignment',
        'Prohibited Use Screening (LC 2.7)',
        'Restricted Entities Screening (LC 2.5)',
        'Source / Provenance',
        'License / Permissions',
        'Bundled Tools / Dependencies'
    ],
    'source_code': [
        'Project & Usage Alignment',
        'Prohibited Use Screening (LC 2.7)',
        'Source / Provenance & Restricted Entities (LC 2.5)',
        'License / Permissions',
        'Dependencies / Bundled Components',
        'Sample Inspection'
    ],
    'datasets_user_files': [
        'Project & Usage Alignment',
        'Prohibited Use Screening (LC 2.7)',
        'Restricted Entities Screening (LC 2.5)',
        'Prompts / Fine-tuning Scripts',
        'Sample Inspection',
        'Provenance',
        'License / Permissions'
    ],
    'models': [
        'Project & Usage Alignment',
        'Prohibited Use Screening (LC 2.7)',
        'Source / Provenance & Restricted Entities (LC 2.5)',
        'License / Permissions',
        'Training Data Documentation',
        'Customisation / Fine-tuning',
        'FLOPS Calculation',
        'Sample Inspection'
    ]
}

# Header
st.title("🔍 AI Model Control Review (AIMCR)")
st.markdown("**KAUST Supercomputing Lab (KSL) - Project Proposal**")
st.divider()

# Sidebar navigation
with st.sidebar:
    st.header("Navigation")
    section = st.radio(
        "Select Section",
        ["Metadata", "Third-Party Software", "Source Code", "Datasets & User Files", "Models", "Final Review"],
        key="navigation"
    )
    st.session_state.current_section = section.lower().replace(" & ", "_").replace(" ", "_").replace("-", "_")
    
    st.divider()
    
    # Draft Management Section
    st.subheader("📂 Draft Management")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("💾 Save Draft", use_container_width=True):
            project_id = st.session_state.data['metadata'].get('project_id', '')
            try:
                draft_path = save_draft(LOCAL_REPO_PATH, st.session_state.data, project_id)
                
                # Push to GitHub
                commit_msg = f"Save draft: {project_id or 'unnamed'} - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                success, message = push_to_github(LOCAL_REPO_PATH, commit_msg)
                
                if success:
                    st.success("✅ Draft saved and synced!")
                else:
                    st.warning(f"⚠️ Draft saved locally but not synced: {message}")
                st.rerun()
            except Exception as e:
                st.error(f"Error saving draft: {str(e)}")
    
    with col2:
        if st.button("🔄 Sync", use_container_width=True):
            with st.spinner("Syncing..."):
                success, message = setup_local_workspace(LOCAL_REPO_PATH, GITHUB_REPO_URL)
                if success:
                    st.success("✅ Synced!")
                else:
                    st.error(f"❌ {message}")
                st.rerun()
    
    # Load Draft Section
    drafts = get_draft_files(LOCAL_REPO_PATH)
    if drafts:
        st.write(f"**Available Drafts ({len(drafts)})**")
        
        for draft in drafts[:5]:  # Show last 5 drafts
            with st.expander(f"📄 {draft['project_id']}", expanded=False):
                st.write(f"**Title:** {draft['proposal_title'][:30]}...")
                st.write(f"**Modified:** {draft['modified'].strftime('%Y-%m-%d %H:%M')}")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Load", key=f"load_{draft['filename']}", use_container_width=True):
                        loaded_data = load_draft(draft['path'])
                        if loaded_data:
                            st.session_state.data = loaded_data
                            st.success("Draft loaded!")
                            st.rerun()
                        else:
                            st.error("Failed to load draft")
                
                with col2:
                    if st.button("Delete", key=f"del_{draft['filename']}", use_container_width=True):
                        success, msg = delete_draft(draft['path'])
                        if success:
                            # Push deletion to GitHub
                            commit_msg = f"Delete draft: {draft['filename']}"
                            push_to_github(LOCAL_REPO_PATH, commit_msg)
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)
    else:
        st.info("No drafts available")
    
    st.divider()
    st.subheader("Risk Score Legend")
    for score, level in RISK_LEVELS.items():
        st.write(f"**{score}**: {level}")

# Metadata Section
if st.session_state.current_section == 'metadata':
    st.header("📋 Project Metadata")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.session_state.data['metadata']['proposal_title'] = st.text_input(
            "Proposal Title",
            value=st.session_state.data['metadata']['proposal_title']
        )
        
        st.session_state.data['metadata']['principal_investigator'] = st.text_input(
            "Principal Investigator",
            value=st.session_state.data['metadata']['principal_investigator']
        )
        
        st.session_state.data['metadata']['proposal_date'] = st.date_input(
            "Proposal Date",
            value=datetime.strptime(st.session_state.data['metadata']['proposal_date'], "%Y-%m-%d") if st.session_state.data['metadata']['proposal_date'] else datetime.now()
        ).strftime("%Y-%m-%d")
    
    with col2:
        st.session_state.data['metadata']['project_id'] = st.text_input(
            "Project ID",
            value=st.session_state.data['metadata']['project_id']
        )
        
        st.session_state.data['metadata']['reviewer_name'] = st.text_input(
            "Reviewer Name",
            value=st.session_state.data['metadata']['reviewer_name']
        )
        
        st.session_state.data['metadata']['reviewer_id'] = st.text_input(
            "Reviewer ID",
            value=st.session_state.data['metadata']['reviewer_id']
        )
        
        st.session_state.data['metadata']['aimcr_date'] = st.date_input(
            "AIMCR Date",
            value=datetime.strptime(st.session_state.data['metadata']['aimcr_date'], "%Y-%m-%d") if st.session_state.data['metadata']['aimcr_date'] else datetime.now()
        ).strftime("%Y-%m-%d")

# Function to render artifact form
def render_artifact_form(section_key, section_title, checks):
    st.header(f"📦 {section_title}")
    
    # Display existing artifacts
    artifacts = st.session_state.data[section_key]
    
    if artifacts:
        st.subheader("Existing Artifacts")
        
        for idx, artifact in enumerate(artifacts):
            # Create a container for each artifact
            artifact_container = st.container()
            
            with artifact_container:
                # Header row with artifact name and buttons
                col1, col2, col3 = st.columns([6, 1, 1])
                
                with col1:
                    st.markdown(f"### Artifact {idx + 1}: {artifact.get('name', 'Unnamed')}")
                
                with col2:
                    if st.button("✏️ Edit", key=f"edit_{section_key}_{idx}", use_container_width=True):
                        st.session_state.edit_index[section_key] = idx
                        st.rerun()
                
                with col3:
                    if st.button("🗑️ Delete", key=f"delete_{section_key}_{idx}", use_container_width=True):
                        st.session_state.data[section_key].pop(idx)
                        st.rerun()
                
                # Details in expander
                with st.expander("View Details", expanded=False):
                    # Calculate individual artifact score
                    artifact_score = sum(check['score'] for check in artifact['checks'])
                    has_critical = any(check['score'] == 5 for check in artifact['checks'])
                    
                    if has_critical or artifact_score >= 21:
                        st.markdown(f"**Total Score:** <span style='color:red; font-weight:bold;'>{artifact_score}</span>", unsafe_allow_html=True)
                    else:
                        st.write(f"**Total Score:** {artifact_score}")
                    
                    # Display checks
                    for check in artifact['checks']:
                        st.write(f"- {check['name']}: Score {check['score']} | Notes: {check['notes']}")
                
                st.divider()
        
        # Calculate cumulative risk
        total_risk, max_scores = calculate_section_risk(artifacts)
        has_critical = any(score == 5 for score in max_scores)
        
        st.divider()
        st.subheader("Section Cumulative Risk Score")
        
        if has_critical or total_risk >= 21:
            st.markdown(f"### <span style='color:red; font-weight:bold;'>Total: {total_risk}</span>", unsafe_allow_html=True)
            st.error("⚠️ CRITICAL: This section has critical risk (score ≥21 or individual check = 5)")
        else:
            st.markdown(f"### Total: {total_risk}")
        
        st.write("**Maximum scores per check:**")
        for i, (check_name, max_score) in enumerate(zip(checks, max_scores)):
            if max_score == 5:
                st.markdown(f"- {check_name}: <span style='color:red; font-weight:bold;'>{max_score}</span>", unsafe_allow_html=True)
            else:
                st.write(f"- {check_name}: {max_score}")
    
    st.divider()
    
    # Add/Edit artifact form
    edit_mode = section_key in st.session_state.edit_index
    if edit_mode:
        st.info(f"✏️ **Editing Artifact {st.session_state.edit_index[section_key] + 1}** - Make your changes below and click 'Save Artifact' when done.")
        artifact = artifacts[st.session_state.edit_index[section_key]]
        form_key = f"{section_key}_form_edit_{st.session_state.edit_index[section_key]}"
    else:
        st.subheader("Add New Artifact")
        artifact = None
        form_key = f"{section_key}_form_add"
    
    with st.form(form_key):
        artifact_name = st.text_input(
            "Artifact Name",
            value=artifact['name'] if artifact else ""
        )
        
        st.write("### Risk Assessment Checks")
        
        checks_data = []
        for i, check_name in enumerate(checks):
            col1, col2 = st.columns([1, 2])
            
            # Create unique keys for edit vs add mode
            widget_suffix = f"edit_{st.session_state.edit_index[section_key]}" if edit_mode else "add"
            
            with col1:
                score = st.selectbox(
                    f"{check_name}",
                    options=[1, 2, 3, 4, 5],
                    format_func=lambda x: f"{x} - {RISK_LEVELS[x]}",
                    index=artifact['checks'][i]['score'] - 1 if artifact else 0,
                    key=f"{section_key}_check_{i}_{widget_suffix}"
                )
            
            with col2:
                notes = st.text_area(
                    f"Notes for {check_name}",
                    value=artifact['checks'][i]['notes'] if artifact else "",
                    key=f"{section_key}_notes_{i}_{widget_suffix}",
                    height=100
                )
            
            checks_data.append({
                'name': check_name,
                'score': score,
                'notes': notes
            })
        
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            submit = st.form_submit_button("Save Artifact", type="primary")
        
        with col2:
            if edit_mode:
                cancel = st.form_submit_button("Cancel Edit")
                if cancel:
                    del st.session_state.edit_index[section_key]
                    st.rerun()
        
        if submit:
            new_artifact = {
                'name': artifact_name,
                'checks': checks_data
            }
            
            if edit_mode:
                st.session_state.data[section_key][st.session_state.edit_index[section_key]] = new_artifact
                del st.session_state.edit_index[section_key]
            else:
                st.session_state.data[section_key].append(new_artifact)
            
            st.success("Artifact saved successfully!")
            st.rerun()

# Render sections
if st.session_state.current_section == 'third_party_software':
    render_artifact_form('third_party_software', 'Third-Party Software (Packages, Libraries, Containers & Binaries)', SECTION_CHECKS['third_party_software'])

elif st.session_state.current_section == 'source_code':
    render_artifact_form('source_code', 'Source Code', SECTION_CHECKS['source_code'])

elif st.session_state.current_section == 'datasets_user_files':
    render_artifact_form('datasets_user_files', 'Datasets & User Files', SECTION_CHECKS['datasets_user_files'])

elif st.session_state.current_section == 'models':
    render_artifact_form('models', 'Models', SECTION_CHECKS['models'])

# Final Review Section
elif st.session_state.current_section == 'final_review':
    st.header("📊 Final Review and Summary")
    
    # Display metadata
    st.subheader("Project Information")
    meta = st.session_state.data['metadata']
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**Proposal Title:** {meta['proposal_title']}")
        st.write(f"**Principal Investigator:** {meta['principal_investigator']}")
        st.write(f"**Proposal Date:** {meta['proposal_date']}")
    with col2:
        st.write(f"**Project ID:** {meta['project_id']}")
        st.write(f"**Reviewer Name:** {meta['reviewer_name']}")
        st.write(f"**Reviewer ID:** {meta['reviewer_id']}")
        st.write(f"**AIMCR Date:** {meta['aimcr_date']}")
    
    st.divider()
    
    # Display all section scores
    st.subheader("Risk Score Summary")
    
    sections_summary = {
        'Third-Party Software': ('third_party_software', SECTION_CHECKS['third_party_software']),
        'Source Code': ('source_code', SECTION_CHECKS['source_code']),
        'Datasets & User Files': ('datasets_user_files', SECTION_CHECKS['datasets_user_files']),
        'Models': ('models', SECTION_CHECKS['models'])
    }
    
    overall_critical = False
    
    for section_name, (section_key, checks) in sections_summary.items():
        artifacts = st.session_state.data[section_key]
        if artifacts:
            total_risk, max_scores = calculate_section_risk(artifacts)
            has_critical = any(score == 5 for score in max_scores)
            
            if has_critical or total_risk >= 21:
                overall_critical = True
                st.markdown(f"### <span style='color:red;'>{section_name}: {total_risk} ⚠️ CRITICAL</span>", unsafe_allow_html=True)
            else:
                st.write(f"### {section_name}: {total_risk}")
            
            with st.expander(f"View {section_name} Details"):
                st.write(f"**Number of artifacts:** {len(artifacts)}")
                st.write("**Maximum scores per check:**")
                for check_name, max_score in zip(checks, max_scores):
                    if max_score == 5:
                        st.markdown(f"- {check_name}: <span style='color:red; font-weight:bold;'>{max_score}</span>", unsafe_allow_html=True)
                    else:
                        st.write(f"- {check_name}: {max_score}")
        else:
            st.write(f"### {section_name}: No artifacts added")
    
    st.divider()
    
    # Overall status
    if overall_critical:
        st.error("⚠️ CRITICAL RISK DETECTED: One or more sections have critical risk scores!")
    else:
        st.success("✅ All sections are within acceptable risk levels")
    
    st.divider()
    
    # Observations and Recommendations
    st.subheader("Observations and Recommendations")
    
    st.session_state.data['observations'] = st.text_area(
        "Observations",
        value=st.session_state.data['observations'],
        height=150
    )
    
    st.session_state.data['recommendation'] = st.text_area(
        "Recommendation",
        value=st.session_state.data['recommendation'],
        height=150
    )
    
    st.divider()
    
    # Save and Export
    st.subheader("💾 Save and Export")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("💾 Save Draft", type="secondary", use_container_width=True):
            project_id = meta['project_id']
            if not project_id:
                st.error("Please enter a Project ID in the Metadata section")
            else:
                try:
                    draft_path = save_draft(LOCAL_REPO_PATH, st.session_state.data, project_id)
                    
                    # Push to GitHub
                    commit_msg = f"Save draft: {project_id} - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                    success, message = push_to_github(LOCAL_REPO_PATH, commit_msg)
                    
                    if success:
                        st.success(f"✅ Draft saved and synced to GitHub!")
                    else:
                        st.warning(f"⚠️ Draft saved locally: {draft_path}")
                        st.info(f"Sync issue: {message}")
                except Exception as e:
                    st.error(f"Error saving draft: {str(e)}")
    
    with col2:
        if st.button("📤 Submit Final", type="primary", use_container_width=True):
            if not meta['project_id']:
                st.error("Please enter a Project ID in the Metadata section")
            else:
                try:
                    # Save to submissions folder
                    submission_path = save_final_submission(LOCAL_REPO_PATH, st.session_state.data, meta['project_id'])
                    
                    # Push to GitHub
                    commit_msg = f"Final submission: {meta['project_id']} - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                    success, message = push_to_github(LOCAL_REPO_PATH, commit_msg)
                    
                    if success:
                        st.success(f"✅ Final submission saved and pushed to GitHub!")
                        st.info(f"📁 Submission saved in: {submission_path}")
                        
                        # Clean up draft if exists
                        drafts_dir = LOCAL_REPO_PATH / "drafts"
                        for draft_file in drafts_dir.glob(f"draft_{meta['project_id']}_*.json"):
                            draft_file.unlink()
                        
                        # Commit draft cleanup
                        push_to_github(LOCAL_REPO_PATH, f"Clean up drafts for {meta['project_id']}")
                        
                    else:
                        st.warning(f"⚠️ Submission saved locally but not synced: {message}")
                        st.info(f"📁 Files saved in: {submission_path}")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
    
    with col3:
        if st.button("📥 Save Local Copy", use_container_width=True):
            if not meta['project_id']:
                st.error("Please enter a Project ID in the Metadata section")
            else:
                try:
                    folder_path = create_folder_structure(meta['project_id'])
                    json_path = save_to_json(st.session_state.data, folder_path)
                    st.success(f"✅ Data saved to {json_path}")
                except Exception as e:
                    st.error(f"Error saving file: {str(e)}")
    
    # Download JSON
    if meta['project_id']:
        st.download_button(
            label="📥 Download JSON",
            data=json.dumps(st.session_state.data, indent=2),
            file_name=f"aimcr_{meta['project_id']}_{datetime.now().strftime('%Y%m%d')}.json",
            mime="application/json",
            use_container_width=True
        )
    
    st.divider()
    
    # Workspace Information
    st.subheader("📊 Workspace Information")
    st.write(f"**Local Workspace:** `{LOCAL_REPO_PATH}`")
    st.write(f"**GitHub Repository:** `{GITHUB_REPO}`")
    
    # Show recent activity
    drafts = get_draft_files(LOCAL_REPO_PATH)
    st.write(f"**Drafts:** {len(drafts)}")
    
    submissions_dir = LOCAL_REPO_PATH / "submissions"
    if submissions_dir.exists():
        submissions = list(submissions_dir.glob("AIMCR-*"))
        st.write(f"**Submissions:** {len(submissions)}")
    else:
        st.write(f"**Submissions:** 0")

# Footer
st.divider()
st.caption("AI Model Control Review (AIMCR) - KAUST Supercomputing Lab")