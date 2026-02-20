"""Evaluation framework endpoints."""

from fastapi import APIRouter, Request

router = APIRouter()


@router.post("/evaluate/accuracy")
async def evaluate_accuracy(request: Request) -> dict:
    """Run response accuracy evaluation against labeled tickets."""
    from sentinelcx.evaluation.accuracy import evaluate_response_accuracy

    settings = request.app.state.settings
    results = await evaluate_response_accuracy(settings)
    return results


@router.post("/evaluate/routing")
async def evaluate_routing(request: Request) -> dict:
    """Run routing accuracy evaluation (precision/recall per category)."""
    from sentinelcx.evaluation.routing import evaluate_routing_accuracy

    settings = request.app.state.settings
    results = await evaluate_routing_accuracy(settings)
    return results


@router.post("/evaluate/hallucination")
async def evaluate_hallucination(request: Request) -> dict:
    """Run hallucination detection on recent responses."""
    from sentinelcx.evaluation.hallucination import detect_hallucinations

    settings = request.app.state.settings
    results = await detect_hallucinations(settings)
    return results
