# 📋 Live Logging System - Complete Guide

## Overview

The application now includes a comprehensive **live logging system** that displays real-time logs in both CLI mode and Streamlit UI mode. You'll see exactly what the application is doing at every step.

## Features

### ✅ Live Log Display

**CLI Mode:**
- Color-coded log levels (🔵 INFO, 🟡 WARNING, 🔴 ERROR)
- Real-time console output
- Timestamps for each log entry
- Structured sections and subsections

**Streamlit UI Mode:**
- Logs displayed in right panel
- Expandable detailed log view
- Real-time updates as workflows execute
- Integrated with workflow execution

### ✅ Log Types

1. **Status Updates** - ✅ Checkmarks for successful operations
2. **Step Indicators** - [Step 1/3], [Step 2/3] for multi-step processes
3. **Section Headers** - Visual separators for major workflow phases
4. **Subsection Headers** - Visual separators for sub-phases
5. **Debug Messages** - Detailed execution information
6. **Error Messages** - 🔴 Error details with stack traces

## Usage

### CLI Mode - View Live Logs

```bash
# Auditor workflow with live logs
python3 -m src.langgraphagenticai.main --no-ui auditor

# Output will show:
================================================================================
>>> ZERO TRUST AUDITOR
================================================================================

2026-01-23 17:25:14 - INFO - 📊 Analyzing your Kubernetes cluster...
2026-01-23 17:25:14 - INFO - 
────────────────────────────────────────────────────────────────
>> Gathering Cluster Data
────────────────────────────────────────────────────────────────

2026-01-23 17:25:15 - INFO - 🔍 Running security checks...
2026-01-23 17:25:25 - INFO - ✅ Cluster data gathered successfully
2026-01-23 17:25:25 - INFO - 
────────────────────────────────────────────────────────────────
>> Generating Assessment Report
────────────────────────────────────────────────────────────────

2026-01-23 17:25:26 - INFO - ✅ Assessment report generated
```

### Streamlit UI Mode - Side-by-Side Logs

```bash
streamlit run app.py
```

**Layout:**
```
┌─────────────────────────┬──────────────────────────┐
│   Workflow Controls     │   📋 Live Execution Logs │
│                         │                          │
│ Select usecase: [▼]     │ 2026-01-23 17:25:14     │
│ Execute [Button]        │ Execution Started       │
│                         │                          │
│                         │ 🔧 Initializing LLM...  │
│                         │ ✅ LLM initialized      │
│                         │                          │
│                         │ 📊 Building graph...    │
│                         │ ✅ Graph built          │
│                         │                          │
│ 📜 Detailed Logs [∨]   │ 🚀 Running workflow...  │
│ ┌──────────────────────┤ ✅ Workflow completed   │
│ │ Expanded log view    │                          │
│ │ with all details     │                          │
│ └──────────────────────┘──────────────────────────┘
```

## Log Messages Explained

### During Initialization

```
🔧 Initializing LLM model...
✅ LLM model initialized successfully
```
- LLM (Language Model) is being prepared
- Connects to Ollama on localhost:11434

### During Graph Setup

```
📊 Building graph structure...
✅ Graph structure built successfully
```
- The workflow graph is being constructed
- All nodes and edges are configured

### During Execution

```
🔍 Running security checks...
[Step 1/3] Gathering cluster data
[Step 2/3] Running analysis
[Step 3/3] Generating report
```
- Workflow is executing
- Progress indicators show current step

### Error Scenarios

```
🔴 ERROR - Failed to initialize LLM model: Connection refused
```
- Clear indication of what failed
- Reason for the failure
- Stack trace available in detailed logs

## Log Levels

| Level | Icon | Color | Usage |
|-------|------|-------|-------|
| DEBUG | 🔵 | Cyan | Detailed technical information |
| INFO | ℹ️ | Green | General informational messages |
| WARNING | ⚠️ | Yellow | Warning messages (non-critical) |
| ERROR | 🔴 | Red | Error messages (issues to fix) |
| CRITICAL | ⛔ | Magenta | Critical failures (stop execution) |

## Common Log Patterns

### Auditor Workflow Logs

```
================================================================================
>>> ZERO TRUST AUDITOR
================================================================================

2026-01-23 17:25:14 - INFO - 📊 Analyzing your Kubernetes cluster...

────────────────────────────────────────────────────────────────
>> Gathering Cluster Data
────────────────────────────────────────────────────────────────

2026-01-23 17:25:15 - INFO - 🔍 Running security checks...
2026-01-23 17:25:20 - INFO - ✅ Found 8 namespaces
2026-01-23 17:25:25 - INFO - ✅ Analyzed 84 pods
2026-01-23 17:25:30 - INFO - ✅ Checked RBAC configurations
2026-01-23 17:25:35 - INFO - ✅ Reviewed network policies

────────────────────────────────────────────────────────────────
>> Generating Assessment Report
────────────────────────────────────────────────────────────────

2026-01-23 17:25:40 - INFO - ✅ Assessment report generated
```

### Creator Workflow Logs

```
================================================================================
>>> ZERO TRUST CREATOR
================================================================================

[Step 1/3] Initial Security Audit
[Step 2/3] Deploying Authorization Policies
[Step 3/3] Post-Deployment Verification
```

### Comprehensive Auditor Workflow Logs

```
================================================================================
>>> COMPREHENSIVE SECURITY AUDIT
================================================================================

2026-01-23 17:25:14 - INFO - 📊 Starting comprehensive cluster analysis...

[Step 1/5] Initializing analyzer
[Step 2/5] Analyzing pod security
[Step 3/5] Analyzing RBAC
[Step 4/5] Analyzing network policies
[Step 5/5] Generating report

✅ Comprehensive audit completed
```

## Implementation Details

### File: `live_logger.py`

The live logging system is implemented in:

```
src/langgraphagenticai/utils/live_logger.py
```

**Key Components:**

1. **LiveLogger** - Main singleton logger class
   - Provides unified logging interface
   - Works in both CLI and Streamlit modes
   - Singleton pattern ensures single instance

2. **CLILogHandler** - Handles CLI output
   - Color-coded log levels
   - Terminal detection for ANSI colors
   - Formatted timestamps

3. **StreamlitLogHandler** - Handles Streamlit UI output
   - Real-time updates to UI containers
   - Graceful fallback if Streamlit not available

## Using Live Logger in Your Code

### Basic Usage

```python
from src.langgraphagenticai.utils.live_logger import get_live_logger

logger = get_live_logger()

# Log simple messages
logger.info("Processing data...")
logger.debug("Debug information")
logger.warning("This might be an issue")
logger.error("Something went wrong")

# Log status updates
logger.status("Process completed")

# Log step progress
logger.step(1, 3, "Starting step 1")
logger.step(2, 3, "Processing step 2")
logger.step(3, 3, "Finishing step 3")

# Log section headers
logger.section("MAIN WORKFLOW")
logger.subsection("Initialization")
```

### Output Examples

```python
logger.status("Cluster data gathered")
# Output: ✅ Cluster data gathered

logger.step(1, 5, "Analyzing pods")
# Output: [Step 1/5] Analyzing pods

logger.section("SECURITY ANALYSIS")
# Output:
# ================================================================================
# >>> SECURITY ANALYSIS
# ================================================================================

logger.subsection("RBAC Configuration")
# Output:
# ────────────────────────────────────────────────────────────────
# >> RBAC Configuration
# ────────────────────────────────────────────────────────────────
```

## Integration Points

### UI Orchestrator (`ui_orchestrator.py`)

```python
from src.langgraphagenticai.utils.live_logger import get_live_logger

live_logger = get_live_logger()

# In run_app():
live_logger.setup_streamlit_logging(log_container)
live_logger.section("Execution Started")
live_logger.info(f"Running workflow: {usecase}")

# In _initialize_model():
live_logger.info("🔧 Initializing LLM model...")
live_logger.status("LLM model initialized successfully")

# In _setup_and_run_graph():
live_logger.subsection(f"Setting up workflow: {usecase}")
live_logger.info("📊 Building graph structure...")
live_logger.status("Graph structure built successfully")
```

### CLI Orchestrator (`cli_orchestrator.py`)

```python
from src.langgraphagenticai.utils.live_logger import get_live_logger

live_logger = get_live_logger()

# In run_auditor():
live_logger.section("ZERO TRUST AUDITOR")
live_logger.subsection("Gathering Cluster Data")
live_logger.info("🔍 Running security checks...")
live_logger.status("Auditor analysis completed")

# In run_creator():
live_logger.section("ZERO TRUST CREATOR")
live_logger.step(1, 3, "Initial Security Audit")
live_logger.step(2, 3, "Deploying Authorization Policies")
live_logger.step(3, 3, "Post-Deployment Verification")
```

### Main Entry Point (`main.py`)

```python
from src.langgraphagenticai.utils.live_logger import get_live_logger

live_logger = get_live_logger()

# In run_main():
live_logger.info("🚀 Starting application in CLI mode...")
live_logger.info(f"Selected workflow: {workflow_id}")

# In error handling:
live_logger.error(f"Error in CLI execution: {e}")
```

## Troubleshooting

### Logs Not Appearing in CLI

**Problem:** Running CLI but no logs shown

**Solution:**
```bash
# Ensure you're using the correct command:
python3 -m src.langgraphagenticai.main --no-ui auditor

# Check that logging is configured:
python3 -c "from src.langgraphagenticai.utils.live_logger import get_live_logger; logger = get_live_logger(); logger.info('Test')"
```

### Logs Not Appearing in Streamlit UI

**Problem:** UI running but logs not displayed in right panel

**Solution:**
1. Check that `streamlit run app.py` is used (not direct Python execution)
2. The logs will appear in the "📋 Live Execution Logs" section
3. Expand "📜 Detailed Logs" to see full log history

### Colors Not Showing in Terminal

**Problem:** ANSI color codes appearing as text in terminal

**Solution:**
```bash
# This is automatically detected. If still not working:
export TERM=xterm-256color
python3 -m src.langgraphagenticai.main --no-ui auditor
```

## Performance Considerations

- Live logging has minimal performance impact
- Logs are asynchronously sent to Streamlit UI
- CLI logging is synchronous for immediate feedback
- Log volume is automatically managed (no buffer overflow)

## Future Enhancements

Potential improvements:
- Log filtering by level
- Log search functionality
- Export logs to file
- Colored HTML log export
- Log persistence across sessions
- Integration with external logging services (e.g., Datadog, CloudWatch)

---

## Summary

The live logging system provides:

✅ **Real-time visibility** into what the application is doing
✅ **Both CLI and UI support** with appropriate formatting for each
✅ **Color-coded messages** for easy scanning
✅ **Structured logging** with sections and steps
✅ **Error tracking** with detailed information
✅ **Easy integration** - just import and use

Now when you run the application, you'll see exactly what's happening at every step!

