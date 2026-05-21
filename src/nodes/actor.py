from dotenv import load_dotenv
from langchain_groq import ChatGroq

from src.state import AgentState

load_dotenv()
llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.3)


def generate_answer(state: AgentState):
    messages = state.get("messages", [])
    history_text = "No prior history."

    if len(messages) > 1:
        history_lines = []
        for m in messages[:-1]:
            role = m[0] if isinstance(m, tuple) else m.type
            content = m[1] if isinstance(m, tuple) else m.content
            history_lines.append(f"{role.capitalize()}: {content}")
        history_text = "\n".join(history_lines)

    intent = state.get("intent", "research")

    # Construct entirely isolated operational payloads
    if intent == "casual":
        prompt = f"""
        You are CodexEngine, chatting with Anmol. Be warm, friendly, witty, and highly conversational.
        Use the CHAT HISTORY to maintain context about who he is and his preferences. Keep answers snappy and organic.
        Do NOT mention databases, contexts, or missing files. Just talk to him like a peer.

        CRITICAL: Output ONLY your direct response to the user. Do NOT prefix your answer with "CodexEngine:", "casual", or any other labels.

        === CHAT HISTORY ===
        {history_text}

        === CURRENT USER INPUT ===
        Anmol: {state["user_query"]}
        """

    elif intent == "explanatory":
        prompt = f"""
        You are CodexEngine, a brilliant technical educator and world-class AI developer.
        Answer the user's query comprehensively using your vast internal pre-trained knowledge base.
        Explain concepts clearly, use rich markdown, provide clean code snippets if applicable, and maintain an informative tone.
        You do not need to rely on or look for local database citations for this mode.

        CRITICAL: Output ONLY your direct response. Do NOT prefix your answer with your role, name, or labels.

        === CHAT HISTORY ===
        {history_text}

        === THE TECHNICAL QUESTION ===
        User: {state["user_query"]}
        """
    else:  # strict research mode
        prompt = f"""
        You are CodexEngine, a precise corporate RAG analyst.

        CRITICAL LAWS:
        1. Base your response primarily on the RETRIEVED CONTEXT below.
        2. COGNITIVE EXCEPTION: If the user is asking about the state of the current conversation, session rules you were given, or their own personal info, use the CHAT HISTORY to answer completely.
        3. If it is a purely factual document search and both the RETRIEVED CONTEXT and CHAT HISTORY are completely empty or lack the answer, reply with exactly:
           "I don't have enough specific information in my database to answer that accurately."
        4. Output ONLY your direct response. Do NOT prefix your answer with your role, name, or labels.

        === CHAT HISTORY ===
        {history_text}

        === CURRENT INTENT ===
        LATEST USER QUERY: {state["user_query"]}
        RETRIEVED CONTEXT FROM DATABASE: {state["context"]}
        """

    print(f"\n--- [ACTOR] Generating Response for {intent.upper()} Mode ---")
    response = llm.invoke(prompt)

    return {"response": response.content, "messages": [("assistant", response.content)]}
