"""
SentryAI Cognitive Architecture

This package contains the "brain" components that govern agent behavior:

- system_prompts: Structured prompting with JSON schemas for LLM outputs
- scope_enforcer: Target safety and kill switch implementation  
- budgets: Cognitive budgets to prevent infinite loops
"""
from .system_prompts import (
    AgentThought,
    ThoughtType,
    ToolCall,
    PlanStep,
    ExecutionPlan,
    FindingReport,
    AgentResponse,
    format_system_prompt,
    format_tool_selection_prompt,
    get_tool_definitions,
    parse_agent_response,
    MASTER_SYSTEM_PROMPT,
)

from .scope_enforcer import (
    ScopeConfig,
    ScopeDecision,
    ScopeEnforcer,
    ScopeMiddleware,
    ScopeViolationError,
    create_scope_config_from_db,
    create_strict_scope,
)

from .budgets import (
    CognitiveBudget,
    BudgetState,
    BudgetEnforcer,
    BudgetMiddleware,
    BudgetViolation,
    BudgetExhaustedError,
    MissionKilledError,
    estimate_cost,
)

__all__ = [
    # System Prompts
    "AgentThought",
    "ThoughtType", 
    "ToolCall",
    "PlanStep",
    "ExecutionPlan",
    "FindingReport",
    "AgentResponse",
    "format_system_prompt",
    "format_tool_selection_prompt",
    "get_tool_definitions",
    "parse_agent_response",
    "MASTER_SYSTEM_PROMPT",
    
    # Scope Enforcement
    "ScopeConfig",
    "ScopeDecision",
    "ScopeEnforcer",
    "ScopeMiddleware",
    "ScopeViolationError",
    "create_scope_config_from_db",
    "create_strict_scope",
    
    # Budgets
    "CognitiveBudget",
    "BudgetState",
    "BudgetEnforcer",
    "BudgetMiddleware",
    "BudgetViolation",
    "BudgetExhaustedError",
    "MissionKilledError",
    "estimate_cost",
]

