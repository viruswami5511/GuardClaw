"""
Base class for GuardClaw skills.
All skills inherit from this.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List
from datetime import datetime


class Skill(ABC):
    """Base class for all skills"""
    
    def __init__(self, name: str, description: str, capabilities: List[str]):
        """
        Initialize skill.
        
        Args:
            name: Skill name (e.g., "web_search")
            description: Human-readable description
            capabilities: List of required capabilities (e.g., ["network", "read"])
        """
        self.name = name
        self.description = description
        self.capabilities = capabilities
        self.execution_history = []
    
    @abstractmethod
    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute the skill.
        
        Args:
            **kwargs: Skill-specific parameters
            
        Returns:
            Dict with:
                - success: bool
                - result: Any (skill output)
                - error: str (if success=False)
        """
        pass
    
    def validate_capabilities(self, allowed_capabilities: List[str]) -> bool:
        """
        Check if skill capabilities are allowed.
        
        Args:
            allowed_capabilities: List of allowed capabilities
            
        Returns:
            True if all required capabilities are allowed
        """
        return all(cap in allowed_capabilities for cap in self.capabilities)
    
    def log_execution(self, params: Dict, result: Dict):
        """Log skill execution for audit trail"""
        self.execution_history.append({
            "timestamp": datetime.now().isoformat(),
            "params": params,
            "result": {
                "success": result.get("success"),
                "error": result.get("error")
            }
        })
    
    def get_manifest(self) -> Dict[str, Any]:
        """
        Get skill manifest (metadata).
        
        Returns:
            Dict with skill metadata
        """
        return {
            "name": self.name,
            "description": self.description,
            "capabilities": self.capabilities,
            "executions": len(self.execution_history)
        }
