"""Offline regression gate over versioned retrieval and generation fixtures.

Predictions are supplied by a separate run of node 06/07. This script never
calls a provider and never changes a production prompt or safety rule.
"""

import argparse
import json
from pathlib import Path


def evaluate(golden: list[dict], predictions: list[dict]) -> dict:
    by_question = {item["question"]: item for item in predictions}
    if len(by_question) != len(predictions):
        raise ValueError("duplicate prediction question")
    if not golden:
        raise ValueError("golden set is empty")

    hits = reciprocal_ranks = 0.0
    faithfulness = relevance = 0.0
    judged = 0
    failures = []
    for item in golden:
        question = item["question"]
        prediction = by_question.get(question)
        if prediction is None:
            failures.append({"question": question, "reason": "missing prediction"})
            continue
        expected = set(item["expected_chunk_ids"])
        ids = prediction.get("retrieved_chunk_ids", [])
        if not isinstance(ids, list) or any(not isinstance(chunk_id, str) for chunk_id in ids):
            raise ValueError("retrieved_chunk_ids must be a string array")
        rank = next((position for position, chunk_id in enumerate(ids, 1) if chunk_id in expected), None)
        if rank is None:
            failures.append({"question": question, "reason": "expected evidence missing"})
        else:
            hits += 1
            reciprocal_ranks += 1 / rank

        scores = prediction.get("judge_scores")
        if scores is not None:
            if not isinstance(scores, dict) or set(scores) != {"faithfulness", "relevance"}:
                raise ValueError("judge_scores must contain faithfulness and relevance")
            values = (scores["faithfulness"], scores["relevance"])
            if any(type(value) not in (int, float) or not 1 <= value <= 10 for value in values):
                raise ValueError("judge scores must be numbers from 1 to 10")
            faithfulness += values[0]
            relevance += values[1]
            judged += 1

    count = len(golden)
    return {
        "case_count": count,
        "hit_rate": hits / count,
        "mrr": reciprocal_ranks / count,
        "judged_count": judged,
        "mean_faithfulness": faithfulness / judged if judged else None,
        "mean_relevance": relevance / judged if judged else None,
        "failures": failures,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("predictions", type=Path)
    parser.add_argument("--golden", type=Path, default=Path(__file__).resolve().parents[1] / "02_api_backend/data/golden_set.json")
    parser.add_argument("--min-hit-rate", type=float, default=1.0)
    parser.add_argument("--min-mrr", type=float, default=0.5)
    parser.add_argument("--min-faithfulness", type=float, default=8.0)
    parser.add_argument("--min-relevance", type=float, default=8.0)
    args = parser.parse_args()
    golden = json.loads(args.golden.read_text(encoding="utf-8"))
    predictions = json.loads(args.predictions.read_text(encoding="utf-8"))
    report = evaluate(golden, predictions)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    passed = (
        report["hit_rate"] >= args.min_hit_rate
        and report["mrr"] >= args.min_mrr
        and report["judged_count"] == report["case_count"]
        and report["mean_faithfulness"] >= args.min_faithfulness
        and report["mean_relevance"] >= args.min_relevance
    )
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
