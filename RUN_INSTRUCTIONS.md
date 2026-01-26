# How to Run LangGraph AgenticAI Application

## Prerequisites

1. **MCP Server**: Ensure the Kubernetes MCP server is running on `http://localhost:3001/mcp`
2. **Ollama**: Make sure Ollama is installed and running with your desired model
3. **Python Environment**: Activate your virtual environment (if using one)

## Running the Application

### Command Line Interface (CLI) Mode

To run the application without the Streamlit UI, use the `--no-ui` flag:

```bash
# From the project root directory
python -m src.langgraphagenticai.main --no-ui
```

Or with a specific usecase:

```bash
# Run auditor usecase
python -m src.langgraphagenticai.main --no-ui auditor

# Run creator usecase
python -m src.langgraphagenticai.main --no-ui creator
```

### Streamlit UI Mode

To run with the web interface:

```bash
# From the project root directory (RECOMMENDED)
streamlit run app.py
```

This will launch the Streamlit interface at:
- **Local URL:** http://localhost:8501
- **Network URL:** http://192.168.1.125:8501 (or your machine's IP)

**Note:** Always use `streamlit run app.py` from the project root. Direct invocation of main.py with Streamlit has import issues due to module path resolution differences.

### Environment Setup

If you haven't set up the environment:

```bash
# Install dependencies
pip install -r requirements.txt

# Or using uv (if you use it)
uv pip install -r requirements.txt
```

### Verification Checklist

Before running the application, ensure:

1. **MCP Server is running** on port 3001:
   ```bash
   curl http://localhost:3001/mcp
   ```
   Should return HTTP 200/202

2. **Ollama is running** with mistral model:
   ```bash
   ollama list
   ```
   Should show `mistral:latest` in the list

3. **Kubernetes cluster is accessible**:
   ```bash
   kubectl cluster-info
   ```

4. **Python environment is configured**:
   ```bash
   python -c "from langchain_ollama.chat_models import ChatOllama; print('✓ Imports OK')"
   ```