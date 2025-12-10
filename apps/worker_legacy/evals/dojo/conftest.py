"""
Pytest fixtures for The Dojo evaluation tests.

Usage:
    pytest apps/worker/evals/dojo/tests/ -v
"""
import pytest
import asyncio
import os
from typing import Generator


# =============================================================================
# ASYNC FIXTURES
# =============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# =============================================================================
# ENVIRONMENT FIXTURES
# =============================================================================

@pytest.fixture(scope="session")
def mock_mode() -> bool:
    """Determine if tests should run in mock mode"""
    return os.getenv("DOJO_MOCK_MODE", "true").lower() == "true"


@pytest.fixture(scope="session")
def use_judge() -> bool:
    """Determine if LLM judge should be used"""
    has_key = bool(os.getenv("OPENAI_API_KEY") or os.getenv("JUDGE_OPENAI_KEY"))
    return has_key and os.getenv("DOJO_USE_JUDGE", "true").lower() == "true"


@pytest.fixture(scope="session")
def min_score() -> int:
    """Minimum score required to pass"""
    return int(os.getenv("DOJO_MIN_SCORE", "70"))


# =============================================================================
# AGENT FIXTURES
# =============================================================================

@pytest.fixture
def agent_runner(mock_mode):
    """Get an agent runner instance"""
    from evals.dojo.run_evals import AgentRunner
    return AgentRunner(mock_mode=mock_mode)


@pytest.fixture
def eval_runner(mock_mode, use_judge):
    """Get an evaluation runner instance"""
    from evals.dojo.run_evals import EvaluationRunner
    return EvaluationRunner(mock_mode=mock_mode, use_judge=use_judge)


# =============================================================================
# SCENARIO FIXTURES
# =============================================================================

@pytest.fixture
def sqli_scenarios():
    """Get SQL injection scenarios"""
    from evals.dojo.scenarios.sqli_scenarios import SQLI_SCENARIOS
    return SQLI_SCENARIOS


@pytest.fixture
def xss_scenarios():
    """Get XSS scenarios"""
    from evals.dojo.scenarios.xss_scenarios import XSS_SCENARIOS
    return XSS_SCENARIOS


@pytest.fixture
def auth_scenarios():
    """Get authentication scenarios"""
    from evals.dojo.scenarios.auth_scenarios import AUTH_SCENARIOS
    return AUTH_SCENARIOS


@pytest.fixture
def scope_scenarios():
    """Get scope adherence scenarios"""
    from evals.dojo.scenarios.scope_scenarios import SCOPE_SCENARIOS
    return SCOPE_SCENARIOS


@pytest.fixture
def loop_scenarios():
    """Get loop prevention scenarios"""
    from evals.dojo.scenarios.loop_scenarios import LOOP_SCENARIOS
    return LOOP_SCENARIOS


@pytest.fixture
def all_scenarios(sqli_scenarios, xss_scenarios, auth_scenarios, scope_scenarios, loop_scenarios):
    """Get all scenarios"""
    return sqli_scenarios + xss_scenarios + auth_scenarios + scope_scenarios + loop_scenarios


# =============================================================================
# JUDGE FIXTURES
# =============================================================================

@pytest.fixture
def judge(use_judge):
    """Get LLM judge instance"""
    if not use_judge:
        return None
    from evals.dojo.judge import get_judge
    return get_judge()


# =============================================================================
# MARKERS
# =============================================================================

def pytest_configure(config):
    """Register custom markers"""
    config.addinivalue_line("markers", "sqli: SQL injection scenarios")
    config.addinivalue_line("markers", "xss: Cross-site scripting scenarios")
    config.addinivalue_line("markers", "auth: Authentication scenarios")
    config.addinivalue_line("markers", "scope: Scope adherence scenarios")
    config.addinivalue_line("markers", "loop: Loop prevention scenarios")
    config.addinivalue_line("markers", "slow: Tests that take longer to run")
    config.addinivalue_line("markers", "requires_llm: Tests that require LLM judge")

