# Understanding the Code: LangChain & LangGraph Architecture

## 📚 Table of Contents

1. [What is LangChain?](#what-is-langchain)
2. [What is LangGraph?](#what-is-langgraph)
3. [How Your Application Works](#how-your-application-works)
4. [Complete Flow Diagram](#complete-flow-diagram)
5. [Code Walkthrough](#code-walkthrough)
6. [Key Concepts](#key-concepts)

---

## What is LangChain?

### Overview
**LangChain** is a Python framework for building applications with Large Language Models (LLMs).

### Core Components

```
LangChain
├── Language Models (LLMs)
│   ├── OpenAI (GPT-4, etc.)
│   ├── Anthropic (Claude)
│   ├── Ollama (Local models like Mistral, LLama2)
│   └── Others...
│
├── Chains
│   ├── Prompt + LLM + Output Parser
│   ├── Sequential operations
│   └── Complex workflows
│
├── Tools/Agents
│   ├── Define what actions the LLM can take
│   ├── Execute external functions
│   └── Allow LLM to reason and decide which tool to use
│
└── Memory
    ├── Store conversation history
    ├── Context management
    └── State tracking
```

### In Your Application

You're using **LangChain** for:

```python
# 1. LLM Integration (in LLMS/ollamallm.py)
from langchain_ollama.chat_models import ChatOllama

llm = ChatOllama(model="mistral:latest", temperature=0.0)
# This is your local Mistral model running via Ollama

# 2. Tool Binding (in graph_builder.py)
llm_with_tools = self.llm.bind_tools(tools)
# Attach Kubernetes tools to the LLM so it can call them

# 3. Messages (in nodes/chatbot_with_Tool_node.py)
from langchain_core.messages import SystemMessage, AIMessage
# Handle conversation messages
```

---

## What is LangGraph?

### Overview
**LangGraph** is built on top of LangChain. It provides a **State Graph** system for building multi-step AI workflows.

### Key Concept: State Graph

A **State Graph** is like a flowchart where:
- **Nodes** = Processing steps (can run LLM, execute tools, analyze data, etc.)
- **Edges** = Transitions between nodes (can be conditional)
- **State** = Shared data passed between nodes

```
┌─────────────────┐
│ Entry Point     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐       Can execute
│  Chatbot Node   │───────tools?
└────┬────────────┘
     │ No     │ Yes
     │        │
     │        ▼
     │   ┌──────────────┐
     │   │  Tools Node  │
     │   │ (kubectl_get)│
     │   └──────┬───────┘
     │          │
     │          ▼
     └────────► Exit
```

### In Your Application

Your application has **2 main nodes**:

```python
# In graph_builder.py
sg = StateGraph(State)  # Create a state graph

# Node 1: Chatbot
sg.add_node("chatbot", chatbot_node)
# Responsibilities:
# - Accept user message
# - Send to LLM with tools
# - LLM decides: Should I call a tool or respond?

# Node 2: Tools
sg.add_node("tools", tool_node)
# Responsibilities:
# - Execute the tool the LLM requested
# - Return results back to chatbot

# Flow Control
sg.set_entry_point("chatbot")  # Start here
sg.add_conditional_edges("chatbot", tools_condition)
# After chatbot: If tool was called, go to tools node
#                Otherwise, exit (end conversation)
```

---

## How Your Application Works

### Complete Execution Flow

```
User Input: "Perform Zero Trust Auditor checks"
    │
    ▼
┌──────────────────────────────────────────────────────┐
│ 1. main.py - Entry Point                             │
│    - Parse CLI arguments                             │
│    - Initialize components                           │
└──────────────────┬───────────────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────────────────┐
│ 2. CLIOrchestrator.run_auditor()                     │
│    - Set up the workflow                             │
│    - Create audit message                            │
└──────────────────┬───────────────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────────────────┐
│ 3. GraphExecutor.execute_graph()                     │
│    - Call: graph.astream({"messages": [message]})    │
│    - Async stream events from the graph              │
└──────────────────┬───────────────────────────────────┘
                   │
                   ▼
         ┌─────────────────────┐
         │  LangGraph Execution│
         │   (StateGraph)      │
         └──────────┬──────────┘
                    │
      ┌─────────────┴─────────────┐
      │                           │
      ▼                           ▼
┌──────────────────┐        ┌──────────────────┐
│  CHATBOT NODE 1  │        │   STATE          │
│                  │        │  ┌────────────┐  │
│ LLM + Tools      │        │  │ messages   │  │
│                  │        │  └────────────┘  │
│ Input: User msg  │        │                  │
│ Output:          │        │ Shared between   │
│  - Tool call? OR │        │ all nodes        │
│  - Response?     │        └──────────────────┘
└────────┬─────────┘
         │
   ┌─────┴─────┐
   │ Tool call?│
   └─────┬─────┘
         │
    ┌────┴──────┐
    │ Yes      No│
    ▼            ▼
┌──────────┐  ┌──────────┐
│TOOLS NODE│  │ End      │
│          │  │ (Exit)   │
│Execute   │  └──────────┘
│kubectl   │
│commands  │
└────┬─────┘
     │
     ▼ (Return results)
Back to CHATBOT NODE
(with tool output added to messages)
```

---

## Complete Flow Diagram

### Step-by-Step Execution

```
Step 1: Initialize
─────────────────
  User runs: python -m src.langgraphagenticai.main --no-ui auditor
                    │
                    ▼
          CLIArgumentParser
          parses command → "Zero Trust Auditor"
                    │
                    ▼
          Initialize:
          ├─ OllamaLLM (Mistral model)
          ├─ GraphBuilder
          ├─ GraphExecutor
          ├─ ProbeManager
          └─ CLIOrchestrator


Step 2: Build Graph
───────────────────
  GraphBuilder.build_auditor_graph()
                    │
                    ▼
          1. Load Kubernetes tools (kubectl_get, kubectl_describe, etc.)
          2. Bind tools to Mistral LLM
             llm_with_tools = llm.bind_tools(tools)
          3. Create StateGraph
             ├─ Node: "chatbot" (LLM with tools)
             └─ Node: "tools" (execute tools)
          4. Add edges
             chatbot → tools (if tool called)
             tools → end (return to chatbot with results)
          5. Compile graph


Step 3: Execute Graph
─────────────────────
  GraphExecutor.execute_graph(graph, user_message, ...)
                    │
                    ▼
          graph.astream({"messages": [user_message]})
          
          Async streaming events:
          
          Event 1: {"chatbot": {"messages": [AIMessage(...)]}}
          ├─ Mistral LLM receives:
          │  - AUDITOR_PROMPT (system message)
          │  - User message: "Execute auditor checks"
          │  - List of available tools
          │
          ├─ Mistral analyzes and decides:
          │  "I need to check Kubernetes resources"
          │
          └─ Output: Tool call
             {
               "name": "kubectl_get",
               "parameters": {
                 "resourceType": "namespaces"
               }
             }
          
          Event 2: {"tools": {"messages": [ToolMessage(...)]}}
          ├─ Execute: kubectl get namespaces
          ├─ Capture output
          └─ Create ToolMessage with results
          
          Event 3: Back to chatbot with results
          ├─ Mistral receives tool output
          ├─ Makes another decision:
          │  - Call another tool? Or
          │  - Provide final response?
          └─ Loop continues...


Step 4: Collect Results
───────────────────────
  GraphExecutor collects:
  ├─ Tool names called
  ├─ Tool outputs
  ├─ Probe keys executed
  └─ Tracking data
  
  Returns: (tool_results, executed_probes)


Step 5: Analysis & Output
──────────────────────────
  ZeroTrustAnalyzer.analyze_and_generate_report()
  ├─ Filter results
  ├─ Parse outputs
  └─ Generate assessment

  CLIOutputFormatter.get_final_output()
  └─ Format and display to user
```

---

## Code Walkthrough

### 1. State Definition (state.py)

```python
from typing_extensions import TypedDict, List
from langgraph.graph.message import add_messages
from typing import Annotated

class State(TypedDict):
    """The state shared across all graph nodes"""
    messages: Annotated[List, add_messages]
```

**What it does:**
- Defines what data flows through the graph
- `messages` = list of conversation messages (human + AI)
- `add_messages` = merger function (adds new messages to existing list)

**In action:**
```
Initial state:
{"messages": [HumanMessage(content="Execute auditor checks")]}

After chatbot node:
{"messages": [
  HumanMessage(content="Execute auditor checks"),
  AIMessage(content="...", tool_calls=[...])
]}

After tools node:
{"messages": [
  HumanMessage(content="Execute auditor checks"),
  AIMessage(content="...", tool_calls=[...]),
  ToolMessage(content="<kubectl output>", tool_call_id="...")
]}
```

### 2. Chatbot Node (chatbot_with_Tool_node.py)

```python
class ChatbotWithToolNode:
    def __init__(self, model, system_prompt):
        self.llm = model  # Mistral LLM bound with tools
        self.system_prompt = system_prompt  # AUDITOR_PROMPT or CREATOR_PROMPT

    def create_chatbot(self, tools, usecase):
        """Create the actual node function"""
        async def chatbot_node(state: State) -> dict:
            # 1. Get all messages from state
            messages = state["messages"]
            
            # 2. Prepend system prompt
            system = SystemMessage(content=self.system_prompt)
            
            # 3. Call LLM with system + messages
            # LLM sees available tools and decides which to call
            response = self.llm.invoke([system] + messages)
            
            # 4. Check if LLM made tool calls
            tool_calls = response.tool_calls
            
            if tool_calls:
                # LLM decided to use tools
                # Response has: content + tool_calls
                return {"messages": [response]}
            else:
                # LLM gave final answer
                return {"messages": [response]}
        
        return chatbot_node
```

**Flow:**
```
Input state:
├─ Messages: [user query]
├─ Available tools: [kubectl_get, kubectl_describe, ...]
└─ System prompt: AUDITOR_PROMPT

↓

LLM Decision:
├─ Reads user query
├─ Reads system prompt (tells it to perform audit)
├─ Sees available tools
└─ Decides: "I need to check namespaces first"

↓

Output:
├─ Message with tool_calls: [
│    {
│      "type": "tool_use",
│      "id": "tool_123",
│      "name": "kubectl_get",
│      "input": {"resourceType": "namespaces"}
│    }
│  ]
└─ Added to state["messages"]
```

### 3. Tools Node

```python
# In graph_builder.py
tools = await get_tools()  # Load Kubernetes tools
tool_node = create_tool_node(tools)  # Create execution node

# Later in StateGraph:
sg.add_node("tools", tool_node)
```

**What happens:**
```
Tool node receives state with:
└─ messages: [..., AIMessage with tool_calls]

Tool node:
1. Extracts tool_calls from AIMessage
2. For each tool_call:
   ├─ Look up tool by name (kubectl_get)
   ├─ Execute: kubectl get namespaces
   ├─ Capture output
   └─ Create ToolMessage with results
3. Add all ToolMessages to state
4. Return updated state
```

### 4. Graph Compilation & Execution

```python
# In graph_builder.py
sg = StateGraph(State)
sg.add_node("chatbot", chatbot_node)
sg.add_node("tools", tool_node)
sg.set_entry_point("chatbot")
sg.add_conditional_edges("chatbot", tools_condition)

compiled = sg.compile()

# In executor.py
async for event in compiled.astream(
    {"messages": [("human", user_message)]},
    {"recursion_limit": 50}
):
    # Each event is a partial state update
    # Process and track results
```

**Conditional edges explained:**
```
tools_condition() function determines:
├─ If message has tool_calls
│  ├─ Yes: route to "tools" node
│  └─ No: END (exit graph)
└─ If "tools" node output
   └─ Always route back to "chatbot" node
```

---

## Key Concepts

### 1. **Agentic Loop**

Your application implements an **agent loop**:

```
┌─────────────────────────────────────┐
│     Agent Loop (Agentic AI)         │
├─────────────────────────────────────┤
│                                     │
│  1. Observe                         │
│     └─ What's the current state?    │
│                                     │
│  2. Reason                          │
│     └─ What should I do next?       │
│        (LLM decides based on tools) │
│                                     │
│  3. Act                             │
│     └─ Execute the chosen tool      │
│        (kubectl_get, kubectl_describe)
│                                     │
│  4. Learn                           │
│     └─ Update state with results    │
│                                     │
│  Loop until task complete           │
│                                     │
└─────────────────────────────────────┘
```

In your code:
```python
# Observe: messages in state
messages = state["messages"]

# Reason: LLM thinks about what to do
response = llm.invoke([system] + messages)

# Act: Tool is executed
tool_output = execute_tool(response.tool_calls[0])

# Learn: Add tool output to messages
state["messages"].append(ToolMessage(tool_output))

# Loop: Back to LLM with new information
```

### 2. **Tool Binding**

```python
# Original LLM
llm = ChatOllama(model="mistral:latest")

# With tools attached
llm_with_tools = llm.bind_tools(tools)

# Now when you call it:
response = llm_with_tools.invoke(messages)
# Response might include:
# - response.content = text response
# - response.tool_calls = [{"name": "kubectl_get", "args": {...}}]
```

### 3. **State Management**

The `State` dict flows through the graph:

```
Initial State:
├─ messages: [HumanMessage("Execute auditor checks")]

Chatbot Node Input:
├─ messages: [HumanMessage(...)]

Chatbot Node Output:
├─ messages: [HumanMessage(...), AIMessage(...tool_calls=[...])]

Tools Node Input:
├─ messages: [HumanMessage(...), AIMessage(...tool_calls=[...])]

Tools Node Output:
├─ messages: [HumanMessage(...), AIMessage(...), ToolMessage(...result...)]

Back to Chatbot Input:
├─ messages: [HumanMessage(...), AIMessage(...), ToolMessage(...)]
```

### 4. **Async Streaming**

```python
async for event in graph.astream(input_state, config):
    # event is a dict like:
    # {"node_name": {"messages": [...]}}
    
    # Example events:
    # {"chatbot": {"messages": [AIMessage(...)]}}
    # {"tools": {"messages": [ToolMessage(...)]}}
```

---

## How LangChain Components Work Together

```
┌─────────────────────────────────────────────────────────┐
│ LangChain / LangGraph Architecture in Your App         │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Language Model (LangChain)                             │
│  ├─ ChatOllama (Mistral via Ollama)                    │
│  ├─ Tool Binding                                        │
│  └─ Message Processing                                  │
│         ▲                                               │
│         │ (send messages)                               │
│         │                                               │
│  Orchestration (LangGraph)                              │
│  ├─ State Graph Structure                              │
│  ├─ Node Management (Chatbot + Tools)                  │
│  ├─ Conditional Routing                                │
│  └─ Event Streaming                                     │
│         ▲                                               │
│         │ (control flow)                                │
│         │                                               │
│  Application Layer (Your Code)                          │
│  ├─ CLIOrchestrator (workflow coordination)            │
│  ├─ GraphExecutor (execution & collection)             │
│  ├─ ProbeManager (state persistence)                   │
│  └─ ZeroTrustAnalyzer (result analysis)                │
│         ▲                                               │
│         │ (user commands)                               │
│         │                                               │
│  User Input                                             │
│  "Execute Zero Trust Auditor checks"                    │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## Summary

### What Happens When You Run the App

1. **User input**: "Perform Zero Trust Auditor checks"

2. **LangGraph creates a conversation loop**:
   - Chatbot node receives input
   - Sends to Mistral LLM with tools
   - Mistral decides: "I need to check namespaces"

3. **Tools node executes**:
   - Runs: `kubectl get namespaces`
   - Returns results to chatbot

4. **Chatbot continues**:
   - Sees results
   - Decides: "Check pods next"
   - Makes another tool call

5. **Loop repeats** until Mistral says: "I've gathered enough info, here's my assessment"

6. **Your code processes** the accumulated results and generates a report

### Key Takeaways

- **LangChain** = Framework for LLM interactions
- **LangGraph** = Framework for building multi-step AI workflows
- **Your App** = Uses LangGraph to orchestrate Kubernetes auditing with Mistral LLM
- **Agent Loop** = The core pattern (Observe → Reason → Act → Learn)
- **Tools** = Kubernetes commands that Mistral can call
- **State** = Messages flowing through the graph, accumulating information
