import streamlit as st
import os

def render_sidebar():
    st.sidebar.title("⚙️ Configuration")
    
    provider = st.sidebar.selectbox(
        "Select AI Provider",
        options=["Groq", "Openai", "Gemini", "Anthropic"],
        index=0
    )
    
    # Map providers to their default state-of-the-art models
    model_mapping = {
        "Groq": "llama-3.3-70b-versatile",
        "Openai": "gpt-4o",
        "Gemini": "gemini-2.0-flash",
        "Anthropic": "claude-3-5-sonnet-20241022"
    }
    
    model_name = st.sidebar.text_input("Model Name", value=model_mapping[provider])
    
    env_key_name = f"{provider.upper()}_API_KEY"
    api_key = st.sidebar.text_input(
        f"{provider.capitalize()} API Key", 
        type="password", 
        value=os.getenv(env_key_name, "")
    )
    
    st.session_state.provider = provider
    st.session_state.model_name = model_name
    st.session_state.api_key = api_key
    
    st.sidebar.markdown("---")
    if st.sidebar.button("Clear Chat History"):
        st.session_state.messages = []
        st.rerun()