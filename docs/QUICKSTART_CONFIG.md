# Quick Reference: Configuration-Driven Architecture

## 30-Second Overview

Your code now has **zero hardcoded configuration**. Everything is in `config/`:

```
config/mcp.yaml      ← MCP server + tools
config/prompts.yaml  ← Workflows + prompts  
config/settings.yaml ← LLM + settings
```

Change these files → app works with different domains (AWS, Docker, custom, etc.)

## Common Tasks

### 1. Run Current Auditor
```bash
python -m src.langgraphagenticai.main --no-ui
```

### 2. Switch to AWS Auditor
```bash
cp config/examples/mcp_aws.yaml config/mcp.yaml
cp config/examples/prompts_aws.yaml config/prompts.yaml
python -m src.langgraphagenticai.main --no-ui aws_auditor
```

### 3. Add New Workflow
Edit `config/prompts.yaml`:
```yaml
workflows:
  my_workflow:           # workflow ID
    name: "My Workflow"  # display name
    system_prompt: |
      You are a...
      AVAILABLE TOOLS: [list]
```

### 4. Add New Tool
Edit `config/mcp.yaml`:
```yaml
tools:
  - name: "my_tool"
    description: "Does something"
    parameters:
      - name: "param"
        type: "string"
        required: true
```

### 5. Change LLM Model
Edit `config/settings.yaml`:
```yaml
llm:
  model: "different-model:latest"
```

## File Purposes

| File | Purpose | Example |
|------|---------|---------|
| `config/mcp.yaml` | Define MCP server & tools | `server.host`, `tools: [...]` |
| `config/prompts.yaml` | Define workflows & prompts | `workflows: {auditor: {...}}` |
| `config/settings.yaml` | LLM, workflow, UI settings | `llm.model`, `ui.port` |

## Code That Uses Configuration

```python
from src.langgraphagenticai.config.config_loader import get_config

config = get_config()

# Get MCP server info
url = config.get_mcp_url()
tools = config.get_mcp_tools()

# Get workflows
workflows = config.get_workflows()
prompt = config.get_workflow_system_prompt("auditor")

# Get LLM config
model = config.get_llm_model()

# Validate
validation = config.validate()
```

## Structure

```
Your App (langgraphagenticai/)
    ↓
config/ ← CUSTOMIZE HERE
    ├── mcp.yaml (MCP server + tools)
    ├── prompts.yaml (workflows + prompts)
    ├── settings.yaml (LLM + settings)
    └── examples/ (AWS, Docker examples)
    ↓
src/langgraphagenticai/ ← NO CHANGES NEEDED
    ├── config/config_loader.py (loads config)
    ├── graph/graph_builder.py (uses config)
    ├── main.py (entry point)
    └── core/ (orchestrators)
```

## Available Examples

```bash
# AWS Auditor
cp config/examples/mcp_aws.yaml config/mcp.yaml
cp config/examples/prompts_aws.yaml config/prompts.yaml

# Docker Scanner
cp config/examples/mcp_docker.yaml config/mcp.yaml
cp config/examples/prompts_docker.yaml config/prompts.yaml
```

## Validation

```bash
python3 -c "
from src.langgraphagenticai.config.config_loader import get_config
config = get_config()
config.print_summary()
"
```

## Tips

✅ Keep configs in version control
✅ Use examples/ as templates  
✅ Validate before running
✅ Backup current config before switching
✅ Add descriptions to workflows

## Real Example: Kubernetes → AWS

```bash
# 1. Backup current K8s config
cp config/mcp.yaml config/mcp.k8s
cp config/prompts.yaml config/prompts.k8s

# 2. Switch to AWS
cp config/examples/mcp_aws.yaml config/mcp.yaml
cp config/examples/prompts_aws.yaml config/prompts.yaml

# 3. Run (exactly same code!)
python -m src.langgraphagenticai.main --no-ui aws_auditor

# 4. Switch back
cp config/mcp.k8s config/mcp.yaml
cp config/prompts.k8s config/prompts.yaml
```

## Core Insight

The **same LangGraph logic** (state, nodes, edges, execution) now works with:
- Any MCP server
- Any tools
- Any prompts
- Any domain

Because configuration is completely separated from code.

**No code changes needed to reuse with different systems!** 🚀

---

See `CONFIG_GUIDE.md` for complete reference
See `config/examples/README.md` for working examples
