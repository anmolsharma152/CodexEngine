from langchain_core.prompts import ChatPromptTemplate
from src.state import AgentState
from src.log_utils import logger
from src.llm import get_chat_model

llm = get_chat_model(temperature=0, max_retries=3)


async def condense_question_node(state: AgentState):
    history = state["messages"][:-1]

    if not history:
        logger.info("No history — skipping condensation")
        return {"search_query": state["user_query"]}

    prompt = ChatPromptTemplate.from_template("""
        Given the following conversation history and a follow-up question,
        rephrase the follow-up to be a standalone question.

        Chat History: {history}
        Follow-up Question: {user_query}
        Standalone Question:
    """)

    chain = prompt | llm
    result = await chain.ainvoke({"history": history, "user_query": state["user_query"]})
    logger.info(f"Resolved Query: {result.content}")
    return {"search_query": result.content}
