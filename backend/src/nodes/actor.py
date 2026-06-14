from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, BaseMessage

from src.state import AgentState
from src.log_utils import logger
from src.llm import get_chat_model

llm = get_chat_model(model="llama-3.3-70b-versatile", temperature=0.3, max_retries=3)


async def generate_answer(state: AgentState):
    messages = state.get("messages", [])
    intent = state.get("intent", "retrieval_required")
    context = state.get("context", "")
    evaluation = state.get("evaluation", {})

    if intent in ["casual", "direct_casual"]:
        sys_instructions = """You are CodexEngine. Be warm, helpful, and conversational.
Do not mention databases. Begin your response immediately without labels.
Format your response with excellent spacing, short paragraphs, and bullet points if explaining multiple items."""
    elif intent == "direct_parametric":
        sys_instructions = """You are CodexEngine, an elite AI knowledge agent.
You are answering this query directly from your internal pre-trained weights.

CRITICAL REQUIREMENT: You MUST prefix your response with this exact source tag:
"[Source: Internal AI Knowledge]\n\n"

CRITICAL FORMATTING LAWS:
1. Format for high readability: Use short paragraphs (max 2-3 sentences), clear bullet points, or numbered lists.
2. Put blank lines between paragraphs and list items to keep the response airy and easy to scan.
3. Answer comprehensively, clearly, and immediately after the tag. Do not use speaker labels."""
    else:
        is_sufficient = evaluation.get("sufficient", False)

        if is_sufficient and context.strip():
            sys_instructions = f"""You are CodexEngine, an elite corporate RAG analyst.
Synthesize your response using the provided RETRIEVED CONTEXT below when relevant.

=== RETRIEVED CONTEXT ===
{context}
=========================

CRITICAL EXECUTION & FORMATTING LAWS:
1. If the RETRIEVED CONTEXT contains information relevant to the user's question, use it. If it is irrelevant or insufficient, IGNORE IT and answer from your internal knowledge.
2. PROVENANCE RULE:
   - If a fact explicitly came from the RETRIEVED CONTEXT, attach its compact citation marker (e.g., `[p. 5]`, `[r. 3]`, `[doc]`) after the sentence.
   - Do NOT invent or attach citations for facts not present in the RETRIEVED CONTEXT.
   - If you used ANY retrieved context in your answer (evidenced by at least one citation), do NOT append the Internal AI Knowledge tag. The citations themselves are sufficient provenance.
   - Only if you used ZERO facts from the RETRIEVED CONTEXT (the context was entirely irrelevant) append "[Source: Internal AI Knowledge]" at the end.
3. FORMAT FOR HIGH READABILITY:
   - Break information into small, digestible paragraphs (maximum 2-3 sentences per paragraph).
   - Use bullet points or numbered lists extensively when listing details, features, steps, or facts.
   - Insert empty lines between all paragraphs and list items to avoid dense walls of text.
4. Begin your response immediately. Do not use speaker labels."""
        else:
            sys_instructions = """You are CodexEngine, an elite AI knowledge agent.
The database search did not return sufficient or relevant local documents.

CRITICAL EXECUTION & FORMATTING LAWS:
1. You are authorized to answer using your internal pre-trained knowledge.
2. You MUST begin your response with this exact warning tag:
   "[Source: Internal AI Knowledge] - No relevant documents found in the database.\n\n"
3. FORMAT FOR HIGH READABILITY: Use short paragraphs (max 2-3 sentences), clear bullet points, and blank lines to separate blocks of text.
4. If you do not know the answer internally, reply: "I don't have enough specific information to answer that."
5. Begin your response immediately. Do not use speaker labels."""

    structured_messages: list[BaseMessage] = [SystemMessage(content=sys_instructions)]

    for m in messages:
        if isinstance(m, tuple):
            if m[0] == "user":
                structured_messages.append(HumanMessage(content=m[1]))
            elif m[0] == "assistant":
                structured_messages.append(AIMessage(content=m[1]))
        else:
            structured_messages.append(m)

    logger.info(f"Generating Response for {intent.upper()} Mode")
    response = await llm.ainvoke(structured_messages)

    return {"response": response.content, "messages": [("assistant", response.content)]}
