"""
Main scanner entry point.
Orchestrates security checks and report generation.
"""

import click
from pathlib import Path
from .checks import SecurityChecks
from .report import Report


class Scanner:
    """Main scanner class"""
    
    def __init__(self, config_path: str):
        self.config_path = Path(config_path).expanduser()
        self.checks = SecurityChecks(str(self.config_path))
        self.report = Report()
    
    def scan(self, output_format: str = "console", output_path: str = None):
        """Run the security scan"""
        
        # Run all checks
        findings = self.checks.run_all_checks()
        
        # Generate report
        if output_format == "console":
            self.report.print_summary(findings, str(self.config_path))
        
        elif output_format == "json":
            if not output_path:
                output_path = "guardclaw_scan_results.json"
            self.report.export_json(findings, output_path)
        
        return findings


@click.command()
@click.argument('config_path', type=click.Path(exists=True))
@click.option('--format', '-f', type=click.Choice(['console', 'json']), default='console',
              help='Output format')
@click.option('--output', '-o', type=click.Path(), help='Output file (for JSON format)')
def main(config_path, format, output):
    """
    GuardClaw Security Scanner
    
    Scan OpenClaw configurations for security issues.
    
    Example:
        guardclaw-scanner ~/.openclaw
        guardclaw-scanner ~/.openclaw --format json --output results.json
    """
    scanner = Scanner(config_path)
    scanner.scan(output_format=format, output_path=output)


if __name__ == "__main__":
    main()
