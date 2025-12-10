"""
SentryAI Cognitive Engine
Dynamic System Prompt Strategy with ReAct Loop

This module implements the "Brain" of SentryAI:
1. Dynamic System Prompt assembly from four injected blocks
2. Structured ReAct loop (THOUGHT -> PLAN -> ACTION -> OBSERVATION)
3. Tool definition injection for dynamic tool learning
4. Guardrail validation before execution
"""
import os
import json
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import asyncio
import redis.asyncio as redis

from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from pydantic import BaseModel, Field, ValidationError


# =============================================================================
# LLM INITIALIZATION
# =============================================================================

def get_llm(temperature: float = 0.2, model: str = None):
    """
    Initialize the NVIDIA LLM.
    Fails fast if NVIDIA_API_KEY is not set (privacy guarantee).
    """
    api_key = os.getenv("NVIDIA_API_KEY")
    if not api_key:
        raise ValueError(
            "NVIDIA_API_KEY is not set. SentryAI requires NVIDIA NIMs. "
            "This is a safety feature to prevent accidental data leakage to other providers."
        )
    
    model = model or os.getenv("NVIDIA_MODEL", "mistralai/mistral-large-3-675b-instruct-2512")
    
    return ChatNVIDIA(
        model=model,
        api_key=api_key,
        temperature=temperature
    )


# =============================================================================
# OUTPUT SCHEMA (What the LLM must return)
# =============================================================================

class AgentOutput(BaseModel):
    """
    Strict JSON schema that the LLM must output.
    This enforces the ReAct pattern.
    """
    thought_process: str = Field(
        ...,
        description="Analyze the previous observation. What does it mean?"
    )
    reasoning: str = Field(
        ..., 
        description="Why am I choosing the next step?"
    )
    tool_call: Optional[Dict[str, Any]] = Field(
        None,
        description="The tool to execute. Set to null if task is complete."
    )
    status_update: str = Field(
        ...,
        description="Human-readable status for the UI"
    )
    is_complete: bool = Field(
        False,
        description="Set to true when the mission objective is achieved"
    )
    findings: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Any vulnerabilities or discoveries found"
    )


# =============================================================================
# DYNAMIC SYSTEM PROMPT ASSEMBLY
# =============================================================================

# Block 1: Identity & Prime Directives
IDENTITY_BLOCK = """<system_role>
You are SENTRY, an Autonomous Senior Security Engineer.
Your goal is to audit infrastructure, identify vulnerabilities, and verify them safely.
You operate in a Loop: THOUGHT -> PLAN -> ACTION -> OBSERVATION.
</system_role>

<prime_directives>
1. SAFETY FIRST: Never execute destructive commands (rm -rf, shutdown, format, del /f).
2. SCOPE ADHERENCE: Only scan domains explicitly listed in the <scope> tag. NEVER scan outside scope.
3. NO HALLUCINATION: You cannot "pretend" to run a tool. You must invoke the tool_call object.
4. EVIDENCE BASED: Do not report a vulnerability unless you have validated it with a successful tool output.
5. EFFICIENCY: Use the minimum number of steps necessary. Avoid redundant scans.
6. LEGALITY: You are authorized to scan the targets in scope. Do not attempt social engineering.
</prime_directives>"""

# Block 4: Output Format
OUTPUT_FORMAT_BLOCK = """<output_format>
You must respond STRICTLY in JSON format. Do not write any text outside the JSON object.
No markdown code fences. Just raw JSON.

Schema:
{
  "thought_process": "Analyze the previous observation. What does it mean?",
  "reasoning": "Why am I choosing the next step?",
  "tool_call": {
    "name": "tool_name",
    "arguments": {"arg1": "value1", "arg2": "value2"}
  },
  "status_update": "Human-readable status for the UI",
  "is_complete": false,
  "findings": []
}

When the mission is complete, set "is_complete": true and "tool_call": null.
When you find a vulnerability, add it to the "findings" array with:
{
  "type": "sqli|xss|idor|rce|ssrf|etc",
  "severity": "critical|high|medium|low|info",
  "title": "Brief description",
  "evidence": "The proof from tool output",
  "location": "URL or endpoint affected"
}
</output_format>"""


class DynamicPromptBuilder:
    """
    Assembles the System Prompt at runtime from four injected blocks:
    1. Identity & Prime Directives (static)
    2. Memory Context (from Redis - last N steps)
    3. Tool Definitions (from enabled tools)
    4. Current Goal & Scope
    """
    
    def __init__(self, redis_client: redis.Redis = None):
        self.redis = redis_client
    
    async def get_memory_context(
        self,
        mission_id: str,
        window_size: int = 5
    ) -> str:
        """
        Fetch the last N steps from Redis for "midrun" context.
        """
        if not self.redis:
            return "<memory_context>\nNo previous context available.\n</memory_context>"
        
        try:
            # Fetch recent observations from Redis
            key = f"mission:{mission_id}:history"
            history = await self.redis.lrange(key, -window_size, -1)
            
            if not history:
                return "<memory_context>\nThis is the first step. No previous actions.\n</memory_context>"
            
            context_lines = []
            for i, entry in enumerate(history):
                data = json.loads(entry)
                context_lines.append(
                    f"Step {i+1}: {data.get('action', 'Unknown')} -> {data.get('result_summary', 'No result')}"
                )
            
            return f"<memory_context>\n" + "\n".join(context_lines) + "\n</memory_context>"
            
        except Exception as e:
            return f"<memory_context>\nError loading context: {str(e)}\n</memory_context>"
    
    def format_tool_definitions(self, tools: List[Dict[str, Any]]) -> str:
        """
        Format tool definitions as the LLM-readable schema.
        """
        if not tools:
            return "<available_tools>\nNo tools available.\n</available_tools>"
        
        formatted = []
        for tool in tools:
            tool_doc = f"""
- name: {tool['name']}
  description: {tool.get('description', 'No description')}
  parameters:
    required: {tool.get('parameters', {}).get('required', [])}
    properties:"""
            
            props = tool.get('parameters', {}).get('properties', {})
            for prop_name, prop_def in props.items():
                prop_type = prop_def.get('type', 'string')
                prop_desc = prop_def.get('description', '')
                enum_vals = prop_def.get('enum', [])
                
                tool_doc += f"\n      {prop_name}: {prop_type}"
                if prop_desc:
                    tool_doc += f" - {prop_desc}"
                if enum_vals:
                    tool_doc += f" (options: {', '.join(enum_vals)})"
            
            formatted.append(tool_doc)
        
        return "<available_tools>" + "".join(formatted) + "\n</available_tools>"
    
    def format_scope(self, allowed: List[str], excluded: List[str] = None) -> str:
        """
        Format the scope block.
        """
        scope_text = "<scope>\n"
        scope_text += "ALLOWED TARGETS (you may ONLY scan these):\n"
        for target in allowed:
            scope_text += f"  - {target}\n"
        
        if excluded:
            scope_text += "\nEXCLUDED (do NOT scan even if in allowed range):\n"
            for target in excluded:
                scope_text += f"  - {target}\n"
        
        scope_text += "</scope>"
        return scope_text
    
    async def build_prompt(
        self,
        mission_id: str,
        goal: str,
        allowed_scope: List[str],
        excluded_scope: List[str] = None,
        tools: List[Dict[str, Any]] = None,
        previous_observation: str = None
    ) -> str:
        """
        Assemble the complete dynamic system prompt.
        """
        # Block 1: Identity (static)
        prompt_parts = [IDENTITY_BLOCK]
        
        # Block 2: Memory Context (dynamic from Redis)
        memory_context = await self.get_memory_context(mission_id)
        prompt_parts.append(memory_context)
        
        # Block 3: Tool Definitions (dynamic from enabled tools)
        tool_defs = self.format_tool_definitions(tools or [])
        prompt_parts.append(tool_defs)
        
        # Scope Block
        scope_block = self.format_scope(allowed_scope, excluded_scope)
        prompt_parts.append(scope_block)
        
        # Block 4: Output Format (static)
        prompt_parts.append(OUTPUT_FORMAT_BLOCK)
        
        # Current Goal
        goal_block = f"<current_goal>\n{goal}\n</current_goal>"
        prompt_parts.append(goal_block)
        
        # Previous Observation (if any)
        if previous_observation:
            obs_block = f"<previous_observation>\n{previous_observation}\n</previous_observation>"
            prompt_parts.append(obs_block)
        
        return "\n\n".join(prompt_parts)


# =============================================================================
# GUARDRAIL VALIDATOR
# =============================================================================

class GuardrailValidator:
    """
    Validates LLM output before execution.
    
    Checks:
    1. JSON Parse Check: Is it valid JSON?
    2. Schema Check: Does it match AgentOutput schema?
    3. Hallucination Check: Is the tool actually installed?
    4. Argument Check: Do arguments match tool schema?
    5. Safety Check: Are there dangerous patterns?
    """
    
    DANGEROUS_PATTERNS = [
        r'rm\s+-rf',
        r'rm\s+-fr',
        r'rm\s+--force',
        r'rmdir\s+/s',
        r'del\s+/[fqs]',
        r'format\s+',
        r'shutdown',
        r'reboot',
        r'mkfs\.',
        r'dd\s+if=',
        r'>\s*/dev/',
        r'chmod\s+777',
        r'chmod\s+-R\s+777',
        r'\|\s*sh',
        r'\|\s*bash',
        r'curl.*\|\s*sh',
        r'wget.*\|\s*sh',
    ]
    
    def __init__(self, installed_tools: List[str], tool_schemas: Dict[str, Dict]):
        self.installed_tools = set(installed_tools)
        self.tool_schemas = tool_schemas
        self._compiled_patterns = [re.compile(p, re.IGNORECASE) for p in self.DANGEROUS_PATTERNS]
    
    def validate(self, raw_output: str) -> Tuple[bool, Optional[AgentOutput], Optional[str]]:
        """
        Validate LLM output.
        
        Returns:
            Tuple of (is_valid, parsed_output, error_message)
        """
        # Step 1: Clean the output (remove markdown fences if present)
        cleaned = self._clean_output(raw_output)
        
        # Step 2: JSON Parse Check
        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError as e:
            return False, None, f"Invalid JSON: {str(e)}"
        
        # Step 3: Schema Validation
        try:
            output = AgentOutput.model_validate(data)
        except ValidationError as e:
            return False, None, f"Schema validation failed: {str(e)}"
        
        # Step 4: Tool Existence Check (Hallucination Prevention)
        if output.tool_call:
            tool_name = output.tool_call.get("name")
            if tool_name and tool_name not in self.installed_tools:
                return False, None, f"Hallucination detected: Tool '{tool_name}' is not installed"
        
        # Step 5: Argument Validation
        if output.tool_call:
            tool_name = output.tool_call.get("name")
            args = output.tool_call.get("arguments", {})
            
            if tool_name in self.tool_schemas:
                is_valid, error = self._validate_arguments(tool_name, args)
                if not is_valid:
                    return False, None, error
        
        # Step 6: Safety Check
        safety_error = self._check_safety(output)
        if safety_error:
            return False, None, safety_error
        
        return True, output, None
    
    def _clean_output(self, raw: str) -> str:
        """Remove markdown code fences and extra whitespace."""
        cleaned = raw.strip()
        
        # Remove ```json ... ``` wrapper
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            # Remove first and last lines if they're fence markers
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            cleaned = "\n".join(lines)
        
        return cleaned.strip()
    
    def _validate_arguments(self, tool_name: str, args: Dict) -> Tuple[bool, Optional[str]]:
        """Validate tool arguments against schema."""
        schema = self.tool_schemas.get(tool_name, {})
        properties = schema.get("parameters", {}).get("properties", {})
        required = schema.get("parameters", {}).get("required", [])
        
        # Check required arguments
        for req in required:
            if req not in args:
                return False, f"Missing required argument '{req}' for tool '{tool_name}'"
        
        # Type check (basic)
        for arg_name, arg_value in args.items():
            if arg_name in properties:
                expected_type = properties[arg_name].get("type")
                if expected_type == "integer" and not isinstance(arg_value, int):
                    try:
                        int(arg_value)
                    except (ValueError, TypeError):
                        return False, f"Argument '{arg_name}' must be an integer"
                
                # Enum check
                enum_values = properties[arg_name].get("enum")
                if enum_values and arg_value not in enum_values:
                    return False, f"Argument '{arg_name}' must be one of: {enum_values}"
        
        return True, None
    
    def _check_safety(self, output: AgentOutput) -> Optional[str]:
        """Check for dangerous patterns in tool arguments."""
        if not output.tool_call:
            return None
        
        args = output.tool_call.get("arguments", {})
        
        # Convert all arguments to string for pattern matching
        args_str = json.dumps(args)
        
        for pattern in self._compiled_patterns:
            if pattern.search(args_str):
                return f"Safety violation: Dangerous pattern detected in arguments"
        
        return None


# =============================================================================
# THE COGNITIVE ENGINE (Main Class)
# =============================================================================

class CognitiveEngine:
    """
    The main "Brain" of SentryAI.
    Implements the ReAct loop with dynamic prompting and guardrails.
    """
    
    def __init__(
        self,
        redis_url: str = "redis://redis:6379",
        installed_tools: List[str] = None,
        tool_schemas: Dict[str, Dict] = None
    ):
        self.llm = get_llm()
        self.prompt_builder = DynamicPromptBuilder()
        self.validator = GuardrailValidator(
            installed_tools=installed_tools or [],
            tool_schemas=tool_schemas or {}
        )
        self.redis_url = redis_url
        self._redis: Optional[redis.Redis] = None
    
    async def _get_redis(self) -> redis.Redis:
        """Lazy Redis connection."""
        if self._redis is None:
            self._redis = redis.from_url(self.redis_url)
            self.prompt_builder.redis = self._redis
        return self._redis
    
    async def think(
        self,
        mission_id: str,
        goal: str,
        allowed_scope: List[str],
        excluded_scope: List[str] = None,
        tools: List[Dict[str, Any]] = None,
        previous_observation: str = None,
        max_retries: int = 3
    ) -> AgentOutput:
        """
        Execute one step of the ReAct loop.
        
        Args:
            mission_id: Unique identifier for this mission
            goal: The user's objective
            allowed_scope: Targets the agent may scan
            excluded_scope: Targets to exclude
            tools: Available tool definitions
            previous_observation: Output from the last tool execution
            max_retries: Number of retries if LLM output is invalid
        
        Returns:
            Validated AgentOutput
        """
        await self._get_redis()
        
        # Build the dynamic prompt
        system_prompt = await self.prompt_builder.build_prompt(
            mission_id=mission_id,
            goal=goal,
            allowed_scope=allowed_scope,
            excluded_scope=excluded_scope,
            tools=tools,
            previous_observation=previous_observation
        )
        
        # Execute with retries
        last_error = None
        for attempt in range(max_retries):
            try:
                # Call LLM
                response = self.llm.invoke(system_prompt)
                raw_output = response.content if hasattr(response, 'content') else str(response)
                
                # Validate output
                is_valid, output, error = self.validator.validate(raw_output)
                
                if is_valid:
                    # Store in history
                    await self._store_step(mission_id, output)
                    return output
                
                last_error = error
                
                # Add error feedback for retry
                if attempt < max_retries - 1:
                    system_prompt += f"\n\n<error>Your previous response was invalid: {error}. Please fix and respond again.</error>"
                    
            except Exception as e:
                last_error = str(e)
        
        # All retries failed - return a safe fallback
        return AgentOutput(
            thought_process=f"Failed to generate valid response after {max_retries} attempts",
            reasoning=f"Error: {last_error}",
            tool_call=None,
            status_update="Agent encountered an error and needs human intervention",
            is_complete=True,
            findings=[]
        )
    
    async def _store_step(self, mission_id: str, output: AgentOutput):
        """Store the step in Redis for memory context."""
        r = await self._get_redis()
        
        step_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "action": output.tool_call.get("name") if output.tool_call else "complete",
            "status": output.status_update,
            "result_summary": output.thought_process[:200]
        }
        
        key = f"mission:{mission_id}:history"
        await r.rpush(key, json.dumps(step_data))
        
        # Keep only last 20 steps
        await r.ltrim(key, -20, -1)
        
        # Set expiry (24 hours)
        await r.expire(key, 86400)
    
    async def emit_status(self, mission_id: str, status: str):
        """Emit status update to Redis pub/sub for UI streaming."""
        r = await self._get_redis()
        
        await r.publish(
            f"agent_events:{mission_id}",
            json.dumps({
                "type": "status_update",
                "mission_id": mission_id,
                "status": status,
                "timestamp": datetime.utcnow().isoformat()
            })
        )
    
    async def close(self):
        """Clean up resources."""
        if self._redis:
            await self._redis.close()


# =============================================================================
# SIMPLE PLANNING FUNCTION (Legacy compatibility)
# =============================================================================

def create_scan_plan(prompt: str) -> str:
    """
    Legacy function for simple plan generation.
    Use CognitiveEngine for full ReAct loop.
    """
    llm = get_llm()
    
    template = """You are SentryAI, an elite cybersecurity planning agent.
    Your goal is to break down a high-level security objective into actionable steps for scanning tools.
    
    Available Tools:
    - subfinder: Subdomain discovery (args: -d domain)
    - nuclei: Vulnerability scanning (args: -u url, -t template, -tags tags)
    - naabu: Port scanning (args: -host target, -p ports)
    - httpx: HTTP probing (args: -u url, -td for tech detect)
    
    User Query: {input}
    
    Return a JSON array of steps. No markdown formatting.
    Example:
    [
        {{"tool": "subfinder", "args": "-d example.com", "reason": "Discover subdomains"}},
        {{"tool": "naabu", "args": "-host example.com", "reason": "Find open ports"}}
    ]
    """
    
    prompt_template = ChatPromptTemplate.from_template(template)
    chain = prompt_template | llm | StrOutputParser()
    
    result = chain.invoke({"input": prompt})
    return result


# =============================================================================
# DEFAULT TOOL SCHEMAS
# =============================================================================

DEFAULT_TOOL_SCHEMAS = {
    "run_subfinder": {
        "name": "run_subfinder",
        "description": "Passive subdomain enumeration using multiple sources",
        "parameters": {
            "type": "object",
            "properties": {
                "domain": {
                    "type": "string",
                    "description": "Target domain to enumerate (e.g., example.com)"
                },
                "recursive": {
                    "type": "boolean",
                    "description": "Enable recursive enumeration"
                }
            },
            "required": ["domain"]
        }
    },
    "run_nuclei": {
        "name": "run_nuclei",
        "description": "Scans a target for vulnerabilities using YAML templates",
        "parameters": {
            "type": "object",
            "properties": {
                "target_url": {
                    "type": "string",
                    "description": "The target URL to scan"
                },
                "tags": {
                    "type": "string",
                    "description": "Comma-separated tags (e.g., cve,xss,sqli)"
                },
                "severity": {
                    "type": "string",
                    "enum": ["info", "low", "medium", "high", "critical"],
                    "description": "Minimum severity to report"
                },
                "templates": {
                    "type": "string",
                    "description": "Specific template path or directory"
                }
            },
            "required": ["target_url"]
        }
    },
    "run_naabu": {
        "name": "run_naabu",
        "description": "Fast port scanner for discovering open ports",
        "parameters": {
            "type": "object",
            "properties": {
                "host": {
                    "type": "string",
                    "description": "Target host (IP or domain)"
                },
                "ports": {
                    "type": "string",
                    "description": "Port specification (e.g., '80,443' or '1-1000' or 'top-100')"
                },
                "rate": {
                    "type": "integer",
                    "description": "Packets per second"
                }
            },
            "required": ["host"]
        }
    },
    "run_httpx": {
        "name": "run_httpx",
        "description": "HTTP toolkit for probing and fingerprinting web servers",
        "parameters": {
            "type": "object",
            "properties": {
                "target": {
                    "type": "string",
                    "description": "Target URL or domain"
                },
                "tech_detect": {
                    "type": "boolean",
                    "description": "Enable technology detection"
                },
                "follow_redirects": {
                    "type": "boolean",
                    "description": "Follow HTTP redirects"
                }
            },
            "required": ["target"]
        }
    }
}


def get_default_tools() -> List[Dict[str, Any]]:
    """Get default tool schemas for injection into prompts."""
    return list(DEFAULT_TOOL_SCHEMAS.values())


def get_installed_tools() -> List[str]:
    """Get list of installed tool names."""
    return list(DEFAULT_TOOL_SCHEMAS.keys())
