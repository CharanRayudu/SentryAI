"""
Cognitive Budgets & Loop Prevention
Prevents the "Loop of Death" scenario where agents get stuck

This module implements:
1. Step budgets - Maximum operations per mission
2. Cost budgets - Maximum API token spend
3. Time budgets - Maximum runtime
4. Loop detection - Identify repetitive behavior
5. Hard kill - Emergency stop mechanism
"""
import time
import hashlib
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from collections import deque
import asyncio


class BudgetViolation(Enum):
    """Types of budget violations"""
    STEP_LIMIT = "step_limit"
    COST_LIMIT = "cost_limit"
    TIME_LIMIT = "time_limit"
    LOOP_DETECTED = "loop_detected"
    MANUAL_KILL = "manual_kill"


@dataclass
class CognitiveBudget:
    """
    Budget configuration for an agent mission.
    """
    # Step limits
    max_steps: int = 50                    # Max tool invocations
    max_consecutive_errors: int = 3        # Max errors before pause
    max_retries_per_target: int = 3        # Max retries for same target
    
    # Cost limits (in USD)
    max_cost_usd: float = 5.0              # Total API cost limit
    warning_cost_threshold: float = 0.8    # Warn at 80% of budget
    
    # Time limits
    max_runtime_minutes: int = 60          # Max mission duration
    max_idle_seconds: int = 120            # Max time between actions
    
    # Loop detection
    loop_detection_window: int = 10        # Number of recent actions to analyze
    similarity_threshold: float = 0.8      # How similar actions must be to flag loop
    
    # Emergency settings
    enable_hard_kill: bool = True          # Allow emergency stops
    pause_on_warning: bool = False         # Pause and notify on warnings


@dataclass
class BudgetState:
    """
    Current state of budget consumption.
    """
    # Counters
    steps_taken: int = 0
    total_cost_usd: float = 0.0
    errors_encountered: int = 0
    consecutive_errors: int = 0
    
    # Timestamps
    started_at: datetime = field(default_factory=datetime.utcnow)
    last_action_at: datetime = field(default_factory=datetime.utcnow)
    
    # History for loop detection
    action_history: deque = field(default_factory=lambda: deque(maxlen=50))
    retry_counts: Dict[str, int] = field(default_factory=dict)
    
    # Flags
    is_paused: bool = False
    is_killed: bool = False
    kill_reason: Optional[str] = None


class BudgetEnforcer:
    """
    Enforces cognitive budgets on agent operations.
    Must be called before and after every agent action.
    """
    
    def __init__(self, budget: CognitiveBudget, mission_id: str):
        self.budget = budget
        self.mission_id = mission_id
        self.state = BudgetState()
        self._callbacks: List[Callable] = []
    
    def on_violation(self, callback: Callable[[BudgetViolation, str], None]):
        """Register callback for budget violations"""
        self._callbacks.append(callback)
    
    def _notify_violation(self, violation: BudgetViolation, details: str):
        """Notify all registered callbacks of a violation"""
        for callback in self._callbacks:
            try:
                callback(violation, details)
            except Exception:
                pass  # Don't let callback errors affect enforcement
    
    def check_can_proceed(self) -> tuple[bool, Optional[str]]:
        """
        Check if the agent can proceed with the next action.
        
        Returns:
            Tuple of (can_proceed, reason_if_not)
        """
        if self.state.is_killed:
            return False, f"Mission killed: {self.state.kill_reason}"
        
        if self.state.is_paused:
            return False, "Mission is paused - awaiting human intervention"
        
        # Check step budget
        if self.state.steps_taken >= self.budget.max_steps:
            self._notify_violation(
                BudgetViolation.STEP_LIMIT,
                f"Step limit reached ({self.budget.max_steps})"
            )
            return False, f"Step budget exhausted ({self.state.steps_taken}/{self.budget.max_steps})"
        
        # Check cost budget
        if self.state.total_cost_usd >= self.budget.max_cost_usd:
            self._notify_violation(
                BudgetViolation.COST_LIMIT,
                f"Cost limit reached (${self.budget.max_cost_usd:.2f})"
            )
            return False, f"Cost budget exhausted (${self.state.total_cost_usd:.2f}/${self.budget.max_cost_usd:.2f})"
        
        # Check time budget
        runtime = datetime.utcnow() - self.state.started_at
        max_runtime = timedelta(minutes=self.budget.max_runtime_minutes)
        if runtime > max_runtime:
            self._notify_violation(
                BudgetViolation.TIME_LIMIT,
                f"Time limit reached ({self.budget.max_runtime_minutes} minutes)"
            )
            return False, f"Time budget exhausted ({runtime.total_seconds()/60:.1f}/{self.budget.max_runtime_minutes} minutes)"
        
        # Check idle time
        idle_time = (datetime.utcnow() - self.state.last_action_at).total_seconds()
        if idle_time > self.budget.max_idle_seconds:
            return False, f"Agent idle too long ({idle_time:.0f}s > {self.budget.max_idle_seconds}s)"
        
        # Check consecutive errors
        if self.state.consecutive_errors >= self.budget.max_consecutive_errors:
            return False, f"Too many consecutive errors ({self.state.consecutive_errors})"
        
        return True, None
    
    def record_action(
        self,
        action_type: str,
        target: str,
        parameters: Dict[str, Any],
        cost_usd: float = 0.0
    ):
        """
        Record an agent action for budget tracking.
        Call this AFTER the action completes successfully.
        """
        self.state.steps_taken += 1
        self.state.total_cost_usd += cost_usd
        self.state.last_action_at = datetime.utcnow()
        self.state.consecutive_errors = 0  # Reset on success
        
        # Record for loop detection
        action_signature = self._compute_action_signature(action_type, target, parameters)
        self.state.action_history.append({
            "signature": action_signature,
            "type": action_type,
            "target": target,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Check for warnings
        self._check_warnings()
        
        # Check for loops
        self._check_for_loops()
    
    def record_error(self, error_type: str, details: str):
        """
        Record an error from an agent action.
        """
        self.state.errors_encountered += 1
        self.state.consecutive_errors += 1
        self.state.last_action_at = datetime.utcnow()
    
    def record_retry(self, target: str) -> bool:
        """
        Record a retry attempt for a target.
        
        Returns:
            True if retry is allowed, False if limit exceeded
        """
        key = self._normalize_target(target)
        current_retries = self.state.retry_counts.get(key, 0)
        
        if current_retries >= self.budget.max_retries_per_target:
            return False
        
        self.state.retry_counts[key] = current_retries + 1
        return True
    
    def _compute_action_signature(
        self,
        action_type: str,
        target: str,
        parameters: Dict[str, Any]
    ) -> str:
        """
        Compute a signature for an action to detect loops.
        Similar actions will have similar signatures.
        """
        # Normalize parameters (sort keys, ignore timestamps)
        normalized_params = {
            k: v for k, v in sorted(parameters.items())
            if k not in ('timestamp', 'request_id', 'session_id')
        }
        
        sig_string = f"{action_type}:{target}:{str(normalized_params)}"
        return hashlib.md5(sig_string.encode()).hexdigest()[:16]
    
    def _normalize_target(self, target: str) -> str:
        """Normalize target for comparison"""
        return target.lower().strip().rstrip('/')
    
    def _check_warnings(self):
        """Check if we should warn about budget consumption"""
        cost_ratio = self.state.total_cost_usd / self.budget.max_cost_usd
        step_ratio = self.state.steps_taken / self.budget.max_steps
        
        if cost_ratio >= self.budget.warning_cost_threshold:
            if self.budget.pause_on_warning:
                self.state.is_paused = True
            # Could emit a warning event here
        
        if step_ratio >= 0.9:  # 90% of steps used
            if self.budget.pause_on_warning:
                self.state.is_paused = True
    
    def _check_for_loops(self):
        """
        Detect if the agent is stuck in a loop.
        Analyzes recent action signatures for repetitive patterns.
        """
        if len(self.state.action_history) < self.budget.loop_detection_window:
            return
        
        recent_actions = list(self.state.action_history)[-self.budget.loop_detection_window:]
        signatures = [a["signature"] for a in recent_actions]
        
        # Count signature frequencies
        from collections import Counter
        freq = Counter(signatures)
        
        # Check if any signature appears too frequently
        most_common = freq.most_common(1)[0]
        repetition_rate = most_common[1] / len(signatures)
        
        if repetition_rate >= self.budget.similarity_threshold:
            self._notify_violation(
                BudgetViolation.LOOP_DETECTED,
                f"Detected repetitive action pattern: {most_common[0]} ({most_common[1]} times in last {len(signatures)} actions)"
            )
            
            if self.budget.pause_on_warning:
                self.state.is_paused = True
    
    def pause(self, reason: str = "Manual pause"):
        """Pause the mission - requires human intervention to resume"""
        self.state.is_paused = True
    
    def resume(self):
        """Resume a paused mission"""
        self.state.is_paused = False
        self.state.consecutive_errors = 0  # Reset on resume
    
    def kill(self, reason: str = "Manual kill"):
        """
        Hard kill the mission - cannot be resumed.
        Use for emergencies only.
        """
        self.state.is_killed = True
        self.state.kill_reason = reason
        self._notify_violation(BudgetViolation.MANUAL_KILL, reason)
    
    def get_status(self) -> Dict[str, Any]:
        """Get current budget status"""
        runtime = datetime.utcnow() - self.state.started_at
        
        return {
            "mission_id": self.mission_id,
            "is_active": not self.state.is_killed and not self.state.is_paused,
            "is_paused": self.state.is_paused,
            "is_killed": self.state.is_killed,
            "kill_reason": self.state.kill_reason,
            "steps": {
                "used": self.state.steps_taken,
                "limit": self.budget.max_steps,
                "remaining": self.budget.max_steps - self.state.steps_taken,
                "percent": round(self.state.steps_taken / self.budget.max_steps * 100, 1)
            },
            "cost": {
                "used_usd": round(self.state.total_cost_usd, 4),
                "limit_usd": self.budget.max_cost_usd,
                "remaining_usd": round(self.budget.max_cost_usd - self.state.total_cost_usd, 4),
                "percent": round(self.state.total_cost_usd / self.budget.max_cost_usd * 100, 1)
            },
            "time": {
                "elapsed_minutes": round(runtime.total_seconds() / 60, 1),
                "limit_minutes": self.budget.max_runtime_minutes,
                "remaining_minutes": round(self.budget.max_runtime_minutes - runtime.total_seconds() / 60, 1),
                "percent": round(runtime.total_seconds() / 60 / self.budget.max_runtime_minutes * 100, 1)
            },
            "errors": {
                "total": self.state.errors_encountered,
                "consecutive": self.state.consecutive_errors
            }
        }
    
    def add_cost(self, cost_usd: float):
        """Add cost from an API call (LLM tokens, etc.)"""
        self.state.total_cost_usd += cost_usd
        self._check_warnings()


class BudgetMiddleware:
    """
    Async middleware that wraps agent execution with budget enforcement.
    """
    
    def __init__(self, enforcer: BudgetEnforcer):
        self.enforcer = enforcer
    
    async def execute_with_budget(
        self,
        executor: Callable,
        action_type: str,
        target: str,
        parameters: Dict[str, Any],
        cost_usd: float = 0.0
    ):
        """
        Execute an action with budget enforcement.
        
        Raises:
            BudgetExhaustedError: If budget is exhausted
            MissionKilledError: If mission was hard-killed
        """
        # Pre-check
        can_proceed, reason = self.enforcer.check_can_proceed()
        if not can_proceed:
            if self.enforcer.state.is_killed:
                raise MissionKilledError(reason)
            raise BudgetExhaustedError(reason)
        
        try:
            # Execute
            result = await executor()
            
            # Record success
            self.enforcer.record_action(action_type, target, parameters, cost_usd)
            
            return result
            
        except Exception as e:
            # Record error
            self.enforcer.record_error(type(e).__name__, str(e))
            raise


class BudgetExhaustedError(Exception):
    """Raised when budget is exhausted"""
    pass


class MissionKilledError(Exception):
    """Raised when mission is hard-killed"""
    pass


# ============================================================================
# TOKEN COST ESTIMATION
# ============================================================================

# Approximate costs per 1K tokens (as of late 2024)
TOKEN_COSTS = {
    "gpt-4-turbo": {"input": 0.01, "output": 0.03},
    "gpt-4": {"input": 0.03, "output": 0.06},
    "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
    "claude-3-opus": {"input": 0.015, "output": 0.075},
    "claude-3-sonnet": {"input": 0.003, "output": 0.015},
    "mistral-large": {"input": 0.008, "output": 0.024},
    "llama-3-70b": {"input": 0.0, "output": 0.0},  # Self-hosted
    "nvidia-nim": {"input": 0.001, "output": 0.002},  # NVIDIA pricing varies
}


def estimate_cost(
    model: str,
    input_tokens: int,
    output_tokens: int
) -> float:
    """
    Estimate the cost of an LLM API call.
    """
    costs = TOKEN_COSTS.get(model, {"input": 0.001, "output": 0.001})
    
    input_cost = (input_tokens / 1000) * costs["input"]
    output_cost = (output_tokens / 1000) * costs["output"]
    
    return input_cost + output_cost


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    # Create budget with conservative limits
    budget = CognitiveBudget(
        max_steps=25,
        max_cost_usd=2.0,
        max_runtime_minutes=30,
        pause_on_warning=True
    )
    
    enforcer = BudgetEnforcer(budget, mission_id="test-mission-001")
    
    # Register violation callback
    def on_violation(violation: BudgetViolation, details: str):
        print(f"⚠️ VIOLATION: {violation.value} - {details}")
    
    enforcer.on_violation(on_violation)
    
    # Simulate some actions
    for i in range(10):
        can_proceed, reason = enforcer.check_can_proceed()
        if not can_proceed:
            print(f"❌ Cannot proceed: {reason}")
            break
        
        # Simulate action
        enforcer.record_action(
            action_type="nuclei_scan",
            target="example.com",
            parameters={"tags": ["xss"]},
            cost_usd=0.15
        )
        
        print(f"Step {i+1}: {enforcer.get_status()['steps']['percent']}% steps, ${enforcer.get_status()['cost']['used_usd']:.2f} spent")

