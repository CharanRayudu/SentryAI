from temporalio import activity
import docker
import asyncio

# Initialize Docker Client (connects to the socket mounted in docker-compose)
try:
    docker_client = docker.from_env()
except Exception as e:
    print(f"Warning: Docker client failed to initialize: {e}")
    docker_client = None

@activity.defn
async def run_tool_scan(params: dict) -> list:
    tool = params.get("tool")
    target = params.get("target")
    args = params.get("args", "")
    
    activity.logger.info(f"Running {tool} on {target} with args {args}")
    
    if not docker_client:
        return [{"error": "Docker socket not connected. Cannot run scan."}]

    # Sandwich Strategy: Ephemeral Container
    # We pull the image first (this might take time on first run)
    image_map = {
        "subfinder": "projectdiscovery/subfinder:latest",
        "nuclei": "projectdiscovery/nuclei:latest",
        "naabu": "projectdiscovery/naabu:latest"
    }
    
    image = image_map.get(tool)
    if not image:
        return [{"error": f"Unknown tool: {tool}"}]

    try:
        # Run container
        # Equivalent to: docker run --rm projectdiscovery/subfinder -d target.com
        cmd = f"-d {target} {args}"
        if tool == "nuclei":
            cmd = f"-u {target} {args}"
            
        logs = docker_client.containers.run(
            image,
            command=cmd,
            remove=True,
            network_mode="host", # Caution: Phase 2 should lock this down
            stderr=True,
            stdout=True
        )
        
        output = logs.decode('utf-8')
        # TODO: Parse output into JSON/Graph Nodes
        return [{"raw": output}]
        
    except Exception as e:
        activity.logger.error(f"Scan failed: {e}")
        return [{"error": str(e)}]
