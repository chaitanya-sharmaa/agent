from typing import Any, Dict, Optional
import json
from langchain_core.tools.base import ToolException

class K8sResourceErrorHandler:
    """Handles errors related to Kubernetes resource operations, especially for missing CRDs."""
    
    @staticmethod
    def handle_missing_crd_error(error: Exception) -> Dict[str, Any]:
        """Handle errors when a Custom Resource Definition (CRD) is not found."""
        error_str = str(error)
        
        # Check if it's a missing CRD error
        if "not found" in error_str.lower() and any(crd in error_str.lower() for crd in [
            "peerauthentication", "authorizationpolicy", "virtualservice", "destinationrule"
        ]):
            # Extract resource type from error message
            resource_type = "unknown resource"
            if "peerauthentication" in error_str.lower():
                resource_type = "PeerAuthentication"
            elif "authorizationpolicy" in error_str.lower():
                resource_type = "AuthorizationPolicy"
            elif "virtualservice" in error_str.lower():
                resource_type = "VirtualService"
            elif "destinationrule" in error_str.lower():
                resource_type = "DestinationRule"
            
            return {
                "error": "crd_not_found",
                "resource_type": resource_type,
                "message": f"{resource_type} CRD not found. This usually means Istio is not installed or the CRDs are not available.",
                "items": [],
                "status": "not_available"
            }
        
        # For other errors, return a generic error response
        return {
            "error": "unknown_error",
            "message": str(error),
            "items": [],
            "status": "error"
        }
    
    @staticmethod
    def format_error_for_ai(error_response: Dict[str, Any]) -> str:
        """Format error response for AI to understand and process."""
        if error_response.get("error") == "crd_not_found":
            return json.dumps({
                "items": [],
                "error": error_response["message"],
                "resource_not_available": True
            })
        return json.dumps(error_response)


def safe_tool_wrapper(tool_func):
    """Wrapper to handle tool exceptions gracefully."""
    async def wrapper(*args, **kwargs):
        try:
            result = await tool_func(*args, **kwargs)
            return result
        except ToolException as e:
            error_handler = K8sResourceErrorHandler()
            error_response = error_handler.handle_missing_crd_error(e)
            return error_handler.format_error_for_ai(error_response)
        except Exception as e:
            error_handler = K8sResourceErrorHandler()
            error_response = error_handler.handle_missing_crd_error(e)
            return error_handler.format_error_for_ai(error_response)
    
    return wrapper