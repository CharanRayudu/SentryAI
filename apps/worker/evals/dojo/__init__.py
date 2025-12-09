"""
The Dojo - SentryAI Agent Evaluation Pipeline
=============================================

An automated continuous evaluation environment for testing
the SentryAI autonomous security agent.

Components:
- Arena: Docker Compose stack with deliberately vulnerable applications
- Scenarios: Golden test cases with known vulnerabilities
- Judge: LLM-as-a-Judge scoring system
- Runner: Automated test execution and regression detection

Usage:
    # Run all evaluations
    python -m evals.dojo.run_evals
    
    # Run specific category
    python -m evals.dojo.run_evals --category sqli
    
    # Run regression test
    python -m evals.dojo.run_evals --regression v1.0 v1.1
    
    # Use pytest
    pytest apps/worker/evals/dojo/tests/ -v
"""
from .scenarios import (
    GoldenScenario,
    ScenarioResult,
    ScenarioOutcome,
    ALL_SCENARIOS,
)
from .judge import (
    LLMJudge,
    JudgeVerdict,
    RegressionVerdict,
    get_judge,
)
from .run_evals import (
    EvaluationRunner,
    AgentRunner,
    EvalRun,
    run_regression_test,
)

__all__ = [
    # Scenarios
    "GoldenScenario",
    "ScenarioResult",
    "ScenarioOutcome",
    "ALL_SCENARIOS",
    # Judge
    "LLMJudge",
    "JudgeVerdict",
    "RegressionVerdict",
    "get_judge",
    # Runner
    "EvaluationRunner",
    "AgentRunner",
    "EvalRun",
    "run_regression_test",
]

