# Agentic AI LangGraph Application

Configuration-driven LangGraph application for building reusable AI agents that work with any MCP server.

## 🚀 Quick Start

### Run Quick Security Audit
```bash
python -m src.langgraphagenticai.main --no-ui auditor
```

### Run Comprehensive Security & Compliance Analysis
```bash
python -m src.langgraphagenticai.main --no-ui comprehensive_auditor
```

### Run with Streamlit UI
```bash
python -m src.langgraphagenticai.main
```

### Switch to Different Domain (No Code Changes!)
```bash
# Switch to AWS Auditor
cp config/examples/mcp_aws.yaml config/mcp.yaml
cp config/examples/prompts_aws.yaml config/prompts.yaml
python -m src.langgraphagenticai.main --no-ui aws_auditor

# Switch to Docker Scanner
cp config/examples/mcp_docker.yaml config/mcp.yaml
cp config/examples/prompts_docker.yaml config/prompts.yaml
python -m src.langgraphagenticai.main --no-ui docker_scanner
```

## 📋 What This Is

A **configuration-driven** LangGraph application that:
- ✅ Works with ANY MCP server
- ✅ Supports ANY set of tools
- ✅ Uses ANY custom prompts
- ✅ Requires NO code changes to switch domains

Just update `config/` files and it works with Kubernetes, AWS, Docker, custom tools, or any other domain.

## 📁 Project Structure

```
├── config/                      ← CUSTOMIZE THESE
│   ├── mcp.yaml                # MCP server + tools
│   ├── prompts.yaml            # Workflows + prompts
│   ├── settings.yaml           # LLM + settings
│   └── examples/               # Pre-made examples (AWS, Docker)
│
├── src/
│   └── langgraphagenticai/
│       ├── config/
│       │   └── config_loader.py    ← Loads YAML configs
│       ├── graph/
│       │   └── graph_builder.py    ← Builds graphs from config
│       ├── core/
│       │   ├── cli_orchestrator.py
│       │   ├── ui_orchestrator.py
│       │   └── ...
│       └── main.py                 ← Entry point
│
├── docs/                        ← DOCUMENTATION
│   ├── QUICKSTART_CONFIG.md        (30 seconds)
│   ├── CONFIG_GUIDE.md             (Complete reference)
│   ├── REUSE_GUIDE.md              (Reusability guide)
│   ├── CONFIG_INDEX.md             (Index & roadmap)
│   ├── ARCHITECTURE_REFACTORING.md (What changed)
│   ├── TROUBLESHOOTING_GUIDE.md    (Troubleshooting)
│   ├── RUN_INSTRUCTIONS.md         (How to run)
│   └── LANGCHAIN_*.md              (Educational)
│
├── README.md                    ← You are here
├── requirements.txt
├── pyproject.toml
└── K8/                          ← Kubernetes manifests

```

## 📖 Documentation

Start with one of these based on your need:

### 🏃 I Need 30 Seconds
Read: **[docs/QUICKSTART_CONFIG.md](docs/QUICKSTART_CONFIG.md)**
- One-page quick reference
- Common tasks
- Key files explained

### 🔧 I Need to Customize Configuration
Read: **[docs/CONFIG_GUIDE.md](docs/CONFIG_GUIDE.md)**
- Complete configuration reference
- All options explained
- Best practices
- Troubleshooting

### 🔄 I Want to Reuse with Different Domains
Read: **[docs/REUSE_GUIDE.md](docs/REUSE_GUIDE.md)**
- How code reusability works
- Step-by-step for each domain
- AWS, Docker, custom examples

### 📊 I Want to Understand Architecture
Read: **[docs/ARCHITECTURE_REFACTORING.md](docs/ARCHITECTURE_REFACTORING.md)**
- What changed and why
- Before/after comparison
- How configuration-driven works

### 💡 I Want to See Working Examples
Read: **[config/examples/README.md](config/examples/README.md)**
- AWS Security Auditor example
- Docker Container Scanner example
- How to switch between examples

### ❓ I Need Troubleshooting
Read: **[docs/TROUBLESHOOTING_GUIDE.md](docs/TROUBLESHOOTING_GUIDE.md)**
- Common issues and solutions
- Configuration validation
- Testing commands

### 🔍 I Want a Comprehensive Security Audit
Read: **[docs/COMPREHENSIVE_SECURITY_AUDIT.md](docs/COMPREHENSIVE_SECURITY_AUDIT.md)**
- Deep analysis of all namespaces
- Security posture, compliance, best practices
- Resource inventory and recommendations
- How to interpret findings

### 📖 I Want to Learn LangChain/LangGraph
Read: **[docs/LANGCHAIN_LANGGRAPH_GUIDE.md](docs/LANGCHAIN_LANGGRAPH_GUIDE.md)**
- LangChain concepts
- LangGraph state graphs
- How the application works

## ⚡ Configuration System

All configuration is in `config/` directory:

### config/mcp.yaml
Define MCP server and available tools:
```yaml
server:
  host: "localhost"
  port: 3001
tools:
  - name: "your_tool"
    description: "What it does"
```

### config/prompts.yaml
Define workflows with system prompts:
```yaml
workflows:
  your_workflow:
    name: "Display Name"
    system_prompt: |
      You are a...
      AVAILABLE TOOLS: [...]
```

### config/settings.yaml
Configure LLM, workflow behavior, UI options:
```yaml
llm:
  provider: "ollama"
  model: "mistral:latest"
workflow_settings:
  available_workflows:
    - id: "your_workflow"
      name: "Display Name"
      enabled: true
```

## 🧪 Testing

### Validate Configuration
```bash
python3 -c "
from src.langgraphagenticai.config.config_loader import get_config
config = get_config()
config.print_summary()
"
```

### Run CLI Mode
```bash
python -m src.langgraphagenticai.main --no-ui auditor
```

### Run Streamlit UI
```bash
python -m src.langgraphagenticai.main
```

## 🔄 Examples

### Example 1: Current (Kubernetes)
- Tools: kubectl_get, kubectl_describe, kubectl_apply, etc.
- Workflows: Auditor (analyze), Creator (deploy)

### Example 2: AWS (Pre-made)
```bash
cp config/examples/mcp_aws.yaml config/mcp.yaml
cp config/examples/prompts_aws.yaml config/prompts.yaml
python -m src.langgraphagenticai.main --no-ui aws_auditor
```
- Tools: aws_list_buckets, aws_describe_security_groups, etc.
- Workflows: AWS Auditor, Compliance Checker

### Example 3: Docker (Pre-made)
```bash
cp config/examples/mcp_docker.yaml config/mcp.yaml
cp config/examples/prompts_docker.yaml config/prompts.yaml
python -m src.langgraphagenticai.main --no-ui docker_scanner
```
- Tools: docker_scan_image, docker_check_vulnerabilities, etc.
- Workflows: Container Scanner, Dockerfile Linter

### Example 4: Custom Domain
1. Create `config/mcp.yaml` for your MCP server
2. Create `config/prompts.yaml` for your workflows
3. Run: `python -m src.langgraphagenticai.main --no-ui your_workflow`
4. **No code changes needed!**

## 🎯 Key Features

✅ **Configuration-Driven** - All business logic in YAML
✅ **Reusable Code** - Same LangGraph logic works anywhere
✅ **Multiple Domains** - Kubernetes, AWS, Docker, custom
✅ **Easy Customization** - Edit YAML files
✅ **Well Documented** - Complete guides provided
✅ **Production Ready** - Tested and validated
✅ **CLI & UI** - Both modes supported
✅ **Live Progress** - Real-time execution logging

## 🛠️ Setup

### Prerequisites
- Python 3.8+
- Ollama (or other LLM provider)
- MCP server running
- Kubernetes cluster (for default Auditor) or other tools

### Install
```bash
pip install -r requirements.txt
```

### Configure
1. Update `config/mcp.yaml` for your MCP server
2. Update `config/prompts.yaml` for your workflows
3. Update `config/settings.yaml` for LLM and settings

### Run
```bash
python -m src.langgraphagenticai.main
```

## 📚 Documentation Map

| Document | Purpose | Read Time |
|----------|---------|-----------|
| [QUICKSTART_CONFIG.md](docs/QUICKSTART_CONFIG.md) | Quick reference & common tasks | 2 min |
| [CONFIG_GUIDE.md](docs/CONFIG_GUIDE.md) | Complete configuration reference | 10 min |
| [CONFIG_INDEX.md](docs/CONFIG_INDEX.md) | Index & file structure overview | 5 min |
| [REUSE_GUIDE.md](docs/REUSE_GUIDE.md) | How to reuse with different domains | 10 min |
| [ARCHITECTURE_REFACTORING.md](docs/ARCHITECTURE_REFACTORING.md) | What changed in refactoring | 10 min |
| [RUN_INSTRUCTIONS.md](docs/RUN_INSTRUCTIONS.md) | Detailed run instructions | 5 min |
| [TROUBLESHOOTING_GUIDE.md](docs/TROUBLESHOOTING_GUIDE.md) | Common issues & solutions | 5 min |
| [LANGCHAIN_LANGGRAPH_GUIDE.md](docs/LANGCHAIN_LANGGRAPH_GUIDE.md) | LangChain/LangGraph concepts | 15 min |
| [LANGCHAIN_CONCEPTS.md](docs/LANGCHAIN_CONCEPTS.md) | LangChain details | 10 min |
| [LANGCHAIN_INTERACTIVE_GUIDE.md](docs/LANGCHAIN_INTERACTIVE_GUIDE.md) | Interactive learning | 15 min |

## 🚀 Next Steps

1. **Read [docs/QUICKSTART_CONFIG.md](docs/QUICKSTART_CONFIG.md)** (30 seconds)
2. **Try an example:**
   ```bash
   cp config/examples/mcp_aws.yaml config/mcp.yaml
   python -m src.langgraphagenticai.main --no-ui
   ```
3. **Create your own configuration** for your domain
4. **Share configurations** across your team

## 💡 Key Insight

The same core LangGraph logic (state, nodes, edges, execution) works with:
- Different MCP servers
- Different tools
- Different prompts
- Different workflows
- Different domains

**Just change configuration files - no code changes needed!**

## 📞 Support

- **Configuration Issues** → See [docs/CONFIG_GUIDE.md](docs/CONFIG_GUIDE.md)
- **Reusability Questions** → See [docs/REUSE_GUIDE.md](docs/REUSE_GUIDE.md)
- **Examples** → See [config/examples/README.md](config/examples/README.md)
- **Troubleshooting** → See [docs/TROUBLESHOOTING_GUIDE.md](docs/TROUBLESHOOTING_GUIDE.md)
- **Architecture** → See [docs/ARCHITECTURE_REFACTORING.md](docs/ARCHITECTURE_REFACTORING.md)

---

**Your code is now fully reusable across different domains!** 🚀

The same LangGraph application works with any MCP server, any tools, and any custom prompts.
