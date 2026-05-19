import streamlit as st
import os


def render_sidebar():
    # CodexEngine Branding
    st.sidebar.title("🏛️ CodexEngine Config")

    provider = st.sidebar.selectbox(
        "Select AI Provider", options=["Groq", "Openai", "Gemini", "Anthropic"], index=0
    )

    # Map providers to their default state-of-the-art models
    model_mapping = {
        "Groq": "llama-3.3-70b-versatile",
        "Openai": "gpt-4o",
        "Gemini": "gemini-2.0-flash",
        "Anthropic": "claude-3-5-sonnet-20241022",
    }

    model_name = st.sidebar.text_input("Model Name", value=model_mapping[provider])

    env_key_name = f"{provider.upper()}_API_KEY"
    api_key = st.sidebar.text_input(
        f"{provider.capitalize()} API Key",
        type="password",
        value=os.getenv(env_key_name, ""),
    )

    st.session_state.provider = provider
    st.session_state.model_name = model_name
    st.session_state.api_key = api_key

    st.sidebar.markdown("---")

    # ==========================================
    # Target Document Search (Robust ChromaDB Fetch)
    # ==========================================
    st.sidebar.subheader("🎯 Target Search")

    available_docs = []
    if "vector_store" in st.session_state and st.session_state.vector_store is not None:
        try:
            # Bypass wrappers and ask the database exactly what metadata it holds
            db_data = st.session_state.vector_store.collection.get(
                include=["metadatas"]
            )

            if db_data and db_data.get("metadatas"):
                # Deduplicate the source names using a set, then sort them
                unique_sources = list(
                    set(
                        [
                            meta["source"]
                            for meta in db_data["metadatas"]
                            if meta and "source" in meta
                        ]
                    )
                )
                available_docs = sorted(unique_sources)

        except Exception as e:
            # Never fail silently in development. Show the error in the sidebar.
            st.sidebar.error(f"Failed to read index: {str(e)}")

    selected_docs = st.sidebar.multiselect(
        "Select specific documents to search (Leave empty for all):",
        options=available_docs,
        default=[],
    )
    st.session_state.selected_docs = selected_docs

    st.sidebar.markdown("---")

    if st.sidebar.button("Clear Chat History", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
