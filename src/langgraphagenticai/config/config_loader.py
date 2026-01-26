"""
Configuration Loader - Load and validate configuration from YAML files
Enables reusable code across different MCP servers and use cases
"""
import os
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional

class ConfigLoader:
    """Load and manage application configuration from YAML files"""
    
    def __init__(self, config_dir: str = None):
        """
        Initialize config loader
        
        Args:
            config_dir: Path to config directory. Defaults to ./config in project root
        """
        if config_dir is None:
            # Find project root by looking for config directory
            current = Path(__file__).parent.parent.parent.parent  # Go up to project root
            if (current / "config").exists():
                config_dir = str(current / "config")
            else:
                # Fallback: try relative to this file
                config_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "config")
        
        self.config_dir = Path(config_dir)
        if not self.config_dir.exists():
            raise FileNotFoundError(f"Config directory not found: {config_dir}")
        
        self._config_cache = {}
        self._load_all_configs()
    
    def _load_yaml(self, filename: str) -> Dict[str, Any]:
        """Load a single YAML file"""
        filepath = self.config_dir / filename
        if not filepath.exists():
            raise FileNotFoundError(f"Config file not found: {filepath}")
        
        with open(filepath, 'r') as f:
            return yaml.safe_load(f) or {}
    
    def _load_all_configs(self):
        """Load all configuration files"""
        self._config_cache['mcp'] = self._load_yaml('mcp.yaml')
        self._config_cache['prompts'] = self._load_yaml('prompts.yaml')
        self._config_cache['settings'] = self._load_yaml('settings.yaml')
    
    def reload(self):
        """Reload configuration from disk"""
        self._config_cache.clear()
        self._load_all_configs()
    
    # MCP Server Configuration
    
    def get_mcp_server(self) -> Dict[str, Any]:
        """Get MCP server connection settings"""
        return self._config_cache['mcp'].get('server', {})
    
    def get_mcp_url(self) -> str:
        """Get MCP server URL"""
        server = self.get_mcp_server()
        host = server.get('host', 'localhost')
        port = server.get('port', 3001)
        return f"http://{host}:{port}"
    
    def get_mcp_tools(self) -> List[Dict[str, Any]]:
        """Get list of available MCP tools"""
        return self._config_cache['mcp'].get('tools', [])
    
    def get_tool_names(self) -> List[str]:
        """Get list of available tool names"""
        return [tool['name'] for tool in self.get_mcp_tools()]
    
    def get_tool_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get tool configuration by name"""
        tools = self.get_mcp_tools()
        for tool in tools:
            if tool['name'] == name:
                return tool
        return None
    
    # Prompts Configuration
    
    def get_workflows(self) -> Dict[str, Any]:
        """Get all workflow configurations"""
        prompts = self._config_cache['prompts']
        workflows = prompts.get('workflows', {})
        custom = prompts.get('custom_workflows', {})
        return {**workflows, **custom}
    
    def get_workflow(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get specific workflow configuration"""
        return self.get_workflows().get(workflow_id)
    
    def get_workflow_system_prompt(self, workflow_id: str) -> str:
        """Get system prompt for a workflow"""
        workflow = self.get_workflow(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow not found: {workflow_id}")
        return workflow.get('system_prompt', '')
    
    def get_workflow_user_prompt(self, workflow_id: str, prompt_key: str = 'start') -> str:
        """Get user prompt for a workflow"""
        workflow = self.get_workflow(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow not found: {workflow_id}")
        user_prompts = workflow.get('user_prompts', {})
        return user_prompts.get(prompt_key, '')
    
    def get_workflow_name(self, workflow_id: str) -> str:
        """Get friendly name for workflow"""
        workflow = self.get_workflow(workflow_id)
        if not workflow:
            return workflow_id
        return workflow.get('name', workflow_id)
    
    # Settings Configuration
    
    def get_settings(self) -> Dict[str, Any]:
        """Get all settings"""
        return self._config_cache['settings']
    
    def get_workflow_settings(self) -> Dict[str, Any]:
        """Get workflow settings"""
        return self._config_cache['settings'].get('workflow_settings', {})
    
    def get_available_workflows(self) -> List[Dict[str, Any]]:
        """Get list of available workflows for UI"""
        settings = self.get_workflow_settings()
        workflows = settings.get('available_workflows', [])
        return [w for w in workflows if w.get('enabled', True)]
    
    def get_llm_config(self) -> Dict[str, Any]:
        """Get LLM configuration"""
        return self._config_cache['settings'].get('llm', {})
    
    def get_llm_model(self) -> str:
        """Get configured LLM model"""
        llm = self.get_llm_config()
        return llm.get('model', 'mistral:latest')
    
    def get_llm_endpoint(self) -> str:
        """Get LLM endpoint URL"""
        llm = self.get_llm_config()
        endpoint = llm.get('endpoint', 'http://localhost:11434')
        return endpoint
    
    def get_graph_settings(self) -> Dict[str, Any]:
        """Get graph execution settings"""
        return self._config_cache['settings'].get('graph', {})
    
    def get_max_events(self) -> int:
        """Get max events for graph execution"""
        graph = self.get_graph_settings()
        return graph.get('max_events', 200)
    
    def get_early_stop_probes(self, workflow_id: str) -> Optional[List[str]]:
        """Get early stopping probe list for auditor workflow"""
        graph = self.get_graph_settings()
        early_stop = graph.get('early_stop', {})
        if workflow_id == 'auditor':
            return early_stop.get('auditor_probes')
        elif workflow_id == 'creator':
            return early_stop.get('creator_tools')
        return None
    
    def get_ui_settings(self) -> Dict[str, Any]:
        """Get UI settings"""
        return self._config_cache['settings'].get('ui', {})
    
    def get_cli_settings(self) -> Dict[str, Any]:
        """Get CLI settings"""
        return self._config_cache['settings'].get('cli', {})
    
    # Validation and Debug
    
    def validate(self) -> Dict[str, Any]:
        """Validate all configuration"""
        errors = []
        warnings = []
        
        # Check MCP server
        try:
            url = self.get_mcp_url()
            if not url:
                errors.append("MCP server URL not configured")
        except Exception as e:
            errors.append(f"MCP configuration error: {e}")
        
        # Check workflows
        try:
            workflows = self.get_workflows()
            if not workflows:
                errors.append("No workflows configured")
        except Exception as e:
            errors.append(f"Prompts configuration error: {e}")
        
        # Check LLM
        try:
            llm = self.get_llm_config()
            if not llm.get('model'):
                warnings.append("LLM model not configured, using default")
        except Exception as e:
            errors.append(f"LLM configuration error: {e}")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    
    def print_summary(self):
        """Print configuration summary"""
        print("\n" + "="*70)
        print("CONFIGURATION SUMMARY")
        print("="*70)
        
        print(f"\n📡 MCP Server: {self.get_mcp_url()}")
        print(f"   Tools available: {len(self.get_mcp_tools())}")
        
        print(f"\n🤖 LLM: {self.get_llm_model()}")
        print(f"   Endpoint: {self.get_llm_endpoint()}")
        
        print(f"\n⚙️  Workflows:")
        for workflow in self.get_available_workflows():
            status = "✅" if workflow.get('enabled') else "❌"
            print(f"   {status} {workflow.get('name')}")
        
        validation = self.validate()
        if validation['valid']:
            print(f"\n✅ Configuration valid")
        else:
            print(f"\n❌ Configuration errors:")
            for error in validation['errors']:
                print(f"   - {error}")
        
        if validation['warnings']:
            print(f"\n⚠️  Warnings:")
            for warning in validation['warnings']:
                print(f"   - {warning}")
        
        print("="*70 + "\n")


# Global config instance
_config_instance = None

def get_config(config_dir: str = None) -> ConfigLoader:
    """Get or create global config instance"""
    global _config_instance
    if _config_instance is None:
        _config_instance = ConfigLoader(config_dir)
    return _config_instance

def reset_config():
    """Reset global config instance (useful for testing)"""
    global _config_instance
    _config_instance = None
