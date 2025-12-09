"""
Security Scan Workflow
The Main Temporal Workflow that Orchestrates Agent Execution

This is where all the safety systems come together:
1. Cognitive Architecture (system prompts)
2. Scope Enforcement (kill switch)
3. Cognitive Budgets (loop prevention)
4. Multi-Tenancy (data isolation)
5. Dynamic Tool Teaching (tool definitions)
"""
import json
import asyncio
from typing import Dict, List, Any, Optional
from datetime import timedelta
from dataclasses import dataclass
import uuid

from temporalio import workflow, activity
from temporalio.common import RetryPolicy

# Import our safety systems
from ..cognitive import (
    format_system_prompt,
    parse_agent_response,
    AgentResponse,
    ExecutionPlan,
    ScopeConfig,
    ScopeEnforcer,
    ScopeViolationError,
    CognitiveBudget,
    BudgetEnforcer,
    BudgetExhaustedError,
    MissionKilledError,
    estimate_cost,
)
from ..tools import ToolRegistry, get_builtin_definition


@dataclass
class ScanInput:
    """Input for a security scan workflow"""
    mission_id: str
    tenant_id: str
    user_id: str
    objective: str                    # Natural language goal
    targets: List[str]                # Target URLs/domains/IPs
    
    # Scope configuration
    allowed_scope: List[str]          # Allowed patterns
    excluded_scope: List[str]         # Excluded patterns
    
    # Budget configuration
    max_steps: int = 50
    max_cost_usd: float = 5.0
    max_runtime_minutes: int = 60
    
    # Execution mode
    auto_pilot: bool = False          # Skip human approval
    notify_on_finding: bool = True    # Send notifications
    
    # Context
    knowledge_ids: List[str] = None   # IDs of knowledge docs to include


@dataclass
class ScanOutput:
    """Output from a security scan workflow"""
    mission_id: str
    status: str                       # completed, failed, killed, exhausted
    findings: List[Dict[str, Any]]
    steps_taken: int
    cost_usd: float
    runtime_seconds: float
    error_message: Optional[str] = None


@workflow.defn
class SecurityScanWorkflow:
    """
    Main workflow for executing a security scan mission.
    
    This workflow:
    1. Validates all inputs and initializes safety systems
    2. Generates an execution plan using the LLM
    3. Either waits for human approval or auto-executes (auto-pilot)
    4. Executes tools in sequence, respecting scope and budgets
    5. Collects and reports findings
    """
    
    def __init__(self):
        self._scope_enforcer: Optional[ScopeEnforcer] = None
        self._budget_enforcer: Optional[BudgetEnforcer] = None
        self._plan: Optional[ExecutionPlan] = None
        self._approved_steps: List[int] = []
        self._findings: List[Dict[str, Any]] = []
        self._is_paused = False
        self._is_killed = False
        self._kill_reason: Optional[str] = None
    
    @workflow.run
    async def run(self, input: ScanInput) -> ScanOutput:
        """Main workflow execution"""
        import time
        start_time = time.time()
        
        try:
            # Initialize safety systems
            await self._initialize_safety_systems(input)
            
            # Generate execution plan
            self._plan = await workflow.execute_activity(
                generate_execution_plan,
                args=[input.objective, input.targets, input.allowed_scope],
                start_to_close_timeout=timedelta(minutes=5),
                retry_policy=RetryPolicy(maximum_attempts=3)
            )
            
            # Wait for approval or auto-execute
            if not input.auto_pilot:
                # Signal that we're waiting for approval
                await workflow.execute_activity(
                    emit_plan_proposal,
                    args=[input.mission_id, self._plan],
                    start_to_close_timeout=timedelta(seconds=30)
                )
                
                # Wait for approval signal
                await workflow.wait_condition(
                    lambda: len(self._approved_steps) > 0 or self._is_killed
                )
            else:
                # Auto-approve all steps
                self._approved_steps = [s.id for s in self._plan.steps]
            
            if self._is_killed:
                return ScanOutput(
                    mission_id=input.mission_id,
                    status="killed",
                    findings=self._findings,
                    steps_taken=self._budget_enforcer.state.steps_taken,
                    cost_usd=self._budget_enforcer.state.total_cost_usd,
                    runtime_seconds=time.time() - start_time,
                    error_message=self._kill_reason
                )
            
            # Execute approved steps
            for step in self._plan.steps:
                if step.id not in self._approved_steps:
                    continue
                
                # Check if we can proceed
                can_proceed, reason = self._budget_enforcer.check_can_proceed()
                if not can_proceed:
                    return ScanOutput(
                        mission_id=input.mission_id,
                        status="exhausted",
                        findings=self._findings,
                        steps_taken=self._budget_enforcer.state.steps_taken,
                        cost_usd=self._budget_enforcer.state.total_cost_usd,
                        runtime_seconds=time.time() - start_time,
                        error_message=reason
                    )
                
                # Validate scope
                try:
                    is_valid, msg = self._scope_enforcer.validate_tool_call(
                        step.tool.tool_name,
                        step.tool.arguments
                    )
                    if not is_valid:
                        # Log but continue with next step
                        await workflow.execute_activity(
                            emit_scope_violation,
                            args=[input.mission_id, step.id, msg],
                            start_to_close_timeout=timedelta(seconds=10)
                        )
                        continue
                except ScopeViolationError as e:
                    await workflow.execute_activity(
                        emit_scope_violation,
                        args=[input.mission_id, step.id, str(e)],
                        start_to_close_timeout=timedelta(seconds=10)
                    )
                    continue
                
                # Execute tool
                tool_result = await workflow.execute_activity(
                    execute_tool,
                    args=[
                        step.tool.tool_name,
                        step.tool.arguments,
                        input.tenant_id
                    ],
                    start_to_close_timeout=timedelta(seconds=step.tool.timeout_seconds + 30),
                    retry_policy=RetryPolicy(
                        maximum_attempts=2,
                        initial_interval=timedelta(seconds=5)
                    )
                )
                
                # Record action in budget
                self._budget_enforcer.record_action(
                    action_type=step.tool.tool_name,
                    target=step.tool.target,
                    parameters=step.tool.arguments,
                    cost_usd=tool_result.get("cost_usd", 0)
                )
                
                # Process findings
                if tool_result.get("findings"):
                    for finding in tool_result["findings"]:
                        finding["step_id"] = step.id
                        finding["mission_id"] = input.mission_id
                        self._findings.append(finding)
                        
                        # Notify if enabled
                        if input.notify_on_finding:
                            await workflow.execute_activity(
                                send_finding_notification,
                                args=[input.tenant_id, finding],
                                start_to_close_timeout=timedelta(seconds=30)
                            )
                
                # Emit progress
                await workflow.execute_activity(
                    emit_step_complete,
                    args=[input.mission_id, step.id, tool_result],
                    start_to_close_timeout=timedelta(seconds=10)
                )
            
            return ScanOutput(
                mission_id=input.mission_id,
                status="completed",
                findings=self._findings,
                steps_taken=self._budget_enforcer.state.steps_taken,
                cost_usd=self._budget_enforcer.state.total_cost_usd,
                runtime_seconds=time.time() - start_time
            )
            
        except MissionKilledError as e:
            return ScanOutput(
                mission_id=input.mission_id,
                status="killed",
                findings=self._findings,
                steps_taken=self._budget_enforcer.state.steps_taken if self._budget_enforcer else 0,
                cost_usd=self._budget_enforcer.state.total_cost_usd if self._budget_enforcer else 0,
                runtime_seconds=time.time() - start_time,
                error_message=str(e)
            )
        except BudgetExhaustedError as e:
            return ScanOutput(
                mission_id=input.mission_id,
                status="exhausted",
                findings=self._findings,
                steps_taken=self._budget_enforcer.state.steps_taken if self._budget_enforcer else 0,
                cost_usd=self._budget_enforcer.state.total_cost_usd if self._budget_enforcer else 0,
                runtime_seconds=time.time() - start_time,
                error_message=str(e)
            )
        except Exception as e:
            return ScanOutput(
                mission_id=input.mission_id,
                status="failed",
                findings=self._findings,
                steps_taken=self._budget_enforcer.state.steps_taken if self._budget_enforcer else 0,
                cost_usd=self._budget_enforcer.state.total_cost_usd if self._budget_enforcer else 0,
                runtime_seconds=time.time() - start_time,
                error_message=str(e)
            )
    
    async def _initialize_safety_systems(self, input: ScanInput):
        """Initialize scope and budget enforcement"""
        # Scope enforcement
        scope_config = ScopeConfig(
            allowed_domains=input.allowed_scope,
            excluded_domains=input.excluded_scope,
            allow_private_ips=False,
            allow_localhost=False
        )
        self._scope_enforcer = ScopeEnforcer(scope_config)
        
        # Budget enforcement
        budget = CognitiveBudget(
            max_steps=input.max_steps,
            max_cost_usd=input.max_cost_usd,
            max_runtime_minutes=input.max_runtime_minutes,
            pause_on_warning=not input.auto_pilot
        )
        self._budget_enforcer = BudgetEnforcer(budget, input.mission_id)
        
        # Register violation callbacks
        self._budget_enforcer.on_violation(self._on_budget_violation)
    
    def _on_budget_violation(self, violation, details):
        """Handle budget violations"""
        # Log violation - in a real implementation, emit to Redis
        pass
    
    # =========================================================================
    # SIGNALS - External control of workflow
    # =========================================================================
    
    @workflow.signal
    async def approve_plan(self, approved_steps: List[int]):
        """Signal to approve specific steps in the plan"""
        self._approved_steps = approved_steps
    
    @workflow.signal
    async def pause(self):
        """Signal to pause execution"""
        self._is_paused = True
        if self._budget_enforcer:
            self._budget_enforcer.pause("User requested pause")
    
    @workflow.signal
    async def resume(self):
        """Signal to resume execution"""
        self._is_paused = False
        if self._budget_enforcer:
            self._budget_enforcer.resume()
    
    @workflow.signal
    async def kill(self, reason: str = "User requested termination"):
        """Signal to kill the mission immediately"""
        self._is_killed = True
        self._kill_reason = reason
        if self._budget_enforcer:
            self._budget_enforcer.kill(reason)
    
    # =========================================================================
    # QUERIES - Read workflow state
    # =========================================================================
    
    @workflow.query
    def get_status(self) -> Dict[str, Any]:
        """Query current mission status"""
        return {
            "is_paused": self._is_paused,
            "is_killed": self._is_killed,
            "findings_count": len(self._findings),
            "budget": self._budget_enforcer.get_status() if self._budget_enforcer else None,
            "current_plan": self._plan.model_dump() if self._plan else None,
            "approved_steps": self._approved_steps
        }
    
    @workflow.query
    def get_findings(self) -> List[Dict[str, Any]]:
        """Query current findings"""
        return self._findings


# =============================================================================
# ACTIVITIES - The actual work
# =============================================================================

@activity.defn
async def generate_execution_plan(
    objective: str,
    targets: List[str],
    scope: List[str]
) -> ExecutionPlan:
    """Generate an execution plan using the LLM"""
    from ..ai_engine import create_scan_plan
    
    # Get tool definitions
    registry = ToolRegistry()
    tools = registry.get_all_for_agent()
    
    # Generate plan
    plan_dict = await create_scan_plan(objective, targets, scope, tools)
    
    # Parse into structured format
    return ExecutionPlan(**plan_dict)


@activity.defn
async def execute_tool(
    tool_name: str,
    arguments: Dict[str, Any],
    tenant_id: str
) -> Dict[str, Any]:
    """Execute a tool in a sandboxed container"""
    from ..activities import run_tool_scan
    
    # Get tool definition
    definition = get_builtin_definition(tool_name)
    if not definition:
        raise ValueError(f"Unknown tool: {tool_name}")
    
    # Build command
    from ..tools import AutoDocumenter
    documenter = AutoDocumenter()
    documenter.definitions_cache[tool_name] = definition
    
    cmd = documenter.build_command(tool_name, arguments)
    
    # Execute in container
    result = await run_tool_scan(
        tool_name=tool_name,
        command=cmd,
        tenant_id=tenant_id
    )
    
    return result


@activity.defn
async def emit_plan_proposal(
    mission_id: str,
    plan: ExecutionPlan
):
    """Emit plan proposal event for frontend"""
    import redis.asyncio as redis
    import json
    
    r = redis.from_url("redis://redis:6379")
    await r.publish(
        f"agent_events:{mission_id}",
        json.dumps({
            "type": "plan_proposal",
            "mission_id": mission_id,
            "plan": plan.model_dump()
        })
    )
    await r.close()


@activity.defn
async def emit_step_complete(
    mission_id: str,
    step_id: int,
    result: Dict[str, Any]
):
    """Emit step completion event"""
    import redis.asyncio as redis
    import json
    
    r = redis.from_url("redis://redis:6379")
    await r.publish(
        f"agent_events:{mission_id}",
        json.dumps({
            "type": "step_complete",
            "mission_id": mission_id,
            "step_id": step_id,
            "result": result
        })
    )
    await r.close()


@activity.defn
async def emit_scope_violation(
    mission_id: str,
    step_id: int,
    message: str
):
    """Emit scope violation event"""
    import redis.asyncio as redis
    import json
    
    r = redis.from_url("redis://redis:6379")
    await r.publish(
        f"agent_events:{mission_id}",
        json.dumps({
            "type": "scope_violation",
            "mission_id": mission_id,
            "step_id": step_id,
            "message": message
        })
    )
    await r.close()


@activity.defn
async def send_finding_notification(
    tenant_id: str,
    finding: Dict[str, Any]
):
    """Send finding notification via configured integrations"""
    from ..notifications import notify_integrations
    
    await notify_integrations(
        event_type="vulnerability_found",
        payload=finding,
        tenant_id=tenant_id
    )

