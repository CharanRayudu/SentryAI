#!/usr/bin/env python3
"""
SentryAI Evaluation Pipeline - "The Dojo"
==========================================

This script runs automated evaluations against golden scenarios.
Use it in CI/CD to catch regressions before deployment.

Usage:
    # Run all scenarios
    python run_evals.py

    # Run specific category
    python run_evals.py --category sqli

    # Run specific scenario
    python run_evals.py --scenario sqli-dvwa-login

    # Compare two prompt versions (regression test)
    python run_evals.py --regression v1.0 v1.1

    # Generate report
    python run_evals.py --report json --output results.json

Example CI/CD usage:
    python run_evals.py --min-score 80 --exit-on-fail
"""
import argparse
import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field, asdict
import time

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from evals.dojo.scenarios.base import GoldenScenario, ScenarioResult, ScenarioOutcome
from evals.dojo.scenarios.sqli_scenarios import SQLI_SCENARIOS
from evals.dojo.scenarios.xss_scenarios import XSS_SCENARIOS
from evals.dojo.scenarios.auth_scenarios import AUTH_SCENARIOS
from evals.dojo.scenarios.loop_scenarios import LOOP_SCENARIOS
from evals.dojo.scenarios.scope_scenarios import SCOPE_SCENARIOS
from evals.dojo.judge import get_judge, LLMJudge, JudgeVerdict


# =============================================================================
# ALL SCENARIOS REGISTRY
# =============================================================================

ALL_SCENARIOS: Dict[str, GoldenScenario] = {}

def register_scenarios():
    """Register all available scenarios"""
    global ALL_SCENARIOS
    
    for scenario in SQLI_SCENARIOS:
        ALL_SCENARIOS[scenario.id] = scenario
    
    for scenario in XSS_SCENARIOS:
        ALL_SCENARIOS[scenario.id] = scenario
    
    for scenario in AUTH_SCENARIOS:
        ALL_SCENARIOS[scenario.id] = scenario
    
    for scenario in LOOP_SCENARIOS:
        ALL_SCENARIOS[scenario.id] = scenario
    
    for scenario in SCOPE_SCENARIOS:
        ALL_SCENARIOS[scenario.id] = scenario

register_scenarios()


# =============================================================================
# AGENT RUNNER (Mock for testing, real impl connects to Temporal)
# =============================================================================

@dataclass
class AgentRunResult:
    """Result from running the agent"""
    findings: List[Dict[str, Any]]
    logs: List[str]
    steps_taken: int
    cost_usd: float
    runtime_seconds: float
    error: Optional[str] = None


class AgentRunner:
    """
    Runs the SentryAI agent against a target.
    
    In production, this connects to the Temporal workflow.
    For testing, can use mock mode.
    """
    
    def __init__(self, mock_mode: bool = False):
        self.mock_mode = mock_mode
        self._redis = None
    
    async def run(
        self,
        prompt: str,
        target_url: str,
        allowed_scope: List[str],
        excluded_scope: List[str] = None,
        max_steps: int = 15,
        timeout: int = 300,
        context_docs: List[str] = None
    ) -> AgentRunResult:
        """
        Run the agent with the given configuration.
        """
        if self.mock_mode:
            return await self._mock_run(prompt, target_url, max_steps)
        
        return await self._real_run(
            prompt, target_url, allowed_scope, 
            excluded_scope, max_steps, timeout, context_docs
        )
    
    async def _mock_run(
        self,
        prompt: str,
        target_url: str,
        max_steps: int
    ) -> AgentRunResult:
        """Mock run for testing the eval framework itself"""
        await asyncio.sleep(0.5)  # Simulate work
        
        # Generate fake results based on prompt keywords
        prompt_lower = prompt.lower()
        
        findings = []
        logs = [
            f"[{datetime.now().isoformat()}] Starting mission",
            f"[INFO] Target: {target_url}",
            f"[INFO] Analyzing objective...",
        ]
        
        if "sql" in prompt_lower:
            logs.extend([
                "[INFO] Running nuclei with sqli templates",
                "[INFO] Found potential SQL injection",
                "[VULN] SQL injection confirmed at /login"
            ])
            findings.append({
                "type": "sqli",
                "severity": "high",
                "title": "SQL Injection in login form",
                "location": "/login",
                "evidence": "Error-based SQLi: ' OR '1'='1"
            })
        
        if "unreachable" in prompt_lower or "non-existent" in prompt_lower:
            logs.extend([
                "[INFO] Attempting to connect...",
                "[WARN] Connection refused",
                "[WARN] Host unreachable",
                "[INFO] Target not responding, stopping scan"
            ])
        
        logs.append(f"[{datetime.now().isoformat()}] Mission complete")
        
        return AgentRunResult(
            findings=findings,
            logs=logs,
            steps_taken=len([l for l in logs if "Running" in l or "Attempting" in l]),
            cost_usd=0.05,
            runtime_seconds=1.5
        )
    
    async def _real_run(
        self,
        prompt: str,
        target_url: str,
        allowed_scope: List[str],
        excluded_scope: List[str],
        max_steps: int,
        timeout: int,
        context_docs: List[str]
    ) -> AgentRunResult:
        """Real run connecting to Temporal"""
        try:
            from temporalio.client import Client
            from workflows.security_scan import SecurityScanWorkflow, ScanInput
            
            # Connect to Temporal
            client = await Client.connect(os.getenv("TEMPORAL_HOST", "localhost:7233"))
            
            # Create input
            scan_input = ScanInput(
                mission_id=f"eval-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                tenant_id="eval-tenant",
                user_id="eval-system",
                objective=prompt,
                targets=[target_url],
                allowed_scope=allowed_scope,
                excluded_scope=excluded_scope or [],
                max_steps=max_steps,
                auto_pilot=True  # No human approval for evals
            )
            
            # Run workflow
            result = await client.execute_workflow(
                SecurityScanWorkflow.run,
                scan_input,
                id=scan_input.mission_id,
                task_queue="security-scans",
                execution_timeout=timeout
            )
            
            return AgentRunResult(
                findings=result.findings,
                logs=[],  # TODO: Fetch from Redis
                steps_taken=result.steps_taken,
                cost_usd=result.cost_usd,
                runtime_seconds=result.runtime_seconds
            )
            
        except ImportError:
            print("Warning: Temporal not available, using mock mode")
            return await self._mock_run(prompt, target_url, max_steps)
        except Exception as e:
            return AgentRunResult(
                findings=[],
                logs=[f"Error: {str(e)}"],
                steps_taken=0,
                cost_usd=0,
                runtime_seconds=0,
                error=str(e)
            )


# =============================================================================
# EVALUATION RUNNER
# =============================================================================

@dataclass
class EvalRun:
    """Complete evaluation run results"""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    prompt_version: str = "default"
    scenarios_run: int = 0
    scenarios_passed: int = 0
    scenarios_failed: int = 0
    avg_score: float = 0.0
    avg_accuracy: float = 0.0
    avg_efficiency: float = 0.0
    avg_safety: float = 0.0
    total_cost_usd: float = 0.0
    total_runtime_seconds: float = 0.0
    results: List[Dict] = field(default_factory=list)
    
    @property
    def pass_rate(self) -> float:
        if self.scenarios_run == 0:
            return 0.0
        return self.scenarios_passed / self.scenarios_run


class EvaluationRunner:
    """
    Orchestrates the full evaluation pipeline.
    """
    
    def __init__(
        self,
        mock_mode: bool = False,
        use_judge: bool = True
    ):
        self.agent_runner = AgentRunner(mock_mode=mock_mode)
        self.judge = get_judge() if use_judge else None
        self.results: List[ScenarioResult] = []
    
    async def run_scenario(self, scenario: GoldenScenario) -> ScenarioResult:
        """Run a single scenario and return results"""
        print(f"\n{'='*60}")
        print(f"Running: {scenario.name}")
        print(f"ID: {scenario.id}")
        print(f"Difficulty: {scenario.difficulty}")
        print(f"{'='*60}")
        
        start_time = time.time()
        
        # Run the agent
        run_result = await self.agent_runner.run(
            prompt=scenario.get_prompt(),
            target_url=scenario.target_url,
            allowed_scope=scenario.allowed_scope,
            excluded_scope=scenario.excluded_scope,
            max_steps=scenario.max_steps,
            timeout=scenario.timeout_seconds,
            context_docs=scenario.context_documents
        )
        
        runtime = time.time() - start_time
        
        # Evaluate using scenario rules
        result = scenario.evaluate(
            findings=run_result.findings,
            logs=run_result.logs,
            steps_taken=run_result.steps_taken,
            cost_usd=run_result.cost_usd,
            runtime_seconds=runtime
        )
        
        # Enhanced evaluation with LLM judge
        if self.judge and self.judge.is_available:
            verdict = await self.judge.evaluate(
                scenario_id=scenario.id,
                scenario_name=scenario.name,
                scenario_description=scenario.description,
                difficulty=scenario.difficulty,
                expected_vuln=scenario.expected_vuln_type,
                expected_location=scenario.expected_location,
                target_url=scenario.target_url,
                allowed_scope=scenario.allowed_scope,
                max_steps=scenario.max_steps,
                logs=run_result.logs,
                findings=run_result.findings
            )
            
            # Use LLM scores (they're more nuanced)
            result.accuracy_score = verdict.accuracy_score * 2  # Scale 50 -> 100
            result.efficiency_score = int(verdict.efficiency_score * 3.33)  # Scale 30 -> 100  
            result.safety_score = verdict.safety_score * 5  # Scale 20 -> 100
        
        self.results.append(result)
        
        # Print result
        status_emoji = "✅" if result.outcome == ScenarioOutcome.PASSED else "❌"
        print(f"\nResult: {status_emoji} {result.outcome.value.upper()}")
        print(f"Score: {result.total_score}/100")
        print(f"  - Accuracy:   {result.accuracy_score}")
        print(f"  - Efficiency: {result.efficiency_score}")
        print(f"  - Safety:     {result.safety_score}")
        
        if result.failure_reason:
            print(f"Reason: {result.failure_reason}")
        
        return result
    
    async def run_all(
        self,
        category: str = None,
        scenario_ids: List[str] = None
    ) -> EvalRun:
        """Run all matching scenarios"""
        scenarios = []
        
        if scenario_ids:
            scenarios = [ALL_SCENARIOS[sid] for sid in scenario_ids if sid in ALL_SCENARIOS]
        elif category:
            scenarios = [s for s in ALL_SCENARIOS.values() if s.category == category]
        else:
            scenarios = list(ALL_SCENARIOS.values())
        
        if not scenarios:
            print("No scenarios to run!")
            return EvalRun()
        
        print(f"\n{'#'*60}")
        print(f"# SentryAI Evaluation Pipeline - The Dojo")
        print(f"# Running {len(scenarios)} scenarios")
        print(f"{'#'*60}")
        
        for scenario in scenarios:
            await self.run_scenario(scenario)
        
        # Compile results
        eval_run = self._compile_results()
        
        # Print summary
        self._print_summary(eval_run)
        
        return eval_run
    
    def _compile_results(self) -> EvalRun:
        """Compile all results into an EvalRun"""
        if not self.results:
            return EvalRun()
        
        passed = sum(1 for r in self.results if r.outcome == ScenarioOutcome.PASSED)
        failed = len(self.results) - passed
        
        scores = [r.total_score for r in self.results]
        accuracy = [r.accuracy_score for r in self.results]
        efficiency = [r.efficiency_score for r in self.results]
        safety = [r.safety_score for r in self.results]
        
        return EvalRun(
            scenarios_run=len(self.results),
            scenarios_passed=passed,
            scenarios_failed=failed,
            avg_score=sum(scores) / len(scores),
            avg_accuracy=sum(accuracy) / len(accuracy),
            avg_efficiency=sum(efficiency) / len(efficiency),
            avg_safety=sum(safety) / len(safety),
            total_cost_usd=sum(r.cost_usd for r in self.results),
            total_runtime_seconds=sum(r.runtime_seconds for r in self.results),
            results=[r.to_dict() for r in self.results]
        )
    
    def _print_summary(self, eval_run: EvalRun):
        """Print evaluation summary"""
        print(f"\n{'='*60}")
        print("EVALUATION SUMMARY")
        print(f"{'='*60}")
        print(f"Scenarios Run:    {eval_run.scenarios_run}")
        print(f"Passed:           {eval_run.scenarios_passed} ({eval_run.pass_rate:.1%})")
        print(f"Failed:           {eval_run.scenarios_failed}")
        print(f"Average Score:    {eval_run.avg_score:.1f}/100")
        print(f"  - Accuracy:     {eval_run.avg_accuracy:.1f}")
        print(f"  - Efficiency:   {eval_run.avg_efficiency:.1f}")
        print(f"  - Safety:       {eval_run.avg_safety:.1f}")
        print(f"Total Cost:       ${eval_run.total_cost_usd:.4f}")
        print(f"Total Runtime:    {eval_run.total_runtime_seconds:.1f}s")
        print(f"{'='*60}")


# =============================================================================
# REGRESSION TESTING
# =============================================================================

async def run_regression_test(
    version_a: str,
    version_b: str,
    category: str = None
) -> Dict:
    """
    Compare two prompt versions for regression.
    """
    print(f"\n{'#'*60}")
    print(f"# REGRESSION TEST: {version_a} vs {version_b}")
    print(f"{'#'*60}")
    
    # Run both versions
    # In real impl, load prompt versions from storage
    runner_a = EvaluationRunner(mock_mode=True)
    runner_b = EvaluationRunner(mock_mode=True)
    
    print(f"\n--- Running Version A ({version_a}) ---")
    results_a = await runner_a.run_all(category=category)
    
    print(f"\n--- Running Version B ({version_b}) ---")
    results_b = await runner_b.run_all(category=category)
    
    # Compare
    judge = get_judge()
    verdict = await judge.compare_versions(
        version_a_summary={
            "version": version_a,
            "avg_score": results_a.avg_score,
            "accuracy": results_a.avg_accuracy,
            "efficiency": results_a.avg_efficiency,
            "safety": results_a.avg_safety,
            "pass_rate": results_a.pass_rate
        },
        version_b_summary={
            "version": version_b,
            "avg_score": results_b.avg_score,
            "accuracy": results_b.avg_accuracy,
            "efficiency": results_b.avg_efficiency,
            "safety": results_b.avg_safety,
            "pass_rate": results_b.pass_rate
        }
    )
    
    print(f"\n{'='*60}")
    print("REGRESSION VERDICT")
    print(f"{'='*60}")
    print(f"Recommendation: {verdict.recommendation.upper()}")
    print(f"Is Regression:  {'YES ❌' if verdict.is_regression else 'NO ✅'}")
    print(f"Reasoning:      {verdict.reasoning}")
    print(f"\nDeltas:")
    print(f"  Accuracy:   {verdict.accuracy_delta:+.1f}")
    print(f"  Efficiency: {verdict.efficiency_delta:+.1f}")
    print(f"  Safety:     {verdict.safety_delta:+.1f}")
    
    if verdict.critical_issues:
        print(f"\nCritical Issues:")
        for issue in verdict.critical_issues:
            print(f"  - {issue}")
    
    return {
        "version_a": version_a,
        "version_b": version_b,
        "verdict": verdict.recommendation,
        "is_regression": verdict.is_regression,
        "deltas": {
            "accuracy": verdict.accuracy_delta,
            "efficiency": verdict.efficiency_delta,
            "safety": verdict.safety_delta
        }
    }


# =============================================================================
# CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="SentryAI Evaluation Pipeline - The Dojo",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        "--scenario", "-s",
        help="Run a specific scenario by ID"
    )
    parser.add_argument(
        "--category", "-c",
        choices=["sqli", "xss", "auth", "scope", "loop", "all"],
        help="Run all scenarios in a category (sqli, xss, auth, scope, loop, or all)"
    )
    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="List all available scenarios"
    )
    parser.add_argument(
        "--regression", "-r",
        nargs=2,
        metavar=("VERSION_A", "VERSION_B"),
        help="Run regression test between two prompt versions"
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Use mock agent (for testing the eval framework)"
    )
    parser.add_argument(
        "--no-judge",
        action="store_true",
        help="Disable LLM judge (use rule-based scoring only)"
    )
    parser.add_argument(
        "--min-score",
        type=int,
        default=0,
        help="Minimum average score required to pass"
    )
    parser.add_argument(
        "--exit-on-fail",
        action="store_true",
        help="Exit with code 1 if any scenario fails"
    )
    parser.add_argument(
        "--report",
        choices=["json", "markdown"],
        help="Generate report in specified format"
    )
    parser.add_argument(
        "--output", "-o",
        help="Output file for report"
    )
    
    args = parser.parse_args()
    
    # List scenarios
    if args.list:
        print("\nAvailable Scenarios:")
        print("-" * 60)
        for scenario in ALL_SCENARIOS.values():
            print(f"  {scenario.id}")
            print(f"    Name:       {scenario.name}")
            print(f"    Category:   {scenario.category}")
            print(f"    Difficulty: {scenario.difficulty}")
            print()
        return 0
    
    # Run evaluations
    async def async_main():
        # Regression test
        if args.regression:
            result = await run_regression_test(
                args.regression[0],
                args.regression[1],
                category=args.category
            )
            
            if result["is_regression"]:
                print("\n❌ REGRESSION DETECTED - Blocking deployment")
                return 1
            return 0
        
        # Normal evaluation
        runner = EvaluationRunner(
            mock_mode=args.mock,
            use_judge=not args.no_judge
        )
        
        scenario_ids = [args.scenario] if args.scenario else None
        eval_run = await runner.run_all(
            category=args.category,
            scenario_ids=scenario_ids
        )
        
        # Generate report
        if args.report:
            report_data = asdict(eval_run)
            
            if args.report == "json":
                output = json.dumps(report_data, indent=2)
            else:  # markdown
                output = f"""# SentryAI Evaluation Report

## Summary
- **Date**: {eval_run.timestamp}
- **Scenarios Run**: {eval_run.scenarios_run}
- **Pass Rate**: {eval_run.pass_rate:.1%}
- **Average Score**: {eval_run.avg_score:.1f}/100

## Scores
| Metric | Score |
|--------|-------|
| Accuracy | {eval_run.avg_accuracy:.1f} |
| Efficiency | {eval_run.avg_efficiency:.1f} |
| Safety | {eval_run.avg_safety:.1f} |

## Results
"""
                for r in eval_run.results:
                    status = "✅" if r["outcome"] == "passed" else "❌"
                    output += f"\n### {status} {r['scenario_name']}\n"
                    output += f"- Score: {r['scores']['total']}\n"
                    if r.get("failure_reason"):
                        output += f"- Reason: {r['failure_reason']}\n"
            
            if args.output:
                with open(args.output, "w") as f:
                    f.write(output)
                print(f"\nReport saved to {args.output}")
            else:
                print(output)
        
        # Check thresholds
        if args.min_score and eval_run.avg_score < args.min_score:
            print(f"\n❌ FAILED: Average score {eval_run.avg_score:.1f} below minimum {args.min_score}")
            return 1
        
        if args.exit_on_fail and eval_run.scenarios_failed > 0:
            print(f"\n❌ FAILED: {eval_run.scenarios_failed} scenarios failed")
            return 1
        
        return 0
    
    return asyncio.run(async_main())


if __name__ == "__main__":
    sys.exit(main())

