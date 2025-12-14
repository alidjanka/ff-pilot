import streamlit as st

from RAG.openai_rag import OpenAIRAG
from utils.projects import load_projects, save_projects, delete_project

st.title("📁 Projekte")

projects = load_projects()

# =====================================================
# SECTION A — Bestehendes Projekt auswählen
# =====================================================
st.header("📂 Bestehendes Projekt auswählen")

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
                    st.write(f"- **{rag.retrieve_filename(f.id)}**")

        except Exception as e:
            st.error(f"Error {e}")

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
    save_projects(projects)

    rag = OpenAIRAG(
        projektbezeichnung=projektbezeichnung,
        objektadresse=objektadresse,
        ansprechpartner=ansprechpartner,
    )
    st.session_state["projektbezeichnung"] = meta["projektbezeichnung"]
    st.session_state["objektadresse"] = meta["objektadresse"]
    st.session_state["ansprechpartner"] = meta["ansprechpartner"]

    with st.spinner("Dokumente werden verarbeitet …"):
        for file in uploaded_files:
            rag.ingest_uploaded_file(file)

    st.success("✅ Projekt erfolgreich erstellt und ausgewählt!")