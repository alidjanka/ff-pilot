import streamlit as st
import os
import json
from datetime import datetime

# Import Google API libraries
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload


# --- CONFIGURATION ---
# IMPORTANT: REPLACE THIS with the ID of your Google Drive folder
#FOLDER_ID = "1rrX8hLwrIwzfzdOsyAF4O1TaXfSmhCMc" 
FOLDER_ID = "1qR1lPW1wim1rGPYFVyF8jsi28qXKCH4N"
SHARED_DRIVE_ID = "0AM0hPlPro9rvUk9PVA"
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
            scopes=['https://www.googleapis.com/auth/drive']
        )
        
        # 5. Build and return the authorized Drive service
        service = build('drive', 'v3', credentials=creds)
        os.remove(temp_file_path)
        return service
        
    except Exception as e:
        print(f"Authentication failed. Check FOLDER_ID, Service Account sharing, and secrets.toml configuration. Error: {e}")
        return None


def find_files_in_drive(
    service,
    file_extensions,
    folder_id=SHARED_DRIVE_ID,
    shared_drive_id=SHARED_DRIVE_ID
):
    """Searches for files with specific extensions within a folder in a Shared Drive."""

    ext_query = " or ".join(
        [f"name contains '{ext}'" for ext in file_extensions]
    )

    query = (
        f"'{folder_id}' in parents and "
        f"( {ext_query} ) and "
        f"trashed = false"
    )

    results = service.files().list(
        q=query,
        corpora="drive",
        driveId=shared_drive_id,
        includeItemsFromAllDrives=True,
        supportsAllDrives=True,
        pageSize=100,
        fields="files(id, name, mimeType)"
    ).execute()

    return results.get("files", [])


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

def get_file_metadata(service, file_id):
    file = service.files().get(
        fileId=file_id,
        fields="id, name, modifiedTime, md5Checksum"
    ).execute()
    return file

def download_updated_file(service, file_id, file_name):
    meta = get_file_metadata(service, file_id)

    if st.session_state["last_modified_time"] != meta["modifiedTime"]:
        local_path = download_file(service, file_id, file_name)
        st.session_state["last_modified_time"] = meta["modifiedTime"]
        return True  # downloaded
    else:
        return False  # no change


def set_configuration_files(extensions=['.docx', '.xlsx']):
    try:
        drive_service = get_drive_service()

        if drive_service:
            
            files = find_files_in_drive(drive_service, extensions)
            
            if not files:
                st.error(f"No files found with extensions {extensions} in the target folder.")
            else:         
                for file in files:
                    if ".docx" in file['name']:
                        st.session_state["template_path"] = download_file(drive_service, file['id'], file['name'])
                    if ".xlsx" in file['name']:
                        st.session_state["masterliste_path"] = download_file(drive_service, file['id'], file['name'])
        return files
    except:
        return None

def update_configuration_files(extensions=['.docx', '.xlsx']):
    try:
        drive_service = get_drive_service()

        if drive_service:
            
            files = find_files_in_drive(drive_service, extensions)
            
            if not files:
                st.error(f"No files found with extensions {extensions} in the target folder.")
            else:         
                for file in files:
                    if ".docx" in file['name']:
                        is_vorlage_updated = download_updated_file(drive_service, file['id'], file['name'])
                    if ".xlsx" in file['name']:
                        is_masterliste_updated = download_updated_file(drive_service, file['id'], file['name'])
        return is_vorlage_updated, is_masterliste_updated
    except:
        return None

def get_or_create_folder(
    service,
    folder_name,
    parent_folder_id=SHARED_DRIVE_ID,
    shared_drive_id=SHARED_DRIVE_ID
):
    """Returns folder_id. Creates folder if it does not exist (Shared Drive–safe)."""

    query = (
        f"'{parent_folder_id}' in parents and "
        f"name = '{folder_name}' and "
        f"mimeType = 'application/vnd.google-apps.folder' and "
        f"trashed = false"
    )

    results = service.files().list(
        q=query,
        corpora="drive",
        driveId=shared_drive_id,
        includeItemsFromAllDrives=True,
        supportsAllDrives=True,
        fields="files(id, name)"
    ).execute()

    folders = results.get("files", [])
    if folders:
        return folders[0]["id"]

    folder_metadata = {
        "name": folder_name,
        "mimeType": "application/vnd.google-apps.folder",
        "parents": [parent_folder_id]
    }

    folder = service.files().create(
        body=folder_metadata,
        supportsAllDrives=True,
        fields="id"
    ).execute()

    return folder["id"]

def save_generated_doc_to_drive(
    project_name,
    generated_doc
):
    service = get_drive_service()
    if not service:
        st.error("Google Drive service not available.")
        return None

    # 1. Project folder (one per project)
    project_folder_id = get_or_create_folder(
        service=service,
        folder_name=project_name,
        parent_folder_id=SHARED_DRIVE_ID,
        shared_drive_id=SHARED_DRIVE_ID
    )

    # 2. Version folder (timestamp-based)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    version_folder_name = f"version_{timestamp}"

    version_folder_id = get_or_create_folder(
        service=service,
        folder_name=version_folder_name,
        parent_folder_id=project_folder_id,
        shared_drive_id=SHARED_DRIVE_ID
    )

    uploaded_files = []

    # ─────────────────────────────────────────────
    # 3. Upload GENERATED DOCUMENT
    # ─────────────────────────────────────────────
    generated_filename = f"FLB_{project_name}_{timestamp}.docx"
    generated_local_path = f"/tmp/{generated_filename}"

    with open(generated_local_path, "wb") as f:
        f.write(generated_doc)

    generated_media = MediaFileUpload(
        generated_local_path,
        mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        resumable=False
    )

    # Upload as Google Doc by setting the target mimeType.
    generated_file = service.files().create(
        body={
            "name": generated_filename,
            "parents": [version_folder_id],
            "mimeType": "application/vnd.google-apps.document"
        },
        media_body=generated_media,
        supportsAllDrives=True,
        fields="id, name, webViewLink"
    ).execute()

    uploaded_files.append(generated_file)
    os.remove(generated_local_path)

    # ─────────────────────────────────────────────
    # 4. Upload TEMPLATE SNAPSHOT
    # ─────────────────────────────────────────────
    template_path = st.session_state.get("template_path")

    if template_path and os.path.exists(template_path):
        template_name = os.path.basename(template_path)

        template_media = MediaFileUpload(
            template_path,
            mimetype="application/vnd.openxmlformats-officedocument.woproject_folder_idrdprocessingml.document",
            resumable=False
        )

        template_file = service.files().create(
            body={
                "name": template_name,
                "parents": [version_folder_id]
            },
            media_body=template_media,
            supportsAllDrives=True,
            fields="id, name"
        ).execute()

        uploaded_files.append(template_file)

    return {
        "project_folder_id": project_folder_id,
        "version_folder_id": version_folder_id,
        "files": uploaded_files,
        "generated_file_link": generated_file.get("webViewLink")
    }
