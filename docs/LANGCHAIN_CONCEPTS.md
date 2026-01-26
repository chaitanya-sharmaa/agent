# LangChain & LangGraph Concepts Explained

## Quick Comparison Table

| Concept | What It Is | In Your App | Real Example |
|---------|-----------|------------|--------------|
| **LangChain** | Python framework for LLM apps | ChatOllama, Messages, Tool binding | `ChatOllama(model="mistral:latest")` |
| **LangGraph** | Workflow orchestration on LangChain | StateGraph, Nodes, Edges, astream | Graph with Chatbot + Tools nodes |
| **State** | Shared data between nodes | `{"messages": [...]}` | Conversation history flowing through graph |
| **Node** | Processing step | Chatbot, Tools | LLM thinking, kubectl executing |
| **Tool** | Function LLM can call | kubectl_get, helm_install | `kubectl get namespaces` |
| **Agent** | LLM that can use tools | Mistral deciding which tool to call | "I need namespaces, calling kubectl_get" |
| **Message** | Data unit in state | HumanMessage, AIMessage, ToolMessage | User input, LLM response, tool output |

---

## Understanding Each Component

### 1. LangChain Components

#### ChatOllama (Your LLM)

```python
from langchain_ollama.chat_models import ChatOllama

llm = ChatOllama(model="mistral:latest", temperature=0.0)

# What it does:
# - Connects to Ollama server (localhost:11434)
# - Sends prompts to Mistral
# - Receives text responses

# Usage:
response = llm.invoke([
    SystemMessage("You are a helpful assistant"),
    HumanMessage("What's the capital of France?")
])
# Output: AIMessage(content="The capital of France is Paris")
```

#### Messages

```python
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage

# System message: Instructions for the LLM
system_msg = SystemMessage(content="You are a Kubernetes expert")

# Human message: User input
human_msg = HumanMessage(content="List all pods")

# AI message: LLM response
ai_msg = AIMessage(content="I'll get the pods for you", tool_calls=[...])

# Tool message: Result from executing a tool
tool_msg = ToolMessage(
    content="pod-1\npod-2\npod-3",
    tool_call_id="call_1"
)
```

#### Tool Binding

```python
# Without tools: LLM just responds
llm.invoke(messages) → "Here are the pods..."

# With tools: LLM can decide to use tools
llm_with_tools = llm.bind_tools(tools)
llm_with_tools.invoke(messages) → {
    "content": "I'll check the pods",
    "tool_calls": [
        {
            "name": "kubectl_get",
            "args": {"resourceType": "pods"}
        }
    ]
}
```

---

### 2. LangGraph Components

#### StateGraph

```python
from langgraph.graph import StateGraph
from typing_extensions import TypedDict, Annotated
from langgraph.graph.message import add_messages

# Define state shape
class State(TypedDict):
    messages: Annotated[List, add_messages]

# Create graph
graph = StateGraph(State)

# Add nodes and edges
graph.add_node("chatbot", chatbot_function)
graph.add_node("tools", tools_function)
graph.set_entry_point("chatbot")
graph.add_conditional_edges("chatbot", tools_condition)

# Compile for execution
compiled_graph = graph.compile()
```

#### Nodes

A **node** is a Python function that:
- Takes a state dict as input
- Performs work (call LLM, execute tool, etc.)
- Returns updated state dict

```python
def chatbot_node(state: State) -> dict:
    """Process messages through the LLM"""
    messages = state["messages"]
    response = llm.invoke(messages)
    return {"messages": [response]}

def tools_node(state: State) -> dict:
    """Execute tools requested by the LLM"""
    messages = state["messages"]
    last_message = messages[-1]
    
    results = []
    for tool_call in last_message.tool_calls:
        result = execute_tool(tool_call["name"], tool_call["args"])
        results.append(ToolMessage(result, tool_call_id=tool_call["id"]))
    
    return {"messages": results}
```

#### Edges

Edges determine the flow between nodes:

```python
# Unconditional edge: always go from A to B
graph.add_edge("chatbot", "tools")

# Conditional edge: decision based on state
graph.add_conditional_edges(
    "chatbot",
    tools_condition  # Function that returns next node
)

# Conditional function:
def tools_condition(state: State) -> str:
    messages = state["messages"]
    last_message = messages[-1]
    
    if last_message.tool_calls:
        return "tools"  # Go to tools node
    else:
        return "__end__"  # Exit graph
```

#### Streaming

```python
# Stream events as graph executes
async for event in graph.astream(
    input_state={"messages": [HumanMessage("Hello")]},
    config={"recursion_limit": 50}
):
    # Each event is a partial state update
    # event = {"node_name": {"messages": [...]}}
    
    # Example events:
    # {"chatbot": {"messages": [AIMessage(...)]}}
    # {"tools": {"messages": [ToolMessage(...)]}}
    # {"chatbot": {"messages": [AIMessage(...)]}}
```

---

## How They Work Together in Your App

### The Flow

```
┌─────────────────────────────────────────────────────┐
│ LangChain Layer (LLM & Messages)                    │
├─────────────────────────────────────────────────────┤
│                                                     │
│ ChatOllama ←→ Messages                              │
│ (Mistral)    (Conversation)                         │
│                                                     │
│ Tool binding:                                       │
│ llm_with_tools = llm.bind_tools(tools)             │
│                                                     │
│ Now LLM can output:                                 │
│ - text responses                                    │
│ - tool_calls                                        │
│                                                     │
└────────────────┬────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────┐
│ LangGraph Layer (Workflow & State)                  │
├─────────────────────────────────────────────────────┤
│                                                     │
│ StateGraph                                          │
│ ├─ State: {"messages": [...]}                      │
│ ├─ Nodes: chatbot, tools                           │
│ └─ Edges: conditional routing                      │
│                                                     │
│ Execution Loop:                                     │
│ 1. Start at chatbot node                           │
│ 2. Send messages to LLM                            │
│ 3. LLM responds (maybe with tool_calls)            │
│ 4. Check: tool_calls present?                      │
│ 5. If yes → go to tools node                       │
│ 6. If no → exit                                    │
│ 7. Tools node executes, adds results               │
│ 8. Loop back to chatbot with new info              │
│                                                     │
└────────────────┬────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────┐
│ Your Application Layer                              │
├─────────────────────────────────────────────────────┤
│                                                     │
│ - CLI Orchestrator: coordinates workflow           │
│ - Graph Executor: runs graph, collects results     │
│ - Probe Manager: tracks state                      │
│ - Zero Trust Analyzer: interprets results          │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

## Real World Analogy

Think of it like a **restaurant kitchen**:

```
LangChain = Your Chef
├─ Can think (LLM)
├─ Can read recipes (prompts)
└─ Can execute actions (tool binding)

LangGraph = Kitchen Workflow
├─ Station 1: Chef reads order, decides what to do
├─ Station 2: Sous chef executes the tasks
├─ Station 3: Chef checks results, decides next step
└─ Repeat until dish is complete

Your App = Restaurant Manager
├─ Takes customer order
├─ Routes to kitchen (LangGraph)
├─ Collects plated dish
└─ Serves to customer (output report)

Example:
┌─────────────────────────────────────────────────────┐
│ Customer: "I want a steak"                          │
└──────────────┬──────────────────────────────────────┘
               │
               ▼ (Restaurant Manager routes to kitchen)
┌─────────────────────────────────────────────────────┐
│ Chef (Station 1, LLM with tools)                    │
│ Reads: "Make a steak"                              │
│ Thinks: "I need to"                                │
│ 1. Prep meat                                       │
│ 2. Cook at high heat                               │
│ 3. Let rest                                        │
│ Calls: "prep_meat_tool"                            │
└──────────────┬──────────────────────────────────────┘
               │
               ▼ (LangGraph routes to tools node)
┌─────────────────────────────────────────────────────┐
│ Sous Chef (Station 2, Execute tools)               │
│ Executes:                                          │
│ - prep_meat_tool: "Meat prepped"                   │
│ Returns result to chef                             │
└──────────────┬──────────────────────────────────────┘
               │
               ▼ (LangGraph routes back to chatbot)
┌─────────────────────────────────────────────────────┐
│ Chef Sees: "Meat prepped"                          │
│ Decides: "Now cook at high heat"                   │
│ Calls: "cook_tool"                                 │
└──────────────┬──────────────────────────────────────┘
               │
               ▼ ... (repeat) ...
               │
               ▼ (Eventually)
┌─────────────────────────────────────────────────────┐
│ Chef: "Steak is done! Here it is."                │
│ (No more tools needed)                             │
└──────────────┬──────────────────────────────────────┘
               │
               ▼ (LangGraph exits)
┌─────────────────────────────────────────────────────┐
│ Restaurant Manager                                 │
│ Plates steak, serves to customer                   │
└─────────────────────────────────────────────────────┘
```

---

## Key Differences

### Without LangGraph (Just LangChain)

```python
# You manage the loop manually
messages = [SystemMessage("..."), HumanMessage("Execute audit")]

for iteration in range(10):
    response = llm.invoke(messages)
    messages.append(response)
    
    if response.tool_calls:
        for tool_call in response.tool_calls:
            result = execute_tool(...)
            messages.append(ToolMessage(result))
    else:
        break  # LLM done

# Problems:
# - Manual state management
# - Error handling everywhere
# - Hard to debug
# - Repetitive code
```

### With LangGraph (What You Use)

```python
# LangGraph manages the loop
graph = StateGraph(State)
graph.add_node("chatbot", chatbot_node)
graph.add_node("tools", tools_node)
graph.add_conditional_edges("chatbot", tools_condition)

compiled = graph.compile()

# Run it
async for event in compiled.astream({"messages": [...]}):
    # LangGraph handles routing, state management, looping
    process_event(event)

# Benefits:
# - Declarative workflow definition
# - Built-in state management
# - Automatic routing
# - Easy to extend
```

---

## Visual: Data Flow

### Message Types and Flow

```
Initial State:
{
  "messages": [
    HumanMessage("Execute audit checks")
  ]
}
          ↓
┌─────────────────────────────────────────┐
│ Chatbot Node 1                          │
│ - Receives messages                     │
│ - Sends to Mistral LLM                  │
│ - LLM reads system prompt               │
│ - LLM thinks about tools                │
└─────────────────────────────────────────┘
          ↓
AI Thinks: "Need to check namespaces"
          ↓
Updated State:
{
  "messages": [
    HumanMessage("Execute audit checks"),
    AIMessage(
      content="Checking resources",
      tool_calls=[{
        "id": "call_1",
        "name": "kubectl_get",
        "args": {"resourceType": "namespaces"}
      }]
    )
  ]
}
          ↓
┌─────────────────────────────────────────┐
│ Conditional Edge: tools_condition()     │
│ "Does last message have tool_calls?"    │
│ Answer: YES → go to tools node          │
└─────────────────────────────────────────┘
          ↓
┌─────────────────────────────────────────┐
│ Tools Node                              │
│ - Extract tool_call                     │
│ - Execute: kubectl get namespaces       │
│ - Capture output                        │
└─────────────────────────────────────────┘
          ↓
Tool Output: "default, kube-system, istio-system"
          ↓
Updated State:
{
  "messages": [
    HumanMessage("Execute audit checks"),
    AIMessage(...tool_calls...),
    ToolMessage(
      content="default, kube-system, istio-system",
      tool_call_id="call_1"
    )
  ]
}
          ↓
┌─────────────────────────────────────────┐
│ Conditional Edge: route back to chatbot │
└─────────────────────────────────────────┘
          ↓
Back to Chatbot with new state
          ↓
AI Sees: "Got namespaces. Now check pods."
          ↓
... (repeat) ...
          ↓
AI Decides: "I have enough info"
(No tool_calls in response)
          ↓
┌─────────────────────────────────────────┐
│ Conditional Edge: no tools → END        │
└─────────────────────────────────────────┘
          ↓
Final Message added to state with assessment
```

---

## Summary: The Three Layers

```
Layer 3: Your Code
├─ main.py (entry point)
├─ cli_orchestrator.py (workflow)
├─ graph_executor.py (runs & collects)
└─ zero_trust_analyzer.py (analysis)

Layer 2: LangGraph
├─ StateGraph (workflow engine)
├─ Nodes (chatbot, tools)
├─ Edges (routing)
└─ astream (execution)

Layer 1: LangChain
├─ ChatOllama (Mistral LLM)
├─ Messages (conversation)
├─ Tool binding (capabilities)
└─ Tool execution (actions)
```

Each layer uses the layer below it. You orchestrate LangGraph, which uses LangChain components.

---

## Next Steps to Master This

1. **Run the app with debug logging** to see message flow
2. **Add print statements** in chatbot_node to see what LLM sees
3. **Inspect state dict** to understand data flow
4. **Trace one full execution** step by step
5. **Modify a prompt** to see how it changes LLM decisions
6. **Add a new tool** to expand what the agent can do

This understanding will unlock the ability to build your own agentic AI systems!
