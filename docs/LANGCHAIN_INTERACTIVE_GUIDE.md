# Interactive LangChain/LangGraph Guide

## Real Execution Example

Let's trace what happens step-by-step when you run:
```bash
python -m src.langgraphagenticai.main --no-ui auditor
```

---

## Step 1: Initialization (0-1 second)

### What Your Code Does

```python
# main.py: _initialize_and_run()
model = OllamaLLM({}).get_llm_model()
# Creates: ChatOllama(model="mistral:latest", temperature=0.0)
# This is the Mistral language model running locally via Ollama

graph_builder = GraphBuilder(model)
# Stores the LLM for later use in graph construction
```

### What Happens Inside

```
┌──────────────────────────────────────┐
│ Ollama (Local Model Server)          │
│ ┌────────────────────────────────────┤
│ │ Mistral Model                      │
│ │ (4-7B parameters)                  │
│ │ Ready to receive prompts            │
│ └────────────────────────────────────┤
└──────────────────────────────────────┘
          ▲
          │ Connected
          │
Local machine:3001 (default Ollama port)
```

---

## Step 2: Graph Building (1-2 seconds)

### Your Code

```python
# cli_orchestrator.py: run_auditor()
auditor_graph = await graph_builder.build_auditor_graph()

# graph_builder.py
async def build_auditor_graph(self):
    return await self._base_graph(AUDITOR_PROMPT, "Zero Trust Auditor")

async def _base_graph(self, system_prompt: str, usecase: str):
    # Step 1: Get tools
    tools = await get_tools()
    # Returns: [kubectl_get, kubectl_describe, ... helm_install, ...]
    
    # Step 2: Bind tools to LLM
    llm_with_tools = self.llm.bind_tools(tools)
    # Now: Mistral knows about available tools
    
    # Step 3: Create graph structure
    sg = StateGraph(State)
    sg.add_node("chatbot", chatbot_node)
    sg.add_node("tools", tool_node)
    sg.set_entry_point("chatbot")
    sg.add_conditional_edges("chatbot", tools_condition)
    
    # Step 4: Compile
    compiled = sg.compile()
    return compiled
```

### What the Graph Looks Like

```
State:
┌──────────────────────────────┐
│ messages: [                  │
│   HumanMessage(...),         │
│   AIMessage(...),            │
│   ToolMessage(...),          │
│   ...                        │
│ ]                            │
└──────────────────────────────┘
          │
          ▼
    ┌─────────────┐
    │   CHATBOT   │ ◄──── Entry point
    │   (Node 1)  │
    └──────┬──────┘
           │
    Has tool_calls?
           │
    ┌──────┴──────┐
    │Yes          │No
    ▼             ▼
┌──────────┐   END
│  TOOLS   │   (Exit)
│ (Node 2) │
└────┬─────┘
     │
     │ Tool output added
     │ to state.messages
     │
     └──► Back to CHATBOT
```

### Tools Available

```python
# tools/kubernetes_tool.py: get_tools()
tools = [
    kubectl_get(resourceType, namespace)
    # Examples:
    # - kubectl_get(resourceType="pods", namespace="default")
    # - kubectl_get(resourceType="services", namespace="istio-system")
    
    kubectl_describe(resourceType, name, namespace)
    # Examples:
    # - kubectl_describe(resourceType="pod", name="pod-xyz", namespace="default")
    
    helm_install(name, chart, namespace)
    # - helm_install(name="auth", chart="https://...", namespace="istio-system")
    
    ... more tools ...
]

# Mistral is told:
print("Available tools you can call:")
print("  1. kubectl_get - Get list of resources")
print("  2. kubectl_describe - Get details of a resource")
print("  3. helm_install - Install a Helm chart")
```

---

## Step 3: Graph Execution (2-60 seconds)

### Your Code

```python
# graph_executor.py: execute_graph()
async for event in graph_obj.astream(
    {"messages": [("human", user_message)]},
    {"recursion_limit": 50}
):
    # Process each event
    formatter.process_event(event)
    
    # Collect tool results
    if "tools" in event:
        # Tool was executed, capture output
```

### Event Stream - Real Walkthrough

#### Initial Input

```python
user_message = "Execute Zero Trust Auditor checks now. Use available tools as needed to gather cluster data and provide a final assessment."

initial_state = {
    "messages": [
        ("human", "Execute Zero Trust Auditor checks now...")
    ]
}
```

#### Event 1: Chatbot Node Thinks (5-30 seconds)

```
Mistral Receives:
┌──────────────────────────────────────────────────────────┐
│ System Prompt (AUDITOR_PROMPT)                           │
├──────────────────────────────────────────────────────────┤
│ You are a Kubernetes Zero Trust auditor. Your job is:   │
│ 1. Check Istio installation                             │
│ 2. Verify mTLS enforcement                              │
│ 3. Check authorization policies                         │
│ 4. Check network policies                               │
│ ...                                                       │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│ Available Tools:                                          │
├──────────────────────────────────────────────────────────┤
│ kubectl_get: Get resources                              │
│ kubectl_describe: Describe resources                    │
│ ... more tools ...                                       │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│ User Message:                                            │
├──────────────────────────────────────────────────────────┤
│ Execute Zero Trust Auditor checks now...                │
└──────────────────────────────────────────────────────────┘

Mistral thinks:
"The user wants me to perform a Kubernetes Zero Trust audit.
 I need to check various resources.
 First, I should check if the cluster has namespaces.
 I'll call the kubectl_get tool with resourceType='namespaces'"

Output:
{
  "type": "tool_use",
  "id": "call_1",
  "name": "kubectl_get",
  "input": {
    "resourceType": "namespaces"
  }
}
```

#### Event 2: Tools Node Executes

```
Tool: kubectl_get
Args: {resourceType: "namespaces"}

Execute:
$ kubectl get namespaces

Output:
NAME              STATUS   AGE
default           Active   365d
kube-system       Active   365d
kube-public       Active   365d
istio-system      Active   30d
istio-ingress     Active   30d
...

Result added to state.messages:
{
  "type": "tool_result",
  "tool_use_id": "call_1",
  "content": "NAME              STATUS   AGE\ndefault..."
}
```

#### Event 3: Chatbot Thinks Again (with new info)

```
Mistral Receives:
┌──────────────────────────────────────────────────────────┐
│ Previous conversation + tool result:                     │
├──────────────────────────────────────────────────────────┤
│ [System Prompt]                                          │
│                                                          │
│ User: "Execute Zero Trust Auditor checks..."           │
│                                                          │
│ Assistant: Called kubectl_get for namespaces           │
│                                                          │
│ Tool Result:                                            │
│ NAME              STATUS   AGE                           │
│ default           Active   365d                          │
│ ...                                                      │
│ istio-system      Active   30d                           │
└──────────────────────────────────────────────────────────┘

Mistral thinks:
"Good! I found namespaces including istio-system.
 Now I should check pods in istio-system to verify Istio installation.
 Let me call kubectl_get for pods."

Output:
{
  "type": "tool_use",
  "id": "call_2",
  "name": "kubectl_get",
  "input": {
    "resourceType": "pods",
    "namespace": "istio-system"
  }
}
```

#### Event 4: Tools Execute Again

```
Tool: kubectl_get
Args: {resourceType: "pods", namespace: "istio-system"}

Execute:
$ kubectl get pods -n istio-system

Output:
NAME                    READY   STATUS
istiod-123abc           1/1     Running
istio-proxy-789def      1/1     Running
...

Result added to state.messages
```

#### Event N: Final Response

```
After multiple tool calls (15-30 iterations typically):

Mistral has gathered enough information:
- Namespaces: ✓ (found istio-system)
- Istio pods: ✓ (found istiod)
- Policies: ✓ (checked for authorization policies)
- mTLS: ✓ (checked PeerAuthentication)

Mistral output (no tool_calls):
"Based on my audit of the Kubernetes cluster:

ISTIO INSTALLATION: ✓ Detected
- istiod version: 1.16.0
- Sidecar injection: Enabled

mTLS STATUS: ⚠ Partial
- PeerAuthentication: Found but not cluster-wide
- Recommendation: Enable mTLS for all namespaces

AUTHORIZATION POLICIES: ❌ Not Found
- No AuthorizationPolicy resources detected
- Recommendation: Implement zero-trust access control

NETWORK POLICIES: ⚠ Limited
- Default policies exist in some namespaces
- Recommendation: Enforce network policies cluster-wide

Security Score: 45/100 (Needs improvement)"
```

---

## Step 4: Collection & Analysis

### GraphExecutor Collects

```python
# In execute_graph(), for each event:

collected_tool_results = []
executed_probe_keys = set()

if "tools" in event:
    for msg in event["tools"].get("messages", []):
        # Extract tool output
        content = msg.content
        tool_name = msg.name
        
        # Add to results
        collected_tool_results.append({
            "output": content,
            "tool_name": tool_name,
            "tool_call_id": msg.tool_call_id
        })
        
        # Track which probes were executed
        if tool_name == "kubectl_get":
            probe_key = f"{resourceType}:{namespace}"
            executed_probe_keys.add(probe_key)
            probe_manager.add_probes({probe_key})
```

### Final Analysis

```python
# cli_orchestrator.py: _print_assessment()

cleaned_results = filter_valid_results(collected_tool_results)
# Removes error messages, formats outputs

assessment = analyzer.analyze_and_generate_report(cleaned_results)
# Uses ZeroTrustAnalyzer to interpret results

print("--- Zero Trust Auditor Assessment (pre-deploy) ---")
print(assessment)
```

---

## Key Points to Understand

### 1. The Agent Loop

```
┌─────────────────────────────────────┐
│ OBSERVE                             │
│ - What does the state contain?      │
│ - What tools are available?         │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│ REASON                              │
│ - LLM (Mistral) analyzes            │
│ - Decides next action               │
│ - Chooses a tool to call            │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│ ACT                                 │
│ - Execute the tool                  │
│ - kubectl_get, kubectl_describe     │
│ - Capture output                    │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│ LEARN                               │
│ - Add tool output to state          │
│ - Update messages                   │
│ - Continue loop                     │
└─────────────────────────────────────┘
```

### 2. LangChain vs LangGraph

```
LangChain:
├─ Base framework for LLM interactions
├─ Handles: Prompts, Messages, Tool binding
└─ Your usage: ChatOllama, Message classes

LangGraph:
├─ Built on LangChain
├─ Adds: State graphs, workflow orchestration
└─ Your usage: StateGraph, Nodes, Edges, astream()
```

### 3. State Management

```
All data flows through the State dict:

Initial: {"messages": [HumanMessage(...)]}
         │
         ▼ (Chatbot adds AI message)
         {"messages": [HumanMessage(...), AIMessage(...tool_calls)]}
         │
         ▼ (Tools execute, add result)
         {"messages": [..., AIMessage(...), ToolMessage(...result)]}
         │
         ▼ (Back to Chatbot, sees new info)
         (Repeat until done)
```

### 4. Tool Calling

```
Step 1: Bind tools to LLM
llm_with_tools = llm.bind_tools(tools)

Step 2: LLM can now output tool_calls
When you call: llm.invoke(messages)
Response includes: response.tool_calls = [...]

Step 3: Route to tools node
if response.tool_calls:
    go to "tools" node
else:
    END (exit graph)

Step 4: Execute tools
for each tool_call:
    tool_name = tool_call["name"]
    tool_args = tool_call["args"]
    result = execute_tool(tool_name, tool_args)
    create ToolMessage(result, tool_call_id)
```

---

## Debugging: How to Understand What's Happening

### See Mistral's Thinking

The logs show HTTP requests to Ollama:
```
2026-01-23 14:51:27,103 - httpx - INFO - HTTP Request: POST http://127.0.0.1:11434/api/chat "HTTP/1.1 200 OK"
```

This means Mistral received the prompt and is thinking.

### See Tool Calls

When tools execute:
```
2026-01-23 14:52:22,679 - httpx - INFO - HTTP Request: POST http://localhost:3001/mcp "HTTP/1.1 200 OK"
```

This is the MCP server executing Kubernetes commands.

### See Results

In collected_tool_results:
```python
{
  "output": "NAME              STATUS   AGE\ndefault           Active   365d\n...",
  "tool_name": "kubectl_get",
  "tool_call_id": "call_1"
}
```

### Trace the Flow

Enable debug logging:
```python
# In main.py
logging.basicConfig(level=logging.DEBUG)
```

Then run:
```bash
python -m src.langgraphagenticai.main --no-ui auditor 2>&1 | grep -E "tool|graph|state"
```

---

## Summary

### The Complete Picture

```
User runs app
    ↓
main.py initializes Mistral LLM
    ↓
graph_builder creates StateGraph
    ├─ Node 1: Chatbot (LLM + tools)
    └─ Node 2: Tools (execute kubectl)
    ↓
CLIOrchestrator starts execution
    ↓
GraphExecutor streams events
    ├─ Event 1: Chatbot decides "I need namespaces"
    ├─ Event 2: Tools execute "kubectl get namespaces"
    ├─ Event 3: Chatbot sees results, decides "I need pods"
    ├─ Event 4: Tools execute "kubectl get pods"
    ├─ ... (repeat)
    └─ Event N: Chatbot finishes "Here's my assessment"
    ↓
Collect results, analyze with ZeroTrustAnalyzer
    ↓
Display comprehensive security assessment
```

### Remember

1. **LangChain** = LLM Framework (Mistral, messages, tools)
2. **LangGraph** = Workflow Framework (State graph, agents, loops)
3. **Your App** = Orchestration (runs the agent, collects results, analyzes output)
4. **Agent Loop** = Observe → Reason → Act → Learn (repeats until done)
5. **Tools** = kubectl commands that Mistral can invoke

That's the core architecture!
