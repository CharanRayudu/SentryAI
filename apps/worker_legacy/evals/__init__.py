"""
SentryAI Agent Evaluation Pipeline

Quality assurance for LLM-based security agents.

This package provides:
- Golden scenarios (deliberately vulnerable environments)
- Metric collection and analysis
- Regression detection across prompt versions
- Determinism analysis
"""
from .evaluation_pipeline import (
    EvalOutcome,
    GoldenScenario,
    EvalResult,
    EvalMetrics,
    EvaluationPipeline,
    GOLDEN_SCENARIOS,
)

__all__ = [
    "EvalOutcome",
    "GoldenScenario",
    "EvalResult",
    "EvalMetrics",
    "EvaluationPipeline",
    "GOLDEN_SCENARIOS",
]

