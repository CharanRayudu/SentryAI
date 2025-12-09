"""
Dynamic Tool Teaching - Auto-Documenter Service

When a new tool is installed from GitHub, the LLM doesn't know how to use it.
This service automatically:
1. Runs `tool --help` to get the help text
2. Parses the output to extract arguments and flags
3. Uses an LLM to generate a structured tool_definition.json
4. Injects the definition into the agent's context

This is the "Plugin Problem" solution.
"""
import subprocess
import json
import re
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from pathlib import Path
from enum import Enum
import shutil


class ParamType(str, Enum):
    """Types of tool parameters"""
    STRING = "string"
    INTEGER = "integer"
    BOOLEAN = "boolean"
    ARRAY = "array"
    FILE = "file"
    URL = "url"


@dataclass
class ToolParameter:
    """A single tool parameter/flag"""
    name: str
    flag: str                          # e.g., "-u", "--url"
    description: str
    param_type: ParamType = ParamType.STRING
    required: bool = False
    default: Optional[Any] = None
    choices: List[str] = field(default_factory=list)
    example: Optional[str] = None


@dataclass
class ToolDefinition:
    """Complete definition of a security tool"""
    name: str
    version: str
    description: str
    binary_path: str
    
    # Parameters
    parameters: List[ToolParameter] = field(default_factory=list)
    
    # Usage patterns
    usage_examples: List[str] = field(default_factory=list)
    
    # Categorization
    category: str = "general"          # recon, scanning, exploitation, etc.
    tags: List[str] = field(default_factory=list)
    
    # Execution hints
    requires_root: bool = False
    timeout_default: int = 300
    output_format: str = "text"        # text, json, csv
    
    def to_openai_function(self) -> Dict[str, Any]:
        """Convert to OpenAI function-calling format"""
        properties = {}
        required = []
        
        for param in self.parameters:
            prop = {
                "type": param.param_type.value,
                "description": param.description
            }
            
            if param.choices:
                prop["enum"] = param.choices
            
            if param.default is not None:
                prop["default"] = param.default
            
            if param.example:
                prop["description"] += f" (e.g., '{param.example}')"
            
            properties[param.name] = prop
            
            if param.required:
                required.append(param.name)
        
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required
            }
        }
    
    def to_json(self) -> str:
        """Serialize to JSON"""
        return json.dumps({
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "binary_path": self.binary_path,
            "parameters": [
                {
                    "name": p.name,
                    "flag": p.flag,
                    "description": p.description,
                    "type": p.param_type.value,
                    "required": p.required,
                    "default": p.default,
                    "choices": p.choices,
                    "example": p.example
                }
                for p in self.parameters
            ],
            "usage_examples": self.usage_examples,
            "category": self.category,
            "tags": self.tags,
            "requires_root": self.requires_root,
            "timeout_default": self.timeout_default,
            "output_format": self.output_format
        }, indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> "ToolDefinition":
        """Deserialize from JSON"""
        data = json.loads(json_str)
        
        params = [
            ToolParameter(
                name=p["name"],
                flag=p["flag"],
                description=p["description"],
                param_type=ParamType(p["type"]),
                required=p.get("required", False),
                default=p.get("default"),
                choices=p.get("choices", []),
                example=p.get("example")
            )
            for p in data.get("parameters", [])
        ]
        
        return cls(
            name=data["name"],
            version=data.get("version", "unknown"),
            description=data["description"],
            binary_path=data["binary_path"],
            parameters=params,
            usage_examples=data.get("usage_examples", []),
            category=data.get("category", "general"),
            tags=data.get("tags", []),
            requires_root=data.get("requires_root", False),
            timeout_default=data.get("timeout_default", 300),
            output_format=data.get("output_format", "text")
        )


class AutoDocumenter:
    """
    Automatically generates tool definitions from help text.
    """
    
    def __init__(
        self,
        llm_client=None,  # Optional LLM for enhanced parsing
        tools_dir: str = "/mnt/tools"
    ):
        self.llm_client = llm_client
        self.tools_dir = Path(tools_dir)
        self.definitions_cache: Dict[str, ToolDefinition] = {}
    
    async def document_tool(
        self,
        binary_name: str,
        binary_path: Optional[str] = None
    ) -> ToolDefinition:
        """
        Generate a complete tool definition.
        
        Args:
            binary_name: Name of the tool (e.g., "nuclei")
            binary_path: Full path to binary (auto-detected if not provided)
        """
        # Find binary
        if not binary_path:
            binary_path = self._find_binary(binary_name)
        
        if not binary_path:
            raise FileNotFoundError(f"Binary not found: {binary_name}")
        
        # Get help text
        help_text = await self._get_help_text(binary_path)
        version = await self._get_version(binary_path)
        
        # Parse help text
        if self.llm_client:
            # Use LLM for sophisticated parsing
            definition = await self._parse_with_llm(binary_name, binary_path, help_text, version)
        else:
            # Fall back to regex-based parsing
            definition = self._parse_with_regex(binary_name, binary_path, help_text, version)
        
        # Cache and return
        self.definitions_cache[binary_name] = definition
        return definition
    
    def _find_binary(self, name: str) -> Optional[str]:
        """Find binary in PATH or tools directory"""
        # Check system PATH
        which_path = shutil.which(name)
        if which_path:
            return which_path
        
        # Check tools directory
        tool_path = self.tools_dir / name
        if tool_path.exists() and tool_path.is_file():
            return str(tool_path)
        
        return None
    
    async def _get_help_text(self, binary_path: str) -> str:
        """Get help text from the tool"""
        help_flags = ["--help", "-h", "help", "-help"]
        
        for flag in help_flags:
            try:
                result = subprocess.run(
                    [binary_path, flag],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                output = result.stdout or result.stderr
                if output and len(output) > 50:  # Sanity check
                    return output
            except (subprocess.TimeoutExpired, subprocess.SubprocessError):
                continue
        
        return ""
    
    async def _get_version(self, binary_path: str) -> str:
        """Get version string from the tool"""
        version_flags = ["--version", "-v", "-V", "version"]
        
        for flag in version_flags:
            try:
                result = subprocess.run(
                    [binary_path, flag],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                output = result.stdout or result.stderr
                if output:
                    # Extract version number
                    match = re.search(r'v?(\d+\.\d+\.?\d*)', output)
                    if match:
                        return match.group(1)
            except (subprocess.TimeoutExpired, subprocess.SubprocessError):
                continue
        
        return "unknown"
    
    def _parse_with_regex(
        self,
        name: str,
        binary_path: str,
        help_text: str,
        version: str
    ) -> ToolDefinition:
        """Parse help text using regex patterns"""
        parameters = []
        
        # Common patterns for CLI flags
        patterns = [
            # -f, --flag VALUE  description
            r'^\s*(-\w),?\s*(--[\w-]+)\s+(\S+)?\s+(.+)$',
            # --flag VALUE  description
            r'^\s*(--[\w-]+)\s+(\S+)?\s+(.+)$',
            # -f VALUE  description
            r'^\s*(-\w)\s+(\S+)?\s+(.+)$',
        ]
        
        lines = help_text.split('\n')
        
        for line in lines:
            for pattern in patterns:
                match = re.match(pattern, line.strip())
                if match:
                    groups = match.groups()
                    
                    if len(groups) == 4:
                        short_flag, long_flag, value_hint, desc = groups
                        flag = long_flag or short_flag
                        param_name = (long_flag or short_flag).lstrip('-').replace('-', '_')
                    elif len(groups) == 3:
                        flag, value_hint, desc = groups
                        short_flag = None
                        param_name = flag.lstrip('-').replace('-', '_')
                    else:
                        continue
                    
                    # Determine type from value hint
                    param_type = self._infer_type(value_hint, desc)
                    
                    # Check if required
                    required = 'required' in desc.lower() or 'mandatory' in desc.lower()
                    
                    parameters.append(ToolParameter(
                        name=param_name,
                        flag=flag,
                        description=desc.strip(),
                        param_type=param_type,
                        required=required
                    ))
                    break
        
        # Extract description from first meaningful line
        description = ""
        for line in lines[:10]:
            line = line.strip()
            if line and not line.startswith('-') and len(line) > 20:
                description = line
                break
        
        return ToolDefinition(
            name=name,
            version=version,
            description=description or f"{name} security tool",
            binary_path=binary_path,
            parameters=parameters,
            category=self._infer_category(name, description)
        )
    
    def _infer_type(self, value_hint: Optional[str], description: str) -> ParamType:
        """Infer parameter type from hints"""
        if not value_hint:
            return ParamType.BOOLEAN
        
        hint_lower = value_hint.lower()
        desc_lower = description.lower()
        
        if any(x in hint_lower for x in ['int', 'number', 'count', 'port']):
            return ParamType.INTEGER
        if any(x in hint_lower for x in ['url', 'http']):
            return ParamType.URL
        if any(x in hint_lower for x in ['file', 'path', 'output']):
            return ParamType.FILE
        if any(x in desc_lower for x in ['comma-separated', 'list of']):
            return ParamType.ARRAY
        
        return ParamType.STRING
    
    def _infer_category(self, name: str, description: str) -> str:
        """Infer tool category from name and description"""
        combined = f"{name} {description}".lower()
        
        categories = {
            "recon": ["subdomain", "dns", "whois", "enumerate", "discover"],
            "scanning": ["scan", "port", "service", "nmap", "masscan"],
            "vulnerability": ["vuln", "nuclei", "exploit", "cve"],
            "fuzzing": ["fuzz", "brute", "wordlist", "directory"],
            "web": ["http", "url", "web", "crawl", "spider"],
            "network": ["network", "packet", "traffic", "tcp", "udp"],
        }
        
        for category, keywords in categories.items():
            if any(kw in combined for kw in keywords):
                return category
        
        return "general"
    
    async def _parse_with_llm(
        self,
        name: str,
        binary_path: str,
        help_text: str,
        version: str
    ) -> ToolDefinition:
        """Use LLM for more sophisticated parsing"""
        if not self.llm_client:
            return self._parse_with_regex(name, binary_path, help_text, version)
        
        prompt = f"""Analyze this CLI tool's help text and generate a structured tool definition.

Tool Name: {name}
Version: {version}
Help Text:
```
{help_text[:4000]}  # Truncate to fit context
```

Generate a JSON object with:
1. description: A clear one-sentence description
2. parameters: Array of parameters with:
   - name: snake_case parameter name
   - flag: The actual CLI flag (e.g., "--target")
   - description: What this parameter does
   - type: "string", "integer", "boolean", "array", "file", or "url"
   - required: true/false
   - default: default value if any
   - example: example value
3. usage_examples: Array of 2-3 example commands
4. category: One of: recon, scanning, vulnerability, fuzzing, web, network, general
5. tags: Array of relevant tags
6. output_format: "text", "json", or "csv"

Respond with ONLY valid JSON, no explanation."""

        try:
            response = await self.llm_client.generate(prompt)
            data = json.loads(response)
            
            params = [
                ToolParameter(
                    name=p["name"],
                    flag=p["flag"],
                    description=p["description"],
                    param_type=ParamType(p.get("type", "string")),
                    required=p.get("required", False),
                    default=p.get("default"),
                    example=p.get("example")
                )
                for p in data.get("parameters", [])
            ]
            
            return ToolDefinition(
                name=name,
                version=version,
                description=data.get("description", f"{name} security tool"),
                binary_path=binary_path,
                parameters=params,
                usage_examples=data.get("usage_examples", []),
                category=data.get("category", "general"),
                tags=data.get("tags", []),
                output_format=data.get("output_format", "text")
            )
            
        except (json.JSONDecodeError, KeyError):
            # Fall back to regex parsing
            return self._parse_with_regex(name, binary_path, help_text, version)
    
    def build_command(
        self,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> List[str]:
        """
        Build a command line from a tool name and arguments.
        Uses the cached definition to map arguments to flags.
        """
        definition = self.definitions_cache.get(tool_name)
        if not definition:
            raise ValueError(f"No definition found for tool: {tool_name}")
        
        cmd = [definition.binary_path]
        
        # Build parameter map
        param_map = {p.name: p for p in definition.parameters}
        
        for arg_name, value in arguments.items():
            param = param_map.get(arg_name)
            if not param:
                continue
            
            if param.param_type == ParamType.BOOLEAN:
                if value:
                    cmd.append(param.flag)
            elif param.param_type == ParamType.ARRAY:
                if isinstance(value, list):
                    cmd.extend([param.flag, ','.join(str(v) for v in value)])
                else:
                    cmd.extend([param.flag, str(value)])
            else:
                cmd.extend([param.flag, str(value)])
        
        return cmd
    
    def get_all_definitions(self) -> List[Dict[str, Any]]:
        """Get all cached definitions in OpenAI function format"""
        return [d.to_openai_function() for d in self.definitions_cache.values()]


class ToolRegistry:
    """
    Central registry for all available tools.
    Persists definitions to disk for reuse.
    """
    
    def __init__(self, storage_path: str = "./tool_definitions"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True)
        self.documenter = AutoDocumenter()
        self._definitions: Dict[str, ToolDefinition] = {}
        self._load_definitions()
    
    def _load_definitions(self):
        """Load definitions from disk"""
        for file_path in self.storage_path.glob("*.json"):
            try:
                with open(file_path, 'r') as f:
                    definition = ToolDefinition.from_json(f.read())
                    self._definitions[definition.name] = definition
            except Exception:
                continue
    
    def _save_definition(self, definition: ToolDefinition):
        """Save a definition to disk"""
        file_path = self.storage_path / f"{definition.name}.json"
        with open(file_path, 'w') as f:
            f.write(definition.to_json())
    
    async def register_tool(
        self,
        binary_name: str,
        binary_path: Optional[str] = None,
        force_refresh: bool = False
    ) -> ToolDefinition:
        """
        Register a tool - generates definition if not cached.
        """
        if binary_name in self._definitions and not force_refresh:
            return self._definitions[binary_name]
        
        definition = await self.documenter.document_tool(binary_name, binary_path)
        self._definitions[binary_name] = definition
        self._save_definition(definition)
        
        return definition
    
    def get_definition(self, tool_name: str) -> Optional[ToolDefinition]:
        """Get a tool definition by name"""
        return self._definitions.get(tool_name)
    
    def get_all_for_agent(self) -> List[Dict[str, Any]]:
        """Get all definitions in agent-consumable format"""
        return [d.to_openai_function() for d in self._definitions.values()]
    
    def list_tools(self) -> List[str]:
        """List all registered tool names"""
        return list(self._definitions.keys())


# ============================================================================
# PRE-BUILT DEFINITIONS (for common tools)
# ============================================================================

BUILTIN_DEFINITIONS = {
    "nuclei": ToolDefinition(
        name="nuclei",
        version="3.0",
        description="Fast and customizable vulnerability scanner using YAML templates",
        binary_path="/usr/local/bin/nuclei",
        parameters=[
            ToolParameter("target", "-u", "Target URL to scan", ParamType.URL, required=True, example="https://example.com"),
            ToolParameter("targets_file", "-l", "File containing list of targets", ParamType.FILE),
            ToolParameter("templates", "-t", "Template or directory path", ParamType.STRING),
            ToolParameter("tags", "-tags", "Template tags to run (comma-separated)", ParamType.ARRAY, example="xss,sqli"),
            ToolParameter("severity", "-severity", "Filter by severity", ParamType.ARRAY, choices=["info", "low", "medium", "high", "critical"]),
            ToolParameter("rate_limit", "-rl", "Max requests per second", ParamType.INTEGER, default=150),
            ToolParameter("concurrency", "-c", "Number of concurrent templates", ParamType.INTEGER, default=25),
            ToolParameter("output", "-o", "Output file path", ParamType.FILE),
            ToolParameter("json_output", "-json", "Output in JSON format", ParamType.BOOLEAN),
            ToolParameter("silent", "-silent", "Suppress output banner", ParamType.BOOLEAN),
        ],
        usage_examples=[
            "nuclei -u https://example.com -tags cve",
            "nuclei -l targets.txt -severity high,critical -json -o results.json",
        ],
        category="vulnerability",
        tags=["scanner", "templates", "cve", "web"],
        output_format="json"
    ),
    "subfinder": ToolDefinition(
        name="subfinder",
        version="2.6",
        description="Passive subdomain enumeration tool using multiple sources",
        binary_path="/usr/local/bin/subfinder",
        parameters=[
            ToolParameter("domain", "-d", "Target domain to enumerate", ParamType.STRING, required=True, example="example.com"),
            ToolParameter("domains_file", "-dL", "File containing list of domains", ParamType.FILE),
            ToolParameter("sources", "-sources", "Specific sources to use", ParamType.ARRAY),
            ToolParameter("recursive", "-recursive", "Enable recursive enumeration", ParamType.BOOLEAN),
            ToolParameter("all_sources", "-all", "Use all available sources", ParamType.BOOLEAN),
            ToolParameter("output", "-o", "Output file path", ParamType.FILE),
            ToolParameter("json_output", "-json", "Output in JSON format", ParamType.BOOLEAN),
            ToolParameter("silent", "-silent", "Suppress output banner", ParamType.BOOLEAN),
        ],
        usage_examples=[
            "subfinder -d example.com -silent",
            "subfinder -dL domains.txt -all -o subdomains.txt",
        ],
        category="recon",
        tags=["subdomain", "dns", "passive", "enumeration"],
        output_format="text"
    ),
    "naabu": ToolDefinition(
        name="naabu",
        version="2.1",
        description="Fast port scanner with SYN/CONNECT scanning support",
        binary_path="/usr/local/bin/naabu",
        parameters=[
            ToolParameter("host", "-host", "Target host to scan", ParamType.STRING, required=True, example="192.168.1.1"),
            ToolParameter("hosts_file", "-l", "File containing list of hosts", ParamType.FILE),
            ToolParameter("ports", "-p", "Ports to scan (e.g., 80,443 or 1-1000)", ParamType.STRING, default="top-100"),
            ToolParameter("top_ports", "-top-ports", "Scan top N ports", ParamType.INTEGER),
            ToolParameter("rate", "-rate", "Packets per second", ParamType.INTEGER, default=1000),
            ToolParameter("retries", "-retries", "Number of retries", ParamType.INTEGER, default=3),
            ToolParameter("output", "-o", "Output file path", ParamType.FILE),
            ToolParameter("json_output", "-json", "Output in JSON format", ParamType.BOOLEAN),
            ToolParameter("silent", "-silent", "Suppress output banner", ParamType.BOOLEAN),
        ],
        usage_examples=[
            "naabu -host 192.168.1.1 -top-ports 1000",
            "naabu -l hosts.txt -p 80,443,8080 -json -o ports.json",
        ],
        category="scanning",
        tags=["port", "scanner", "network", "syn"],
        output_format="text"
    ),
    "httpx": ToolDefinition(
        name="httpx",
        version="1.3",
        description="HTTP toolkit for probing and fingerprinting web servers",
        binary_path="/usr/local/bin/httpx",
        parameters=[
            ToolParameter("url", "-u", "Target URL", ParamType.URL, example="https://example.com"),
            ToolParameter("urls_file", "-l", "File containing URLs", ParamType.FILE),
            ToolParameter("tech_detect", "-td", "Enable technology detection", ParamType.BOOLEAN, default=True),
            ToolParameter("status_code", "-sc", "Display status code", ParamType.BOOLEAN, default=True),
            ToolParameter("title", "-title", "Display page title", ParamType.BOOLEAN, default=True),
            ToolParameter("content_length", "-cl", "Display content length", ParamType.BOOLEAN),
            ToolParameter("follow_redirects", "-fr", "Follow redirects", ParamType.BOOLEAN, default=True),
            ToolParameter("threads", "-t", "Number of threads", ParamType.INTEGER, default=50),
            ToolParameter("output", "-o", "Output file path", ParamType.FILE),
            ToolParameter("json_output", "-json", "Output in JSON format", ParamType.BOOLEAN),
        ],
        usage_examples=[
            "httpx -u https://example.com -td -title -sc",
            "httpx -l urls.txt -json -o results.json",
        ],
        category="web",
        tags=["http", "probe", "fingerprint", "technology"],
        output_format="json"
    ),
}


def get_builtin_definition(tool_name: str) -> Optional[ToolDefinition]:
    """Get a pre-built definition for common tools"""
    return BUILTIN_DEFINITIONS.get(tool_name)


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    async def main():
        # Initialize registry
        registry = ToolRegistry()
        
        # Register built-in tools
        for name, definition in BUILTIN_DEFINITIONS.items():
            registry._definitions[name] = definition
            registry._save_definition(definition)
        
        # Get all definitions for the agent
        agent_tools = registry.get_all_for_agent()
        
        print(f"Registered {len(agent_tools)} tools:")
        for tool in agent_tools:
            print(f"  - {tool['name']}: {tool['description'][:60]}...")
        
        # Build a command
        documenter = AutoDocumenter()
        documenter.definitions_cache = registry._definitions
        
        cmd = documenter.build_command("nuclei", {
            "target": "https://example.com",
            "tags": ["xss", "sqli"],
            "severity": ["high", "critical"],
            "json_output": True
        })
        
        print(f"\nExample command: {' '.join(cmd)}")
    
    asyncio.run(main())

