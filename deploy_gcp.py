# deploy_gcp.py
# Script to automate deployment of the Fraud Detection FastAPI app to Google Cloud Run.

import os
import sys
import shutil
import subprocess

def run_command(command, shell=True, capture_output=False):
    """Run a system command and return output or exit code."""
    try:
        if capture_output:
            result = subprocess.run(command, shell=shell, check=True, text=True, capture_output=True)
            return result.stdout.strip()
        else:
            result = subprocess.run(command, shell=shell, check=True)
            return result.returncode == 0
    except subprocess.CalledProcessError as err:
        if capture_output:
            return f"ERROR: {err.stderr}"
        return False

def check_gcloud():
    """Verify if gcloud CLI is installed and configured."""
    print("Checking for Google Cloud CLI (gcloud) ...")
    gcloud_path = shutil.which("gcloud")
    
    # Check common Windows installer path and add to PATH dynamically if not present
    if gcloud_path is None:
        local_appdata = os.getenv("LOCALAPPDATA", "")
        fallback_path = os.path.join(local_appdata, "Google", "Cloud SDK", "google-cloud-sdk", "bin")
        if os.path.exists(os.path.join(fallback_path, "gcloud.cmd")):
            print(f"Detected Google Cloud CLI in AppData: {fallback_path}")
            os.environ["PATH"] += os.pathsep + fallback_path
            gcloud_path = os.path.join(fallback_path, "gcloud.cmd")
            
    if gcloud_path is None:
        print("\n" + "="*80)
        print("ERROR: Google Cloud CLI (gcloud) is not found in your system path.")
        print("To install it on Windows, you can open PowerShell as Administrator and run:")
        print("    winget install Google.CloudSDK")
        print("Or download the installer from:")
        print("    https://cloud.google.com/sdk/docs/install#windows")
        print("="*80 + "\n")
        return False
    
    version = run_command("gcloud --version", capture_output=True)
    print(f"Found Google Cloud CLI:\n{version.splitlines()[0] if version else 'Unknown version'}\n")
    return True

def main():
    print("="*80)
    print(" MLOps Fraud Detection Pipeline - Google Cloud Run Deployer")
    print("="*80)

    if not check_gcloud():
        sys.exit(1)

    # 1. Authenticate with Google Cloud
    print("Checking auth status ...")
    auth_list = run_command("gcloud auth list --format=json", capture_output=True)
    
    # Simple check if there are any active accounts
    if "active" not in auth_list.lower() or "[]" in auth_list:
        print("No active Google Cloud account detected. Initiating login ...")
        print("Please follow the instructions in the browser window that opens.")
        success = run_command("gcloud auth login")
        if not success:
            print("Authentication failed.")
            sys.exit(1)
    else:
        print("Authenticated account found.")

    # 2. Get GCP Project ID
    print("\nFetching your Google Cloud projects ...")
    projects_output = run_command("gcloud projects list --format=\"value(projectId)\"", capture_output=True)
    
    projects = []
    if projects_output and "error" not in projects_output.lower():
        projects = [p.strip() for p in projects_output.splitlines() if p.strip()]

    selected_project = ""
    if projects:
        print("\nAvailable projects:")
        for idx, project in enumerate(projects, 1):
            print(f"  [{idx}] {project}")
        print(f"  [{len(projects) + 1}] Enter a different Project ID")
        
        while True:
            choice = input(f"\nSelect a project [1-{len(projects)+1}]: ").strip()
            if not choice:
                continue
            try:
                choice_idx = int(choice)
                if 1 <= choice_idx <= len(projects):
                    selected_project = projects[choice_idx - 1]
                    break
                elif choice_idx == len(projects) + 1:
                    selected_project = input("Enter GCP Project ID: ").strip()
                    break
            except ValueError:
                pass
            print("Invalid selection.")
    else:
        selected_project = input("\nEnter your GCP Project ID: ").strip()

    if not selected_project:
        print("Project ID cannot be empty.")
        sys.exit(1)

    # Set project
    print(f"\nSetting active project to: {selected_project} ...")
    run_command(f"gcloud config set project {selected_project}")

    # 3. Choose Cloud Run Region
    default_region = "us-central1"
    region = input(f"\nEnter deployment region (default: {default_region}): ").strip()
    if not region:
        region = default_region

    # 4. Trigger deployment
    # Using Cloud Build in the cloud to package the source and deploy container to Cloud Run
    print("\n" + "="*80)
    print(f"Deploying to Google Cloud Run in project '{selected_project}' (region: '{region}') ...")
    print("This will upload your code, build the container in the cloud via Cloud Build,")
    print("and deploy it to a serverless Cloud Run instance.")
    print("="*80 + "\n")

    deploy_cmd = (
        f"gcloud run deploy fraud-detection-api "
        f"--source . "
        f"--region {region} "
        f"--allow-unauthenticated"
    )
    
    success = run_command(deploy_cmd)
    if success:
        print("\n" + "="*80)
        print("[SUCCESS] Deployment completed successfully!")
        print("You can access your interactive showcase website and API via the URL above.")
        print("="*80 + "\n")
    else:
        print("\n" + "="*80)
        print("[ERROR] Deployment failed.")
        print("Please check the error logs above.")
        print("Common reasons for failure:")
        print("  1. Cloud Build API or Cloud Run API is not enabled in your project.")
        print("     To enable them, run:")
        print(f"       gcloud services enable cloudbuild.googleapis.com run.googleapis.com")
        print("  2. Insufficient permissions or no open Billing account.")
        print("="*80 + "\n")

if __name__ == "__main__":
    main()
