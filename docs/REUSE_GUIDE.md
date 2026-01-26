# Code Restructuring Complete: Configuration-Driven Architecture

## Summary

Your codebase has been restructured to be **fully configuration-driven**. All business logic in LangGraph is now completely separated from configuration, allowing you to reuse the same code with different MCP servers, tools, and prompts without changing any code.

## What Changed

### 1. New Configuration System

**Location:** `/config/` directory (root level)

Three configuration files control all behavior:

- **`config/mcp.yaml`** - Define your MCP server and available tools
- **`config/prompts.yaml`** - Define workflows with system prompts
- **`config/settings.yaml`** - Configure LLM, workflow settings, UI options

### 2. New Configuration Loader

**File:** `src/langgraphagenticai/config/config_loader.py`

Provides `ConfigLoader` class to load and validate all configurations:

```python
from src.langgraphagenticai.config.config_loader import get_config

config = get_config()
mcp_url = config.get_mcp_url()
workflows = config.get_workflows()
llm_model = config.get_llm_model()
```

### 3. Updated Core Components

All core components now use configuration:

| Component | Change |
|-----------|--------|
| `graph_builder.py` | Reads prompts from `config/prompts.yaml` instead of hardcoded `prompts.py` |
| `main.py` | Loads config and passes to all components |
| `cli_orchestrator.py` | Uses workflow names and messages from config |
| `ui_orchestrator.py` | Uses workflow list from config for UI selection |
| `prompts.py` | Deprecated - now just compatibility wrapper pointing to config |

### 4. Example Configurations

**Location:** `config/examples/`

Pre-made examples for different domains:

- **AWS Security Auditor** - `mcp_aws.yaml`, `prompts_aws.yaml`
- **Docker Container Scanner** - `mcp_docker.yaml`, `prompts_docker.yaml`

## How to Use with Different Domains

### Example 1: Switch to AWS Auditor

```bash
cd /path/to/istio-genai-new-working

# Backup current Kubernetes config (optional)
cp config/mcp.yaml config/mcp.yaml.backup
cp config/prompts.yaml config/prompts.yaml.backup

# Use AWS example
cp config/examples/mcp_aws.yaml config/mcp.yaml
cp config/examples/prompts_aws.yaml config/prompts.yaml

# Run AWS auditor (no code changes needed!)
python -m src.langgraphagenticai.main --no-ui aws_auditor
```

### Example 2: Create Your Own Configuration

1. Create `config/mcp.yaml` with your MCP server:
   ```yaml
   server:
     host: "your-server"
     port: 5001
   tools:
     - name: "your_tool"
       description: "What it does"
   ```

2. Create `config/prompts.yaml` with your workflows:
   ```yaml
   workflows:
     your_workflow:
       name: "Your Workflow"
       system_prompt: |
         You are a...
         AVAILABLE TOOLS: [list]
   ```

3. Run (no code changes!):
   ```bash
   python -m src.langgraphagenticai.main --no-ui your_workflow
   ```

## Directory Structure

```
istio-genai-new-working/
├── config/                          # ← ALL CONFIGURATION HERE
│   ├── mcp.yaml                    # MCP server & tools
│   ├── prompts.yaml                # Workflows & prompts
│   ├── settings.yaml               # LLM & workflow settings
│   └── examples/                   # Example configurations
│       ├── mcp_aws.yaml
│       ├── prompts_aws.yaml
│       ├── mcp_docker.yaml
│       ├── prompts_docker.yaml
│       └── README.md
│
├── CONFIG_GUIDE.md                 # How to customize configurations
├── README.md                        # Project overview
├── REUSE_GUIDE.md                  # This file
│
└── src/langgraphagenticai/         # ← CORE LOGIC (NO CHANGES NEEDED)
    ├── graph/
    │   └── graph_builder.py        # Reads from config/prompts.yaml
    ├── core/
    │   ├── cli_orchestrator.py
    │   ├── ui_orchestrator.py
    │   └── ...
    ├── config/
    │   └── config_loader.py        # Loads configuration
    ├── main.py                     # Entry point
    └── ...
```

## Key Benefits

✅ **Code Reusability** - Same LangGraph logic works with any MCP server
✅ **No Code Changes** - Switch domains by just copying config files
✅ **Easy Customization** - Just edit YAML files
✅ **Version Control** - Track config changes separately
✅ **Quick Testing** - Try different configurations instantly
✅ **Team Collaboration** - Share configs without merging code

## Supported Use Cases

### Currently Included
- Kubernetes Zero Trust Auditor
- Kubernetes Zero Trust Creator (deployment)

### Examples Provided
- AWS Security Auditor (2+ workflows)
- Docker Container Scanner (2+ workflows)

### Easy to Add
- GCP Cloud Security
- Azure Infrastructure Audit
- Terraform Compliance Check
- Database Security
- API Security Analysis
- Custom business logic

**No code changes needed for any of these!**

## How It Works

### Before (Hardcoded)
```python
# Old way - had to change code
AUDITOR_PROMPT = """hardcoded prompt"""
CREATOR_PROMPT = """hardcoded prompt"""

# Only supported 2 fixed workflows
def setup_graph(usecase):
    if usecase == "Auditor":
        return build_auditor_graph()
    elif usecase == "Creator":
        return build_creator_graph()
```

### After (Configuration-Driven)
```python
# New way - just configuration
config = get_config()
system_prompt = config.get_workflow_system_prompt("any_workflow_id")
graph = await graph_builder.build_graph("any_workflow_id")

# Supports unlimited workflows - just add to config
```

## Configuration Options

### In `config/mcp.yaml`
- MCP server host/port
- List of available tools
- Tool parameters and descriptions

### In `config/prompts.yaml`
- Define unlimited workflows
- System prompts for each workflow
- User-facing messages

### In `config/settings.yaml`
- LLM provider and model
- Workflow settings (max events, early stopping)
- UI options (what panels to show)
- CLI options (output formatting)

## Testing Your Configuration

```bash
# Validate configuration
python3 -c "
from src.langgraphagenticai.config.config_loader import get_config
config = get_config()
config.print_summary()
validation = config.validate()
print(f'Valid: {validation[\"valid\"]}')
"

# Run workflow in CLI
python -m src.langgraphagenticai.main --no-ui workflow_id

# Run with Streamlit UI
python -m src.langgraphagenticai.main
```

## Next Steps

1. **Read CONFIG_GUIDE.md** - Learn detailed configuration options
2. **Check config/examples/README.md** - See example setups
3. **Try an example** - Copy AWS or Docker config to test
4. **Create your own** - Define your first custom workflow
5. **Share configs** - Version control your configurations

## Documentation

- **CONFIG_GUIDE.md** - Complete configuration reference
- **config/examples/README.md** - Example configurations and how to use them
- **Original docs** - All existing documentation still applies

## Questions?

See the documentation files:
- `CONFIG_GUIDE.md` - Configuration details
- `config/examples/README.md` - Working examples
- `config/mcp.yaml` - Tool definitions
- `config/prompts.yaml` - Workflow definitions

## Summary

Your codebase is now **production-ready for reuse**. The same core logic (LangGraph, state management, execution) works with:

- Any MCP server
- Any set of tools
- Any custom prompts
- Any workflow logic

Just update `config/` files and you're done! 🚀
