# Configuration-Driven Architecture: Complete Index

## 📋 What This Means

Your application is now **fully configuration-driven**. The same LangGraph logic works with ANY MCP server, ANY tools, and ANY custom prompts without changing code. Just update YAML files in the `config/` directory.

## 🚀 Quick Start (30 seconds)

**Current Kubernetes Setup:**
```bash
python -m src.langgraphagenticai.main --no-ui auditor
```

**Switch to AWS (no code changes!):**
```bash
cp config/examples/mcp_aws.yaml config/mcp.yaml
cp config/examples/prompts_aws.yaml config/prompts.yaml
python -m src.langgraphagenticai.main --no-ui aws_auditor
```

**Create Your Own:**
```bash
# Edit these 3 files:
config/mcp.yaml        # Define MCP server + tools
config/prompts.yaml    # Define workflows + prompts
config/settings.yaml   # Configure LLM + settings

# Then run (no code changes!):
python -m src.langgraphagenticai.main --no-ui your_workflow
```

## 📁 Configuration Files

### Root Level: `/config/`

| File | Purpose | Edit This For |
|------|---------|---------|
| **mcp.yaml** | MCP server connection & tools | Different MCP server / tools |
| **prompts.yaml** | Workflow definitions & prompts | New workflows / custom prompts |
| **settings.yaml** | LLM, workflow, UI settings | Different LLM / port / max events |
| **examples/** | Pre-made configurations | Switching to AWS / Docker |

## 📚 Documentation Guide

Start here based on your need:

### 🏃 I Need 30 Seconds
**Read:** `QUICKSTART_CONFIG.md`
- One-page quick reference
- Common tasks
- Key files explained

### 🔧 I Need to Customize Configuration
**Read:** `CONFIG_GUIDE.md`
- Complete reference for all config options
- How to use the configuration loader
- Best practices
- Troubleshooting

### 🔄 I Want to Reuse with Different Domains
**Read:** `REUSE_GUIDE.md`
- How code reusability works
- Examples for AWS, Docker, custom
- Step-by-step for each domain
- Supporting new MCP servers

### 💡 I Want to See Working Examples
**Read:** `config/examples/README.md`
- AWS Security Auditor (complete example)
- Docker Container Scanner (complete example)
- How to switch between examples
- How to create your own example

### 📊 I Want to Understand Architecture Changes
**Read:** `ARCHITECTURE_REFACTORING.md`
- What was changed and why
- Before/after comparison
- New file structure
- How configuration-driven works

## 📂 File Structure

```
project-root/
│
├── 📁 config/                          ← CUSTOMIZE THESE
│   ├── 📄 mcp.yaml                    # MCP server + tools
│   ├── 📄 prompts.yaml                # Workflows + prompts
│   ├── 📄 settings.yaml               # LLM + settings
│   │
│   └── 📁 examples/                   # Pre-made examples
│       ├── 📄 mcp_aws.yaml            # AWS example
│       ├── 📄 prompts_aws.yaml
│       ├── 📄 mcp_docker.yaml         # Docker example
│       ├── 📄 prompts_docker.yaml
│       └── 📄 README.md               # How to use examples
│
├── 📄 QUICKSTART_CONFIG.md            ← START HERE (30 sec)
├── 📄 CONFIG_GUIDE.md                 # Configuration reference
├── 📄 REUSE_GUIDE.md                  # Reusability guide
├── 📄 ARCHITECTURE_REFACTORING.md     # What changed
│
└── 📁 src/langgraphagenticai/        ← CORE LOGIC (don't change)
    ├── 📁 config/
    │   └── 📄 config_loader.py        # NEW: Loads YAML configs
    │
    ├── 📁 graph/
    │   └── 📄 graph_builder.py        # UPDATED: Reads from config
    │
    ├── 📄 main.py                     # UPDATED: Loads config
    │
    └── [other modules unchanged...]
```

## 🎯 Configuration Files Explained

### config/mcp.yaml
```yaml
server:
  host: "localhost"              # MCP server hostname
  port: 3001                     # MCP server port
  timeout_seconds: 30
  retry_attempts: 3

tools:                           # Available tools
  - name: "kubectl_get"
    description: "..."
    parameters:
      - name: "resourceType"
        type: "string"
        required: true
```

**Edit this when:** Using different MCP server / tools

### config/prompts.yaml
```yaml
workflows:
  auditor:                       # Workflow ID
    name: "Zero Trust Auditor"   # Display name
    description: "..."           # Description
    system_prompt: |             # LLM system prompt
      You are a...
      AVAILABLE TOOLS: [...]
      RULES: [...]
    user_prompts:
      start: "User message..."   # Trigger message
```

**Edit this when:** Adding workflows / custom prompts

### config/settings.yaml
```yaml
workflow_settings:
  available_workflows:           # Which workflows show in UI
    - id: "auditor"
      name: "Zero Trust Auditor"
      enabled: true

llm:
  provider: "ollama"             # LLM provider
  model: "mistral:latest"        # Model name
  endpoint: "http://localhost:11434"

graph:
  max_events: 200                # Max iterations
  early_stop:                    # Stop conditions
    auditor_probes: [...]        # When to stop auditor

ui:
  port: 8501                     # Streamlit port
  panels:                        # Which panels to show
    metrics: true
    live_logs: true
```

**Edit this when:** Different LLM / changing max events / port

## 🔌 How Configuration Loader Works

```python
from src.langgraphagenticai.config.config_loader import get_config

# Load configuration
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
config.print_summary()
```

## ✅ Workflow Examples

### Example 1: Kubernetes Auditor (Current)
- **MCP Server:** Kubernetes API
- **Tools:** kubectl_get, kubectl_describe, etc.
- **Workflows:** Auditor, Creator

### Example 2: AWS Auditor (Pre-made)
```bash
cp config/examples/mcp_aws.yaml config/mcp.yaml
cp config/examples/prompts_aws.yaml config/prompts.yaml
python -m src.langgraphagenticai.main --no-ui aws_auditor
```
- **MCP Server:** AWS MCP server
- **Tools:** aws_list_buckets, aws_describe_security_groups, etc.
- **Workflows:** aws_auditor, aws_compliance_checker

### Example 3: Docker Scanner (Pre-made)
```bash
cp config/examples/mcp_docker.yaml config/mcp.yaml
cp config/examples/prompts_docker.yaml config/prompts.yaml
python -m src.langgraphagenticai.main --no-ui docker_scanner
```
- **MCP Server:** Docker MCP server
- **Tools:** docker_scan_image, docker_check_vulnerabilities, etc.
- **Workflows:** docker_scanner, dockerfile_linter

### Example 4: Custom (Your Domain)
```bash
# Create your own config/mcp.yaml
# Create your own config/prompts.yaml
# Run with no code changes:
python -m src.langgraphagenticai.main --no-ui your_workflow
```

## 🔄 Switching Between Domains

```bash
# Backup current (optional)
cp config/mcp.yaml config/mcp.k8s
cp config/prompts.yaml config/prompts.k8s

# Try AWS
cp config/examples/mcp_aws.yaml config/mcp.yaml
cp config/examples/prompts_aws.yaml config/prompts.yaml
python -m src.langgraphagenticai.main --no-ui aws_auditor

# Switch back
cp config/mcp.k8s config/mcp.yaml
cp config/prompts.k8s config/prompts.yaml
python -m src.langgraphagenticai.main --no-ui auditor
```

## 🧪 Testing Configuration

```bash
# Quick validation
python3 -c "
from src.langgraphagenticai.config.config_loader import get_config
config = get_config()
config.print_summary()
"

# Run in CLI
python -m src.langgraphagenticai.main --no-ui

# Run in Streamlit UI
python -m src.langgraphagenticai.main
```

## 📖 Reading Order

1. **First (30 seconds):** `QUICKSTART_CONFIG.md`
   - Get overview
   - Learn key concepts
   - See quick reference

2. **Then (5 minutes):** `config/examples/README.md`
   - Understand working examples
   - Try switching to AWS or Docker

3. **For Details (10 minutes):** `CONFIG_GUIDE.md`
   - All configuration options
   - How to use configuration loader
   - Best practices

4. **For Reuse (10 minutes):** `REUSE_GUIDE.md`
   - How to create own configuration
   - Different domain examples
   - Step-by-step instructions

5. **For Architecture:** `ARCHITECTURE_REFACTORING.md`
   - What changed
   - Why it changed
   - How it works

## 🎓 Key Concepts

### Configuration-Driven
Code doesn't hardcode business logic. Configuration files define:
- What MCP server to use
- What tools are available
- What workflows exist
- What prompts to use

**Benefit:** Same code works with ANY configuration

### Reusability
The same LangGraph logic (graph builder, state management, execution) works with:
- Kubernetes tools
- AWS tools
- Docker tools
- Custom tools
- Any domain

**Benefit:** No code changes to switch domains

### Separation of Concerns
- **Code** - How to execute (LangGraph logic)
- **Configuration** - What to execute (YAML files)

**Benefit:** Teams can work on different areas without conflicts

## 🚀 Next Steps

1. **Try it:** `cp config/examples/mcp_aws.yaml config/mcp.yaml && python -m src.langgraphagenticai.main --no-ui`
2. **Read:** `QUICKSTART_CONFIG.md` (30 seconds)
3. **Create:** Your own `config/mcp.yaml` for your domain
4. **Share:** Version control your configurations
5. **Extend:** Add more workflows to `config/prompts.yaml`

## 💡 Pro Tips

✅ **Backup configuration** before switching
✅ **Validate configuration** before running
✅ **Version control configs** separately from code
✅ **Share configs** across teams
✅ **Use examples** as templates
✅ **Document your workflows** in prompts.yaml

## ❓ FAQ

**Q: Where are the prompts now?**
A: In `config/prompts.yaml` instead of `src/langgraphagenticai/prompts.py`

**Q: Do I need to change code to use different tools?**
A: No! Just update `config/mcp.yaml` and `config/prompts.yaml`

**Q: Can I use this with different MCP servers?**
A: Yes! Update `config/mcp.yaml` with your server details and tools

**Q: How do I add a new workflow?**
A: Add it to `config/prompts.yaml` - no code changes needed

**Q: What if I need custom logic?**
A: Create custom analyzers/orchestrators as needed, but configuration-driven core stays the same

## 📞 Support

- **Configuration Issues:** See `CONFIG_GUIDE.md`
- **Reusability Questions:** See `REUSE_GUIDE.md`
- **Examples:** See `config/examples/README.md`
- **Architecture:** See `ARCHITECTURE_REFACTORING.md`

---

**Your application is now production-ready for reuse and distribution!** 🚀

The same core logic works with ANY MCP server, ANY tools, and ANY custom prompts.
Only configuration changes needed!
