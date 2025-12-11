import subprocess
import json
from datetime import datetime
from pathlib import Path

def calculate_section_risk(artifacts):
    """Calculate cumulative risk score for a section"""
    if not artifacts:
        return 0, []
    
    num_checks = len(artifacts[0]['checks'])
    max_scores = []
    
    # For each check position, find the maximum score across all artifacts
    for i in range(num_checks):
        max_score = max(artifact['checks'][i]['score'] for artifact in artifacts)
        max_scores.append(max_score)
    
    total_score = sum(max_scores)
    return total_score, max_scores

def get_risk_color(score):
    """Return color based on risk score"""
    if score >= 21:
        return "red"
    elif score >= 5:
        return "red"
    elif score >= 15:
        return "orange"
    elif score >= 10:
        return "yellow"
    else:
        return "green"

def create_folder_structure(project_id):
    """Create folder structure for the project"""
    date_str = datetime.now().strftime("%d-%m-%Y")
    folder_name = f"AIMCR-{project_id}-{date_str}"
    folder_path = Path(folder_name)
    folder_path.mkdir(exist_ok=True)
    return folder_path

def save_to_json(data, folder_path):
    """Save data to JSON file"""
    json_path = folder_path / "aimcr_data.json"
    with open(json_path, 'w') as f:
        json.dump(data, f, indent=2)
    return json_path

def init_git_repo(folder_path):
    """Initialize git repository if not exists"""
    try:
        if not (folder_path / ".git").exists():
            subprocess.run(["git", "init"], cwd=folder_path, check=True)
            subprocess.run(["git", "add", "."], cwd=folder_path, check=True)
            subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=folder_path, check=True)
            return True, "Git repository initialized"
        else:
            subprocess.run(["git", "add", "."], cwd=folder_path, check=True)
            subprocess.run(["git", "commit", "-m", f"Update: {datetime.now().isoformat()}"], cwd=folder_path, check=True)
            return True, "Changes committed to git"
    except subprocess.CalledProcessError as e:
        return False, f"Git error: {str(e)}"
    except FileNotFoundError:
        return False, "Git is not installed on this system"

def setup_local_workspace(LOCAL_REPO_PATH, GITHUB_REPO_URL):
    """Setup local workspace and clone/pull from GitHub"""
    LOCAL_REPO_PATH.mkdir(parents=True, exist_ok=True)
    
    try:
        if not (LOCAL_REPO_PATH / ".git").exists():
            # Clone repository
            subprocess.run(
                ["git", "clone", GITHUB_REPO_URL, str(LOCAL_REPO_PATH)],
                check=True,
                capture_output=True,
                text=True
            )
            return True, "Repository cloned successfully"
        else:
            # Pull latest changes
            subprocess.run(
                ["git", "pull"],
                cwd=LOCAL_REPO_PATH,
                check=True,
                capture_output=True,
                text=True
            )
            return True, "Repository updated successfully"
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr if hasattr(e, 'stderr') else str(e)
        return False, f"Git error: {error_msg}"
    except FileNotFoundError:
        return False, "Git is not installed on this system"

def get_draft_files(LOCAL_REPO_PATH):
    """Get list of draft files from the drafts directory"""
    drafts_dir = LOCAL_REPO_PATH / "drafts"
    if not drafts_dir.exists():
        return []
    
    draft_files = []
    for file_path in drafts_dir.glob("*.json"):
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                metadata = data.get('metadata', {})
                draft_files.append({
                    'filename': file_path.name,
                    'path': file_path,
                    'project_id': metadata.get('project_id', 'Unknown'),
                    'proposal_title': metadata.get('proposal_title', 'Untitled'),
                    'modified': datetime.fromtimestamp(file_path.stat().st_mtime)
                })
        except:
            continue
    
    return sorted(draft_files, key=lambda x: x['modified'], reverse=True)

def save_draft(LOCAL_REPO_PATH, data, project_id):
    """Save current progress as a draft"""
    drafts_dir = LOCAL_REPO_PATH / "drafts"
    drafts_dir.mkdir(parents=True, exist_ok=True)
    
    # Create draft filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"draft_{project_id}_{timestamp}.json" if project_id else f"draft_unnamed_{timestamp}.json"
    draft_path = drafts_dir / filename
    
    # Save draft
    with open(draft_path, 'w') as f:
        json.dump(data, f, indent=2)
    
    return draft_path

def save_final_submission(LOCAL_REPO_PATH, data, project_id):
    """Save final submission to the submissions directory"""
    submissions_dir = LOCAL_REPO_PATH / "submissions"
    submissions_dir.mkdir(parents=True, exist_ok=True)
    
    # Create submission folder
    date_str = datetime.now().strftime("%d-%m-%Y")
    folder_name = f"AIMCR-{project_id}-{date_str}"
    submission_path = submissions_dir / folder_name
    submission_path.mkdir(exist_ok=True)
    
    # Save JSON
    json_path = submission_path / "aimcr_data.json"
    with open(json_path, 'w') as f:
        json.dump(data, f, indent=2)
    
    return submission_path

def push_to_github(LOCAL_REPO_PATH, commit_message):
    """Push changes to GitHub repository"""
    try:
        # Add all changes
        subprocess.run(
            ["git", "add", "."],
            cwd=LOCAL_REPO_PATH,
            check=True,
            capture_output=True
        )
        
        # Check if there are changes to commit
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=LOCAL_REPO_PATH,
            check=True,
            capture_output=True,
            text=True
        )
        
        if not result.stdout.strip():
            return True, "No changes to commit"
        
        # Commit changes
        subprocess.run(
            ["git", "commit", "-m", commit_message],
            cwd=LOCAL_REPO_PATH,
            check=True,
            capture_output=True
        )
        
        # Push to remote
        subprocess.run(
            ["git", "push"],
            cwd=LOCAL_REPO_PATH,
            check=True,
            capture_output=True,
            text=True
        )
        
        return True, "Changes pushed to GitHub successfully"
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.decode() if hasattr(e, 'stderr') and e.stderr else str(e)
        return False, f"Git error: {error_msg}"

def load_draft(draft_path):
    """Load a draft file"""
    try:
        with open(draft_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        return None

def delete_draft(draft_path):
    """Delete a draft file"""
    try:
        draft_path.unlink()
        return True, "Draft deleted successfully"
    except Exception as e:
        return False, f"Error deleting draft: {str(e)}"