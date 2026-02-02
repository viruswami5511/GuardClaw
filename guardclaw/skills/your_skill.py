from .base import Skill
from typing import Dict, Any

class YourSkill(Skill):
    def __init__(self):
        super().__init__(
            name="your_skill",
            description="What your skill does",
            capabilities=["network", "read"]  # Required capabilities
        )
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        # Your skill logic here
        return {
            "success": True,
            "result": "Your result"
        }
