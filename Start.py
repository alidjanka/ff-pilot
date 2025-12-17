import streamlit as st

from RAG.openai_rag import OpenAIRAG
from utils.projects import load_projects, save_projects, delete_project
from utils.file_system import get_drive_service, find_files_in_folder, download_file

st.title("📁 Projekte")

projects = load_projects()

def set_configuration_files():
    try:
        drive_service = get_drive_service()

        if drive_service:
            
            extensions = ['.docx', '.xlsx']
            files = find_files_in_folder(drive_service, extensions)
            
            if not files:
                st.error(f"No files found with extensions {extensions} in the target folder.")
            else:         
                for file in files:
                    if ".docx" in file['name']:
                        st.session_state["template_path"] = download_file(drive_service, file['id'], file['name'])
                    elif ".xlsx" in file['name']:
                        st.session_state["masterliste_path"] = download_file(drive_service, file['id'], file['name'])
        return True
    except:
        return False

# =====================================================
# SECTION A — Bestehendes Projekt auswählen
# =====================================================
st.header("📂 Bestehendes Projekt auswählen")
if set_configuration_files():
    st.write(f"Ok {st.session_state["template_path"]}")
else:
    st.write("Config failed")

if not projects:
    st.info("Noch keine Projekte vorhanden.")
else:
    project_options = {
        v["projektbezeichnung"]: k for k, v in projects.items()
    }

    selected_name = st.selectbox(
        "Projekt auswählen",
        options=list(project_options.keys()),
        index=None,
        placeholder="Bitte Projekt auswählen",
    )

    if selected_name:
        project_id = project_options[selected_name]
        meta = projects[project_id]

        st.subheader("📌 Projektdetails")
        st.write(f"**Objektadresse:** {meta['objektadresse']}")
        st.write(f"**Ansprechpartner:** {meta['ansprechpartner']}")

        rag = OpenAIRAG(
            projektbezeichnung=meta["projektbezeichnung"],
            objektadresse=meta["objektadresse"],
            ansprechpartner=meta["ansprechpartner"],
        )

        st.session_state["project_id"] = project_id
        st.session_state["projektbezeichnung"] = meta["projektbezeichnung"]
        st.session_state["objektadresse"] = meta["objektadresse"]
        st.session_state["ansprechpartner"] = meta["ansprechpartner"]

        # -------------------------------------------------
        # Uploaded files
        # -------------------------------------------------
        st.subheader("📄 Bereits hochgeladene Dokumente")

        try:
            files = rag.list_files()

            if len(files.data) == 0:
                st.info("Keine Datei im System!")
            else:
                for f in files.data:
                    col1, col2 = st.columns([4, 1])

                    filename = rag.retrieve_filename(f.id)

                    with col1:
                        st.write(f"📄 **{filename}**")

                    with col2:
                        if st.button(
                            "🗑️",
                            key=f"delete_file_{f.id}",
                            help="Datei löschen",
                        ):
                            rag.delete_file(f.id)
                            st.success(f"{filename} gelöscht")
                            st.rerun()

        except Exception as e:
            st.error(f"Error: {e}")
        # -------------------------------------------------
        # Upload additional documents
        # -------------------------------------------------
        st.subheader("➕ Weitere Dokumente hochladen")

        uploaded_files = st.file_uploader(
            "Dokumente auswählen",
            type=["pdf", "docx", "txt"],
            accept_multiple_files=True,
        )

        if uploaded_files:
            with st.spinner("Dokumente werden verarbeitet …"):
                for file in uploaded_files:
                    rag.ingest_uploaded_file(file)  

        # -------------------------------------------------
        # Delete project (stub)
        # -------------------------------------------------
        if st.button("🗑️ Projekt löschen", type="secondary"):
            if rag.delete_vector_store():
                delete_project(project_id)
                st.success(f"Projekt {st.session_state['projektbezeichnung']} ist gelöscht.")
                st.session_state["project_id"] = None
                st.session_state["projektbezeichnung"] = None
                st.session_state["objektadresse"] = None
                st.session_state["ansprechpartner"] = None


st.divider()

# =====================================================
# SECTION B — Neues Projekt erstellen
# =====================================================
st.header("➕ Neues Projekt erstellen")

projektbezeichnung = st.text_input("Projektbezeichnung")
objektadresse = st.text_input("Objektadresse")
ansprechpartner = st.text_input("Ansprechpartner")

uploaded_files = st.file_uploader(
    "Dokumente hochladen (PDF)",
    type=["pdf"],
    accept_multiple_files=True,
)

if st.button("🚀 Neues Projekt anlegen"):
    if not projektbezeichnung or not uploaded_files:
        st.error("Projektbezeichnung und mindestens eine Datei sind erforderlich.")
        st.stop()

    project_id = projektbezeichnung.lower().replace(" ", "_")

    if project_id in projects:
        st.error("Projekt existiert bereits.")
        st.stop()

    # Save project metadata locally
    projects[project_id] = {
        "projektbezeichnung": projektbezeichnung,
        "objektadresse": objektadresse,
        "ansprechpartner": ansprechpartner,
        "project_id": project_id,
    }

    rag = OpenAIRAG(
        projektbezeichnung=projektbezeichnung,
        objektadresse=objektadresse,
        ansprechpartner=ansprechpartner,
    )
    st.session_state["projektbezeichnung"] = projektbezeichnung
    st.session_state["objektadresse"] = objektadresse
    st.session_state["ansprechpartner"] = ansprechpartner

    with st.spinner("Dokumente werden verarbeitet …"):
        for file in uploaded_files:
            rag.ingest_uploaded_file(file)
    save_projects(projects)

    st.success("✅ Projekt erfolgreich erstellt und ausgewählt!")