import streamlit as st
from src.graph import create_codex_engine
import time

# --- ADWAITA DARK UI CONFIG ---
st.set_page_config(page_title="CodexEngine V2", page_icon="🏛️", layout="centered")

# Custom CSS for Adwaita-dark feel
st.markdown("""
    <style>
    .stApp { background-color: #1e1e1e; color: #dededa; }
    [data-testid="stSidebar"] { background-color: #242424; }
    .stChatMessage { border-radius: 10px; border: 1px solid #353535; margin-bottom: 10px; }
    code { color: #f6d32d; } /* GNOME yellow for code */
    </style>
""", unsafe_allow_html=True)

st.title("🏛️ CodexEngine V2")
st.caption("Agentic RAG | Hybrid Search | Adwaita Dark")

# Initialize Graph and Session State
if "agent" not in st.session_state:
    st.session_state.agent = create_codex_engine()
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- SIDEBAR: DEV CONSOLE ---
with st.sidebar:
    st.header("Settings")
    if st.button("Clear Conversation"):
        st.session_state.messages = []
        st.rerun()
    
    st.divider()
    st.subheader("Agent Debugger")
    # This will display the most recent node outputs
    debug_container = st.empty()

# --- CHAT DISPLAY ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- INPUT & AGENTIC EXECUTION ---
if prompt := st.chat_input("Ask your documents..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        # The 'Brain' process visible to the user
        with st.status("Agentic loop initiated...", expanded=True) as status:
            initial_state = {
                "initial_query": prompt,
                "current_query": prompt,
                "iteration": 0,
                "context": "",
                "answer": ""
            }
            
            # Streaming the graph for transparency
            final_state = initial_state
            for step in st.session_state.agent.stream(initial_state):
                for node, data in step.items():
                    st.write(f"⚙️ Executing: **{node}**")
                    final_state.update(data) # Update state as we go
                    
                    if node == "evaluate" and data.get("route") == "retry":
                        st.write(f"🔍 *Evaluator:* Context insufficient. Rewriting query to: `{data['current_query']}`")
            
            status.update(label="Response Synthesized!", state="complete", expanded=False)
        
        # Display the Final Answer
        answer = final_state.get("answer", "Error: No answer generated.")
        st.markdown(answer)
        st.session_state.messages.append({"role": "assistant", "content": answer})
        
        # Update Debugger
        debug_container.json(final_state)