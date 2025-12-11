import streamlit as st
from RAG.openai_rag import OpenAIRAG

st.title("📁 Hochladen")


# ---------------------------
# 1. Folder Upload
# ---------------------------

st.subheader("Ordner Hochladen")

uploaded_files = st.file_uploader(
    "Select a folder",
    type=None,
    accept_multiple_files=True,
    help="Drag & drop a folder – Streamlit uploads all files inside it."
)

if uploaded_files:
    st.success(f"{len(uploaded_files)} Dokumente sind hochgeladen.")

    st.write("### Hochgeladene Dateien")
    for f in uploaded_files:
        st.write(f"- {f.name}")

    # TODO: Add your folder processing & ingestion logic here


# ---------------------------
# 2. List Files in Vector Store
# ---------------------------

st.subheader("📄 Dokumente im System")

try:
    rag = OpenAIRAG(collection_name="ff-pilot")
    files = rag.list_files()

    if len(files.data) == 0:
        st.info("Keine Datei im System!")
    else:
        for f in files.data:
            st.write(f"- **{rag.retrieve_filename(f.id)}**")

except Exception as e:
    st.error(f"Error {e}")
