#!/usr/bin/env python3
"""
Test script for comprehensive security audit in CLI mode
"""
import asyncio
import json
from src.langgraphagenticai.LLMS.ollamallm import OllamaLLM
from langchain_mcp_adapters.client import MultiServerMCPClient
from src.langgraphagenticai.graph.graph_builder import GraphBuilder
from src.langgraphagenticai.config.config_loader import get_config

async def main():
    print("=" * 80)
    print("COMPREHENSIVE SECURITY AUDIT - CLI TEST")
    print("=" * 80)
    
    # Initialize LLM
    print("\n🔧 Initializing LLM...")
    user_controls = {"selected_ollama_model": "mistral:latest"}
    model = OllamaLLM(user_controls).get_llm_model()
    
    # Stage 1: Get namespaces
    print("\n" + "=" * 80)
    print("STAGE 1: Getting all namespaces")
    print("=" * 80)
    
    builder = GraphBuilder(model)
    stage1_graph = await builder.setup_graph("Comprehensive Security Auditor")
    
    stage1_input = {"messages": [("user", "Query all Kubernetes namespaces to get the complete list.")]}
    
    print("\n📊 Executing Stage 1...")
    stage1_results = []
    async for event in stage1_graph.astream(stage1_input):
        for node_name, node_output in event.items():
            print(f"\n[{node_name}]")
            if node_name == "chatbot":
                messages = node_output.get("messages", [])
                for msg in messages:
                    if hasattr(msg, "tool_calls") and msg.tool_calls:
                        print(f"  Tool calls: {len(msg.tool_calls)}")
                        for tc in msg.tool_calls:
                            print(f"    - {tc.get('name', 'unknown')}: {tc.get('args', {})}")
            elif node_name == "tools":
                for message in node_output.get("messages", []):
                    if hasattr(message, "content"):
                        # Content is a list of dicts with 'type' and 'text' fields
                        content = message.content
                        if isinstance(content, list):
                            for item in content:
                                if isinstance(item, dict) and item.get('type') == 'text':
                                    text_content = item.get('text', '')
                                    stage1_results.append(text_content)
                                    print(f"  Tool result: {text_content[:200]}...")
                        elif isinstance(content, str):
                            stage1_results.append(content)
                            print(f"  Tool result: {content[:200]}...")
    
    # Parse namespaces
    namespaces = []
    for result in stage1_results:
        try:
            data = json.loads(result)
            if "items" in data:
                for item in data["items"]:
                    if item.get("kind") == "Namespace":
                        ns_name = item.get("name")
                        namespaces.append(ns_name)
                        print(f"  - {ns_name}")
        except:
            pass
    
    print(f"\n✅ Stage 1 Complete: Found {len(namespaces)} namespaces")
    
    # Stage 2: Direct MCP tool calls per resource type (skip LLM to avoid duplicate calls)
    print("\n" + "=" * 80)
    print("STAGE 2: Querying each resource type individually (direct MCP)")
    print("=" * 80)

    resource_types = ["pods", "deployments", "daemonsets", "statefulsets", "rolebindings", "networkpolicies"]
    test_namespaces = namespaces[:3]
    total_queries = 0
    stage2_results = []
    namespace_resources = {}  # Initialize tracking dict

    config = get_config()
    client = MultiServerMCPClient({
        "kubernetes": {
            "url": config.get_mcp_url(),
            "transport": config.get_mcp_transport(),
        }
    })
    tools = await client.get_tools()
    kubectl_get_tool = next(t for t in tools if t.name == "kubectl_get")

    for ns_idx, ns in enumerate(test_namespaces, 1):
        print(f"\n📦 Processing namespace {ns_idx}/{len(test_namespaces)}: {ns}")
        print("=" * 80)
        ns_query_count = 0
        ns_tool_calls = []
        ns_results = {}
        # Initialize this namespace in our tracking dict
        namespace_resources[ns] = {
            "pods": {"count": 0, "items": []},
            "deployments": {"count": 0, "items": []},
            "daemonsets": {"count": 0, "items": []},
            "statefulsets": {"count": 0, "items": []},
            "rolebindings": {"count": 0, "items": []},
            "networkpolicies": {"count": 0, "items": []},
        }

        for rt in resource_types:
            args = {"resourceType": rt, "namespace": ns, "output": "json"}
            try:
                result = await kubectl_get_tool.ainvoke(args)
                ns_query_count += 1
                total_queries += 1
                ns_tool_calls.append(f"kubectl_get({rt})")
                ns_results[rt] = result
                
                # Parse and store in namespace_resources
                parsed = None
                if isinstance(result, list) and len(result) > 0 and isinstance(result[0], dict):
                    if "text" in result[0]:
                        parsed = json.loads(result[0]["text"])
                
                if parsed and isinstance(parsed, dict) and "items" in parsed:
                    items = parsed.get("items", [])
                    namespace_resources[ns][rt]["count"] = len(items)
                    namespace_resources[ns][rt]["items"] = items
                
                if isinstance(result, dict) and "content" in result:
                    stage2_results.append(result["content"])
                else:
                    stage2_results.append(str(result))
            except Exception as e:
                ns_tool_calls.append(f"kubectl_get({rt}) [error: {e}]")
                ns_results[rt] = {"error": str(e)}

        print(f"  ✅ Executed {ns_query_count} queries for {ns}")
        print(f"     Tool calls: {', '.join(ns_tool_calls)}")
        
        # Display resource details for this namespace
        print(f"\n  📊 RESOURCES IN {ns}:")
        for rt in resource_types:
            print(f"\n    {rt.upper()}:")
            result_data = ns_results.get(rt)
            try:
                # Extract text from MCP content wrapper if present
                if isinstance(result_data, list) and len(result_data) > 0 and isinstance(result_data[0], dict):
                    if "text" in result_data[0]:
                        result_data = json.loads(result_data[0]["text"])
                    elif "type" in result_data[0] and result_data[0]["type"] == "text":
                        result_data = json.loads(result_data[0].get("text", "{}"))
                elif isinstance(result_data, str):
                    result_data = json.loads(result_data)
                elif isinstance(result_data, dict) and "content" in result_data:
                    content = result_data["content"]
                    if isinstance(content, str):
                        result_data = json.loads(content)
                    elif isinstance(content, list) and len(content) > 0:
                        if isinstance(content[0], dict) and "text" in content[0]:
                            result_data = json.loads(content[0]["text"])
                        else:
                            result_data = content[0]
                    else:
                        result_data = content
                
                if isinstance(result_data, dict) and "items" in result_data:
                    items = result_data["items"]
                    if items:
                        print(f"      ✓ Found {len(items)} {rt}")
                        for item in items[:2]:  # Show first 2 items
                            name = item.get("name", "unknown")
                            print(f"        - {name}")
                    else:
                        print(f"      No {rt} found")
                else:
                    print(f"      Result: {str(result_data)[:80]}")
            except Exception as e:
                print(f"      Error parsing: {str(e)[:60]}")

    print(f"\n✅ Stage 2 Complete: Executed {total_queries} total queries")
    
    # ============================================
    # ANALYSIS & SUMMARY
    # ============================================
    print("\n" + "=" * 80)
    print("COMPREHENSIVE SECURITY AUDIT ANALYSIS")
    print("=" * 80)
    
    # Display by namespace
    for ns in test_namespaces:
        print(f"\n\n{'='*80}")
        print(f"📦 NAMESPACE: {ns.upper()}")
        print('='*80)
        
        resources = namespace_resources[ns]
        
        # Summary table
        print(f"\n{'Resource Type':<20} {'Count':<10} {'Status':<10}")
        print("-" * 40)
        for rt in resource_types:
            count = resources[rt]["count"]
            status = "✓ Found" if count > 0 else "○ Empty"
            print(f"{rt:<20} {count:<10} {status:<10}")
        
        # Detailed resource listing
        for rt in resource_types:
            items = resources[rt]["items"]
            if items:
                print(f"\n  📋 {rt.upper()} ({len(items)} found):")
                for item in items[:5]:  # Show first 5
                    name = item.get("name", "unknown")
                    status = item.get("status", {}).get("phase", "N/A") if isinstance(item.get("status"), dict) else "N/A"
                    print(f"     ✓ {name:<40} [Status: {status}]")
                if len(items) > 5:
                    print(f"     ... and {len(items) - 5} more")
    
    # ============================================
    # SECURITY ANALYSIS
    # ============================================
    print(f"\n\n{'='*80}")
    print("🔒 SECURITY ASSESSMENT")
    print('='*80)
    
    security_findings = {
        "high_risk": [],
        "medium_risk": [],
        "low_risk": [],
        "suggestions": []
    }
    
    # Analyze resources
    total_pods = sum(r["pods"]["count"] for r in namespace_resources.values())
    total_deployments = sum(r["deployments"]["count"] for r in namespace_resources.values())
    total_daemonsets = sum(r["daemonsets"]["count"] for r in namespace_resources.values())
    total_statefulsets = sum(r["statefulsets"]["count"] for r in namespace_resources.values())
    total_rolebindings = sum(r["rolebindings"]["count"] for r in namespace_resources.values())
    total_networkpolicies = sum(r["networkpolicies"]["count"] for r in namespace_resources.values())
    
    # Generate findings
    if total_pods == 0:
        security_findings["low_risk"].append("No pods running in queried namespaces")
    
    if total_networkpolicies == 0:
        security_findings["high_risk"].append("⚠️  NO NETWORK POLICIES FOUND - Cluster may lack network segmentation")
        security_findings["suggestions"].append("• Implement NetworkPolicies to restrict pod-to-pod communication")
        security_findings["suggestions"].append("• Create default-deny policies and allow specific flows")
    
    if total_deployments > 0 and total_rolebindings == 0:
        security_findings["medium_risk"].append("Deployments found but no role bindings defined")
        security_findings["suggestions"].append("• Define RoleBindings for proper RBAC control")
    
    if total_daemonsets > 0:
        security_findings["medium_risk"].append("DaemonSets detected - ensure they run only on intended nodes")
        security_findings["suggestions"].append("• Review DaemonSet node selectors and taints/tolerations")
    
    if total_statefulsets > 0:
        security_findings["medium_risk"].append("StatefulSets found - verify persistent volume security")
        security_findings["suggestions"].append("• Ensure PVCs have proper access controls")
        security_findings["suggestions"].append("• Implement StorageClass encryption policies")
    
    security_findings["suggestions"].append("• Enable Pod Security Standards (PSS) for namespace enforcement")
    security_findings["suggestions"].append("• Implement admission controllers (OPA/Gatekeeper) for policy enforcement")
    security_findings["suggestions"].append("• Enable audit logging for all API calls")
    security_findings["suggestions"].append("• Use ImagePullSecrets to secure container image access")
    
    # Display security findings
    print(f"\n📊 RESOURCE INVENTORY:")
    print(f"  Total Pods:              {total_pods}")
    print(f"  Total Deployments:       {total_deployments}")
    print(f"  Total DaemonSets:        {total_daemonsets}")
    print(f"  Total StatefulSets:      {total_statefulsets}")
    print(f"  Total RoleBindings:      {total_rolebindings}")
    print(f"  Total NetworkPolicies:   {total_networkpolicies}")
    
    if security_findings["high_risk"]:
        print(f"\n🔴 HIGH RISK FINDINGS:")
        for finding in security_findings["high_risk"]:
            print(f"  {finding}")
    
    if security_findings["medium_risk"]:
        print(f"\n🟠 MEDIUM RISK FINDINGS:")
        for finding in security_findings["medium_risk"]:
            print(f"  {finding}")
    
    if security_findings["low_risk"]:
        print(f"\n🟡 LOW RISK FINDINGS:")
        for finding in security_findings["low_risk"]:
            print(f"  {finding}")
    
    print(f"\n💡 RECOMMENDATIONS:")
    for suggestion in security_findings["suggestions"]:
        print(f"  {suggestion}")
        
        print(f"  ✅ Executed {ns_query_count} queries for {ns}")
        print(f"     Tool calls: {', '.join(ns_tool_calls)}")
    
    print(f"\n✅ Stage 2 Complete: Executed {total_queries} total queries")
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Namespaces found: {len(namespaces)}")
    print(f"Namespaces queried: {len(test_namespaces)} (test mode)")
    print(f"Resource types per namespace: {len(resource_types)}")
    print(f"Expected total queries: {len(test_namespaces)} namespaces × {len(resource_types)} resource types = {len(test_namespaces) * len(resource_types)}")
    print(f"Actual queries executed: {total_queries}")
    
    if total_queries >= len(test_namespaces) * len(resource_types):
        print("\n✅ SUCCESS: All expected queries executed!")
    else:
        print(f"\n❌ ISSUE: Missing {len(test_namespaces) * len(resource_types) - total_queries} queries")
        print("   Check the Stage 2 prompt and execution logic")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    asyncio.run(main())
