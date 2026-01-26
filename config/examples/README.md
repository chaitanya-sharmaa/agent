# Configuration Examples

This directory contains example configurations for different use cases. Copy these to your root `config/` directory to adapt the application for different domains.

## Available Examples

### 1. Kubernetes Auditor (Default)
**What it does:** Audits Kubernetes clusters for Zero Trust security posture
- Checks Istio/service mesh configuration
- Verifies mTLS enforcement
- Analyzes network policies and RBAC
- Generates security assessment report

**Files:** Already in root `config/` directory
- `../mcp.yaml` - Kubernetes tools (kubectl_get, kubectl_describe, etc.)
- `../prompts.yaml` - Auditor and Creator workflows

### 2. AWS Security Auditor
**What it does:** Audits AWS infrastructure for security and compliance

**To use:**
```bash
# Backup current config (optional)
cp config/mcp.yaml config/mcp.yaml.backup
cp config/prompts.yaml config/prompts.yaml.backup

# Copy AWS examples
cp config/examples/mcp_aws.yaml config/mcp.yaml
cp config/examples/prompts_aws.yaml config/prompts.yaml

# Run the AWS auditor
python -m src.langgraphagenticai.main --no-ui aws_auditor
```

**Features:**
- List and audit S3 buckets
- Analyze IAM policies
- Check security groups
- Verify encryption
- Generate compliance report

### 3. Docker Container Scanner
**What it does:** Scans Docker images and containers for vulnerabilities

**To use:**
```bash
# Copy Docker examples
cp config/examples/mcp_docker.yaml config/mcp.yaml
cp config/examples/prompts_docker.yaml config/prompts.yaml

# Run the Docker scanner
python -m src.langgraphagenticai.main --no-ui docker_scanner
```

**Features:**
- Scan images for CVEs
- Check base image security
- Verify image signatures
- Analyze container permissions
- Generate vulnerability report

## Creating Your Own Configuration

### 1. Define Your MCP Tools

Create `config/mcp.yaml` with your MCP server:

```yaml
server:
  host: "your-server.com"
  port: 3001
  
tools:
  - name: "your_tool_name"
    description: "What it does"
    parameters:
      - name: "param"
        type: "string"
        required: true
```

### 2. Create Your Workflows

Create `config/prompts.yaml` with system prompts:

```yaml
workflows:
  your_workflow:
    name: "Friendly Name"
    description: "What this does"
    system_prompt: |
      You are a specialized AI for...
      AVAILABLE TOOLS: [list them]
      RULES: [specify behavior]
    user_prompts:
      start: "User message to trigger"
```

### 3. Adjust Settings (Optional)

Edit `config/settings.yaml`:

```yaml
workflow_settings:
  available_workflows:
    - id: "your_workflow"
      name: "Your Workflow"
      enabled: true
```

### 4. Run Your Configuration

```bash
python -m src.langgraphagenticai.main --no-ui your_workflow
```

## Best Practices

1. **Backup before changing** - Keep your current config safe
2. **Test with CLI first** - Debug with `--no-ui` flag before running UI
3. **Document your workflows** - Add clear descriptions
4. **Validate configuration** - Use `config.validate()` to check for errors
5. **Version control configs** - Track changes to configuration files

## Switching Back to Kubernetes Auditor

```bash
# Copy original Kubernetes config
cp config/examples/../mcp.yaml config/mcp.yaml
cp config/examples/../prompts.yaml config/prompts.yaml

# Or restore from backup
cp config/mcp.yaml.backup config/mcp.yaml
cp config/prompts.yaml.backup config/prompts.yaml
```

## Extending with Custom Tools

Your MCP server can provide any tools. Examples:

- **Cloud Providers**: AWS, GCP, Azure tools
- **Infrastructure**: Terraform, CloudFormation, Ansible
- **Monitoring**: Prometheus, Datadog, New Relic
- **Database**: SQL, NoSQL, data security tools
- **Code Analysis**: SAST, dependency scanning, SBOM tools
- **Network**: DNS, firewall, traffic analysis
- **Custom**: Your proprietary tools

The LangGraph logic stays the same - only configuration changes!

## Troubleshooting

**Configuration not loading?**
- Ensure YAML syntax is valid (use a YAML validator)
- Check file paths match your MCP server
- Verify `mcp.yaml`, `prompts.yaml`, `settings.yaml` exist

**Workflows not showing?**
- Add workflow to `settings.yaml` `available_workflows`
- Set `enabled: true`
- Restart the application

**Tools not available?**
- Check MCP server is running
- Verify tool names in `prompts.yaml` match `mcp.yaml`
- Ensure MCP server URL is correct in `settings.yaml`

## Example: Quick AWS Audit Setup

```bash
cd /path/to/istio-genai-new-working

# 1. Backup current config
cp config/mcp.yaml config/mcp.yaml.k8s
cp config/prompts.yaml config/prompts.yaml.k8s

# 2. Use AWS example
cp config/examples/mcp_aws.yaml config/mcp.yaml
cp config/examples/prompts_aws.yaml config/prompts.yaml

# 3. Run AWS auditor
python -m src.langgraphagenticai.main --no-ui aws_auditor

# 4. View results
cat audit_results.json

# 5. Switch back to Kubernetes
cp config/mcp.yaml.k8s config/mcp.yaml
cp config/prompts.yaml.k8s config/prompts.yaml
```

That's it! No code changes needed.
