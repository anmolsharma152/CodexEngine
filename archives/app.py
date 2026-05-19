import streamlit as st
from src.graph import app
from src.state import AgentState

# --- Page Config ---
st.set_page_config(
    page_title="CodexEngine V2.5", 
    page_icon="🏛️", 
    layout="centered"
)

st.title("🏛️ CodexEngine V2.5")
st.caption("Production-Grade Agentic RAG powered by LangGraph & pgvector")
st.divider()

# --- Session State Management ---
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Welcome to CodexEngine. What would you like to explore today?"}
    ]

# Render existing chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- Chat Input & Execution ---
if prompt := st.chat_input("Ask a technical, narrative, or academic question..."):
    
    # 1. Display User Message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. Display Assistant Response
    with st.chat_message("assistant"):
        
        # The "Thought Trace" Collapsible UI
        with st.status("🧠 Initializing Agentic Loop...", expanded=True) as status:
            try:
                inputs = AgentState(query=prompt)
                final_answer = ""
                
                # Stream the LangGraph execution
                for output in app.stream(inputs):
                    for node, state in output.items():
                        if node == "retrieve":
                            st.write(f"🔍 **Retrieving:** `{state.get('query', prompt)}`")
                        elif node == "evaluate":
                            score = state.get("critic_score", 0.0)
                            if score >= 0.7:
                                st.success(f"✅ **Critic Score:** {score}")
                            else:
                                st.error(f"❌ **Critic Score:** {score}")
                        elif node == "rewrite":
                            st.warning(f"🔄 **Rewriter Pivot:** `{state.get('query', '')}`")
                        elif node == "actor":
                            st.info("✍️ **Synthesizing**...")
                            final_answer = state.get("answer", "")

                status.update(label="Agentic Loop Complete!", state="complete", expanded=False)

            except Exception as e:
                # Handle the Groq TPD/RPM limit specifically
                if "rate_limit" in str(e).lower():
                    error_msg = "📉 **Groq Quota Exhausted.** The daily token limit has been reached. Please try again later."
                else:
                    error_msg = f"⚠️ **Engine Error:** {str(e)}"
                
                status.update(label="Loop Interrupted", state="error", expanded=True)
                final_answer = error_msg
        
        # 3. Render the Final Answer (or Error Message)
        st.markdown(final_answer)
        
    # 4. Save to Session State
    st.session_state.messages.append({"role": "assistant", "content": final_answer})
