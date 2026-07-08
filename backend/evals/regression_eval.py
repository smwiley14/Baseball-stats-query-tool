"""LangSmith regression eval for the NL2SQL chat workflow.

Runs a fixed set of known questions against the *live* running backend
(same API a browser would hit) and scores each response with both
deterministic checks (row counts, tie consistency, expected values, SQL
execution status) and an LLM-as-judge check of answer quality. Results are
uploaded to LangSmith as an experiment, so you can compare runs after
changing configs/prompts.yml or backend/configs/sql_examples.yml.

Usage:
    cd backend
    source .venv/bin/activate
    BASE_URL=http://localhost:8000 python -m evals.regression_eval

Requires the same env vars the app itself uses: LANGCHAIN_API_KEY (to
upload results) and OPENAI_API_KEY (for the LLM-judge evaluator). API_KEY
is read from backend/.env if not set explicitly.
"""

import os
from pathlib import Path

import requests
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langsmith import Client
from langsmith.schemas import Example, Run

load_dotenv()

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
API_KEY = os.getenv("API_KEY")
if not API_KEY:
    env_path = Path(__file__).parent.parent / ".env"
    for line in env_path.read_text().splitlines():
        if line.startswith("API_KEY="):
            API_KEY = line.split("=", 1)[1].strip()
            break

DATASET_NAME = "baseball-nl2sql-regression"

# Each example encodes the question plus whatever criteria matter for it.
# Not every key applies to every question - evaluators skip checks whose
# key is absent rather than failing them.
EXAMPLES = [
    {
        "question": "Who hit the most home runs in a game?",
        "min_rows": 2,
        "tie_column": "Home Runs",
    },
    {
        "question": "Who hit the most home runs in 2020?",
        "min_rows": 1,
        "expected_values": {"Player Name": "Luke Voit", "Home Runs": 22},
    },
    {
        "question": "What were Aaron Judge's batting stats in 2020?",
        "min_rows": 1,
    },
    {
        "question": "What are Mike Trout's career batting totals?",
        "min_rows": 1,
    },
    {
        "question": "What were the Yankees' team batting totals in 2020?",
        "min_rows": 1,
        # table_data uses human-readable Title Case keys, not raw SQL aliases.
        "expected_values": {"Home Runs": "94"},
    },
    {
        "question": "Who had the highest OPS in 2020 among qualified hitters?",
        "min_rows": 1,
    },
    {
        # Shorthand: "<Player> <Year>" should behave like the full-sentence version above.
        "question": "Aaron judge 2020",
        "min_rows": 1,
        "expected_values": {"Home Runs": 9},
    },
    {
        # Shorthand: bare "Most <stat>" with no season/game means all-time career leader.
        "question": "Most home runs",
        "min_rows": 1,
        # 762, not the earlier (incorrect, pre-filter-fix) 773 — see career-view
        # regular-season/AL-NL filter fix.
        "expected_values": {"Player Name": "Barry Bonds", "Career HR": 762},
    },
    {
        # Shorthand: "N <stat> games" means exactly N in a single game, not the record max.
        "question": "4 home run games",
        "min_rows": 2,
        "tie_column": "Home Runs",
    },
    {
        "question": "What is the capital of France?",
        "should_execute": False,
    },
    {
        "question": "Delete all players who played for the Yankees in 2020",
        "should_execute": False,
    },
]


def ensure_dataset(client: Client) -> str:
    if client.has_dataset(dataset_name=DATASET_NAME):
        return DATASET_NAME
    client.create_dataset(
        dataset_name=DATASET_NAME,
        description="Known-good NL2SQL questions for the baseball chat agent, "
        "covering season leaderboards, single-game ties, career/team "
        "aggregates, and off-topic/destructive rejection.",
    )
    client.create_examples(
        dataset_name=DATASET_NAME,
        examples=[
            {"inputs": {"question": ex["question"]}, "outputs": ex}
            for ex in EXAMPLES
        ],
    )
    return DATASET_NAME


def target(inputs: dict) -> dict:
    """Hits the real running backend, exactly like the frontend does."""
    resp = requests.post(
        f"{BASE_URL}/chat",
        headers={"Content-Type": "application/json", "X-API-Key": API_KEY},
        json={"message": inputs["question"]},
        # Some questions take 30-40s even without contention; under
        # max_concurrency=2 that occasionally pushed past a 60s timeout.
        timeout=120,
    )
    resp.raise_for_status()
    body = resp.json()
    metadata = body.get("metadata") or {}
    return {
        "answer": body.get("summary") or body.get("message"),
        "table_data": body.get("table_data") or [],
        "sql_query": metadata.get("sql_query"),
        "sql_execution_status": metadata.get("sql_execution_status"),
    }


def min_row_count(run: Run, example: Example) -> dict:
    expected = (example.outputs or {}).get("min_rows")
    if expected is None:
        return {"key": "min_row_count", "score": None, "comment": "not applicable"}
    actual = len(run.outputs.get("table_data") or [])
    return {
        "key": "min_row_count",
        "score": actual >= expected,
        "comment": f"expected >= {expected} rows, got {actual}",
    }


def tie_consistency(run: Run, example: Example) -> dict:
    column = (example.outputs or {}).get("tie_column")
    if column is None:
        return {"key": "tie_consistency", "score": None, "comment": "not applicable"}
    rows = run.outputs.get("table_data") or []
    values = {row.get(column) for row in rows}
    return {
        "key": "tie_consistency",
        "score": len(values) == 1,
        "comment": f"all rows should share one {column} value, saw {values}",
    }


def sql_execution_matches_expectation(run: Run, example: Example) -> dict:
    should_execute = (example.outputs or {}).get("should_execute", True)
    status = run.outputs.get("sql_execution_status")
    executed = status == "success"
    return {
        "key": "sql_execution_matches_expectation",
        "score": executed == should_execute,
        "comment": f"expected should_execute={should_execute}, got status={status}",
    }


def expected_values_present(run: Run, example: Example) -> dict:
    expected = (example.outputs or {}).get("expected_values")
    if expected is None:
        return {"key": "expected_values_present", "score": None, "comment": "not applicable"}
    rows = run.outputs.get("table_data") or []
    match = any(
        all(str(row.get(k)) == str(v) for k, v in expected.items()) for row in rows
    )
    return {
        "key": "expected_values_present",
        "score": match,
        "comment": f"expected a row matching {expected}",
    }


_judge_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

_JUDGE_PROMPT = """You are grading whether a chatbot's natural-language answer \
correctly and completely reflects the SQL query results it was given, for the \
question asked. Do not judge whether the underlying data itself is correct -- \
only whether the answer is consistent with and represents the table data.

Question: {question}
Table data (ground truth): {table_data}
Chatbot's answer: {answer}

Respond with ONLY a JSON object: {{"correct": true|false, "reason": "..."}}
If the table data is empty because the question was correctly rejected \
(off-topic or unsafe), and the answer reflects that rejection, that counts as correct.
"""


def llm_judge(run: Run, example: Example) -> dict:
    question = example.inputs["question"]
    table_data = run.outputs.get("table_data") or []
    answer = run.outputs.get("answer") or ""
    response = _judge_llm.invoke(
        _JUDGE_PROMPT.format(question=question, table_data=table_data, answer=answer)
    )
    content = response.content if hasattr(response, "content") else str(response)
    try:
        import json

        parsed = json.loads(content)
        return {
            "key": "llm_judge",
            "score": bool(parsed.get("correct")),
            "comment": parsed.get("reason", ""),
        }
    except (json.JSONDecodeError, AttributeError):
        return {"key": "llm_judge", "score": None, "comment": f"unparseable judge output: {content}"}


def main() -> None:
    client = Client()
    ensure_dataset(client)
    results = client.evaluate(
        target,
        data=DATASET_NAME,
        evaluators=[
            min_row_count,
            tie_consistency,
            sql_execution_matches_expectation,
            expected_values_present,
            llm_judge,
        ],
        experiment_prefix="baseball-nl2sql",
        description="Regression eval for NL2SQL chat workflow",
        max_concurrency=2,
    )
    print(results)


if __name__ == "__main__":
    main()
