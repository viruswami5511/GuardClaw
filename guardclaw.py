#!/usr/bin/env python3
"""
GuardClaw CLI
Main command-line interface.
"""

import click
import json
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from guardclaw import CredentialVault, Agent, OpenClawImporter
from scanner.scanner import Scanner


@click.group()
@click.version_option(version="0.2.0")
def cli():
    """
    GuardClaw - Secure AI Agent Runtime
    
    OpenClaw alternative with encrypted credentials and audit logging.
    """
    pass


@cli.command()
@click.argument("task")
@click.option("--workspace", "-w", default="default", help="Workspace to use")
@click.option("--model", "-m", default="anthropic/claude-3-5-sonnet-20241022", help="LLM model")
@click.option("--dry-run", is_flag=True, help="Preview without executing")
def run(task, workspace, model, dry_run):
    """
    Run a task.
    
    Example:
        guardclaw run "search for Python tutorials"
        guardclaw run "what is the weather today" --dry-run
    """
    agent = Agent(workspace=workspace, model=model, dry_run=dry_run)
    result = agent.run(task)
    
    if not result["success"]:
        raise click.ClickException(result.get("error", "Unknown error"))


@cli.group()
def vault():
    """Manage encrypted credentials"""
    pass


@vault.command("store")
@click.argument("key")
@click.argument("value")
@click.option("--workspace", "-w", default="default", help="Workspace name")
def vault_store(key, value, workspace):
    """
    Store encrypted credential.
    
    Example:
        guardclaw vault store anthropic_api_key sk-ant-...
    """
    v = CredentialVault()
    v.store(key, value, workspace=workspace)
    
    console = Console()
    console.print(f"[green]✓[/green] Stored credential: {key} (workspace: {workspace})")


@vault.command("list")
@click.option("--workspace", "-w", default="default", help="Workspace name")
def vault_list(workspace):
    """
    List credentials in workspace.
    
    Example:
        guardclaw vault list
    """
    v = CredentialVault()
    creds = v.list_credentials(workspace=workspace)
    
    console = Console()
    
    if not creds:
        console.print(f"[yellow]No credentials in workspace '{workspace}'[/yellow]")
        return
    
    table = Table(title=f"Credentials (workspace: {workspace})")
    table.add_column("Key", style="cyan")
    
    for key in creds:
        table.add_row(key)
    
    console.print(table)


@vault.command("delete")
@click.argument("key")
@click.option("--workspace", "-w", default="default", help="Workspace name")
def vault_delete(key, workspace):
    """
    Delete credential.
    
    Example:
        guardclaw vault delete old_api_key
    """
    v = CredentialVault()
    v.delete(key, workspace=workspace)
    
    console = Console()
    console.print(f"[green]✓[/green] Deleted credential: {key}")


@vault.command("export")
@click.option("--workspace", "-w", default="default", help="Workspace name")
def vault_export(workspace):
    """
    Export credentials as .env format.
    
    Example:
        guardclaw vault export > .env
    """
    v = CredentialVault()
    env_content = v.export_for_env(workspace=workspace)
    
    console = Console()
    console.print(env_content)


@cli.command("import")
@click.argument("openclaw_path")
@click.option("--workspace", "-w", default="default", help="Target workspace")
def import_openclaw(openclaw_path, workspace):
    """
    Import OpenClaw configuration.
    
    Example:
        guardclaw import ~/.openclaw
        guardclaw import test_openclaw_config
    """
    importer = OpenClawImporter(openclaw_path, workspace=workspace)
    importer.import_config()


@cli.command()
@click.argument("config_path")
@click.option("--format", "-f", type=click.Choice(['console', 'json']), default='console')
@click.option("--output", "-o", type=click.Path(), help="Output file (for JSON)")
def scan(config_path, format, output):
    """
    Scan configuration for security issues.
    
    Example:
        guardclaw scan ~/.openclaw
        guardclaw scan test_openclaw_config --format json --output report.json
    """
    scanner = Scanner(config_path)
    scanner.scan(output_format=format, output_path=output)


@cli.command()
def info():
    """
    Display GuardClaw system information.
    """
    console = Console()
    
    v = CredentialVault()
    
    # Count credentials
    creds = v.list_credentials("default")
    
    console.print()
    console.print(Panel.fit(
        "[bold cyan]GuardClaw v0.2.0[/bold cyan]\n\n"
        f"[dim]Vault location:[/dim] {v.vault_path}\n"
        f"[dim]Credentials stored:[/dim] {len(creds)}\n"
        f"[dim]Default workspace:[/dim] default",
        border_style="cyan",
        title="[bold]System Info[/bold]"
    ))
    console.print()


if __name__ == "__main__":
    cli()
