import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import json, asyncio, statistics, re
from datetime import datetime
from langgraph.checkpoint.memory import MemorySaver
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
from server import create_graph
from src.log_utils import logger

checkpointer = MemorySaver()
app = create_graph(checkpointer)

judge_llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0, max_retries=3)


async def llm_judge(prompt: str, retries=5) -> str:
    for attempt in range(retries):
        try:
            resp = await judge_llm.ainvoke([HumanMessage(content=prompt)])
            return resp.content.strip()
        except Exception as e:
            if "429" in str(e) or "rate_limit" in str(e).lower():
                wait = min(2 ** attempt * 2, 30)
                logger.warning(f"Rate limited, waiting {wait}s...")
                await asyncio.sleep(wait)
                continue
            raise e
    return ""


def extract_claims(answer: str) -> list[str]:
    sentences = re.split(r'(?<=[.!?])\s+', answer.strip())
    return [s.strip() for s in sentences if len(s.strip()) > 20]


async def faithfulness(question: str, answer: str, contexts: list[str]) -> float:
    if not answer or not contexts:
        return 0.0
    claims = extract_claims(answer)
    if not claims:
        return 0.0
    context_text = "\n\n".join(contexts)
    supported = 0
    for claim in claims:
        resp = await llm_judge(
            f"Context:\n{context_text[:3000]}\n\nClaim: {claim}\n\n"
            f"Answer ONLY with YES if the claim is supported by the context, otherwise NO."
        )
        if resp.upper().startswith("YES"):
            supported += 1
    return supported / len(claims)


async def answer_relevancy(question: str, answer: str) -> float:
    if not answer:
        return 0.0
    resp = await llm_judge(
        f"Rate how relevant this answer is to the question (0.0 to 1.0).\n"
        f"Question: {question}\nAnswer: {answer[:2000]}\n"
        f"Output ONLY a float."
    )
    try:
        return max(0.0, min(1.0, float(resp)))
    except ValueError:
        return 0.5


async def context_precision(question: str, contexts: list[str]) -> float:
    if not contexts:
        return 0.0
    relevant = 0
    for ctx in contexts:
        if not ctx.strip():
            continue
        resp = await llm_judge(
            f"Question: {question}\nContext: {ctx[:1500]}\n\n"
            f"Answer ONLY with YES if this context is relevant, otherwise NO."
        )
        if resp.upper().startswith("YES"):
            relevant += 1
    return relevant / len(contexts)


async def context_recall(question: str, contexts: list[str]) -> float:
    if not contexts:
        return 0.0
    resp = await llm_judge(
        f"Question: {question}\n\nContext:\n{''.join(contexts)[:4000]}\n\n"
        f"Rate how much of the answer can be derived from the context (0.0 to 1.0). "
        f"Output ONLY a float."
    )
    try:
        return max(0.0, min(1.0, float(resp)))
    except ValueError:
        return 0.5


async def evaluate_query(q: dict) -> dict:
    query = q["question"]
    query_id = q["query_id"]

    inputs = {
        "user_query": query,
        "search_query": query,
        "messages": [("user", query)],
        "context": "",
        "critic_score": 0.0,
        "revision_count": 0,
        "response": "",
    }
    config = {"configurable": {"thread_id": f"ragas_{query_id}"}}

    final_answer = ""
    retrieved_context = ""
    async for output in app.astream(inputs, config):
        for node, state in output.items():
            if node == "actor":
                final_answer = state.get("response", "")
            if node == "retrieve":
                retrieved_context = state.get("context", "")

    contexts = [c.strip() for c in retrieved_context.split("\n\n") if c.strip()]

    logger.info(f"Answer len={len(final_answer)}, chunks={len(contexts)}")

    fth, ar, cp, cr = await asyncio.gather(
        faithfulness(query, final_answer, contexts),
        answer_relevancy(query, final_answer),
        context_precision(query, contexts),
        context_recall(query, contexts),
    )

    return {
        "query_id": query_id,
        "question": query,
        "faithfulness": round(fth, 4),
        "answer_relevancy": round(ar, 4),
        "context_precision": round(cp, 4),
        "context_recall": round(cr, 4),
        "answer_length": len(final_answer),
        "num_chunks": len(contexts),
    }


async def main():
    with open("eval/golden_queries.json") as f:
        queries = json.load(f)["dataset"]

    logger.info(f"Running RAGAS evaluation on {len(queries)} queries...\n")
    results = []
    for q in queries:
        logger.info(f"[{q['query_id']}] {q['question'][:60]}...")
        r = await evaluate_query(q)
        results.append(r)
        logger.info(f"    faith={r['faithfulness']} rel={r['answer_relevancy']} "
                    f"prec={r['context_precision']} recall={r['context_recall']}")

    assert results, "No results produced"
    report = {
        "generated_at": datetime.now().isoformat(),
        "model": "llama-3.3-70b-versatile (actor) / llama-3.1-8b-instant (judge)",
        "metrics": ["faithfulness", "answer_relevancy", "context_precision", "context_recall"],
        "aggregate": {
            "faithfulness_mean": round(statistics.mean(r["faithfulness"] for r in results), 4),
            "answer_relevancy_mean": round(statistics.mean(r["answer_relevancy"] for r in results), 4),
            "context_precision_mean": round(statistics.mean(r["context_precision"] for r in results), 4),
            "context_recall_mean": round(statistics.mean(r["context_recall"] for r in results), 4),
        },
        "results": results,
    }
    with open("eval/ragas_report.json", "w") as f:
        json.dump(report, f, indent=2)
    logger.info("RAGAS Report:")
    for m in report["metrics"]:
        logger.info(f"  {m}: {report['aggregate'][m + '_mean']:.4f}")
    logger.info(f"Report saved to eval/ragas_report.json")

    # Verify all queries produced non-zero answer lengths (pipeline works)
    for r in results:
        assert r["answer_length"] > 0, f"[{r['query_id']}] Empty answer"


if __name__ == "__main__":
    asyncio.run(main())
