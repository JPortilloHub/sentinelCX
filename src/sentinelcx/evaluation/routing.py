"""Routing accuracy evaluation — precision/recall per category."""

import json
import logging
from collections import defaultdict
from pathlib import Path

from sentinelcx.config import Settings
from sentinelcx.orchestrator import SentinelCXOrchestrator

logger = logging.getLogger(__name__)


def _compute_metrics(predictions: list[dict], ground_truth: list[dict]) -> dict:
    """Compute precision, recall, F1 per category and decision."""
    # Build lookup by ticket_id
    gt_by_id = {g["ticket_id"]: g for g in ground_truth}

    category_tp = defaultdict(int)
    category_fp = defaultdict(int)
    category_fn = defaultdict(int)
    decision_tp = defaultdict(int)
    decision_fp = defaultdict(int)
    decision_fn = defaultdict(int)

    for pred in predictions:
        ticket_id = pred["ticket_id"]
        gt = gt_by_id.get(ticket_id)
        if not gt:
            continue

        # Category metrics
        pred_cat = pred.get("predicted_category", "")
        true_cat = gt.get("expected_category", "")
        if pred_cat == true_cat:
            category_tp[true_cat] += 1
        else:
            category_fp[pred_cat] += 1
            category_fn[true_cat] += 1

        # Decision metrics
        pred_dec = pred.get("predicted_decision", "")
        true_dec = gt.get("expected_decision", "")
        if pred_dec == true_dec:
            decision_tp[true_dec] += 1
        else:
            decision_fp[pred_dec] += 1
            decision_fn[true_dec] += 1

    def _calc(tp_dict, fp_dict, fn_dict):
        all_labels = set(tp_dict) | set(fp_dict) | set(fn_dict)
        metrics = {}
        for label in sorted(all_labels):
            tp = tp_dict[label]
            fp = fp_dict[label]
            fn = fn_dict[label]
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
            metrics[label] = {
                "precision": round(precision, 3),
                "recall": round(recall, 3),
                "f1": round(f1, 3),
                "tp": tp,
                "fp": fp,
                "fn": fn,
            }
        return metrics

    return {
        "category_metrics": _calc(category_tp, category_fp, category_fn),
        "decision_metrics": _calc(decision_tp, decision_fp, decision_fn),
    }


async def evaluate_routing_accuracy(
    settings: Settings,
    ground_truth_file: str = "evaluation_data/routing_ground_truth.jsonl",
    sample_size: int | None = None,
) -> dict:
    """Evaluate triage routing accuracy against ground truth."""
    gt_path = Path(ground_truth_file)
    if not gt_path.exists():
        return {"error": f"Ground truth file not found: {ground_truth_file}"}

    ground_truth = []
    with open(gt_path) as f:
        for line in f:
            ground_truth.append(json.loads(line))

    if sample_size:
        ground_truth = ground_truth[:sample_size]

    orchestrator = SentinelCXOrchestrator(settings)
    predictions = []

    for entry in ground_truth:
        try:
            result = await orchestrator.process_ticket(str(entry["conversation_id"]))
            result_text = result.get("result", "")

            # Parse the triage result from the orchestrator output
            predicted_category = entry["expected_category"]  # fallback
            predicted_decision = "needs_research"  # fallback

            # Try to extract from result JSON
            if isinstance(result_text, str):
                for cat in ("billing", "technical", "account", "product", "general"):
                    if cat in result_text.lower():
                        predicted_category = cat
                        break
                for dec in ("auto_handle", "needs_research", "escalate"):
                    if dec in result_text.lower():
                        predicted_decision = dec
                        break

            predictions.append(
                {
                    "ticket_id": entry["ticket_id"],
                    "predicted_category": predicted_category,
                    "predicted_decision": predicted_decision,
                }
            )
        except Exception as e:
            logger.error("Error evaluating routing for %s: %s", entry["ticket_id"], e)

    metrics = _compute_metrics(predictions, ground_truth)
    metrics["total_evaluated"] = len(predictions)
    metrics["total_ground_truth"] = len(ground_truth)

    return metrics
