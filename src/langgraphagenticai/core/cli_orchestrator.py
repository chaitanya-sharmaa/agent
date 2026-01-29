"""
CLI orchestrator module for managing CLI workflows.
Handles auditor, creator, and comprehensive auditor flows.
"""

import asyncio
import logging
import json
from typing import Optional

from langchain_mcp_adapters.client import MultiServerMCPClient
from src.langgraphagenticai.core.graph_executor import GraphExecutor
from src.langgraphagenticai.graph.graph_builder import GraphBuilder
from src.langgraphagenticai.utils.zero_trust_analyzer import ZeroTrustAnalyzer
from src.langgraphagenticai.utils.live_logger import get_live_logger
try:
    from src.langgraphagenticai.integrations.crewai_executor import CrewAIExecutor
    HAS_CREWAI = True
except ImportError:
    HAS_CREWAI = False

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
        llm_model=None,
    ):
        """
        Initialize the CLI orchestrator.
        
        Args:
            graph_builder: GraphBuilder instance for creating workflows
            executor: GraphExecutor instance for running workflows
            analyzer: ZeroTrustAnalyzer instance for analysis
            config: Configuration loader instance (optional)
            llm_model: LLM model instance for Crew AI (optional)
        """
        self.graph_builder = graph_builder
        self.analyzer = analyzer
        if config is None:
            from src.langgraphagenticai.config.config_loader import get_config
            config = get_config()
        self.config = config
        
        # Setup executors based on engine selection
        execution_engine = self.config.get_execution_engine()
        self.execution_engine = execution_engine
        self.graph_executor = executor  # Always keep GraphExecutor for langgraph mode
        self.crew_ai_executor = None
        
        if execution_engine == "crew_ai" and HAS_CREWAI:
            logger.info("Initializing Crew AI execution engine with multi-agent support")
            try:
                # Create CrewAIExecutor with necessary dependencies
                if llm_model is None:
                    from src.langgraphagenticai.LLMS.ollamallm import OllamaLLM
                    llm_config = self.config.get_llm_config()
                    llm_model = OllamaLLM(llm_config).get_llm_model()
                
                from src.langgraphagenticai.utils.cli_output_formatter import CLIOutputFormatter
                from src.langgraphagenticai.core.probe_manager import ProbeManager
                
                formatter = CLIOutputFormatter(show_raw_output=True)
                PERSISTENT_PROBES_PATH = "/tmp/executed_probes.json"
                probe_manager = ProbeManager(PERSISTENT_PROBES_PATH)
                
                self.crew_ai_executor = CrewAIExecutor(
                    formatter=formatter,
                    probe_manager=probe_manager,
                    config=self.config,
                    llm_model=llm_model
                )
                logger.info("✓ Crew AI executor initialized")
                print("✓ Crew AI multi-agent executor initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Crew AI executor: {e}")
                logger.info("Falling back to LangGraph executor")
                self.execution_engine = "langgraph"
        
        if execution_engine == "langgraph" or self.crew_ai_executor is None:
            logger.info("Using LangGraph execution engine (default)")
            self.executor = executor
            self.execution_engine = "langgraph"
        else:
            logger.info("Using Crew AI execution engine with multi-agent support")
            self.executor = None  # Use crew_ai_executor instead

    async def run_comprehensive_auditor(self) -> None:
        """Execute the Comprehensive Security Auditor workflow.
        
        Orchestrates four modular phases:
        1. Namespace discovery via LLM
        2. Resource querying in parallel
        3. Namespace security analysis
        4. Cluster-wide security assessment
        """
        print("=" * 80)
        print("COMPREHENSIVE SECURITY AUDIT - CLI")
        print("=" * 80)

        # Phase 1: Discover namespaces
        namespaces = await self._stage1_discover_namespaces()

        # Phase 2: Query resources
        namespace_resources, cluster_resources, total_queries = await self._stage2_query_resources(namespaces)

        # Phase 3 & 4: Analyze and report
        print("\n" + "=" * 80)
        print("COMPREHENSIVE SECURITY AUDIT ANALYSIS")
        print("=" * 80)

        # Per-namespace security assessment
        for ns in namespaces:
            resources = namespace_resources[ns]
            ns_findings = await self._analyze_namespace_security(ns, resources)
            self._print_namespace_report(ns, resources, ns_findings)

        # Cluster-wide security assessment
        cluster_findings = await self._analyze_cluster_security(namespace_resources, cluster_resources)
        self._print_cluster_report(cluster_findings, namespace_resources, total_queries, namespaces)

    async def _stage1_discover_namespaces(self) -> list[str]:
        """Phase 1: Discover all Kubernetes namespaces using LLM-driven graph.
        
        Returns:
            List of namespace names discovered in the cluster
        """
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
        return namespaces

    async def _stage2_query_resources(self, namespaces: list[str]) -> tuple:
        """Phase 2: Query resources for all namespaces and cluster-wide.
        
        Args:
            namespaces: List of namespace names to query
            
        Returns:
            Tuple of (namespace_resources_dict, cluster_resources_dict, total_queries_count)
        """
        print("\n" + "=" * 80)
        print("STAGE 2: Querying each resource type individually (direct MCP)")
        print("=" * 80)

        resource_types = [
            "pods", "deployments", "daemonsets", "statefulsets",
            "rolebindings", "networkpolicies", "services", "ingresses",
            "virtualservices", "destinationrules", "gateways", "configmaps",
        ]
        cluster_resource_types = [
            "clusterroles", "clusterrolebindings", "peerauthentication", "authorizationpolicy",
        ]

        namespace_resources = {ns: self._initialize_namespace_resources(resource_types) for ns in namespaces}
        cluster_resources = {crt: {"count": 0, "items": []} for crt in cluster_resource_types}

        # Setup MCP client and tools
        client = MultiServerMCPClient({
            "kubernetes": {
                "url": self.config.get_mcp_url(),
                "transport": self.config.get_mcp_transport(),
            }
        })
        tools = await client.get_tools()
        kubectl_get_tool = next(t for t in tools if t.name == "kubectl_get")

        # Filter resource types based on available APIs
        available_resources = await self._get_available_resources(tools)
        if available_resources:
            resource_types = [rt for rt in resource_types if rt.lower() in available_resources]
            cluster_resource_types = [rt for rt in cluster_resource_types if rt.lower() in available_resources]

        # Query namespace-scoped resources in parallel
        total_queries = await self._query_namespace_resources(
            kubectl_get_tool, namespaces, resource_types, namespace_resources
        )

        # Query cluster-wide resources in parallel
        total_queries += await self._query_cluster_resources(kubectl_get_tool, cluster_resource_types, cluster_resources)

        print(f"✅ Stage 2 Complete: Executed {total_queries} total queries")
        return namespace_resources, cluster_resources, total_queries

    def _initialize_namespace_resources(self, resource_types: list[str]) -> dict:
        """Initialize empty resource structure for a namespace."""
        return {rt: {"count": 0, "items": []} for rt in resource_types}

    async def _get_available_resources(self, tools):
        """Discover available Kubernetes resource types from the cluster."""
        list_api_tool = next((t for t in tools if t.name == "list_api_resources"), None)
        if not list_api_tool:
            return None
        
        try:
            timeout_seconds = self.config.get_mcp_timeout_seconds() if self.config else 30
            result = await asyncio.wait_for(list_api_tool.ainvoke({}), timeout=timeout_seconds)
            
            raw_text = self._extract_text_from_result(result)
            resources = set()
            for line in raw_text.splitlines():
                line = line.strip()
                if not line or line.lower().startswith("name "):
                    continue
                parts = line.split()
                if parts:
                    resources.add(parts[0].lower())
            return resources if resources else None
        except Exception as e:
            logger.warning(f"Failed to list API resources: {e}")
            return None

    def _extract_text_from_result(self, result) -> str:
        """Extract text content from MCP tool result."""
        if isinstance(result, dict) and "content" in result:
            content = result.get("content", "")
            if isinstance(content, list):
                parts = [str(item.get("text", "")) for item in content if isinstance(item, dict) and "text" in item]
                return "\n".join(parts) if parts else str(content)
            else:
                return str(content)
        elif isinstance(result, list) and result:
            parts = [str(item.get("text", "")) if isinstance(item, dict) else str(item) for item in result]
            return "\n".join(parts)
        else:
            return str(result)

    async def _query_namespace_resources(self, kubectl_tool, namespaces: list[str], 
                                        resource_types: list[str], namespace_resources: dict) -> int:
        """Query all resources for all namespaces in parallel."""
        total_queries = 0
        
        for ns_idx, ns in enumerate(namespaces, 1):
            print(f"📦 Processing namespace {ns_idx}/{len(namespaces)}: {ns}")
            
            # Execute all resource type queries in parallel for this namespace
            tasks = [self._query_single_resource(kubectl_tool, ns, rt) for rt in resource_types]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            ns_tool_calls = []
            for item in results:
                if isinstance(item, Exception):
                    continue
                rt, result, error = item
                total_queries += 1
                ns_tool_calls.append(f"kubectl_get({rt})")
                
                if not error:
                    await self._process_resource_result(result, ns, rt, namespace_resources)
            
            print(f"  ✅ Executed {len(ns_tool_calls)} queries for {ns}")
            print(f"     Tool calls: {', '.join(ns_tool_calls)}")
        
        return total_queries

    async def _query_single_resource(self, kubectl_tool, namespace: str, resource_type: str):
        """Query a single resource type in a namespace."""
        args = {"resourceType": resource_type, "namespace": namespace, "output": "json"}
        try:
            timeout_seconds = self.config.get_mcp_timeout_seconds() if self.config else 30
            result = await asyncio.wait_for(kubectl_tool.ainvoke(args), timeout=timeout_seconds)
            return resource_type, result, None
        except Exception as e:
            return resource_type, None, str(e)

    async def _process_resource_result(self, result, namespace: str, resource_type: str, namespace_resources: dict):
        """Parse and store resource query result."""
        try:
            parsed = None
            if isinstance(result, list) and len(result) > 0 and isinstance(result[0], dict):
                if "text" in result[0]:
                    parsed = json.loads(result[0]["text"])

            if parsed and isinstance(parsed, dict) and "items" in parsed:
                items = parsed.get("items", [])
                namespace_resources[namespace][resource_type]["count"] = len(items)
                namespace_resources[namespace][resource_type]["items"] = items
        except Exception as e:
            logger.debug(f"Error processing {resource_type} in {namespace}: {e}")

    async def _query_cluster_resources(self, kubectl_tool, cluster_resource_types: list[str], 
                                      cluster_resources: dict) -> int:
        """Query all cluster-wide resources in parallel."""
        tasks = [self._query_single_cluster_resource(kubectl_tool, crt) for crt in cluster_resource_types]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        total_queries = 0
        for item in results:
            if isinstance(item, Exception):
                continue
            crt, result, error = item
            total_queries += 1
            
            if not error:
                try:
                    parsed = None
                    if isinstance(result, list) and len(result) > 0 and isinstance(result[0], dict) and "text" in result[0]:
                        parsed = json.loads(result[0]["text"])
                    if parsed and isinstance(parsed, dict) and "items" in parsed:
                        items = parsed.get("items", [])
                        cluster_resources[crt]["count"] = len(items)
                        cluster_resources[crt]["items"] = items
                except Exception as e:
                    cluster_resources[crt]["error"] = str(e)
        
        return total_queries

    async def _query_single_cluster_resource(self, kubectl_tool, cluster_resource_type: str):
        """Query a single cluster-wide resource."""
        args = {"resourceType": cluster_resource_type, "output": "json"}
        try:
            timeout_seconds = self.config.get_mcp_timeout_seconds() if self.config else 30
            result = await asyncio.wait_for(kubectl_tool.ainvoke(args), timeout=timeout_seconds)
            return cluster_resource_type, result, None
        except Exception as e:
            return cluster_resource_type, None, str(e)

    async def _analyze_namespace_security(self, namespace: str, resources: dict) -> dict:
        """Analyze security for a single namespace.
        
        Returns:
            Dictionary with security findings organized by risk level
        """
        findings = {"high_risk": [], "medium_risk": [], "low_risk": [], "suggestions": []}
        
        # NetworkPolicy coverage
        if resources.get("pods", {}).get("count", 0) > 0 and resources.get("networkpolicies", {}).get("count", 0) == 0:
            self._add_finding(findings, "high_risk", "Namespace has workloads but NO NetworkPolicies", 
                            "NIST AC-4, CIS 5.x, NSA/CISA Segmentation")
            findings["suggestions"].append("• Add default-deny ingress/egress NetworkPolicies")
        
        # Service exposure risks
        for svc in resources.get("services", {}).get("items", [])[:3]:
            svc_type = (svc.get("spec", {}) or {}).get("type") if isinstance(svc, dict) else None
            if svc_type in {"LoadBalancer", "NodePort"} and resources.get("networkpolicies", {}).get("count", 0) == 0:
                self._add_finding(findings, "medium_risk", 
                                f"Service {svc.get('name','unknown')} is {svc_type} without NetworkPolicy",
                                "NIST AC-4, CIS 5.x")
        
        # Ingress security
        for ing in resources.get("ingresses", {}).get("items", [])[:3]:
            tls = (ing.get("spec", {}) or {}).get("tls") if isinstance(ing, dict) else None
            if not tls:
                self._add_finding(findings, "medium_risk", "Ingress missing TLS", "NIST AC-4, CIS 5.x")
        
        # Workload security contexts
        await self._check_workload_security(resources.get("pods", {}).get("items", []), "Pod", findings)
        await self._check_workload_security(resources.get("deployments", {}).get("items", []), "Deployment", findings)
        
        return findings

    def _add_finding(self, findings_dict: dict, level: str, text: str, standards: str = ""):
        """Add a security finding."""
        suffix = f" [{standards}]" if standards else ""
        findings_dict[level].append(f"{text}{suffix}")

    async def _check_workload_security(self, items: list, kind_label: str, findings: dict):
        """Check workload security contexts for issues."""
        standards_priv = "NIST CM-7, CIS 5.2.x"
        for wk in items[:3]:
            if not isinstance(wk, dict):
                continue
            
            spec = wk.get("spec", {}) or {}
            tpl = spec.get("template", {}).get("spec", {}) if isinstance(spec.get("template"), dict) else spec
            sc = tpl.get("securityContext", {}) if isinstance(tpl, dict) else {}
            
            if tpl.get("hostNetwork"):
                self._add_finding(findings, "medium_risk", f"{kind_label} uses hostNetwork", standards_priv)
            
            if sc:
                if sc.get("runAsUser") in (0, "0") or sc.get("runAsNonRoot") is False:
                    self._add_finding(findings, "medium_risk", f"{kind_label} runs as root", standards_priv)
                if sc.get("privileged"):
                    self._add_finding(findings, "high_risk", f"{kind_label} is privileged", standards_priv)

    async def _analyze_cluster_security(self, namespace_resources: dict, cluster_resources: dict) -> dict:
        """Analyze cluster-wide security posture.
        
        Returns:
            Dictionary with cluster-level security findings
        """
        findings = {"high_risk": [], "medium_risk": [], "low_risk": [], "suggestions": []}
        
        # mTLS configuration
        peer_items = cluster_resources.get("peerauthentication", {}).get("items", [])
        if not peer_items:
            self._add_finding(findings, "high_risk", "No PeerAuthentication found (mTLS likely not enforced)",
                            "NIST SC-8/SC-13, CIS 5.1.6, NSA/CISA mTLS")
            findings["suggestions"].append("• Enforce STRICT mTLS mesh-wide via PeerAuthentication")
        
        # Authorization policies
        authz_items = cluster_resources.get("authorizationpolicy", {}).get("items", [])
        if not authz_items:
            self._add_finding(findings, "medium_risk", "No AuthorizationPolicy found (no authZ restrictions)",
                            "NIST AC-3, CIS 5.x")
            findings["suggestions"].append("• Add AuthorizationPolicy to restrict service-to-service access")
        
        # RBAC configuration
        crb_items = cluster_resources.get("clusterrolebindings", {}).get("items", [])
        for crb in crb_items:
            role_ref = (crb.get("roleRef", {}) or {}).get("name") if isinstance(crb, dict) else None
            if role_ref and "cluster-admin" in role_ref:
                self._add_finding(findings, "high_risk", "ClusterRoleBinding grants cluster-admin",
                                "NIST AC-3, CIS 1.x/2.x")
                findings["suggestions"].append("• Limit cluster-admin bindings; use namespace-scoped roles")
                break
        
        # General recommendations
        findings["suggestions"].extend([
            "• Enable Pod Security Standards (PSS) or PSA enforcing baseline/restricted",
            "• Implement admission controls (OPA/Gatekeeper/Kyverno) for policy enforcement",
            "• Enable audit logging for all API calls",
            "• Use ImagePullSecrets and pinned image tags"
        ])
        
        return findings

    def _print_namespace_report(self, namespace: str, resources: dict, findings: dict):
        """Print formatted namespace security report."""
        print(f"\n\n{'='*80}")
        print(f"📦 NAMESPACE: {namespace.upper()}")
        print('='*80)

        # Resource inventory
        resource_types = [rt for rt in resources.keys() if rt in [
            "pods", "deployments", "daemonsets", "statefulsets", 
            "rolebindings", "networkpolicies", "services", "ingresses"
        ]]
        
        print(f"\n{'Resource Type':<20} {'Count':<10} {'Status':<10}")
        print("-" * 40)
        for rt in resource_types:
            count = resources[rt]["count"]
            status = "✓ Found" if count > 0 else "○ Empty"
            print(f"{rt:<20} {count:<10} {status:<10}")

        # Resource details
        for rt in resource_types:
            items = resources[rt]["items"]
            if items:
                print(f"\n  📋 {rt.upper()} ({len(items)} found):")
                for item in items[:5]:
                    name = item.get("name", "unknown") if isinstance(item, dict) else "unknown"
                    status = self._get_resource_status(item, rt)
                    print(f"     ✓ {name:<40} [Status: {status}]")
                if len(items) > 5:
                    print(f"     ... and {len(items) - 5} more")

        # Security findings
        if findings["high_risk"] or findings["medium_risk"] or findings["low_risk"]:
            print(f"\n  🔒 SECURITY FINDINGS:")
            
            if findings["high_risk"]:
                print(f"\n  🔴 HIGH RISK:")
                for finding in findings["high_risk"]:
                    print(f"    {finding}")
            
            if findings["medium_risk"]:
                print(f"\n  🟠 MEDIUM RISK:")
                for finding in findings["medium_risk"]:
                    print(f"    {finding}")
            
            if findings["low_risk"]:
                print(f"\n  🟡 LOW RISK:")
                for finding in findings["low_risk"]:
                    print(f"    {finding}")

            if findings["suggestions"]:
                print(f"\n  💡 RECOMMENDATIONS:")
                for suggestion in findings["suggestions"]:
                    print(f"    {suggestion}")

    def _get_resource_status(self, item: dict, resource_type: str) -> str:
        """Extract status for a specific resource type."""
        if not isinstance(item, dict):
            return "Active"
        
        status_obj = item.get("status", {})
        
        if resource_type == "pods":
            return status_obj.get("phase", "Active") if isinstance(status_obj, dict) else "Active"
        elif resource_type in ["deployments", "statefulsets"]:
            if isinstance(status_obj, dict):
                ready = status_obj.get("readyReplicas", 0)
                desired = status_obj.get("replicas", 0)
                return f"{ready}/{desired} Ready" if desired > 0 else "Pending"
        elif resource_type == "daemonsets":
            if isinstance(status_obj, dict):
                ready = status_obj.get("numberReady", 0)
                desired = status_obj.get("desiredNumberScheduled", 0)
                return f"{ready}/{desired} Ready" if desired > 0 else "Pending"
        elif resource_type in ["rolebindings", "networkpolicies"]:
            return "Applied"
        
        return "Active"

    def _print_cluster_report(self, findings: dict, namespace_resources: dict, 
                            total_queries: int, namespaces: list[str]):
        """Print cluster-wide security assessment report."""
        print(f"\n\n{'='*80}")
        print("🔒 CLUSTER-WIDE SECURITY ASSESSMENT")
        print('='*80)

        # Resource inventory
        total_pods = sum(r["pods"]["count"] for r in namespace_resources.values())
        total_deployments = sum(r["deployments"]["count"] for r in namespace_resources.values())
        total_daemonsets = sum(r["daemonsets"]["count"] for r in namespace_resources.values())
        total_statefulsets = sum(r["statefulsets"]["count"] for r in namespace_resources.values())
        total_rolebindings = sum(r["rolebindings"]["count"] for r in namespace_resources.values())
        total_networkpolicies = sum(r["networkpolicies"]["count"] for r in namespace_resources.values())

        print(f"\n📊 RESOURCE INVENTORY:")
        print(f"  Total Pods:              {total_pods}")
        print(f"  Total Deployments:       {total_deployments}")
        print(f"  Total DaemonSets:        {total_daemonsets}")
        print(f"  Total StatefulSets:      {total_statefulsets}")
        print(f"  Total RoleBindings:      {total_rolebindings}")
        print(f"  Total NetworkPolicies:   {total_networkpolicies}")

        # Security findings
        if findings["high_risk"]:
            print(f"\n🔴 HIGH RISK FINDINGS:")
            for finding in findings["high_risk"]:
                print(f"  {finding}")

        if findings["medium_risk"]:
            print(f"\n🟠 MEDIUM RISK FINDINGS:")
            for finding in findings["medium_risk"]:
                print(f"  {finding}")

        if findings["low_risk"]:
            print(f"\n🟡 LOW RISK FINDINGS:")
            for finding in findings["low_risk"]:
                print(f"  {finding}")

        print(f"\n💡 RECOMMENDATIONS:")
        for suggestion in findings["suggestions"]:
            print(f"  {suggestion}")

        print(f"\n✅ Stage 2 Complete: Executed {total_queries} total queries")

        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print(f"Namespaces found: {len(namespaces)}")
        print(f"Namespaces queried: {len(namespace_resources)}")
        print(f"Actual queries executed: {total_queries}")
        print("\n✅ SUCCESS: Comprehensive audit completed!")
        print("\n" + "=" * 80)

    async def run_creator(self) -> None:
        """Execute the Zero Trust Creator workflow (audit + deploy + verify)."""
        logger.info("Starting Zero Trust Creator")
        live_logger.section("ZERO TRUST CREATOR")
        live_logger.step(1, 3, "Initial Comprehensive Security Audit")
        print("\n" + "🛡️  ZERO TRUST CREATOR ".center(70, "="))
        print("📋 Step 1: Initial Comprehensive Security Audit\n")

        # Step 1: Run comprehensive initial audit
        await self.run_comprehensive_auditor()

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

        deploy_message = self._get_helm_deploy_message()

        if self.execution_engine == "crew_ai" and self.crew_ai_executor:
            print("🤖 Using Crew AI agent for Helm deployment\n")
            from src.langgraphagenticai.tools.kubernetes_tool import get_tools
            tools = await get_tools()
            tool_results, _ = await self.crew_ai_executor.execute_workflow(
                workflow_id="creator",
                user_message=deploy_message,
                tools=tools,
            )
        else:
            # LangGraph execution (default)
            creator_graph = await self.graph_builder.build_creator_graph()
            tool_results, _ = await self.graph_executor.execute_graph(
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

        user_message = "Execute Zero Trust Auditor checks now. Use available tools as needed to gather cluster data and provide a final assessment."

        if self.execution_engine == "crew_ai" and self.crew_ai_executor:
            print("🤖 Using Crew AI agent for post-deployment verification\n")
            from src.langgraphagenticai.tools.kubernetes_tool import get_tools
            tools = await get_tools()
            tool_results, _ = await self.crew_ai_executor.execute_workflow(
                workflow_id="comprehensive_auditor",
                user_message=user_message,
                tools=tools,
            )
        else:
            # LangGraph execution (default) - use comprehensive auditor for verification
            verification_graph = await self.graph_builder.setup_graph("comprehensive_auditor")
            tool_results, _ = await self.graph_executor.execute_graph(
                verification_graph,
                user_message,
                max_events=200,
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
