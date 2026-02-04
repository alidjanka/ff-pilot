import streamlit as st
import time

from RAG.openai_rag import OpenAIRAG
#from utils.projects import load_projects, save_projects, delete_project
from utils.file_system import set_configuration_files

MAX_PROJEKTE=30

#st.title("📁 Projekte")
st.image("assets/logo_2.svg", width=200)
st.markdown(
        "[📄 Vorlage & Masterliste hier](https://drive.google.com/drive/folders/1rrX8hLwrIwzfzdOsyAF4O1TaXfSmhCMc?usp=sharing)"
    )

if "template_path" not in st.session_state:
    r = set_configuration_files()
    if r is None:
        st.error("Config failed")

init_rag = OpenAIRAG()
st.session_state["projects"] = init_rag.list_project_names()
if "last_modified_time" not in st.session_state:
    st.session_state["last_modified_time"] = None

# =====================================================
# SECTION A — Bestehendes Projekt auswählen
# =====================================================
st.header("📂 Bestehendes Projekt auswählen")

if not st.session_state["projects"]:
    st.info("Noch keine Projekte vorhanden.")
else:
    selected_name = st.selectbox(
        "Projekt auswählen",
        options=list(st.session_state["projects"].keys()),
        index=None,
        placeholder="Bitte Projekt auswählen",
    )

    if selected_name:
        project_id = st.session_state["projects"][selected_name]

        st.session_state["project_id"] = project_id
        st.session_state["projektbezeichnung"] = selected_name
        st.session_state["objektadresse"] = ""
        st.session_state["ansprechpartner"] = ""

        rag = OpenAIRAG(
            projektbezeichnung=st.session_state["projektbezeichnung"],
            objektadresse=st.session_state["objektadresse"],
            ansprechpartner=st.session_state["ansprechpartner"],
        )
        st.success(f'Projekt {st.session_state["projektbezeichnung"]} ist ausgewählt!')
    # -------------------------------------------------
    # Uploaded files
    # -------------------------------------------------
        st.subheader("📄 Bereits hochgeladene Dokumente")

        try:
            st.session_state["files"] = rag.list_files()

            if len(st.session_state["files"].data) == 0:
                st.info("Keine Datei im System!")
            else:
                for f in st.session_state["files"].data:
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
                            st.session_state["files"] = rag.list_files()
                            st.rerun()

        except Exception as e:
            st.error(f"Error: {e}")
        # -------------------------------------------------
        # Upload additional documents
        # -------------------------------------------------
        st.subheader("➕ Weitere Dokumente hochladen")

        uploaded_files = st.file_uploader(
            "Dokumente auswählen",
            type=["pdf", "png", "jpeg", "jpg"],
            accept_multiple_files=True,
        )

        if uploaded_files:
            with st.spinner("Dokumente werden hochgeladen …"):
                for file in uploaded_files:
                    rag.ingest_uploaded_file(file)  

        # -------------------------------------------------
        # Delete project (stub)
        # -------------------------------------------------
        if st.button("🗑️ Projekt löschen", type="secondary"):
            with st.spinner("Projekt wird gelöscht …"):
                if rag.delete_vector_store():
                    #delete_project(project_id)
                    st.success(f"Projekt {st.session_state['projektbezeichnung']} ist gelöscht.")
                    st.session_state["project_id"] = None
                    st.session_state["projektbezeichnung"] = None
                    st.session_state["objektadresse"] = None
                    st.session_state["ansprechpartner"] = None
                    st.session_state["projects"] = rag.list_project_names()


st.divider()

# =====================================================
# SECTION B — Neues Projekt (FORM!)
# =====================================================
st.header("➕ Neues Projekt erstellen")

with st.form("new_project_form", clear_on_submit=True):
    new_project_name = st.text_input("Projektbezeichnung")
    new_files = st.file_uploader(
        "Dokumente hochladen (PDF)",
        type=["pdf"],
        accept_multiple_files=True,
    )

    submitted = st.form_submit_button("🚀 Neues Projekt anlegen")

if submitted:
    if len(st.session_state["projects"]) >= MAX_PROJEKTE:
        st.warning(
            f"Maximal erlaubte Anzahl von Projekten ist {MAX_PROJEKTE}. "
            "Lösche ein altes Projekt und versuch erneut."
        )
        st.stop()

    if not new_project_name or not new_files:
        st.error("Projektbezeichnung und mindestens eine Datei sind erforderlich.")
        st.stop()

    if new_project_name in st.session_state["projects"]:
        st.error("Projekt existiert bereits.")
        st.stop()

    rag = OpenAIRAG(
        projektbezeichnung=new_project_name,
        objektadresse="",
        ansprechpartner="",
    )

    with st.spinner("Dokumente werden hochgeladen …"):
        for f in new_files:
            rag.ingest_uploaded_file(f)
        # sleep until all files are registered, i observed a slight delay
        time.sleep(2)
        st.session_state["projects"] = rag.list_project_names()
        st.success("✅ Projekt erfolgreich erstellt!")
    time.sleep(1)
    st.rerun()