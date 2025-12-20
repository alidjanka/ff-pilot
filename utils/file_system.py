#
import streamlit as st
import os
import json

# Import Google API libraries
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload


# --- CONFIGURATION ---
# IMPORTANT: REPLACE THIS with the ID of your Google Drive folder
FOLDER_ID = "1rrX8hLwrIwzfzdOsyAF4O1TaXfSmhCMc" 
# ---------------------

def get_drive_service():
    """
    Authenticates using the Service Account credentials from Streamlit secrets,
    writes them to a temporary file in /tmp, and builds the Drive service object.
    """
    try:
        temp_file_path = "/tmp/pilot-ff.json"
        # 1. Load the secrets dictionary from the secrets.toml file
        service_account_info = {
            "type": st.secrets["google_drive"]["type"],
            "project_id": st.secrets["google_drive"]["project_id"],
            "private_key_id": st.secrets["google_drive"]["private_key_id"],
            "private_key": st.secrets["google_drive"]["private_key"].replace('\\n', '\n'),
            "client_email": st.secrets["google_drive"]["client_email"],
            "client_id": st.secrets["google_drive"]["client_id"],
            "auth_uri": st.secrets["google_drive"]["auth_uri"],
            "token_uri": st.secrets["google_drive"]["token_uri"],
            "auth_provider_x509_cert_url": st.secrets["google_drive"]["auth_provider_x509_cert_url"],
            "client_x509_cert_url": st.secrets["google_drive"]["client_x509_cert_url"],
            "universe_domain": st.secrets["google_drive"]["universe_domain"]
        }

        # 3. Write the secrets dictionary to the temporary JSON file
        with open(temp_file_path, "w") as f:
            json.dump(service_account_info, f)

        # 4. Authenticate using the temporary JSON file and the Drive read-only scope
        creds = Credentials.from_service_account_file(
            temp_file_path, 
            scopes=['https://www.googleapis.com/auth/drive.readonly'] 
        )
        
        # 5. Build and return the authorized Drive service
        service = build('drive', 'v3', credentials=creds)
        os.remove(temp_file_path)
        return service
        
    except Exception as e:
        print(f"Authentication failed. Check FOLDER_ID, Service Account sharing, and secrets.toml configuration. Error: {e}")
        return None

def find_files_in_folder(service, file_extensions, folder_id=FOLDER_ID):
    """Searches for files with specific extensions within a given folder ID."""
    
    ext_query = " or ".join([f"name contains '{ext}'" for ext in file_extensions])
    
    query = (
        f"'{folder_id}' in parents "
        f"and ( {ext_query} ) "
        f"and trashed = false"
    )

    results = service.files().list(
        q=query, 
        pageSize=10, 
        fields="nextPageToken, files(id, name, mimeType)"
    ).execute()
    
    return results.get('files', [])

def download_file(service, file_id, file_name):
    """
    Downloads a file from Google Drive and saves it to the /tmp directory.
    Returns the full local path to the downloaded file.
    """
    # 1. Define the full local path in /tmp
    local_path = f"/tmp/{file_name}"
    
    print(f"Downloading {file_name} to {local_path}...")
    
    # 2. Prepare the request
    request = service.files().get_media(fileId=file_id)
    
    # 3. Open the local file in write-binary mode
    with open(local_path, "wb") as f:
        downloader = MediaIoBaseDownload(f, request)
        done = False
        
        # 4. Execute the download in chunks
        while done is False:
            status, done = downloader.next_chunk()
    return local_path

def set_configuration_files(extensions=['.docx', '.xlsx']):
    try:
        drive_service = get_drive_service()

        if drive_service:
            
            files = find_files_in_folder(drive_service, extensions)
            
            if not files:
                st.error(f"No files found with extensions {extensions} in the target folder.")
            else:         
                for file in files:
                    if ".docx" in file['name']:
                        st.session_state["template_path"] = download_file(drive_service, file['id'], file['name'])
                    elif ".xlsx" in file['name']:
                        st.session_state["masterliste_path"] = download_file(drive_service, file['id'], file['name'])
        return files
    except:
        return None