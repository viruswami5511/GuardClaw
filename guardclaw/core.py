"""
GuardClaw Agent Runtime
Executes tasks using LLM + skills with secure credential injection.
"""

import os
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
import litellm
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from .vault import CredentialVault
from .skills.base import Skill
from .skills.search import WebSearchSkill
from .skills.email_skill import EmailSkill
from .skills.file_skill import FileSkill


class Agent:
    """AI Agent with encrypted credentials and audit logging"""
    
    def __init__(
        self,
        workspace: str = "default",
        model: str = "anthropic/claude-3-5-sonnet-20241022",
        dry_run: bool = False
    ):
        """
        Initialize agent.
        
        Args:
            workspace: Credential workspace to use
            model: LLM model name (litellm format)
            dry_run: If True, preview actions without executing
        """
        self.workspace = workspace
        self.model = model
        self.dry_run = dry_run
        
        self.vault = CredentialVault()
        self.console = Console()
        
        # Load skills
        self.skills: Dict[str, Skill] = {}
        self._load_skills()
        
        # Audit log
        self.audit_log = []
    
    def _load_skills(self):
        """Load available skills"""
        try:
            self.skills["web_search"] = WebSearchSkill()
            self.console.print("[dim]✓ Loaded skill: web_search[/dim]")
        except Exception as e:
            self.console.print(f"[yellow]Warning:[/yellow] Could not load web_search: {e}")
        
        try:
            self.skills["send_email"] = EmailSkill()
            self.console.print("[dim]✓ Loaded skill: send_email[/dim]")
        except Exception as e:
            self.console.print(f"[yellow]Warning:[/yellow] Could not load send_email: {e}")
        
        try:
            self.skills["file_operations"] = FileSkill(read_only=True)
            self.console.print("[dim]✓ Loaded skill: file_operations[/dim]")
        except Exception as e:
            self.console.print(f"[yellow]Warning:[/yellow] Could not load file_operations: {e}")
    
    def run(self, task: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Run a task.
        
        Args:
            task: Natural language task description
            context: Optional context dict
            
        Returns:
            Dict with execution result
        """
        self.console.print()
        self.console.print(Panel.fit(
            f"[bold cyan]GuardClaw Agent[/bold cyan]\n"
            f"[dim]Task: {task}[/dim]",
            border_style="cyan"
        ))
        self.console.print()
        
        if self.dry_run:
            self.console.print("[yellow]🔍 DRY RUN MODE[/yellow] - Preview only\n")
        
        # Log task
        self._audit_log("task_started", {"task": task, "workspace": self.workspace})
        
        try:
            # Get API key from vault
            api_key = self._get_api_key()
            
            # Generate response
            with Progress(
                SpinnerColumn(),
                TextColumn("[cyan]{task.description}[/cyan]"),
                console=self.console
            ) as progress:
                task_progress = progress.add_task("Thinking...", total=None)
                
                if self.dry_run:
                    result = "Dry run mode - task would be executed here"
                else:
                    result = self._execute_task(task, api_key)
            
            # Display result
            self.console.print()
            self.console.print(Panel(
                result,
                title="[bold green]Result[/bold green]",
                border_style="green"
            ))
            
            # Log completion
            self._audit_log("task_completed", {"success": True})
            
            return {
                "success": True,
                "result": result,
                "task": task
            }
        
        except Exception as e:
            self.console.print(f"\n[red]✗ Error:[/red] {e}")
            self._audit_log("task_failed", {"error": str(e)})
            
            return {
                "success": False,
                "error": str(e),
                "task": task
            }
    
    def _get_api_key(self) -> str:
        """Get API key from vault"""
        
        # Try to get Anthropic key first (preferred)
        try:
            return self.vault.retrieve("anthropic_api_key", workspace=self.workspace)
        except KeyError:
            pass
        
        # Try OpenAI
        try:
            return self.vault.retrieve("openai_api_key", workspace=self.workspace)
        except KeyError:
            pass
        
        # Check environment
        if "ANTHROPIC_API_KEY" in os.environ:
            return os.environ["ANTHROPIC_API_KEY"]
        
        if "OPENAI_API_KEY" in os.environ:
            return os.environ["OPENAI_API_KEY"]
        
        raise ValueError(
            "No API key found. Add one with:\n"
            "  guardclaw vault store anthropic_api_key <your-key>"
        )
    
    def _execute_task(self, task: str, api_key: str) -> str:
        """Execute task using LLM"""
        
        # Build system prompt
        system_prompt = self._build_system_prompt()
        
        # Call LLM
        try:
            response = litellm.completion(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": task}
                ],
                api_key=api_key,
                temperature=0.3
            )
            
            return response.choices[0].message.content
        
        except Exception as e:
            raise Exception(f"LLM execution failed: {e}")
    
    def _build_system_prompt(self) -> str:
        """Build system prompt with available skills"""
        
        skills_desc = []
        for skill in self.skills.values():
            skills_desc.append(f"- {skill.name}: {skill.description}")
        
        skills_text = "\n".join(skills_desc) if skills_desc else "No skills loaded"
        
        return f"""You are GuardClaw, a helpful and secure AI assistant.

Available skills:
{skills_text}

You can help with tasks by:
1. Answering questions directly with accurate information
2. Using available skills when needed (not yet implemented in this version)
3. Providing clear, concise, and helpful responses

Be accurate, helpful, and honest. If you're not sure about something, say so."""
    
    def _audit_log(self, event: str, data: Dict[str, Any]):
        """Log event to audit trail"""
        self.audit_log.append({
            "timestamp": datetime.now().isoformat(),
            "event": event,
            "data": data
        })
    
    def get_audit_log(self) -> List[Dict[str, Any]]:
        """Get audit log"""
        return self.audit_log
