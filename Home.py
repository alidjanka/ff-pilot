import streamlit as st

st.set_page_config(page_title="Dokument Generator", layout="wide")

# ------------------- Initialize session state -------------------
if "generated_doc" not in st.session_state:
    st.session_state.generated_doc = None

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# ------------------- Layout -------------------
st.title("📘 Dokument Generator")

# Two columns for split screen
left_col, right_col = st.columns([2, 1])  # bigger left side


# ------------------- LEFT COLUMN: DOCUMENT GENERATOR -------------------
with left_col:
    st.header("📄 Dokumenterstellung")

    if st.button("📄 Dokument mit Vorlage generieren"):
        # TODO: Replace with your backend logic
        st.session_state.generated_doc = (
            "**Beispiel-Dokument:**\n\n"
            "Dies ist ein Platzhalter. Hier fügt dein Backend das generierte "
            "Dokument ein."
        )
        st.success("Dokument wurde generiert!")

    st.markdown("---")

    if st.session_state.generated_doc:
        st.subheader("📘 Generiertes Dokument")
        st.markdown(st.session_state.generated_doc)
    else:
        st.info("Noch kein Dokument generiert.")


# ------------------- RIGHT COLUMN: CHAT INTERFACE -------------------
with right_col:
    st.header("💬 Chat")

    # Show chat history
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    # Chat input at bottom
    user_input = st.chat_input("Nachricht eingeben...")

    if user_input:
        # Append user message
        st.session_state.chat_history.append({
            "role": "user",
            "content": user_input
        })

        # TODO: Replace this with backend LLM call
        bot_reply = "Platzhalter-Antwort. Hier kommt die Antwort des AI-Assistenten."

        st.session_state.chat_history.append({
            "role": "assistant",
            "content": bot_reply
        })

        st.rerun()