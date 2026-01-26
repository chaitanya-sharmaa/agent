"""
CLI orchestrator module for managing CLI workflows.
Handles auditor, creator, and comprehensive auditor flows.
"""

import logging
import json
from typing import Optional

from langchain_mcp_adapters.client import MultiServerMCPClient
from src.langgraphagenticai.core.graph_executor import GraphExecutor
from src.langgraphagenticai.graph.graph_builder import GraphBuilder
from src.langgraphagenticai.utils.zero_trust_analyzer import ZeroTrustAnalyzer
from src.langgraphagenticai.utils.live_logger import get_live_logger

logger = logging.getLogger(__name__)
live_logger = get_live_logger()


class CLIOrchestrator:
    """Orchestrates CLI execution flows for auditor and creator modes."""

    # Required probe types for auditor checks
    REQUIRED_PROBES = {
        "namespaces",
        "pods",
        "daemonsets",
        "peerauthentication",
        "authorizationpolicy",
        "networkpolicy",
    }

    # Helm chart configuration
    HELM_CHART_URL = (
        "https://rohkum143.github.io/zero-trust-charts/authorization-policy-0.1.0.tgz"
    )
    HELM_RELEASE_NAME = "auth"
    HELM_NAMESPACE = "istio-system"

    def __init__(
        self,
        graph_builder: GraphBuilder,
        executor: GraphExecutor,
        analyzer: ZeroTrustAnalyzer,
        config=None,
    ):
        """
        Initialize the CLI orchestrator.
        
        Args:
            graph_builder: GraphBuilder instance for creating workflows
            executor: GraphExecutor instance for running workflows
            analyzer: ZeroTrustAnalyzer instance for analysis
            config: Configuration loader instance (optional)
        """
        self.graph_builder = graph_builder
        self.executor = executor
        self.analyzer = analyzer
        if config is None:
            from src.langgraphagenticai.config.config_loader import get_config
            config = get_config()
        self.config = config

    async def run_comprehensive_auditor(self) -> None:
        """Execute the Comprehensive Security Auditor workflow using the same logic as test_comprehensive.py."""
        print("=" * 80)
        print("COMPREHENSIVE SECURITY AUDIT - CLI")
        print("=" * 80)

        # Stage 1: Get namespaces (LLM-driven graph)
        print("\n" + "=" * 80)
        print("STAGE 1: Getting all namespaces")
        print("=" * 80)

        stage1_graph = await self.graph_builder.setup_graph("Comprehensive Security Auditor")
        stage1_input = {"messages": [("user", "Query all Kubernetes namespaces to get the complete list.")]}

        stage1_results = []
        tool_call_count = 0
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
                            tool_call_count += 1
                            
            # Stop after first tool execution (we only need namespaces)
            if tool_call_count > 0:
                break

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
            except Exception:
                continue

        print(f"\n✅ Stage 1 Complete: Found {len(namespaces)} namespaces")

        # Stage 2: Direct MCP tool calls per resource type
        print("\n" + "=" * 80)
        print("STAGE 2: Querying each resource type individually (direct MCP)")
        print("=" * 80)

        resource_types = ["pods", "deployments", "daemonsets", "statefulsets", "rolebindings", "networkpolicies"]
        all_namespaces = namespaces
        total_queries = 0
        stage2_results = []
        namespace_resources = {}

        client = MultiServerMCPClient({
            "kubernetes": {
                "url": "http://48.194.37.51:3001/mcp",
                "transport": "streamable_http",
            }
        })
        tools = await client.get_tools()
        kubectl_get_tool = next(t for t in tools if t.name == "kubectl_get")

        for ns_idx, ns in enumerate(all_namespaces, 1):
            print(f"\n📦 Processing namespace {ns_idx}/{len(all_namespaces)}: {ns}")
            print("=" * 80)
            ns_query_count = 0
            ns_tool_calls = []
            ns_results = {}

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

                    parsed = None
                    if isinstance(result, list) and len(result) > 0 and isinstance(result[0], dict):
                        if "text" in result[0]:
                            parsed = json.loads(result[0]["text"])

                    if parsed and isinstance(parsed, dict) and "items" in parsed:
                        items = parsed.get("items", [])
                        namespace_resources[ns][rt]["count"] = len(items)
                        namespace_resources[ns][rt]["items"] = items
                        
                        # DEBUG: Print first item structure
                        if items and len(items) > 0:
                            print(f"\n      [DEBUG {rt}] First item keys: {list(items[0].keys()) if isinstance(items[0], dict) else 'not a dict'}")
                            if isinstance(items[0], dict):
                                print(f"      [DEBUG {rt}] name: {items[0].get('name')}")
                                print(f"      [DEBUG {rt}] status keys: {list(items[0].get('status', {}).keys()) if isinstance(items[0].get('status'), dict) else 'no status'}")
                                if isinstance(items[0].get('status'), dict):
                                    print(f"      [DEBUG {rt}] status.phase: {items[0].get('status', {}).get('phase')}")

                    if isinstance(result, dict) and "content" in result:
                        stage2_results.append(result["content"])
                    else:
                        stage2_results.append(str(result))
                except Exception as e:
                    ns_tool_calls.append(f"kubectl_get({rt}) [error: {e}]")
                    ns_results[rt] = {"error": str(e)}

            print(f"  ✅ Executed {ns_query_count} queries for {ns}")
            print(f"     Tool calls: {', '.join(ns_tool_calls)}")

            print(f"\n  📊 RESOURCES IN {ns}:")
            for rt in resource_types:
                print(f"\n    {rt.upper()}:")
                result_data = ns_results.get(rt)
                try:
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
                            for item in items[:2]:
                                name = item.get("name", "unknown")
                                print(f"        - {name}")
                        else:
                            print(f"      No {rt} found")
                    else:
                        print(f"      Result: {str(result_data)[:80]}")
                except Exception as e:
                    print(f"      Error parsing: {str(e)[:60]}")

        print(f"\n✅ Stage 2 Complete: Executed {total_queries} total queries")

        # Analysis and summary (same as test script)
        print("\n" + "=" * 80)
        print("COMPREHENSIVE SECURITY AUDIT ANALYSIS")
        print("=" * 80)

        for ns in all_namespaces:
            print(f"\n\n{'='*80}")
            print(f"📦 NAMESPACE: {ns.upper()}")
            print('='*80)

            resources = namespace_resources[ns]

            print(f"\n{'Resource Type':<20} {'Count':<10} {'Status':<10}")
            print("-" * 40)
            for rt in resource_types:
                count = resources[rt]["count"]
                status = "✓ Found" if count > 0 else "○ Empty"
                print(f"{rt:<20} {count:<10} {status:<10}")

            for rt in resource_types:
                items = resources[rt]["items"]
                if items:
                    print(f"\n  📋 {rt.upper()} ({len(items)} found):")
                    for item in items[:5]:
                        # Handle both dict and potentially nested structures
                        if isinstance(item, dict):
                            name = item.get("name") or item.get("metadata", {}).get("name", "unknown")
                        else:
                            name = "unknown"
                        
                        # Extract status based on resource type
                        status_obj = item.get("status", {}) if isinstance(item, dict) else {}
                        status = "Active"  # Default to Active for resources that exist
                        
                        if rt == "pods":
                            if isinstance(status_obj, dict):
                                status = status_obj.get("phase", "Active")
                        elif rt == "deployments":
                            if isinstance(status_obj, dict):
                                ready = status_obj.get("readyReplicas", 0)
                                desired = status_obj.get("replicas", 0)
                                if desired > 0:
                                    status = f"{ready}/{desired} Ready"
                                else:
                                    status = "Pending"
                        elif rt == "statefulsets":
                            if isinstance(status_obj, dict):
                                ready = status_obj.get("readyReplicas", 0)
                                desired = status_obj.get("replicas", 0)
                                if desired > 0:
                                    status = f"{ready}/{desired} Ready"
                                else:
                                    status = "Pending"
                        elif rt in ["rolebindings", "networkpolicies"]:
                            status = "Applied"
                        elif rt == "daemonsets":
                            if isinstance(status_obj, dict):
                                ready = status_obj.get("numberReady", 0)
                                desired = status_obj.get("desiredNumberScheduled", 0)
                                if desired > 0:
                                    status = f"{ready}/{desired} Ready"
                                else:
                                    status = "Pending"
                        
                        print(f"     ✓ {name:<40} [Status: {status}]")
                    if len(items) > 5:
                        print(f"     ... and {len(items) - 5} more")

        print(f"\n\n{'='*80}")
        print("🔒 SECURITY ASSESSMENT")
        print('='*80)

        security_findings = {
            "high_risk": [],
            "medium_risk": [],
            "low_risk": [],
            "suggestions": []
        }

        total_pods = sum(r["pods"]["count"] for r in namespace_resources.values())
        total_deployments = sum(r["deployments"]["count"] for r in namespace_resources.values())
        total_daemonsets = sum(r["daemonsets"]["count"] for r in namespace_resources.values())
        total_statefulsets = sum(r["statefulsets"]["count"] for r in namespace_resources.values())
        total_rolebindings = sum(r["rolebindings"]["count"] for r in namespace_resources.values())
        total_networkpolicies = sum(r["networkpolicies"]["count"] for r in namespace_resources.values())

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

        print(f"\n✅ Stage 2 Complete: Executed {total_queries} total queries")

        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)
        expected_queries = len(namespace_resources) * len(resource_types)
        print(f"Namespaces found: {len(namespaces)}")
        print(f"Namespaces queried: {len(namespace_resources)}")
        print(f"Resource types per namespace: {len(resource_types)}")
        print(f"Expected total queries: {expected_queries}")
        print(f"Actual queries executed: {total_queries}")

        if total_queries >= expected_queries:
            print("\n✅ SUCCESS: All expected queries executed!")
        else:
            print(f"\n❌ ISSUE: Missing {expected_queries - total_queries} queries")
            print("   Check the Stage 2 prompt and execution logic (some tool calls may have failed)")

        print("\n" + "=" * 80)

    async def run_auditor(self) -> None:
        """Execute the Zero Trust Auditor workflow."""
        logger.info("Starting Zero Trust Auditor")
        live_logger.section("ZERO TRUST AUDITOR")
        live_logger.info("📊 Analyzing your Kubernetes cluster for security compliance...")
        print("\n" + "🔐 ZERO TRUST AUDITOR ".center(70, "="))
        print("📊 Analyzing your Kubernetes cluster for security compliance...\n")

        live_logger.subsection("Gathering Cluster Data")
        auditor_graph = await self.graph_builder.build_auditor_graph()
        user_message = "Execute Zero Trust Auditor checks now. Use available tools as needed to gather cluster data and provide a final assessment."

        live_logger.info("🔍 Running security checks...")
        tool_results, _ = await self.executor.execute_graph(
            auditor_graph,
            user_message,
            max_events=200,
            required_probe_prefixes=self.REQUIRED_PROBES,
        )

        live_logger.subsection("Generating Assessment Report")
        print("\n📋 GENERATING ASSESSMENT REPORT...")
        self._print_assessment(tool_results, "pre-deploy")
        live_logger.status("Auditor analysis completed")

    async def run_creator(self) -> None:
        """Execute the Zero Trust Creator workflow (audit + deploy + verify)."""
        logger.info("Starting Zero Trust Creator")
        live_logger.section("ZERO TRUST CREATOR")
        live_logger.step(1, 3, "Initial Security Audit")
        print("\n" + "🛡️  ZERO TRUST CREATOR ".center(70, "="))
        print("📋 Step 1: Initial Security Audit\n")

        # Step 1: Run initial audit
        await self.run_auditor()

        # Step 2: Deploy Helm chart
        live_logger.step(2, 3, "Deploying Authorization Policies")
        print("\n" + "🚀 Step 2: Deploying Authorization Policies".center(70, "="))
        await self._deploy_helm_chart()

        # Step 3: Verify post-deployment
        live_logger.step(3, 3, "Post-Deployment Verification")
        print("\n" + "✅ Step 3: Post-Deployment Verification".center(70, "="))
        await self._verify_post_deployment()

    async def _deploy_helm_chart(self) -> None:
        """Deploy the authorization policy Helm chart."""
        print("📦 Installing Helm chart: authorization-policy\n")

        creator_graph = await self.graph_builder.build_creator_graph()
        deploy_message = self._get_helm_deploy_message()

        tool_results, _ = await self.executor.execute_graph(
            creator_graph,
            deploy_message,
            max_events=100,
            stop_on_tool_names={"upgrade_helm_chart", "install_helm_chart"},
        )

        if tool_results:
            print("\n✓ Deployment completed successfully")
        else:
            print("\n⚠️  No deployment output detected")

    async def _verify_post_deployment(self) -> None:
        """Verify the cluster state after deployment."""
        print("🔍 Re-running audit to verify changes...\n")

        auditor_graph = await self.graph_builder.build_auditor_graph()
        user_message = "Execute Zero Trust Auditor checks now. Use available tools as needed to gather cluster data and provide a final assessment."

        tool_results, _ = await self.executor.execute_graph(
            auditor_graph,
            user_message,
            max_events=200,
            required_probe_prefixes=self.REQUIRED_PROBES,
        )

        self._print_assessment(tool_results, "post-deploy")

    def _print_assessment(self, tool_results: list, phase: str) -> None:
        """
        Print the Zero Trust assessment.
        
        Args:
            tool_results: List of tool execution results
            phase: Phase name (pre-deploy or post-deploy)
        """
        if tool_results:
            cleaned = self._filter_valid_results(tool_results)
            if cleaned:
                assessment = self.analyzer.analyze_and_generate_report(cleaned)
                print(f"\n--- Zero Trust Auditor Assessment ({phase}) ---")
                print(assessment)
            else:
                print(f"\n--- No valid results for assessment ({phase}) ---")
        else:
            print(f"\n--- Auditor found no tool results ({phase}) ---")

    @staticmethod
    def _filter_valid_results(tool_results: list) -> list:
        """
        Filter out error results from tool results.
        
        Args:
            tool_results: List of tool execution results
            
        Returns:
            Filtered list of valid results
        """
        return [
            r
            for r in tool_results
            if isinstance(r, dict)
            and r.get("output")
            and not (
                str(r.get("output", "")).strip().lower().startswith("error:")
                or "status is not a valid tool"
                in str(r.get("output", "")).lower()
            )
        ]

    @staticmethod
    def _get_helm_deploy_message() -> str:
        """Get the Helm deployment instruction message."""
        return f"""YOU MUST OUTPUT ONLY VALID JSON TOOL CALLS. NO TEXT, NO EXPLANATIONS, NO REASONING, NO MARKDOWN.

Your task is to deploy the Helm chart as release name "{CLIOrchestrator.HELM_RELEASE_NAME}" in namespace "{CLIOrchestrator.HELM_NAMESPACE}".

The chart URL is: {CLIOrchestrator.HELM_CHART_URL}

Always use upgrade_helm_chart — it is idempotent and will not create new revisions if nothing changed.

OUTPUT EXACTLY THIS JSON (copy precisely, do not change anything):

{{"name": "upgrade_helm_chart", "parameters": {{"name": "{CLIOrchestrator.HELM_RELEASE_NAME}", "chart": "{CLIOrchestrator.HELM_CHART_URL}", "namespace": "{CLIOrchestrator.HELM_NAMESPACE}"}}}}

If the above fails with "release not found", then use:

{{"name": "install_helm_chart", "parameters": {{"name": "{CLIOrchestrator.HELM_RELEASE_NAME}", "chart": "{CLIOrchestrator.HELM_CHART_URL}", "namespace": "{CLIOrchestrator.HELM_NAMESPACE}"}}}}

CRITICAL RULES:
- Use "name" parameter with value "{CLIOrchestrator.HELM_RELEASE_NAME}" — never omit it.
- Use absolute chart URL as "chart".
- Do not add repo, values, or any other fields.
- Output only one JSON line.
- After successful deployment, you are done — do not call more tools.

OUTPUT ONLY THE JSON ABOVE."""
