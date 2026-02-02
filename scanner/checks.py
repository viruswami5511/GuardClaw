"""
Security checks for OpenClaw configurations.
Each check returns a dict with:
- severity: "critical" | "high" | "medium" | "low"
- title: Short description
- description: Detailed explanation
- remediation: How to fix
- finding: Specific data found
- context: Severity explanation
"""

import os
import re
import math
from pathlib import Path
from typing import Dict, List, Any


class SecurityChecks:
    """Collection of security checks"""
    
    # High-confidence API key patterns (provider-specific formats)
    API_KEY_PATTERNS = {
        "Anthropic API Key": r"sk-ant-api03-[a-zA-Z0-9_-]{95,}",
        "OpenAI API Key": r"sk-[a-zA-Z0-9]{48}",
        "OpenAI Organization Key": r"sk-org-[a-zA-Z0-9]{48}",
        "Google API Key": r"AIza[0-9A-Za-z\-_]{35}",
        "AWS Access Key": r"AKIA[0-9A-Z]{16}",
        "GitHub Token (classic)": r"ghp_[a-zA-Z0-9]{36}",
        "GitHub Token (fine-grained)": r"github_pat_[a-zA-Z0-9]{22}_[a-zA-Z0-9]{59}",
        "Stripe Secret Key": r"sk_live_[0-9a-zA-Z]{24,}",
        "Stripe Restricted Key": r"rk_live_[0-9a-zA-Z]{24,}",
        "Slack Token": r"xox[baprs]-[0-9]{10,13}-[0-9]{10,13}-[a-zA-Z0-9]{24,}",
        "Twilio API Key": r"SK[0-9a-fA-F]{32}",
        "SendGrid API Key": r"SG\.[a-zA-Z0-9_-]{22}\.[a-zA-Z0-9_-]{43}",
    }
    
    # Known placeholder/example values (NOT real secrets)
    PLACEHOLDER_VALUES = {
        "your-api-key-here",
        "your_api_key",
        "sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
        "placeholder",
        "example",
        "test",
        "demo",
        "sample",
        "changeme",
        "replace-this",
        "insert-key-here",
        "xxx",
        "yyy",
        "zzz",
        "abc123",
        "test123",
        "1234567890",
    }
    
    def __init__(self, config_path: str):
        self.config_path = Path(config_path)
        self.findings: List[Dict[str, Any]] = []
    
    def run_all_checks(self) -> List[Dict[str, Any]]:
        """Run all security checks"""
        self.findings = []
        
        # Check if path exists
        if not self.config_path.exists():
            return [{
                "severity": "critical",
                "title": "Configuration not found",
                "description": f"Path does not exist: {self.config_path}",
                "remediation": "Ensure the OpenClaw configuration path is correct",
                "finding": str(self.config_path),
                "context": None
            }]
        
        # Run checks
        self.check_plaintext_secrets()
        self.check_file_permissions()
        self.check_exposed_endpoints()
        self.check_unsafe_configs()
        self.check_logging_risks()
        
        return self.findings
    
    def check_plaintext_secrets(self):
        """Check for plaintext secrets in config files (with entropy validation)"""
        secrets_found = []
        
        # Scan all files in config directory
        for file_path in self._get_config_files():
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # Check for high-confidence API key patterns
                for secret_type, pattern in self.API_KEY_PATTERNS.items():
                    matches = re.finditer(pattern, content)
                    for match in matches:
                        secret_value = match.group(0)
                        
                        # Skip if it's a known placeholder
                        if self._is_placeholder(secret_value):
                            continue
                        
                        # Additional entropy check for generic patterns
                        if not self._has_sufficient_entropy(secret_value):
                            continue
                        
                        # Mask the secret (show first/last 4 chars)
                        if len(secret_value) > 8:
                            masked = f"{secret_value[:8]}...{secret_value[-4:]}"
                        else:
                            masked = "***"
                        
                        secrets_found.append({
                            "file": str(file_path.relative_to(self.config_path)),
                            "type": secret_type,
                            "masked_value": masked,
                            "line": self._get_line_number(content, match.start())
                        })
            
            except Exception as e:
                # Skip files we can't read
                continue
        
        if secrets_found:
            # Add context note
            context_note = (
                "Severity is CRITICAL if this configuration is:\n"
                "  • Committed to version control (git)\n"
                "  • Stored in cloud backups\n"
                "  • Accessible to multiple users\n"
                "  • On an internet-facing machine"
            )
            
            self.findings.append({
                "severity": "critical",
                "title": f"Found {len(secrets_found)} plaintext secret(s)",
                "description": "API keys and tokens are stored in plaintext. If this configuration is exposed (git, logs, backups), these credentials can be stolen.",
                "remediation": "Use GuardClaw's encrypted vault: `guardclaw import ~/.openclaw`",
                "finding": secrets_found[:5],  # Show first 5
                "context": context_note
            })
    
    def check_file_permissions(self):
        """Check if config files have loose permissions"""
        if os.name == 'nt':
            # Windows - add explicit note
            self.findings.append({
                "severity": "low",
                "title": "Windows file permissions not evaluated",
                "description": "File permission checks are not performed on Windows due to different security model (ACLs vs. Unix permissions).",
                "remediation": "Manually review file permissions using Windows Explorer > Properties > Security tab. Ensure only your user account has access.",
                "finding": None,
                "context": "This is informational, not a security issue."
            })
            return
        
        loose_files = []
        
        for file_path in self._get_config_files():
            try:
                stat_info = file_path.stat()
                mode = oct(stat_info.st_mode)[-3:]
                
                # Check if world-readable or group-readable (last two digits)
                group_read = int(mode[-2]) >= 4
                other_read = int(mode[-1]) >= 4
                
                if group_read or other_read:
                    loose_files.append({
                        "file": str(file_path.relative_to(self.config_path)),
                        "permissions": mode,
                        "readable_by": "group and others" if group_read and other_read else ("group" if group_read else "others")
                    })
            except:
                continue
        
        if loose_files:
            context_note = (
                "Severity is HIGH if:\n"
                "  • This is a multi-user system\n"
                "  • You don't trust all users with group/other access\n"
                "Severity is LOW if you're the only user on this machine."
            )
            
            self.findings.append({
                "severity": "high",
                "title": f"Found {len(loose_files)} file(s) with loose permissions",
                "description": "Config files are readable by other users on the system. Secrets can be accessed by anyone with local access.",
                "remediation": "Run: `chmod 600 ~/.openclaw/*.json`",
                "finding": loose_files[:5],
                "context": context_note
            })
    
    def check_exposed_endpoints(self):
        """Check for exposed admin endpoints"""
        exposed = []
        
        # Look for config files that specify bind addresses
        for file_path in self._get_config_files():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Check for dangerous bind patterns
                dangerous_patterns = [
                    (r'["\']?0\.0\.0\.0["\']?', "Binds to all network interfaces"),
                    (r'["\']host["\']\s*:\s*["\']0\.0\.0\.0["\']', "Host explicitly set to 0.0.0.0"),
                    (r'["\']listen["\']\s*:\s*["\']0\.0\.0\.0', "Listen address set to all interfaces"),
                ]
                
                for pattern, risk in dangerous_patterns:
                    matches = list(re.finditer(pattern, content))
                    if matches:
                        exposed.append({
                            "file": str(file_path.relative_to(self.config_path)),
                            "risk": risk,
                            "line": self._get_line_number(content, matches[0].start())
                        })
                        break
            
            except:
                continue
        
        if exposed:
            context_note = (
                "Severity is HIGH if this machine is:\n"
                "  • Directly exposed to the internet\n"
                "  • On a network you don't fully control\n"
                "Severity is LOW if this is only for local development behind a firewall."
            )
            
            self.findings.append({
                "severity": "high",
                "title": f"Found {len(exposed)} potentially exposed endpoint(s)",
                "description": "Admin interfaces or APIs may be accessible from the internet. This allows attackers to control your agent remotely.",
                "remediation": "Bind to 127.0.0.1 (localhost only) or use firewall rules to restrict access",
                "finding": exposed,
                "context": context_note
            })
    
    def check_unsafe_configs(self):
        """Check for unsafe configuration options"""
        unsafe = []
        
        for file_path in self._get_config_files():
            try:
                content = file_path.read_text(encoding='utf-8')
                
                # Check for dangerous settings
                dangerous_settings = [
                    (r'"disable[_-]?security"?\s*:\s*true', "Security features disabled"),
                    (r'"allow[_-]?remote[_-]?exec"?\s*:\s*true', "Remote code execution enabled"),
                    (r'"debug"?\s*:\s*true', "Debug mode enabled (may leak secrets in logs)"),
                    (r'"verbose"?\s*:\s*true', "Verbose logging (may leak sensitive data)"),
                ]
                
                for pattern, risk in dangerous_settings:
                    matches = list(re.finditer(pattern, content, re.IGNORECASE))
                    if matches:
                        unsafe.append({
                            "file": str(file_path.relative_to(self.config_path)),
                            "risk": risk,
                            "line": self._get_line_number(content, matches[0].start())
                        })
            except:
                continue
        
        if unsafe:
            context_note = "Debug/verbose modes are safe during development but should be disabled in production."
            
            self.findings.append({
                "severity": "medium",
                "title": f"Found {len(unsafe)} unsafe configuration(s)",
                "description": "Configuration options that may reduce security or leak data are enabled.",
                "remediation": "Review and disable debug/verbose settings in production deployments",
                "finding": unsafe,
                "context": context_note
            })
    
    def check_logging_risks(self):
        """Check for logs that might contain secrets"""
        log_files = []
        
        # Look for log files
        for ext in ['*.log', '*.txt']:
            log_files.extend(self.config_path.rglob(ext))
        
        risky_logs = []
        for log_file in log_files[:10]:  # Check first 10 logs
            try:
                # Only check recent logs (< 10MB)
                if log_file.stat().st_size > 10 * 1024 * 1024:
                    continue
                
                content = log_file.read_text(encoding='utf-8', errors='ignore')
                
                # Check if logs contain potential secrets (high-confidence patterns only)
                for secret_type, pattern in list(self.API_KEY_PATTERNS.items())[:5]:
                    matches = list(re.finditer(pattern, content))
                    if matches:
                        # Verify it's not a placeholder
                        for match in matches:
                            if not self._is_placeholder(match.group(0)):
                                risky_logs.append({
                                    "file": str(log_file.relative_to(self.config_path)),
                                    "risk": f"Contains {secret_type}",
                                    "size": f"{log_file.stat().st_size // 1024}KB"
                                })
                                break
                        break
            except:
                continue
        
        if risky_logs:
            self.findings.append({
                "severity": "medium",
                "title": f"Found {len(risky_logs)} log file(s) with potential secrets",
                "description": "Log files may contain secrets that were printed during execution or debugging.",
                "remediation": "Delete old logs: `rm ~/.openclaw/*.log` and configure log redaction",
                "finding": risky_logs,
                "context": "Old logs should be rotated and deleted regularly."
            })
    
    def _is_placeholder(self, value: str) -> bool:
        """Check if a value is likely a placeholder, not a real secret"""
        value_lower = value.lower()
        
        # Check against known placeholders
        for placeholder in self.PLACEHOLDER_VALUES:
            if placeholder in value_lower:
                return True
        
        # Check for repetitive patterns (e.g., "xxxxxxxx", "11111111")
        if len(set(value)) <= 3:  # Only 1-3 unique characters
            return True
        
        # Check for sequential patterns
        if value.lower().startswith(("abc", "test", "demo", "example")):
            return True
        
        return False
    
    def _has_sufficient_entropy(self, value: str) -> bool:
        """Calculate Shannon entropy to detect low-entropy (likely fake) values"""
        if len(value) < 16:
            return False
        
        # Calculate Shannon entropy
        entropy = 0
        for char in set(value):
            prob = value.count(char) / len(value)
            entropy -= prob * math.log2(prob)
        
        # Real API keys have entropy > 3.5 bits
        # (random base62 has ~5.95 bits)
        return entropy > 3.5
    
    def _get_line_number(self, content: str, position: int) -> int:
        """Get line number from character position"""
        return content[:position].count('\n') + 1
    
    def _get_config_files(self) -> List[Path]:
        """Get all config files to scan"""
        extensions = ['.json', '.yaml', '.yml', '.env', '.conf', '.config', '.toml']
        files = []
        
        if self.config_path.is_file():
            return [self.config_path]
        
        for ext in extensions:
            files.extend(self.config_path.rglob(f'*{ext}'))
        
        # Limit to reasonable number
        return files[:100]
