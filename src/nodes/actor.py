import os
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

        === CHAT HISTORY ===
        {history_text}

        === THE TECHNICAL QUESTION ===
        User: {state["user_query"]}
        """

    else:  # strict research mode
        prompt = f"""
        You are CodexEngine, a precise, strict corporate RAG analyst. You must answer the user's intent using ONLY the facts provided in the RETRIEVED CONTEXT section below.

        CRITICAL LAWS FOR RESEARCH MODE:
        1. Base your response strictly and exclusively on the RETRIEVED CONTEXT.
        2. If the RETRIEVED CONTEXT is empty, irrelevant, or does not contain the specific answer to the user's query, you MUST reply with exactly this text and nothing else:
           "I don't have enough specific information in my database to answer that accurately."
        3. Do not utilize your general world pre-trained knowledge to fill in gaps. If the database chunks don't say it, you don't know it.

        === CHAT HISTORY ===
        {history_text}

        === CURRENT INTENT ===
        LATEST USER QUERY: {state["user_query"]}
        RETRIEVED CONTEXT FROM DATABASE: {state["context"]}
        """

    print(f"\n--- [ACTOR] Generating Response for {intent.upper()} Mode ---")
    response = llm.invoke(prompt)

    return {"response": response.content}
