"""
Agent Evaluation Pipeline
Quality Assurance for LLM-based Security Agents

Traditional unit tests don't work on LLMs - the agent might succeed today
and fail tomorrow because it chose a different reasoning path.

This module provides:
1. Golden Scenarios - Deliberately vulnerable environments to test against
2. Metric Collection - Quantitative measures of agent performance
3. Regression Detection - Comparing agent behavior across prompt versions
4. Determinism Analysis - Measuring output consistency
"""
import json
import asyncio
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import hashlib
import statistics
from pathlib import Path


class EvalOutcome(Enum):
    """Possible outcomes of an evaluation"""
    PASSED = "passed"           # Agent found the expected vulnerability
    FAILED = "failed"           # Agent missed the vulnerability
    PARTIAL = "partial"         # Agent found related issues but not exact target
    FALSE_POSITIVE = "false_positive"  # Agent reported non-existent vuln
    TIMEOUT = "timeout"         # Agent exceeded time budget
    ERROR = "error"             # Agent crashed or threw exception
    LOOP = "loop"               # Agent got stuck in a loop


@dataclass
class GoldenScenario:
    """
    A test scenario with known vulnerabilities.
    The agent is expected to find specific issues.
    """
    id: str
    name: str
    description: str
    
    # Target configuration
    target_url: str                    # Base URL to scan
    target_type: str                   # Type: "juice-shop", "dvwa", "custom", etc.
    docker_image: Optional[str] = None # Docker image to spin up for testing
    
    # Expected findings
    expected_vulns: List[Dict[str, Any]] = field(default_factory=list)
    # Example: [{"type": "sqli", "location": "/rest/products/search", "severity": "high"}]
    
    # Agent configuration
    max_steps: int = 30
    max_cost_usd: float = 1.0
    timeout_seconds: int = 600         # 10 minutes
    
    # Success criteria
    min_vulns_found: int = 1           # At least this many expected vulns
    min_coverage: float = 0.5          # At least 50% of expected vulns
    max_false_positives: int = 3       # No more than 3 false positives
    
    # Tags for filtering
    tags: List[str] = field(default_factory=list)  # e.g., ["xss", "auth", "quick"]


@dataclass
class EvalResult:
    """Result of running a single evaluation"""
    scenario_id: str
    run_id: str
    timestamp: datetime
    
    # Outcome
    outcome: EvalOutcome
    
    # Findings
    vulns_found: List[Dict[str, Any]]
    expected_vulns_matched: List[str]  # IDs of matched expected vulns
    false_positives: List[Dict[str, Any]]
    
    # Metrics
    steps_taken: int
    cost_usd: float
    runtime_seconds: float
    
    # Agent trace (for debugging)
    thought_trace: List[Dict[str, Any]] = field(default_factory=list)
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)
    
    # Metadata
    agent_version: str = ""
    prompt_hash: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "run_id": self.run_id,
            "timestamp": self.timestamp.isoformat(),
            "outcome": self.outcome.value,
            "vulns_found": self.vulns_found,
            "expected_matched": self.expected_vulns_matched,
            "false_positives": self.false_positives,
            "steps_taken": self.steps_taken,
            "cost_usd": self.cost_usd,
            "runtime_seconds": self.runtime_seconds,
            "agent_version": self.agent_version,
            "prompt_hash": self.prompt_hash
        }


@dataclass
class EvalMetrics:
    """Aggregate metrics from multiple evaluation runs"""
    total_runs: int = 0
    passed: int = 0
    failed: int = 0
    partial: int = 0
    false_positives_total: int = 0
    timeouts: int = 0
    errors: int = 0
    loops: int = 0
    
    # Performance metrics
    avg_steps: float = 0.0
    avg_cost_usd: float = 0.0
    avg_runtime_seconds: float = 0.0
    
    # Coverage metrics
    avg_vuln_coverage: float = 0.0  # % of expected vulns found
    
    # Consistency metrics (for determinism analysis)
    outcome_variance: float = 0.0   # How much outcomes vary across runs
    
    @property
    def pass_rate(self) -> float:
        return self.passed / max(1, self.total_runs)
    
    @property
    def partial_rate(self) -> float:
        return self.partial / max(1, self.total_runs)
    
    @property
    def fail_rate(self) -> float:
        return (self.failed + self.timeouts + self.errors) / max(1, self.total_runs)


# ============================================================================
# GOLDEN SCENARIOS LIBRARY
# ============================================================================

GOLDEN_SCENARIOS = [
    GoldenScenario(
        id="owasp-juice-shop-sqli",
        name="OWASP Juice Shop - SQL Injection",
        description="Test SQL injection detection in the product search endpoint",
        target_url="http://localhost:3000",
        target_type="juice-shop",
        docker_image="bkimminich/juice-shop:latest",
        expected_vulns=[
            {
                "id": "sqli-search",
                "type": "sqli",
                "location": "/rest/products/search",
                "severity": "high",
                "description": "SQL injection in search query parameter"
            }
        ],
        max_steps=20,
        tags=["sqli", "quick", "owasp"]
    ),
    GoldenScenario(
        id="owasp-juice-shop-xss",
        name="OWASP Juice Shop - XSS",
        description="Test reflected and stored XSS detection",
        target_url="http://localhost:3000",
        target_type="juice-shop",
        docker_image="bkimminich/juice-shop:latest",
        expected_vulns=[
            {
                "id": "xss-track-order",
                "type": "xss",
                "location": "/track-result",
                "severity": "medium",
                "description": "Reflected XSS in order tracking"
            },
            {
                "id": "xss-dom",
                "type": "xss",
                "location": "/search",
                "severity": "medium",
                "description": "DOM-based XSS in search"
            }
        ],
        max_steps=25,
        tags=["xss", "owasp"]
    ),
    GoldenScenario(
        id="owasp-juice-shop-auth",
        name="OWASP Juice Shop - Authentication Bypass",
        description="Test broken authentication detection",
        target_url="http://localhost:3000",
        target_type="juice-shop",
        docker_image="bkimminich/juice-shop:latest",
        expected_vulns=[
            {
                "id": "auth-bypass-admin",
                "type": "authentication",
                "location": "/rest/user/login",
                "severity": "critical",
                "description": "Admin login bypass via SQL injection"
            },
            {
                "id": "password-reset-weak",
                "type": "authentication",
                "location": "/rest/user/reset-password",
                "severity": "high",
                "description": "Weak password reset token"
            }
        ],
        max_steps=30,
        tags=["auth", "owasp"]
    ),
    GoldenScenario(
        id="dvwa-command-injection",
        name="DVWA - Command Injection",
        description="Test OS command injection in ping function",
        target_url="http://localhost:8080",
        target_type="dvwa",
        docker_image="vulnerables/web-dvwa",
        expected_vulns=[
            {
                "id": "cmd-injection-ping",
                "type": "command_injection",
                "location": "/vulnerabilities/exec/",
                "severity": "critical",
                "description": "OS command injection in IP ping field"
            }
        ],
        max_steps=15,
        tags=["command-injection", "critical", "quick"]
    ),
    GoldenScenario(
        id="custom-api-idor",
        name="Custom API - IDOR",
        description="Test Insecure Direct Object Reference in REST API",
        target_url="http://localhost:5000",
        target_type="custom",
        expected_vulns=[
            {
                "id": "idor-user-profile",
                "type": "idor",
                "location": "/api/users/{id}/profile",
                "severity": "high",
                "description": "Can access other users' profiles by changing ID"
            },
            {
                "id": "idor-orders",
                "type": "idor",
                "location": "/api/orders/{id}",
                "severity": "high",
                "description": "Can access other users' orders by changing ID"
            }
        ],
        max_steps=20,
        tags=["idor", "api", "authorization"]
    ),
]


class EvaluationPipeline:
    """
    Runs evaluation scenarios and collects metrics.
    """
    
    def __init__(
        self,
        agent_executor: Callable,  # The actual agent function
        results_dir: str = "./eval_results"
    ):
        self.agent_executor = agent_executor
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(exist_ok=True)
        
        self._scenarios: Dict[str, GoldenScenario] = {
            s.id: s for s in GOLDEN_SCENARIOS
        }
    
    def add_scenario(self, scenario: GoldenScenario):
        """Add a custom scenario"""
        self._scenarios[scenario.id] = scenario
    
    def list_scenarios(self, tags: List[str] = None) -> List[GoldenScenario]:
        """List available scenarios, optionally filtered by tags"""
        scenarios = list(self._scenarios.values())
        
        if tags:
            scenarios = [
                s for s in scenarios
                if any(t in s.tags for t in tags)
            ]
        
        return scenarios
    
    async def run_scenario(
        self,
        scenario_id: str,
        prompt_version: str = "default",
        num_runs: int = 1
    ) -> List[EvalResult]:
        """
        Run a scenario multiple times and collect results.
        Multiple runs help measure determinism.
        """
        scenario = self._scenarios.get(scenario_id)
        if not scenario:
            raise ValueError(f"Unknown scenario: {scenario_id}")
        
        results = []
        
        for i in range(num_runs):
            run_id = f"{scenario_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{i}"
            
            try:
                result = await self._execute_single_run(scenario, run_id, prompt_version)
            except Exception as e:
                result = EvalResult(
                    scenario_id=scenario_id,
                    run_id=run_id,
                    timestamp=datetime.utcnow(),
                    outcome=EvalOutcome.ERROR,
                    vulns_found=[],
                    expected_vulns_matched=[],
                    false_positives=[],
                    steps_taken=0,
                    cost_usd=0,
                    runtime_seconds=0,
                    agent_version=prompt_version
                )
            
            results.append(result)
            self._save_result(result)
        
        return results
    
    async def _execute_single_run(
        self,
        scenario: GoldenScenario,
        run_id: str,
        prompt_version: str
    ) -> EvalResult:
        """Execute a single evaluation run"""
        start_time = datetime.utcnow()
        
        # TODO: Spin up Docker container if needed
        # if scenario.docker_image:
        #     container = await self._start_container(scenario.docker_image)
        
        try:
            # Execute agent against target
            agent_result = await asyncio.wait_for(
                self.agent_executor(
                    target=scenario.target_url,
                    max_steps=scenario.max_steps,
                    max_cost=scenario.max_cost_usd
                ),
                timeout=scenario.timeout_seconds
            )
        except asyncio.TimeoutError:
            return EvalResult(
                scenario_id=scenario.id,
                run_id=run_id,
                timestamp=start_time,
                outcome=EvalOutcome.TIMEOUT,
                vulns_found=[],
                expected_vulns_matched=[],
                false_positives=[],
                steps_taken=scenario.max_steps,
                cost_usd=0,
                runtime_seconds=scenario.timeout_seconds,
                agent_version=prompt_version
            )
        
        runtime = (datetime.utcnow() - start_time).total_seconds()
        
        # Analyze results
        vulns_found = agent_result.get("findings", [])
        matched, false_positives = self._match_findings(vulns_found, scenario.expected_vulns)
        
        # Determine outcome
        outcome = self._determine_outcome(
            matched=matched,
            false_positives=false_positives,
            expected=scenario.expected_vulns,
            scenario=scenario
        )
        
        return EvalResult(
            scenario_id=scenario.id,
            run_id=run_id,
            timestamp=start_time,
            outcome=outcome,
            vulns_found=vulns_found,
            expected_vulns_matched=matched,
            false_positives=false_positives,
            steps_taken=agent_result.get("steps", 0),
            cost_usd=agent_result.get("cost", 0),
            runtime_seconds=runtime,
            thought_trace=agent_result.get("thoughts", []),
            tool_calls=agent_result.get("tool_calls", []),
            agent_version=prompt_version,
            prompt_hash=self._hash_prompt(prompt_version)
        )
    
    def _match_findings(
        self,
        found: List[Dict],
        expected: List[Dict]
    ) -> tuple[List[str], List[Dict]]:
        """
        Match found vulnerabilities against expected ones.
        
        Returns:
            Tuple of (matched_expected_ids, false_positives)
        """
        matched = []
        false_positives = []
        
        for finding in found:
            is_match = False
            
            for exp in expected:
                # Check if finding matches expected
                if self._findings_match(finding, exp):
                    if exp["id"] not in matched:
                        matched.append(exp["id"])
                    is_match = True
                    break
            
            if not is_match:
                false_positives.append(finding)
        
        return matched, false_positives
    
    def _findings_match(self, found: Dict, expected: Dict) -> bool:
        """Check if a found vulnerability matches an expected one"""
        # Type must match
        found_type = found.get("type", "").lower()
        expected_type = expected.get("type", "").lower()
        
        type_aliases = {
            "sql injection": "sqli",
            "xss": "xss",
            "cross-site scripting": "xss",
            "command injection": "command_injection",
            "os command injection": "command_injection",
            "idor": "idor",
            "insecure direct object reference": "idor"
        }
        
        found_type = type_aliases.get(found_type, found_type)
        expected_type = type_aliases.get(expected_type, expected_type)
        
        if found_type != expected_type:
            return False
        
        # Location should be similar
        found_loc = found.get("location", "").lower()
        expected_loc = expected.get("location", "").lower()
        
        # Partial match is sufficient
        if expected_loc in found_loc or found_loc in expected_loc:
            return True
        
        return False
    
    def _determine_outcome(
        self,
        matched: List[str],
        false_positives: List[Dict],
        expected: List[Dict],
        scenario: GoldenScenario
    ) -> EvalOutcome:
        """Determine the evaluation outcome"""
        if len(false_positives) > scenario.max_false_positives:
            return EvalOutcome.FALSE_POSITIVE
        
        if not expected:
            # No expected vulns, just check false positives
            return EvalOutcome.PASSED if not false_positives else EvalOutcome.FALSE_POSITIVE
        
        coverage = len(matched) / len(expected)
        
        if coverage >= scenario.min_coverage and len(matched) >= scenario.min_vulns_found:
            return EvalOutcome.PASSED
        elif len(matched) > 0:
            return EvalOutcome.PARTIAL
        else:
            return EvalOutcome.FAILED
    
    def _hash_prompt(self, version: str) -> str:
        """Create a hash of the prompt version for tracking"""
        return hashlib.md5(version.encode()).hexdigest()[:8]
    
    def _save_result(self, result: EvalResult):
        """Save result to disk"""
        filename = f"{result.run_id}.json"
        filepath = self.results_dir / filename
        
        with open(filepath, 'w') as f:
            json.dump(result.to_dict(), f, indent=2)
    
    def compute_metrics(self, results: List[EvalResult]) -> EvalMetrics:
        """Compute aggregate metrics from evaluation results"""
        metrics = EvalMetrics(total_runs=len(results))
        
        steps_list = []
        costs_list = []
        runtimes_list = []
        coverages_list = []
        
        for r in results:
            # Count outcomes
            if r.outcome == EvalOutcome.PASSED:
                metrics.passed += 1
            elif r.outcome == EvalOutcome.FAILED:
                metrics.failed += 1
            elif r.outcome == EvalOutcome.PARTIAL:
                metrics.partial += 1
            elif r.outcome == EvalOutcome.FALSE_POSITIVE:
                metrics.false_positives_total += len(r.false_positives)
            elif r.outcome == EvalOutcome.TIMEOUT:
                metrics.timeouts += 1
            elif r.outcome == EvalOutcome.ERROR:
                metrics.errors += 1
            elif r.outcome == EvalOutcome.LOOP:
                metrics.loops += 1
            
            steps_list.append(r.steps_taken)
            costs_list.append(r.cost_usd)
            runtimes_list.append(r.runtime_seconds)
            
            # Calculate coverage for this result
            scenario = self._scenarios.get(r.scenario_id)
            if scenario and scenario.expected_vulns:
                coverage = len(r.expected_vulns_matched) / len(scenario.expected_vulns)
                coverages_list.append(coverage)
        
        # Compute averages
        if steps_list:
            metrics.avg_steps = statistics.mean(steps_list)
        if costs_list:
            metrics.avg_cost_usd = statistics.mean(costs_list)
        if runtimes_list:
            metrics.avg_runtime_seconds = statistics.mean(runtimes_list)
        if coverages_list:
            metrics.avg_vuln_coverage = statistics.mean(coverages_list)
        
        # Compute variance (for determinism analysis)
        if len(results) > 1:
            outcome_values = [r.outcome.value for r in results]
            unique_outcomes = len(set(outcome_values))
            metrics.outcome_variance = unique_outcomes / len(results)
        
        return metrics
    
    async def run_regression_test(
        self,
        prompt_version_a: str,
        prompt_version_b: str,
        scenario_tags: List[str] = None,
        runs_per_scenario: int = 3
    ) -> Dict[str, Any]:
        """
        Compare two prompt versions to detect regressions.
        """
        scenarios = self.list_scenarios(tags=scenario_tags)
        
        results_a = []
        results_b = []
        
        for scenario in scenarios:
            # Run both versions
            res_a = await self.run_scenario(scenario.id, prompt_version_a, runs_per_scenario)
            res_b = await self.run_scenario(scenario.id, prompt_version_b, runs_per_scenario)
            
            results_a.extend(res_a)
            results_b.extend(res_b)
        
        metrics_a = self.compute_metrics(results_a)
        metrics_b = self.compute_metrics(results_b)
        
        # Compare
        regression = {
            "version_a": prompt_version_a,
            "version_b": prompt_version_b,
            "scenarios_tested": len(scenarios),
            "runs_per_version": len(results_a),
            "comparison": {
                "pass_rate_change": metrics_b.pass_rate - metrics_a.pass_rate,
                "coverage_change": metrics_b.avg_vuln_coverage - metrics_a.avg_vuln_coverage,
                "cost_change": metrics_b.avg_cost_usd - metrics_a.avg_cost_usd,
                "speed_change": metrics_a.avg_runtime_seconds - metrics_b.avg_runtime_seconds,
            },
            "metrics_a": {
                "pass_rate": metrics_a.pass_rate,
                "coverage": metrics_a.avg_vuln_coverage,
                "cost": metrics_a.avg_cost_usd
            },
            "metrics_b": {
                "pass_rate": metrics_b.pass_rate,
                "coverage": metrics_b.avg_vuln_coverage,
                "cost": metrics_b.avg_cost_usd
            },
            "is_regression": metrics_b.pass_rate < metrics_a.pass_rate - 0.1  # 10% threshold
        }
        
        return regression


# ============================================================================
# CLI INTERFACE
# ============================================================================

async def main():
    """Example CLI for running evaluations"""
    import argparse
    
    parser = argparse.ArgumentParser(description="SentryAI Agent Evaluation Pipeline")
    parser.add_argument("--scenario", "-s", help="Scenario ID to run")
    parser.add_argument("--tags", "-t", nargs="+", help="Filter scenarios by tags")
    parser.add_argument("--runs", "-n", type=int, default=1, help="Number of runs per scenario")
    parser.add_argument("--list", "-l", action="store_true", help="List available scenarios")
    
    args = parser.parse_args()
    
    # Mock agent executor for demonstration
    async def mock_agent_executor(target, max_steps, max_cost):
        await asyncio.sleep(1)  # Simulate work
        return {
            "findings": [{"type": "sqli", "location": "/search", "severity": "high"}],
            "steps": 10,
            "cost": 0.25,
            "thoughts": [],
            "tool_calls": []
        }
    
    pipeline = EvaluationPipeline(mock_agent_executor)
    
    if args.list:
        scenarios = pipeline.list_scenarios(tags=args.tags)
        print(f"\n{'='*60}")
        print(f"{'AVAILABLE SCENARIOS':^60}")
        print(f"{'='*60}")
        for s in scenarios:
            print(f"\n📋 {s.id}")
            print(f"   {s.name}")
            print(f"   Tags: {', '.join(s.tags)}")
            print(f"   Expected vulns: {len(s.expected_vulns)}")
        return
    
    if args.scenario:
        results = await pipeline.run_scenario(args.scenario, runs=args.runs)
        metrics = pipeline.compute_metrics(results)
        
        print(f"\n{'='*60}")
        print(f"{'EVALUATION RESULTS':^60}")
        print(f"{'='*60}")
        print(f"Pass Rate: {metrics.pass_rate:.1%}")
        print(f"Avg Coverage: {metrics.avg_vuln_coverage:.1%}")
        print(f"Avg Cost: ${metrics.avg_cost_usd:.4f}")
        print(f"Avg Runtime: {metrics.avg_runtime_seconds:.1f}s")


if __name__ == "__main__":
    asyncio.run(main())

