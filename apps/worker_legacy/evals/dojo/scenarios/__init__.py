"""
Golden Scenarios for The Dojo

Each scenario defines:
1. A specific vulnerability to find
2. Success criteria
3. Failure conditions
4. Expected behavior
"""
from .base import (
    GoldenScenario, 
    ScenarioResult, 
    ScenarioOutcome,
    ContextScenario,
    ScopeTestScenario,
    LoopTestScenario
)
from .sqli_scenarios import SQLI_SCENARIOS
from .xss_scenarios import XSS_SCENARIOS
from .auth_scenarios import AUTH_SCENARIOS
from .scope_scenarios import SCOPE_SCENARIOS
from .loop_scenarios import LOOP_SCENARIOS

# Collect all scenarios
ALL_SCENARIOS = (
    SQLI_SCENARIOS + 
    XSS_SCENARIOS + 
    AUTH_SCENARIOS + 
    SCOPE_SCENARIOS + 
    LOOP_SCENARIOS
)

__all__ = [
    "GoldenScenario",
    "ScenarioResult",
    "ScenarioOutcome",
    "ContextScenario",
    "ScopeTestScenario",
    "LoopTestScenario",
    "SQLI_SCENARIOS",
    "XSS_SCENARIOS",
    "AUTH_SCENARIOS",
    "SCOPE_SCENARIOS",
    "LOOP_SCENARIOS",
    "ALL_SCENARIOS",
]

