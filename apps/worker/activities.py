from temporalio import activity
import docker
import asyncio
import json
from ai_engine import create_scan_plan

# Initialize Docker Client
try:
    docker_client = docker.from_env()
except Exception as e:
    print(f"Warning: Docker client failed to initialize: {e}")
    docker_client = None

@activity.defn
async def ai_plan_scan(prompt: str) -> list:
    """
    Uses NVIDIA NIM (via LangChain) to generate a scan plan.
    """
    activity.logger.info(f"Generating plan for: {prompt}")
    try:
        # This calls our NVIDIA-only module
        plan_json = create_scan_plan(prompt)
        # Basic cleanup if the LLM wraps in markdown codes
        plan_json = plan_json.replace("```json", "").replace("```", "").strip()
        plan = json.loads(plan_json)
        return plan
    except Exception as e:
        activity.logger.error(f"Planning failed: {e}")
        return [{"error": str(e)}]

@activity.defn
async def run_tool_scan(params: dict) -> list:
    tool = params.get("tool")
    target = params.get("target")
    args = params.get("args", "")
    
    activity.logger.info(f"Running {tool} on {target} with args {args}")
    
    if not docker_client:
        return [{"error": "Docker socket not connected. Cannot run scan."}]

    # Sandwich Strategy: Ephemeral Container
    image_map = {
        "subfinder": "projectdiscovery/subfinder:latest",
        "nuclei": "projectdiscovery/nuclei:latest",
        "naabu": "projectdiscovery/naabu:latest"
    }
    
    image = image_map.get(tool)
    if not image:
        return [{"error": f"Unknown tool: {tool}"}]

    try:
        # Construct command
        cmd = f"{args}" 
        # Quick fix for tool-specific argument patterns
        if tool == "subfinder" and "-d" not in args:
             cmd = f"-d {target} {args}"
        elif tool == "nuclei" and "-u" not in args:
             cmd = f"-u {target} {args}"
        elif tool == "naabu" and "-host" not in args:
             cmd = f"-host {target} {args}"
            
        logs = docker_client.containers.run(
            image,
            command=cmd,
            remove=True,
            network_mode="host", 
            stderr=True,
            stdout=True
        )
        
        output = logs.decode('utf-8')
        return [{"tool": tool, "raw": output}]
        
    except Exception as e:
        activity.logger.error(f"Scan failed: {e}")
        return [{"error": str(e)}]
