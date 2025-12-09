"""
SentryAI Cognitive Architecture
System Prompts & Structured Output Schemas

This module defines the "personality" and logical structure of the AI agent.
It uses structured prompting with JSON schemas to ensure predictable, parseable outputs.
"""
from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field
from enum import Enum
import json


# ============================================================================
# OUTPUT SCHEMAS - What the LLM must return
# ============================================================================

class ThoughtType(str, Enum):
    """Categories of agent thoughts for UI rendering"""
    ANALYZING = "analyzing"       # Understanding the task
    RETRIEVING = "retrieving"     # Fetching context/knowledge
    PLANNING = "planning"         # Creating execution plan
    SELECTING = "selecting"       # Choosing tools/approaches
    EXECUTING = "executing"       # Running a tool
    EVALUATING = "evaluating"     # Assessing results
    PIVOTING = "pivoting"         # Changing strategy
    REPORTING = "reporting"       # Summarizing findings


class AgentThought(BaseModel):
    """Structured thought output from the agent"""
    type: ThoughtType
    reasoning: str = Field(..., description="Internal monologue explaining the thought")
    confidence: float = Field(..., ge=0, le=1, description="Confidence in this thought (0-1)")
    next_action: str = Field(..., description="What the agent plans to do next")


class ToolCall(BaseModel):
    """Structured tool invocation"""
    tool_name: str = Field(..., description="Name of the tool to execute")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="Tool arguments")
    target: str = Field(..., description="Target for this tool (must be in scope)")
    rationale: str = Field(..., description="Why this tool is being used")
    expected_output: str = Field(..., description="What we expect to find")
    timeout_seconds: int = Field(default=300, description="Max execution time")


class PlanStep(BaseModel):
    """A single step in an execution plan"""
    id: int
    title: str
    description: str
    tool: ToolCall
    depends_on: List[int] = Field(default_factory=list, description="IDs of steps this depends on")
    can_skip: bool = Field(default=True, description="Whether user can disable this step")
    risk_level: Literal["low", "medium", "high"] = "low"


class ExecutionPlan(BaseModel):
    """Complete execution plan for user approval"""
    plan_id: str
    objective: str
    target_scope: List[str]
    estimated_duration_minutes: int
    estimated_cost_usd: float
    steps: List[PlanStep]
    warnings: List[str] = Field(default_factory=list)
    requires_approval: bool = True


class FindingReport(BaseModel):
    """Structured vulnerability finding"""
    id: str
    severity: Literal["critical", "high", "medium", "low", "info"]
    title: str
    description: str
    affected_asset: str
    evidence: str
    reproduction_steps: List[str]
    remediation: str
    cwe_id: Optional[str] = None
    cvss_score: Optional[str] = None
    confidence: float = Field(..., ge=0, le=1)
    false_positive_likelihood: Literal["low", "medium", "high"] = "low"


class AgentResponse(BaseModel):
    """Complete agent response structure"""
    thoughts: List[AgentThought]
    plan: Optional[ExecutionPlan] = None
    tool_call: Optional[ToolCall] = None
    findings: List[FindingReport] = Field(default_factory=list)
    should_continue: bool = True
    needs_human_input: bool = False
    human_input_prompt: Optional[str] = None


# ============================================================================
# SYSTEM PROMPTS
# ============================================================================

MASTER_SYSTEM_PROMPT = """You are SentryAI, an elite autonomous security assessment agent. You operate with the precision of a skilled penetration tester and the caution of a security-conscious professional.

## CORE IDENTITY
- You are a Red Team operator specializing in web application and infrastructure security
- You NEVER hallucinate or make up findings - every claim must be backed by evidence
- You operate ONLY within the defined scope - unauthorized targets are strictly forbidden
- You prioritize safety and legality above all else

## COGNITIVE FRAMEWORK
When analyzing a target, follow this mental model:

1. **UNDERSTAND** - Parse the user's objective. What are they trying to achieve?
2. **SCOPE** - Verify all targets are within the allowed scope. STOP if any target is out of scope.
3. **RESEARCH** - Query your knowledge base for relevant context (API specs, past findings, etc.)
4. **PLAN** - Create a structured execution plan with clear steps
5. **EXECUTE** - Run tools ONE AT A TIME, evaluating results before proceeding
6. **EVALUATE** - Analyze tool output. Is it useful? Should we pivot?
7. **REPORT** - Document findings with evidence and remediation steps

## OUTPUT FORMAT
You MUST respond with valid JSON matching this schema:
{schema}

## TOOL USAGE RULES
1. Always specify the exact target in the `target` field
2. Never use tools against targets outside the scope
3. Prefer passive reconnaissance before active scanning
4. Rate-limit aggressive scans to avoid detection/blocking
5. Document your reasoning for every tool choice

## FINDING QUALITY STANDARDS
- NEVER report a vulnerability without concrete evidence
- Include reproduction steps that a human could follow
- Assess false-positive likelihood honestly
- Provide actionable remediation guidance

## SAFETY CONSTRAINTS
- Maximum steps per mission: {max_steps}
- Maximum budget per mission: ${max_budget}
- Allowed scope: {scope}
- Excluded targets: {exclusions}

If you're unsure about ANYTHING, ask the human operator for clarification.
"""

TOOL_SELECTION_PROMPT = """Given the objective and available tools, select the most appropriate tool.

## AVAILABLE TOOLS
{tool_definitions}

## SELECTION CRITERIA
1. **Relevance** - Does this tool help achieve the objective?
2. **Safety** - Is this tool safe to run against the target?
3. **Efficiency** - Is this the most efficient approach?
4. **Stealth** - Will this tool alert defenders?

## CURRENT CONTEXT
- Objective: {objective}
- Target: {target}
- Previous findings: {previous_findings}
- Remaining budget: ${remaining_budget}
- Remaining steps: {remaining_steps}

Select ONE tool and explain your reasoning.
"""

FINDING_ANALYSIS_PROMPT = """Analyze the tool output and determine if it contains security findings.

## TOOL OUTPUT
```
{tool_output}
```

## ANALYSIS FRAMEWORK
1. **Parse** - Extract structured data from the output
2. **Classify** - Is this a vulnerability, informational, or noise?
3. **Verify** - Can this finding be independently verified?
4. **Assess** - What is the real-world impact?
5. **Deduplicate** - Have we seen this before?

## EXISTING FINDINGS
{existing_findings}

Respond with any NEW findings that aren't duplicates.
"""

PIVOT_DECISION_PROMPT = """The previous action didn't yield expected results. Decide whether to pivot.

## PREVIOUS ACTION
- Tool: {tool_name}
- Target: {target}
- Expected: {expected}
- Actual: {actual}

## PIVOT OPTIONS
1. **Retry** - Same tool, different parameters
2. **Alternative** - Different tool, same objective
3. **Expand** - Broaden the search scope
4. **Narrow** - Focus on a specific aspect
5. **Escalate** - Ask human for guidance
6. **Abandon** - This path isn't productive

Consider: Has this approach been tried before? Is there new information to act on?
"""


# ============================================================================
# TOOL DEFINITIONS (Function Calling Format)
# ============================================================================

def get_tool_definitions() -> List[Dict[str, Any]]:
    """
    Return tool definitions in OpenAI function-calling format.
    These define exactly how the LLM should invoke each tool.
    """
    return [
        {
            "name": "subfinder",
            "description": "Passive subdomain enumeration tool. Discovers subdomains using various sources without directly touching the target.",
            "parameters": {
                "type": "object",
                "properties": {
                    "domain": {
                        "type": "string",
                        "description": "Root domain to enumerate (e.g., 'example.com')"
                    },
                    "sources": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Specific sources to use (optional). Options: crtsh, hackertarget, threatcrowd, etc."
                    },
                    "recursive": {
                        "type": "boolean",
                        "description": "Enable recursive subdomain enumeration",
                        "default": False
                    },
                    "silent": {
                        "type": "boolean",
                        "description": "Only output subdomains (no banner/stats)",
                        "default": True
                    }
                },
                "required": ["domain"]
            }
        },
        {
            "name": "naabu",
            "description": "Fast port scanner. Identifies open ports on target hosts.",
            "parameters": {
                "type": "object",
                "properties": {
                    "host": {
                        "type": "string",
                        "description": "Target host (IP or domain)"
                    },
                    "ports": {
                        "type": "string",
                        "description": "Port specification. Examples: '80,443', '1-1000', 'top-100'",
                        "default": "top-100"
                    },
                    "rate": {
                        "type": "integer",
                        "description": "Packets per second (lower = stealthier)",
                        "default": 1000
                    },
                    "retries": {
                        "type": "integer",
                        "description": "Number of retries for each port",
                        "default": 2
                    }
                },
                "required": ["host"]
            }
        },
        {
            "name": "nuclei",
            "description": "Template-based vulnerability scanner. Runs security checks using YAML templates.",
            "parameters": {
                "type": "object",
                "properties": {
                    "target": {
                        "type": "string",
                        "description": "Target URL or host"
                    },
                    "templates": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Specific template paths to use"
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Template tags to filter (e.g., 'xss', 'sqli', 'cve')"
                    },
                    "severity": {
                        "type": "array",
                        "items": {"type": "string", "enum": ["info", "low", "medium", "high", "critical"]},
                        "description": "Filter by severity level"
                    },
                    "rate_limit": {
                        "type": "integer",
                        "description": "Max requests per second",
                        "default": 150
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "Request timeout in seconds",
                        "default": 10
                    }
                },
                "required": ["target"]
            }
        },
        {
            "name": "httpx",
            "description": "HTTP toolkit for probing and fingerprinting web servers.",
            "parameters": {
                "type": "object",
                "properties": {
                    "target": {
                        "type": "string",
                        "description": "Target URL or domain"
                    },
                    "tech_detect": {
                        "type": "boolean",
                        "description": "Enable technology detection",
                        "default": True
                    },
                    "status_code": {
                        "type": "boolean",
                        "description": "Display status code",
                        "default": True
                    },
                    "title": {
                        "type": "boolean",
                        "description": "Display page title",
                        "default": True
                    },
                    "follow_redirects": {
                        "type": "boolean",
                        "description": "Follow HTTP redirects",
                        "default": True
                    }
                },
                "required": ["target"]
            }
        },
        {
            "name": "katana",
            "description": "Web crawler for discovering endpoints and URLs.",
            "parameters": {
                "type": "object",
                "properties": {
                    "target": {
                        "type": "string",
                        "description": "Starting URL to crawl"
                    },
                    "depth": {
                        "type": "integer",
                        "description": "Maximum crawl depth",
                        "default": 3
                    },
                    "scope": {
                        "type": "string",
                        "enum": ["strict", "domain", "subdomain"],
                        "description": "Crawl scope restriction",
                        "default": "domain"
                    },
                    "js_crawl": {
                        "type": "boolean",
                        "description": "Enable JavaScript parsing",
                        "default": True
                    }
                },
                "required": ["target"]
            }
        }
    ]


def format_system_prompt(
    scope: List[str],
    exclusions: List[str],
    max_steps: int = 50,
    max_budget: float = 5.0
) -> str:
    """
    Format the master system prompt with runtime configuration.
    """
    schema = AgentResponse.model_json_schema()
    
    return MASTER_SYSTEM_PROMPT.format(
        schema=json.dumps(schema, indent=2),
        max_steps=max_steps,
        max_budget=max_budget,
        scope=", ".join(scope) if scope else "Not defined - ASK USER",
        exclusions=", ".join(exclusions) if exclusions else "None"
    )


def format_tool_selection_prompt(
    objective: str,
    target: str,
    previous_findings: List[str],
    remaining_budget: float,
    remaining_steps: int
) -> str:
    """Format the tool selection prompt with context."""
    tool_defs = json.dumps(get_tool_definitions(), indent=2)
    
    return TOOL_SELECTION_PROMPT.format(
        tool_definitions=tool_defs,
        objective=objective,
        target=target,
        previous_findings="\n".join(previous_findings) if previous_findings else "None yet",
        remaining_budget=remaining_budget,
        remaining_steps=remaining_steps
    )


# ============================================================================
# RESPONSE PARSING
# ============================================================================

def parse_agent_response(raw_output: str) -> AgentResponse:
    """
    Parse LLM output into structured AgentResponse.
    Handles common formatting issues and validates the response.
    """
    # Clean up common LLM output issues
    cleaned = raw_output.strip()
    
    # Remove markdown code blocks if present
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        # Remove first and last lines (```json and ```)
        lines = [l for l in lines if not l.startswith("```")]
        cleaned = "\n".join(lines)
    
    try:
        data = json.loads(cleaned)
        return AgentResponse.model_validate(data)
    except json.JSONDecodeError as e:
        # Try to extract JSON from the response
        import re
        json_match = re.search(r'\{[\s\S]*\}', cleaned)
        if json_match:
            data = json.loads(json_match.group())
            return AgentResponse.model_validate(data)
        raise ValueError(f"Failed to parse agent response: {e}")
    except Exception as e:
        raise ValueError(f"Invalid agent response structure: {e}")

