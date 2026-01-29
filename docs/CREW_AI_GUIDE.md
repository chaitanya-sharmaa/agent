# Crew AI Integration Guide

This guide explains how to use **Crew AI** as an alternative execution engine to the default LangGraph-based orchestration.

## Overview

The agentic framework supports two execution engines:

1. **LangGraph** (default, recommended): State-based directed acyclic graphs with explicit node transitions
2. **Crew AI** (experimental): Multi-agent orchestration with dynamic agent collaboration

Both engines use the same MCP (Model Context Protocol) tools for Kubernetes operations, providing a unified toolset while allowing different orchestration patterns.

## Quick Start

### Enable Crew AI

Edit `config/settings.yaml`:

```yaml
execution_engine: "crew_ai"
```

Then run your workflow:

```bash
python run_workflow_diagnostic.py
```

Or from the CLI:

```bash
python app.py auditor
```

The orchestrator will automatically detect the engine selection and route to Crew AI instead of LangGraph.

### Switch Back to LangGraph

```yaml
execution_engine: "langgraph"
```

This is the default if not specified. LangGraph remains fully supported and is recommended for production use.

## Configuration

### Master Agent Customization

Configure the Crew AI master agent in `config/settings.yaml`:

```yaml
crew_ai:
  master_agent:
    role: "Security Audit Coordinator"
    goal: "Coordinate comprehensive security audits of Kubernetes clusters"
    backstory: "Expert security orchestrator with deep Kubernetes knowledge..."
  
  max_iterations: 150
  tool_budget_per_workflow:
    auditor: 200
    creator: 200
    comprehensive_auditor: 400
  delegate_to_crew: true
  enable_memory: true
```

**Agent Fields:**

- **role**: The agent's primary function (e.g., "Security Audit Coordinator")
- **goal**: What the agent aims to accomplish (e.g., "Conduct comprehensive security audits")
- **backstory**: Context about the agent's expertise and approach

### Multi-Agent Collaboration

**NEW**: The framework now supports multi-agent collaboration with specialized agents working together on complex tasks.

#### Enable Multi-Agent Mode

```yaml
crew_ai:
  delegate_to_crew: true    # ← Enable multi-agent delegation
  enable_memory: true       # ← Enable agent memory
```

#### Specialized Agents

Configure specialized agents in `config/settings.yaml`:

```yaml
crew_ai:
  specialized_agents:
    - id: "data_collector"
      role: "Data Collection Agent"
      goal: "Gather comprehensive Kubernetes cluster data"
      backstory: "Specialist in Kubernetes API interactions..."
      enabled: true
    
    - id: "security_analyzer"
      role: "Security Analysis Agent"
      goal: "Identify security misconfigurations and vulnerabilities"
      backstory: "Security engineer specialized in Kubernetes hardening..."
      enabled: true
    
    - id: "compliance_checker"
      role: "Compliance Verification Agent"
      goal: "Verify compliance with NIST, CIS, and NSA/CISA standards"
      backstory: "Compliance auditor certified in multiple security frameworks..."
      enabled: true
    
    - id: "policy_creator"
      role: "Policy Creation Agent"
      goal: "Create remediation policies and security configurations"
      backstory: "DevOps engineer expert in Kubernetes policy-as-code..."
      enabled: false  # Only enabled in creator workflow
```

#### How Multi-Agent Collaboration Works

```
User Input
    ↓
Master Agent (Coordinator) distributes work to:
    ├─ Data Collector Agent → Gathers raw cluster data
    ├─ Security Analyzer Agent → Identifies vulnerabilities
    ├─ Compliance Checker Agent → Maps to standards
    └─ Policy Creator Agent (optional) → Creates fixes
    ↓
Master Agent synthesizes findings
    ↓
Final comprehensive report
```

**Benefits**:
- ✅ Specialized agents excel at specific tasks
- ✅ Distributed workload across multiple reasoning engines
- ✅ Emergent intelligence from agent collaboration
- ✅ Better handling of complex multi-faceted problems

**When to Use**:
- Deep security audits requiring both data collection and analysis
- Compliance verification against multiple standards
- Comprehensive assessment + remediation in single run
- Exploratory analysis of complex cluster configurations

#### Workflow-Specific Agent Configuration

Agents can be automatically enabled/disabled per workflow:

- **auditor**: Data Collector + Security Analyzer + Compliance Checker + Master
- **creator**: All agents including Policy Creator
- **comprehensive_auditor**: All agents in full collaboration mode

### Execution Parameters

- **max_iterations**: Maximum number of iterations the crew can run (default: 150)
  - Controls how many "thinking → tool call → result" cycles before timeout
  - Increased for multi-agent coordination
  - Lower values (30-50) for quick audits; higher (100-150) for comprehensive analysis

- **tool_budget_per_workflow**: Maximum tool calls allowed per workflow
  - `auditor`: Multi-agent scan (200 calls, was 150)
  - `creator`: Policy creation (200 calls, was 100)  
  - `comprehensive_auditor`: Deep analysis (400 calls, was 250)
  - Distributed across agents; prevents runaway execution

- **delegate_to_crew**: Allow sub-agent delegation (experimental)
  - `false` (default): Single master agent handles all tasks
  - `true`: Master agent can create and delegate to sub-agents (requires additional configuration)

## Architecture

### Single Agent Mode (Legacy)

```
User Input
    ↓
Master Agent (Coordinator)
    ↓
LLM (Ollama/OpenAI) + Tool Recognition
    ↓
MCP Tool Invocation (kubectl_get, kubectl_describe, etc.)
    ↓
Tool Results Processing
    ↓
Final Report
```

**Use when**: `delegate_to_crew: false`

### Multi-Agent Mode (Recommended)

```
User Input
    ↓
Master Agent (Coordinator) ← Orchestrates
    ├─→ Data Collector Agent → Gathers cluster data
    │    └─ Uses: kubectl_get, kubectl_describe, list_api_resources
    │
    ├─→ Security Analyzer Agent → Identifies vulnerabilities
    │    └─ Uses: kubectl output + security rules
    │
    ├─→ Compliance Checker Agent → Verifies standards
    │    └─ Uses: kubectl output + compliance mappings
    │
    └─→ Policy Creator Agent (optional) → Creates fixes
         └─ Uses: kubectl_apply, helm tools
    ↓
Master Agent synthesizes all findings
    ↓
Comprehensive Final Report
```

**Use when**: `delegate_to_crew: true` (default)

**Advantages**:
- Parallel reasoning across multiple agents
- Specialized expertise for each task
- Better handling of complex problems
- Emergent intelligence from collaboration
- Clearer separation of concerns

### Key Differences from LangGraph

| Aspect | LangGraph | Crew AI (Single) | Crew AI (Multi) |
|--------|-----------|------------------|-----------------|
| **Structure** | Explicit DAG with nodes | Dynamic agent | Multiple coordinated agents |
| **Reasoning** | State-based transitions | LLM-driven autonomy | Collaborative intelligence |
| **Tool Calling** | Reactive to tool_calls | Pro-active tool selection | Distributed task execution |
| **Optimization** | Best for structured workflows | Good for exploration | Best for complex analysis |
| **Performance** | Fast (optimized) | Moderate | Slower (more reasoning) |
| **Interpretability** | High (explicit paths) | Medium (agent logic) | Medium (agent interactions) |
| **Production Readiness** | Recommended (stable) | Good (evolving) | Experimental (evolving) |

## Supported Workflows

All engines support the same workflows with varying configurations:

1. **Auditor** (`auditor`)
   - Quick security assessment with agent specialization
   - Single Agent: Scans for common misconfigurations
   - Multi-Agent: Parallel data collection + security analysis
   - Budget: 
     - Single: 150 tool calls
     - Multi: 200 tool calls
   
2. **Creator** (`creator`)
   - Deploys security policies with agent assistance
   - Single Agent: Installs Helm charts
   - Multi-Agent: Analysis → Policy creation → Deployment
   - Budget:
     - Single: 100 tool calls
     - Multi: 200 tool calls

3. **Comprehensive Auditor** (`comprehensive_auditor`)
   - Deep analysis with full agent collaboration
   - Single Agent: Full Kubernetes assessment
   - Multi-Agent: Complete assessment + compliance mapping + remediation
   - Budget:
     - Single: 250 tool calls
     - Multi: 400 tool calls

## MCP Tools Available

Both engines have access to the same tools. Multi-agent mode distributes tool calls across specialized agents:

**Data Collection** (Data Collector Agent)
- `kubectl_get`: List resources
- `kubectl_describe`: Get detailed resource info
- `list_api_resources`: Discover available APIs

**Deployment** (Policy Creator Agent)
- `kubectl_apply`: Apply configuration files
- `install_helm_chart`: Install Helm releases
- `upgrade_helm_chart`: Update Helm releases

**Analysis** (Security Analyzer + Compliance Checker Agents)
- Use tool outputs to identify issues
- Map findings to compliance standards
- Generate recommendations



- `kubectl_get`: Query Kubernetes resources
- `kubectl_describe`: Get detailed resource information
- `kubectl_apply`: Apply configuration files
- `install_helm_chart`: Install Helm charts
- `upgrade_helm_chart`: Upgrade existing releases
- `list_api_resources`: Discover available API resources

Example Crew AI prompt to use tools:

```
Query all Kubernetes namespaces to get the complete list.
Then describe the pods in each namespace to identify security issues.
```

The master agent will:
1. Call `kubectl_get` with `resourceType: "namespaces"`
2. Parse the results
3. Call `kubectl_get` separately for pods in each namespace
4. Synthesize findings into a security report

## LLM Configuration

Both engines use the same LLM configuration from `config/settings.yaml`:

```yaml
llm:
  provider: "ollama"          # or "openai"
  endpoint: "http://localhost:11434"
  model: "mistral:latest"     # or any OpenAI model
  temperature: 0.3
  max_tokens: 2000
  timeout_seconds: 60
```

### Using OpenAI

```yaml
llm:
  provider: "openai"
  model: "gpt-4"
  temperature: 0.3
```

Set `OPENAI_API_KEY` environment variable before running:

```bash
export OPENAI_API_KEY=sk-...
python app.py auditor
```

## Troubleshooting

### Crew AI Takes Too Long

**Problem**: Execution hangs or runs indefinitely

**Solutions**:
1. Reduce `max_iterations` in config:
   ```yaml
   crew_ai:
     max_iterations: 30
   ```
2. Lower `tool_budget_per_workflow` for faster termination:
   ```yaml
   crew_ai:
     tool_budget_per_workflow:
       auditor: 50
   ```
3. Switch to LangGraph temporarily to verify cluster connectivity

### Agent Doesn't Use Tools

**Problem**: Agent generates text instead of calling tools

**Solutions**:
1. Check that Ollama is running: `curl http://localhost:11434/api/tags`
2. Verify model is available: `ollama pull mistral:latest`
3. Increase `temperature` in LLM config to encourage exploration
4. Simplify the agent's `goal` in master_agent config

### Memory/CPU Issues

**Problem**: Process uses excessive resources

**Solutions**:
1. Use smaller LLM model in config
2. Reduce `max_iterations` significantly
3. Limit `tool_budget_per_workflow`
4. Consider switching to LangGraph for production

## Examples

### Example 1: Quick Security Scan

```yaml
# config/settings.yaml
execution_engine: "crew_ai"

crew_ai:
  master_agent:
    role: "Quick Security Scanner"
    goal: "Identify critical security issues in 5 minutes"
    backstory: "Speed-focused auditor with broad security knowledge."
  
  max_iterations: 20
  tool_budget_per_workflow:
    auditor: 50
```

Run:
```bash
python app.py auditor
```

### Example 2: Deep Compliance Audit

```yaml
execution_engine: "crew_ai"

crew_ai:
  master_agent:
    role: "Compliance Auditor"
    goal: "Verify NIST 800-53, CIS Kubernetes Benchmark, and NSA/CISA controls"
    backstory: "Certified auditor specialized in compliance frameworks."
  
  max_iterations: 150
  tool_budget_per_workflow:
    comprehensive_auditor: 500
```

Run:
```bash
python app.py comprehensive_auditor
```

### Example 3: Policy Deployment

```yaml
execution_engine: "crew_ai"

crew_ai:
  master_agent:
    role: "Policy Deployer"
    goal: "Deploy Kubernetes security policies and verify deployment"
    backstory: "DevOps engineer expert in Kubernetes policy-as-code."
  
  max_iterations: 50
  tool_budget_per_workflow:
    creator: 150
  delegate_to_crew: true  # Allow policy creator to delegate verification tasks
```

Run:
```bash
python app.py creator
```

## Advanced: Custom Master Agent Logic

To extend the master agent with custom logic, edit the CrewAIExecutor:

**File**: `src/langgraphagenticai/integrations/crewai_executor.py`

```python
def _create_master_agent(self, workflow_id: str) -> Agent:
    """Create a master agent configured from config."""
    crew_config = self.config.get_crew_ai_config()
    master_config = self.config.get_crew_ai_master_agent()
    
    # Customize agent creation
    agent = Agent(
        role=master_config.get('role', 'Agent'),
        goal=master_config.get('goal', 'Execute tasks'),
        backstory=master_config.get('backstory', 'Helpful assistant'),
        verbose=True,
        allow_delegation=crew_config.get('delegate_to_crew', False),
        # Add custom parameters here:
        # memory=True,  # Enable agent memory
        # max_tokens=4000,  # Custom token limit
    )
    
    return agent
```

## Limitations & Experimental Features

⚠️ **Crew AI integration is experimental**. Known limitations:

1. **No sub-delegation by default** (`delegate_to_crew: false`)
   - Multi-agent trees increase complexity and token usage
   - Not recommended for cost-sensitive OpenAI deployments

2. **Tool result handling** differs from LangGraph
   - May require adjustments for complex workflows
   - Comprehensive auditor may need output formatting tweaks

3. **Performance**
   - Crew AI can be slower than LangGraph due to agent reasoning
   - Recommend LangGraph for time-sensitive operations

4. **Debugging**
   - Less visibility into agent decision-making
   - Consider enabling `verbose: true` in agent config for inspection

5. **Stability**
   - Crew AI library is rapidly evolving
   - Dependencies may require frequent updates

## Migration: LangGraph to Crew AI

To test Crew AI with existing workflows:

1. **Backup current config**:
   ```bash
   cp config/settings.yaml config/settings.yaml.backup
   ```

2. **Enable Crew AI**:
   ```yaml
   execution_engine: "crew_ai"
   ```

3. **Test with auditor** (low risk):
   ```bash
   python app.py auditor
   ```

4. **Compare results** with LangGraph output:
   ```bash
   cp config/settings.yaml.backup config/settings.yaml
   python app.py auditor
   ```

5. **If results match**, gradually enable for other workflows

6. **Revert if issues**:
   ```bash
   cp config/settings.yaml.backup config/settings.yaml
   ```

## Performance Tuning

### For Speed (Quick Audits)

```yaml
crew_ai:
  max_iterations: 30
  tool_budget_per_workflow:
    auditor: 50
llm:
  temperature: 0.1  # Focus, less exploration
```

### For Thoroughness (Deep Analysis)

```yaml
crew_ai:
  max_iterations: 150
  tool_budget_per_workflow:
    comprehensive_auditor: 500
llm:
  temperature: 0.5  # More exploration
```

### For Cost Control (OpenAI)

```yaml
llm:
  provider: "openai"
  model: "gpt-3.5-turbo"  # Cheaper than gpt-4
crew_ai:
  max_iterations: 50
  tool_budget_per_workflow:
    auditor: 75
  delegate_to_crew: false
```

## Getting Help

**Framework Issues**:
- Check [docs/TROUBLESHOOTING_GUIDE.md](TROUBLESHOOTING_GUIDE.md)
- Review [docs/ARCHITECTURE_REFACTORING.md](ARCHITECTURE_REFACTORING.md)

**Crew AI Issues**:
- Official docs: https://docs.crewai.com
- GitHub: https://github.com/joaomdmoura/crewai

**LangGraph Issues**:
- LangGraph docs: https://langchain-ai.github.io/langgraph
- Compare behavior: Set `execution_engine: "langgraph"` and re-run

## See Also

- [CONFIG_GUIDE.md](CONFIG_GUIDE.md) - Full configuration reference
- [QUICK_START_LIVE_LOGGING.md](QUICK_START_LIVE_LOGGING.md) - Enable live logs with Crew AI
- [RUN_COMPREHENSIVE_AUDIT.md](RUN_COMPREHENSIVE_AUDIT.md) - Comprehensive auditor details
