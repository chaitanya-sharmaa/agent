# Configuration Guide - Making Code Reusable

This application is now fully configuration-driven, allowing you to reuse all the LangGraph logic with different MCP servers and custom workflows without changing any code.

## Architecture Overview

```
Your Application (langgraphagenticai/)
├── config/                          # ← Configuration files (CUSTOMIZE THESE)
│   ├── mcp.yaml                    # MCP server connection & tools
│   ├── prompts.yaml                # LLM prompts for workflows
│   └── settings.yaml               # Workflow & LLM settings
│
└── src/langgraphagenticai/         # ← Core logic (NO CHANGES NEEDED)
    ├── graph/
    │   └── graph_builder.py        # Reads config/prompts.yaml
    ├── core/
    │   ├── cli_orchestrator.py     # Reads config/settings.yaml
    │   └── ui_orchestrator.py      # Reads config/settings.yaml
    ├── config/
    │   └── config_loader.py        # Loads all configuration
    └── main.py                     # Entry point (reads config)
```

## How to Adapt for Different Use Cases

### Step 1: Update `config/mcp.yaml`

Define your MCP server and available tools:

```yaml
server:
  host: "your-server.com"
  port: 3001
  
tools:
  - name: "your_tool_name"
    description: "What it does"
    parameters:
      - name: "param_name"
        type: "string"
        required: true
```

### Step 2: Update `config/prompts.yaml`

Define workflows with system prompts:

```yaml
workflows:
  my_workflow:
    name: "My Custom Workflow"
    description: "What this workflow does"
    system_prompt: |
      You are a specialized AI for...
      AVAILABLE TOOLS: [list your tools]
      RULES: [specify what to do]
    user_prompts:
      start: "User message to trigger this workflow"
```

### Step 3: Update `config/settings.yaml`

Configure workflow behavior:

```yaml
workflow_settings:
  available_workflows:
    - id: "my_workflow"
      name: "My Custom Workflow"
      enabled: true

llm:
  provider: "ollama"  # or "openai", "anthropic", etc.
  model: "your-model:latest"
  
graph:
  max_events: 200
```

### Step 4: (Optional) Add Custom Analyzer

If you need custom analysis logic, extend `ZeroTrustAnalyzer`:

```python
from src.langgraphagenticai.utils.zero_trust_analyzer import ZeroTrustAnalyzer

class MyCustomAnalyzer(ZeroTrustAnalyzer):
    def analyze_and_generate_report(self, tool_results):
        # Your custom analysis logic
        pass
```

## Example: Using with Different MCP Server

### Example 1: AWS Security Auditor

**config/mcp.yaml:**
```yaml
server:
  host: "localhost"
  port: 5001
  
tools:
  - name: "aws_list_buckets"
  - name: "aws_check_iam_policies"
  - name: "aws_list_security_groups"
  - name: "aws_describe_instances"
```

**config/prompts.yaml:**
```yaml
workflows:
  aws_auditor:
    name: "AWS Security Auditor"
    system_prompt: |
      You are an AWS security auditor.
      Use aws_list_buckets, aws_check_iam_policies, etc.
      Generate a security report.
```

**No code changes needed!** The same `graph_builder.py` and `main.py` work automatically.

### Example 2: Docker Container Scanner

**config/mcp.yaml:**
```yaml
server:
  host: "localhost"
  port: 5002
  
tools:
  - name: "docker_list_images"
  - name: "docker_scan_image"
  - name: "docker_get_vulnerabilities"
```

**config/prompts.yaml:**
```yaml
workflows:
  docker_scanner:
    name: "Docker Security Scanner"
    system_prompt: |
      Scan Docker images for vulnerabilities.
      Use docker_scan_image for each image.
```

**Again, no code changes!**

## Configuration File Reference

### mcp.yaml
- `server.host` - MCP server hostname
- `server.port` - MCP server port
- `server.timeout_seconds` - Request timeout
- `server.retry_attempts` - Retry count on failure
- `tools` - List of available tools with parameters

### prompts.yaml
- `workflows.<id>.name` - Display name
- `workflows.<id>.description` - Description
- `workflows.<id>.system_prompt` - LLM system prompt
- `workflows.<id>.user_prompts` - User-facing messages
- `custom_workflows` - Add new workflows here

### settings.yaml
- `workflow_settings.available_workflows` - Which workflows to show
- `llm.provider` - LLM provider (ollama, openai, etc.)
- `llm.model` - Model name
- `llm.endpoint` - Model endpoint URL
- `graph.max_events` - Max graph iterations
- `graph.early_stop` - Stopping conditions per workflow
- `ui.port` - Streamlit port
- `ui.panels` - Which UI panels to show

## Using the Configuration Loader in Code

```python
from src.langgraphagenticai.config.config_loader import get_config

config = get_config()

# Get configurations
mcp_url = config.get_mcp_url()
tools = config.get_mcp_tools()
workflow = config.get_workflow("auditor")
system_prompt = config.get_workflow_system_prompt("auditor")
llm_model = config.get_llm_model()

# Validate configuration
validation = config.validate()
config.print_summary()
```

## Running with Custom Configuration

```bash
# Default (uses config/ directory)
python -m src.langgraphagenticai.main --no-ui auditor

# With custom config directory
CONFIG_DIR=/path/to/custom/config python -m src.langgraphagenticai.main --no-ui
```

## Best Practices

1. **Keep configuration in `config/` directory** - Makes it easy to version control and switch between use cases
2. **Never hardcode prompts or tool names** - Always use configuration
3. **Document your workflows** - Add descriptions to each workflow in `prompts.yaml`
4. **Validate before running** - Call `config.validate()` to check configuration
5. **Use workflow IDs consistently** - Same ID in `prompts.yaml` and `settings.yaml`

## Troubleshooting

**"Config file not found"**
- Ensure `config/mcp.yaml`, `config/prompts.yaml`, and `config/settings.yaml` exist
- Run from project root directory

**"Workflow not found"**
- Check that workflow ID in `prompts.yaml` matches usage in code
- Verify workflow is listed in `settings.yaml` `available_workflows`

**LLM not responding**
- Check `config/settings.yaml` LLM settings
- Verify endpoint is running (`curl http://localhost:11434`)
- Check model name is correct (`ollama list`)

**MCP tools not available**
- Verify MCP server is running
- Check `config/mcp.yaml` server host/port
- List available tools: `curl http://localhost:3001/tools`

