
import requests
import os
import json

# Configuration
INVOKE_URL = "https://integrate.api.nvidia.com/v1/chat/completions"
SYSTEM_PROMPT_PATH = r"apps\worker\cognitive\system_prompt.md"
API_KEY = os.getenv("NVIDIA_API_KEY")

if not API_KEY:
    raise ValueError("NVIDIA_API_KEY environment variable is not set")

# 1. Read the official system prompt template from file
# This ensures your script is always using the latest version from the codebase
try:
    with open(SYSTEM_PROMPT_PATH, "r", encoding="utf-8") as f:
        system_prompt_template = f.read()
except FileNotFoundError:
    print(f"Warning: Could not find {SYSTEM_PROMPT_PATH}, using fallback text...")
    # You can paste the raw text here as a fallback if needed
    raise

# 2. Define the runtime variables (Context)
# These MUST be replaced for the agent to work correctly
variables = {
    "MISSION_OBJECTIVE": "Identify potential vulnerabilities in the payment gateway.",
    "TARGET_SCOPE": "*.example.com\n  - api.example.com",
    "SCOPE_EXCLUSIONS": "do-not-scan.example.com",
    "STEPS_BUDGET": "10",
    "COST_BUDGET": "5.00",
    "TIME_BUDGET": "30m",
    "SESSION_CONTEXT": "[]", # Or previous history
    "TOOL_DEFINITIONS": "- subfinder\n- nuclei\n- httpx" 
}

# 3. Perform Template Substitution
system_prompt = system_prompt_template
for key, value in variables.items():
    # Replace {{KEY}} with value
    system_prompt = system_prompt.replace(f"{{{{{key}}}}}", value)

# 4. Construct Payload
payload = {
  "model": "mistralai/mistral-large-3-675b-instruct-2512", # Or your preferred model
  "messages": [
      {
          "role": "system", # Best practice: use 'system' role for system prompts
          "content": system_prompt
      },
      {
          "role": "user",
          "content": "Start the reconnaissance mission."
      }
  ],
  "max_tokens": 2048,
  "temperature": 0.15,
  "stream": True
}

headers = {
  "Authorization": f"Bearer {API_KEY}",
  "Accept": "text/event-stream",
  "Content-Type": "application/json"
}

# 5. Make Request
print("Sending request to NVIDIA API...")
response = requests.post(INVOKE_URL, headers=headers, json=payload, stream=True)

if response.status_code != 200:
    print(f"Error: {response.status_code} - {response.text}")
else:
    for line in response.iter_lines():
        if line:
            line_text = line.decode("utf-8")
            # Parse SSE format "data: {...}"
            if line_text.startswith("data: ") and line_text != "data: [DONE]":
                try:
                    data = json.loads(line_text[6:])
                    if "choices" in data:
                        content = data["choices"][0]["delta"].get("content", "")
                        print(content, end="", flush=True)
                except json.JSONDecodeError:
                    pass
