from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, BaseMessage
from langchain_groq import ChatGroq

from src.state import AgentState

load_dotenv()
llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.3, max_retries=3)


async def generate_answer(state: AgentState):
    messages = state.get("messages", [])
    intent = state.get("intent", "retrieval_required")
    context = state.get("context", "")
    evaluation = state.get("evaluation", {})

    if intent in ["casual", "direct_casual"]:
        sys_instructions = """You are CodexEngine. Be warm and conversational.
Do not mention databases. Begin your response immediately without labels."""
    elif intent == "direct_parametric":
        sys_instructions = """You are CodexEngine, an elite AI knowledge agent.
You are answering this query directly from your internal pre-trained weights.

CRITICAL REQUIREMENT: You MUST prefix your response with this exact source tag:
"**[Source: Internal AI Knowledge]**\n\n"
Answer comprehensively, clearly, and immediately after the tag. Do not use speaker labels."""
    else:
        # retrieval_required / research path
        is_sufficient = evaluation.get("sufficient", False) or evaluation.get("relevant", False)
        
        if is_sufficient and context.strip():
            sys_instructions = f"""You are CodexEngine, an elite corporate RAG analyst.
You MUST synthesize your response using ONLY the provided RETRIEVED CONTEXT below.

=== RETRIEVED CONTEXT ===
{context}
=========================

CRITICAL EXECUTION LAWS:
1. Write a detailed response based strictly on the RETRIEVED CONTEXT.
2. You MUST append inline citations (e.g. [Source: document.pdf | Page: 12]) after every factual sentence you write.
3. Do not make assumptions or use external knowledge.
4. Begin your response immediately. Do not use speaker labels."""
        else:
            sys_instructions = """You are CodexEngine, an elite AI knowledge agent.
The database search did not return sufficient or relevant local documents.

CRITICAL EXECUTION LAWS:
1. You are authorized to answer using your internal pre-trained knowledge.
2. You MUST begin your response with this exact warning tag:
   "**[Source: Internal AI Knowledge]** - *No relevant documents found in the database.*\n\n"
3. If you do not know the answer internally, reply: "I don't have enough specific information to answer that."
4. Begin your response immediately. Do not use speaker labels."""

    structured_messages: list[BaseMessage] = [SystemMessage(content=sys_instructions)]

    for m in messages:
        if isinstance(m, tuple):
            if m[0] == "user":
                structured_messages.append(HumanMessage(content=m[1]))
            elif m[0] == "assistant":
                structured_messages.append(AIMessage(content=m[1]))
        else:
            structured_messages.append(m)

    print(f"\n--- [ACTOR] Generating Response for {intent.upper()} Mode ---")
    response = await llm.ainvoke(structured_messages)

    return {"response": response.content, "messages": [("assistant", response.content)]}
