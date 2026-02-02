"""
Import OpenClaw configurations.
Migrates configs to GuardClaw with encrypted credentials.
"""

import json
import yaml
from pathlib import Path
from typing import Dict, List
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from .vault import CredentialVault


class OpenClawImporter:
    """Import and migrate OpenClaw configurations"""
    
    # Known OpenClaw credential field names
    CREDENTIAL_FIELDS = [
        "anthropic_api_key",
        "openai_api_key",
        "google_api_key",
        "aws_access_key",
        "aws_secret_key",
        "github_token",
        "stripe_key",
        "slack_token",
        "api_key",
        "secret_key",
        "access_token",
        "password",
        "token",
    ]
    
    def __init__(self, openclaw_path: str, workspace: str = "default"):
        """
        Initialize importer.
        
        Args:
            openclaw_path: Path to OpenClaw configuration
            workspace: GuardClaw workspace name
        """
        self.openclaw_path = Path(openclaw_path)
        self.workspace = workspace
        self.vault = CredentialVault()
        self.console = Console()
    
    def import_config(self) -> Dict:
        """
        Import OpenClaw configuration.
        
        Returns:
            Dict with import statistics
        """
        if not self.openclaw_path.exists():
            raise FileNotFoundError(f"OpenClaw config not found: {self.openclaw_path}")
        
        self.console.print(f"\n[cyan]Importing OpenClaw configuration...[/cyan]")
        self.console.print(f"[dim]Source:[/dim] {self.openclaw_path}")
        self.console.print(f"[dim]Workspace:[/dim] {self.workspace}\n")
        
        stats = {
            "credentials_migrated": 0,
            "configs_migrated": 0,
            "files_processed": 0
        }
        
        # Create workspace
        if not self.vault.workspace_exists(self.workspace):
            self.vault.create_workspace(self.workspace)
        
        # Process files
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            
            task = progress.add_task("Scanning files...", total=None)
            
            # Get all config files
            config_files = self._find_config_files()
            stats["files_processed"] = len(config_files)
            
            progress.update(task, description=f"Processing {len(config_files)} files...")
            
            # Process each file
            for config_file in config_files:
                creds_found = self._process_file(config_file)
                stats["credentials_migrated"] += creds_found
                stats["configs_migrated"] += 1
        
        # Print summary
        self._print_summary(stats)
        
        return stats
    
    def _find_config_files(self) -> List[Path]:
        """Find all config files in OpenClaw directory"""
        
        extensions = ['.json', '.yaml', '.yml', '.env', '.conf']
        files = []
        
        if self.openclaw_path.is_file():
            return [self.openclaw_path]
        
        # Scan directory
        for ext in extensions:
            files.extend(self.openclaw_path.rglob(f'*{ext}'))
        
        return files
    
    def _process_file(self, file_path: Path) -> int:
        """Process a single config file and extract credentials"""
        
        credentials_found = 0
        
        try:
            # Load file
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            
            # Try JSON first
            try:
                config = json.loads(content)
            except:
                # Try YAML
                try:
                    config = yaml.safe_load(content)
                except:
                    # Try .env format
                    config = self._parse_env_file(content)
            
            # Extract credentials
            if isinstance(config, dict):
                credentials_found = self._extract_credentials(config, file_path.name)
        
        except Exception as e:
            self.console.print(f"[yellow]Warning:[/yellow] Could not process {file_path.name}: {e}")
        
        return credentials_found
    
    def _extract_credentials(self, config: Dict, source_file: str) -> int:
        """Extract and store credentials from config"""
        
        count = 0
        
        for key, value in config.items():
            # Check if this looks like a credential
            if self._is_credential_field(key) and isinstance(value, str) and len(value) > 8:
                # Skip obvious placeholders
                if value.lower() in ['your-api-key', 'example', 'test', 'changeme']:
                    continue
                
                # Store in vault
                vault_key = f"{key}"
                self.vault.store(vault_key, value, workspace=self.workspace)
                count += 1
                
                self.console.print(f"  [green]✓[/green] Migrated: {key} (from {source_file})")
        
        return count
    
    def _is_credential_field(self, field_name: str) -> bool:
        """Check if field name looks like a credential"""
        field_lower = field_name.lower()
        
        for cred_field in self.CREDENTIAL_FIELDS:
            if cred_field in field_lower:
                return True
        
        return False
    
    def _parse_env_file(self, content: str) -> Dict:
        """Parse .env file format"""
        config = {}
        
        for line in content.split('\n'):
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                config[key.strip()] = value.strip().strip('"').strip("'")
        
        return config
    
    def _print_summary(self, stats: Dict):
        """Print import summary"""
        self.console.print()
        self.console.print("[bold green]✓ Import complete![/bold green]\n")
        self.console.print(f"  Files processed:      {stats['files_processed']}")
        self.console.print(f"  Credentials migrated: {stats['credentials_migrated']}")
        self.console.print(f"  Workspace:            {self.workspace}")
        self.console.print()
        self.console.print("[dim]All credentials are now encrypted and stored securely.[/dim]")
        self.console.print("[dim]Original files were not modified.[/dim]")
        self.console.print()
        self.console.print("[cyan]Next steps:[/cyan]")
        self.console.print("  1. Verify credentials: [bold]guardclaw vault list[/bold]")
        self.console.print("  2. Run your first task: [bold]guardclaw run 'search for Python tutorials'[/bold]")
