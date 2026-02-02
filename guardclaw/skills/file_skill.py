"""
File operations skill - read/write files safely.
"""

from pathlib import Path
from typing import Dict, Any, Optional
from .base import Skill


class FileSkill(Skill):
    """Safe file operations (read-only by default)"""
    
    def __init__(self, read_only: bool = True):
        super().__init__(
            name="file_operations",
            description="Read and write files (with permission)",
            capabilities=["read_files"] if read_only else ["read_files", "write_files"]
        )
        self.read_only = read_only
    
    def execute(
        self,
        operation: str,
        path: str,
        content: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Perform file operation.
        
        Args:
            operation: "read" or "write"
            path: File path
            content: Content to write (for write operation)
            
        Returns:
            Dict with success status and result
        """
        params = {
            "operation": operation,
            "path": path
        }
        
        try:
            file_path = Path(path).resolve()
            
            if operation == "read":
                result = self._read_file(file_path)
            
            elif operation == "write":
                if self.read_only:
                    raise PermissionError("Write operations disabled (read-only mode)")
                
                if content is None:
                    raise ValueError("Content required for write operation")
                
                result = self._write_file(file_path, content)
            
            else:
                raise ValueError(f"Unknown operation: {operation}")
            
            result["success"] = True
        
        except Exception as e:
            result = {
                "success": False,
                "result": None,
                "error": str(e)
            }
        
        # Log execution
        self.log_execution(params, result)
        
        return result
    
    def _read_file(self, path: Path) -> Dict[str, Any]:
        """Read file contents"""
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        
        if not path.is_file():
            raise ValueError(f"Not a file: {path}")
        
        # Limit file size (10MB max)
        if path.stat().st_size > 10 * 1024 * 1024:
            raise ValueError("File too large (max 10MB)")
        
        content = path.read_text(encoding='utf-8', errors='ignore')
        
        return {
            "result": content,
            "path": str(path),
            "size": path.stat().st_size,
            "lines": len(content.split('\n'))
        }
    
    def _write_file(self, path: Path, content: str) -> Dict[str, Any]:
        """Write file contents"""
        
        # Create parent directories if needed
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write file
        path.write_text(content, encoding='utf-8')
        
        return {
            "result": f"Wrote {len(content)} characters to {path}",
            "path": str(path),
            "size": len(content)
        }
