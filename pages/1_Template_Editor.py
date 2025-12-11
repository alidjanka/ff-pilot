import streamlit as st

from prompts.prompts import Sections

st.set_page_config(page_title="Template Editor", layout="wide")

st.title("🧩 Template-Editor für Dokumenterstellung")

# Full section titles (you fill these from backend later)
SECTIONS = Sections

# ---------- Initialize templates in session ----------
if "templates" not in st.session_state:
    st.session_state.templates = {
        sec: f"{sec}" for sec in SECTIONS
    }

# ---------- UI: Sidebar section selector ----------
st.sidebar.markdown("### 📑 Abschnitte")

# Create simple labels: "1. Abschnitt", "2. Abschnitt", …
sidebar_labels = [f"{i+1}. Abschnitt" for i in range(len(SECTIONS))]

# User clicks simple label; we map back to index
selected_label = st.sidebar.radio(
    "Abschnitt auswählen:",
    sidebar_labels,
    index=0,
)

# Extract index from selected label
selected_index = sidebar_labels.index(selected_label)

# Get actual section title
selected_section = SECTIONS[selected_index]

# ---------- UI: Main content ----------
st.markdown(f"## ✏️ Vorlage bearbeiten:")

current_text = st.session_state.templates[selected_section]

edited_text = st.text_area(
    "Template-Anweisungen:",
    value=current_text,
    height=350,
    placeholder="Hier kannst du beschreiben, was in diesem Abschnitt generiert werden soll…",
)

if st.button("💾 Änderungen speichern"):
    st.session_state.templates[selected_section] = edited_text
    # TODO: Save changes to filesystem or backend
    st.success("Änderungen gespeichert (Platzhalter).")
