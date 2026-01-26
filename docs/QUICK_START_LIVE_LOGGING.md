# 🎯 Live Logging Quick Start

## What You Get

When you run the application now, you'll see **live logs** showing exactly what it's doing:

### CLI Mode Example

```bash
$ python3 -m src.langgraphagenticai.main --no-ui auditor

================================================================================
>>> ZERO TRUST AUDITOR
================================================================================

2026-01-23 17:25:14 - langgraphagenticai.live - INFO - 📊 Analyzing Kubernetes cluster...
2026-01-23 17:25:15 - langgraphagenticai.live - INFO - 🔍 Running security checks...
2026-01-23 17:25:20 - langgraphagenticai.live - INFO - ✅ Cluster analysis complete

────────────────────────────────────────────────────────────────
>> Generating Report
────────────────────────────────────────────────────────────────

2026-01-23 17:25:30 - langgraphagenticai.live - INFO - ✅ Report generated
```

### Streamlit UI Example

```bash
$ streamlit run app.py
```

The UI will show:
- **Left Panel**: Workflow controls
- **Right Panel**: 📋 **Live Execution Logs** with real-time updates

## Key Features

✅ **Color-coded log levels** - DEBUG (blue), INFO (green), WARNING (yellow), ERROR (red)
✅ **Real-time updates** - See progress as it happens
✅ **Step indicators** - `[Step 1/3]`, `[Step 2/3]` for multi-step workflows
✅ **Status updates** - ✅ checkmarks for successful operations
✅ **Section headers** - Clear visual separation of workflow phases
✅ **Works in both CLI and Streamlit UI modes**

## What Gets Logged

### Initialization Phase
```
🔧 Initializing LLM model...
✅ LLM model initialized
```

### Execution Phase
```
📊 Building graph structure...
✅ Graph structure built
🚀 Running workflow...
```

### Analysis Phase
```
[Step 1/3] Gathering cluster data
[Step 2/3] Running analysis
[Step 3/3] Generating report
```

### Error Phase
```
🔴 ERROR - Failed to connect to MCP server
Error details and stack trace shown
```

## Running with Live Logs

### CLI Mode (Recommended for Full Logs)

```bash
# Auditor workflow
python3 -m src.langgraphagenticai.main --no-ui auditor

# Creator workflow
python3 -m src.langgraphagenticai.main --no-ui creator

# Comprehensive auditor
python3 -m src.langgraphagenticai.main --no-ui comprehensive_auditor
```

### Streamlit UI Mode (With Log Panel)

```bash
streamlit run app.py
```

Then:
1. Select your workflow from dropdown
2. Click Execute
3. Watch logs appear in the right panel in real-time

## Log Levels

| Symbol | Level | Meaning |
|--------|-------|---------|
| 🔵 | DEBUG | Detailed technical info |
| ℹ️ | INFO | General information |
| ⚠️ | WARNING | Warning (non-critical) |
| 🔴 | ERROR | Error (needs attention) |
| ⛔ | CRITICAL | Critical failure |

## File Locations

- **Live Logger Code**: `src/langgraphagenticai/utils/live_logger.py`
- **Integration in UI**: `src/langgraphagenticai/core/ui_orchestrator.py`
- **Integration in CLI**: `src/langgraphagenticai/core/cli_orchestrator.py`
- **Complete Guide**: `LIVE_LOGGING_GUIDE.md`

## That's It!

Just run your workflows and watch the live logs tell you exactly what's happening at every step.

No configuration needed - it works automatically!

---

**Next Steps:**
1. Run a workflow and see the live logs
2. Check `LIVE_LOGGING_GUIDE.md` for detailed documentation
3. See `RUN_INSTRUCTIONS.md` for execution examples
