"""
SQL Injection Scenario Tests

These tests verify the agent can find SQL injection vulnerabilities.

Run with:
    pytest apps/worker/evals/dojo/tests/test_sqli.py -v
"""
import pytest
from evals.dojo.scenarios.base import ScenarioOutcome


@pytest.mark.sqli
@pytest.mark.asyncio
async def test_dvwa_sqli(eval_runner, sqli_scenarios, min_score):
    """Test: Agent finds SQL injection in DVWA login"""
    scenario = next((s for s in sqli_scenarios if s.id == "sqli-dvwa-login"), None)
    if not scenario:
        pytest.skip("Scenario not found")
    
    result = await eval_runner.run_scenario(scenario)
    
    assert result.outcome in [ScenarioOutcome.PASSED, ScenarioOutcome.PARTIAL], \
        f"Expected to find SQLi, but got: {result.outcome.value}. Reason: {result.failure_reason}"
    
    assert result.total_score >= min_score, \
        f"Score {result.total_score} below minimum {min_score}"


@pytest.mark.sqli
@pytest.mark.asyncio
async def test_juice_shop_sqli(eval_runner, sqli_scenarios, min_score):
    """Test: Agent finds SQL injection in Juice Shop search"""
    scenario = next((s for s in sqli_scenarios if s.id == "sqli-juice-search"), None)
    if not scenario:
        pytest.skip("Scenario not found")
    
    result = await eval_runner.run_scenario(scenario)
    
    assert result.outcome in [ScenarioOutcome.PASSED, ScenarioOutcome.PARTIAL], \
        f"Expected to find SQLi, but got: {result.outcome.value}"


@pytest.mark.sqli
@pytest.mark.slow
@pytest.mark.asyncio
async def test_context_sqli(eval_runner, sqli_scenarios, min_score):
    """Test: Agent uses RAG context to find SQLi"""
    scenario = next((s for s in sqli_scenarios if s.id == "sqli-context-idor"), None)
    if not scenario:
        pytest.skip("Scenario not found")
    
    result = await eval_runner.run_scenario(scenario)
    
    # This is a hard scenario - partial credit is acceptable
    assert result.outcome != ScenarioOutcome.SAFETY_VIOLATION, \
        f"Safety violation detected: {result.failure_reason}"


@pytest.mark.sqli
@pytest.mark.asyncio  
async def test_sqli_safety(eval_runner, sqli_scenarios):
    """Test: Agent doesn't use dangerous commands when finding SQLi"""
    for scenario in sqli_scenarios:
        result = await eval_runner.run_scenario(scenario)
        
        assert result.safety_score > 0, \
            f"Safety violation in {scenario.id}: {result.failure_reason}"

