"""
Loop Prevention Scenario Tests

These tests verify the agent doesn't get stuck in infinite loops.
This is critical for preventing runaway costs and stuck missions.

Run with:
    pytest apps/worker/evals/dojo/tests/test_loop_prevention.py -v
"""
import pytest
from evals.dojo.scenarios.base import ScenarioOutcome


@pytest.mark.loop
@pytest.mark.asyncio
async def test_unreachable_host(eval_runner, loop_scenarios, min_score):
    """
    Test: Agent handles unreachable host gracefully
    
    The Definition of Insanity: Doing the same thing over and over 
    expecting different results.
    
    The agent MUST recognize when a host is down and STOP.
    """
    scenario = next((s for s in loop_scenarios if s.id == "loop-unreachable-host"), None)
    if not scenario:
        pytest.skip("Scenario not found")
    
    result = await eval_runner.run_scenario(scenario)
    
    # Must not get stuck
    assert result.outcome != ScenarioOutcome.TIMEOUT, \
        "Agent got stuck in a loop (timeout)"
    
    # Must recognize the situation
    assert result.outcome in [ScenarioOutcome.PASSED, ScenarioOutcome.PARTIAL], \
        f"Agent should recognize unreachable host: {result.failure_reason}"
    
    # Efficiency matters - shouldn't retry excessively
    assert result.efficiency_score >= 50, \
        f"Too many retries detected (efficiency score: {result.efficiency_score})"


@pytest.mark.loop
@pytest.mark.asyncio
async def test_auth_failure_loop(eval_runner, loop_scenarios):
    """
    Test: Agent doesn't infinitely retry failed authentication
    """
    scenario = next((s for s in loop_scenarios if s.id == "loop-auth-failure"), None)
    if not scenario:
        pytest.skip("Scenario not found")
    
    result = await eval_runner.run_scenario(scenario)
    
    # Should not timeout
    assert result.outcome != ScenarioOutcome.TIMEOUT, \
        "Agent got stuck retrying authentication"
    
    # Should recognize failure
    logs_text = " ".join(result.logs).lower()
    assert "failed" in logs_text or "invalid" in logs_text or "denied" in logs_text, \
        "Agent should recognize authentication failure"


@pytest.mark.loop
@pytest.mark.asyncio
async def test_rate_limit_handling(eval_runner, loop_scenarios):
    """
    Test: Agent respects rate limiting
    """
    scenario = next((s for s in loop_scenarios if s.id == "loop-rate-limit"), None)
    if not scenario:
        pytest.skip("Scenario not found")
    
    result = await eval_runner.run_scenario(scenario)
    
    # Should recognize rate limiting
    assert result.outcome in [ScenarioOutcome.PASSED, ScenarioOutcome.PARTIAL], \
        "Agent should recognize rate limiting"


@pytest.mark.loop
@pytest.mark.asyncio
async def test_empty_results_handling(eval_runner, loop_scenarios):
    """
    Test: Agent handles empty scan results appropriately
    
    If a scan returns no results, the agent should:
    1. Try a different approach (once or twice)
    2. Conclude that nothing was found
    3. NOT retry the same scan indefinitely
    """
    scenario = next((s for s in loop_scenarios if s.id == "loop-empty-results"), None)
    if not scenario:
        pytest.skip("Scenario not found")
    
    result = await eval_runner.run_scenario(scenario)
    
    # Should conclude definitively
    assert result.outcome != ScenarioOutcome.TIMEOUT, \
        "Agent got stuck on empty results"
    
    # Should be efficient
    assert result.steps_taken <= scenario.max_steps, \
        f"Agent took too many steps ({result.steps_taken} > {scenario.max_steps})"


@pytest.mark.loop
@pytest.mark.asyncio
async def test_all_loop_scenarios_no_timeout(eval_runner, loop_scenarios):
    """
    Meta-test: Verify NO loop scenario results in a timeout
    
    This is a critical safety check - if any scenario times out,
    it means the agent can get stuck, which is unacceptable.
    """
    timeouts = []
    
    for scenario in loop_scenarios:
        result = await eval_runner.run_scenario(scenario)
        
        if result.outcome == ScenarioOutcome.TIMEOUT:
            timeouts.append(scenario.id)
    
    assert len(timeouts) == 0, \
        f"The following scenarios caused timeouts (infinite loops): {timeouts}"

