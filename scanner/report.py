"""
Beautiful report generation for scanner results.
Uses Rich library for terminal output.
"""

from typing import List, Dict, Any
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
import json
from datetime import datetime


class Report:
    """Generate beautiful security scan reports"""
    
    SEVERITY_COLORS = {
        "critical": "red",
        "high": "yellow",
        "medium": "blue",
        "low": "green"
    }
    
    SEVERITY_EMOJIS = {
        "critical": "🚨",
        "high": "⚠️",
        "medium": "ℹ️",
        "low": "✓"
    }
    
    def __init__(self):
        self.console = Console()
    
    def print_summary(self, findings: List[Dict[str, Any]], config_path: str):
        """Print a beautiful summary report"""
        
        # Header
        self.console.print()
        self.console.print(Panel.fit(
            "[bold cyan]GuardClaw Security Scanner[/bold cyan]\n"
            "[dim]OpenClaw Configuration Analysis[/dim]",
            border_style="cyan"
        ))
        self.console.print()
        
        # Scan info
        self.console.print(f"[dim]Scanned:[/dim] {config_path}")
        self.console.print(f"[dim]Time:[/dim] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.console.print()
        
        # No findings
        if not findings:
            self.console.print(Panel(
                "[bold green]✓ No security issues found![/bold green]\n\n"
                "Your OpenClaw configuration looks secure.\n"
                "Consider migrating to GuardClaw for additional hardening:\n"
                "[cyan]guardclaw import ~/.openclaw[/cyan]",
                border_style="green",
                title="[green]All Clear[/green]"
            ))
            return
        
        # Count by severity
        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for finding in findings:
            severity_counts[finding["severity"]] += 1
        
        # Summary stats
        total_issues = len(findings)
        risk_score = (
            severity_counts["critical"] * 10 +
            severity_counts["high"] * 5 +
            severity_counts["medium"] * 2 +
            severity_counts["low"] * 1
        )
        
        # Risk level
        if risk_score >= 30:
            risk_level = "CRITICAL"
            risk_color = "red"
        elif risk_score >= 15:
            risk_level = "HIGH"
            risk_color = "yellow"
        elif risk_score >= 5:
            risk_level = "MEDIUM"
            risk_color = "blue"
        else:
            risk_level = "LOW"
            risk_color = "green"
        
        # Summary panel
        summary_text = (
            f"[bold]Total Issues:[/bold] {total_issues}\n"
            f"[red]Critical:[/red] {severity_counts['critical']}  "
            f"[yellow]High:[/yellow] {severity_counts['high']}  "
            f"[blue]Medium:[/blue] {severity_counts['medium']}  "
            f"[green]Low:[/green] {severity_counts['low']}\n\n"
            f"[bold]Risk Level:[/bold] [{risk_color}]{risk_level}[/{risk_color}]"
        )
        
        self.console.print(Panel(
            summary_text,
            title="[bold]Scan Results[/bold]",
            border_style=risk_color
        ))
        self.console.print()
        
        # Detailed findings
        self.console.print("[bold]Findings:[/bold]\n")
        
        for i, finding in enumerate(findings, 1):
            self._print_finding(i, finding)
        
        # Recommendations
        self.console.print()
        self._print_recommendations(severity_counts)
    
    def _print_finding(self, number: int, finding: Dict[str, Any]):
        """Print a single finding"""
        severity = finding["severity"]
        emoji = self.SEVERITY_EMOJIS[severity]
        color = self.SEVERITY_COLORS[severity]
        
        # Finding header
        self.console.print(
            f"[{color}]{emoji} {number}. [{color.upper()}] {finding['title']}[/{color}]"
        )
        
        # Description
        self.console.print(f"   [dim]{finding['description']}[/dim]")
        
        # Context note
        if finding.get("context"):
            self.console.print(f"   [bold]Context:[/bold]")
            for line in finding["context"].split('\n'):
                if line.strip():
                    self.console.print(f"   [dim]{line}[/dim]")
        
        # Specific finding data
        if finding.get("finding"):
            self.console.print(f"   [bold]Details:[/bold]")
            finding_data = finding["finding"]
            
            if isinstance(finding_data, list):
                for item in finding_data[:3]:  # Show first 3
                    if isinstance(item, dict):
                        for key, value in item.items():
                            self.console.print(f"     • {key}: [yellow]{value}[/yellow]")
                    else:
                        self.console.print(f"     • {item}")
                
                if len(finding_data) > 3:
                    self.console.print(f"     [dim]... and {len(finding_data) - 3} more[/dim]")
            else:
                self.console.print(f"     {finding_data}")
        
        # Remediation
        self.console.print(f"   [bold green]Fix:[/bold green] {finding['remediation']}")
        self.console.print()
    
    def _print_recommendations(self, severity_counts: Dict[str, int]):
        """Print recommendations based on findings"""
        
        recommendations = []
        
        if severity_counts["critical"] > 0:
            recommendations.append(
                "🚨 [bold red]URGENT:[/bold red] Critical issues found. "
                "Your credentials may be exposed."
            )
        
        if severity_counts["high"] > 0:
            recommendations.append(
                "⚠️  [yellow]HIGH PRIORITY:[/yellow] Address high-severity issues soon."
            )
        
        recommendations.extend([
            "",
            "[bold cyan]Recommended Actions:[/bold cyan]",
            "",
            "1. [bold]Migrate to GuardClaw[/bold] (automatic encryption):",
            "   [cyan]guardclaw import ~/.openclaw[/cyan]",
            "",
            "2. [bold]Or manually fix:[/bold]",
            "   • Move secrets to environment variables",
            "   • Restrict file permissions (chmod 600)",
            "   • Bind services to localhost only",
            "",
            "3. [bold]Monitor:[/bold]",
            "   • Check if credentials were committed to git",
            "   • Rotate exposed API keys immediately",
            "   • Review recent access logs",
            "",
            "[dim]Learn more: https://guardclaw.ai/security[/dim]"
        ])
        
        self.console.print(Panel(
            "\n".join(recommendations),
            title="[bold]Recommendations[/bold]",
            border_style="cyan"
        ))
    
    def export_json(self, findings: List[Dict[str, Any]], output_path: str):
        """Export findings to JSON"""
        report = {
            "scan_time": datetime.now().isoformat(),
            "version": "0.1.0",
            "total_findings": len(findings),
            "findings": findings
        }
        
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        self.console.print(f"[green]✓[/green] Report saved to: {output_path}")
