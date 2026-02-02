"""
Encrypted credential vault.
Stores API keys and secrets with Fernet encryption.
Never stores plaintext on disk.
"""

import os
import json
from pathlib import Path
from typing import Dict, Optional
from cryptography.fernet import Fernet
import base64
import hashlib


class CredentialVault:
    """Secure credential storage with encryption"""
    
    def __init__(self, vault_path: Optional[str] = None):
        """
        Initialize vault.
        
        Args:
            vault_path: Path to vault directory (default: ~/.guardclaw)
        """
        if vault_path is None:
            vault_path = Path.home() / ".guardclaw"
        
        self.vault_path = Path(vault_path)
        self.vault_path.mkdir(parents=True, exist_ok=True)
        
        self.key_file = self.vault_path / ".vault_key"
        self.creds_file = self.vault_path / ".credentials"
        
        # Initialize encryption
        self.cipher = self._init_encryption()
    
    def _init_encryption(self) -> Fernet:
        """Initialize or load encryption key"""
        
        if self.key_file.exists():
            # Load existing key
            with open(self.key_file, "rb") as f:
                key = f.read()
        else:
            # Generate new key
            key = Fernet.generate_key()
            
            # Save key (secure permissions)
            with open(self.key_file, "wb") as f:
                f.write(key)
            
            # Set restrictive permissions (owner only)
            if os.name != 'nt':  # Unix/Linux/Mac
                os.chmod(self.key_file, 0o600)
        
        return Fernet(key)
    
    def store(self, key: str, value: str, workspace: str = "default") -> None:
        """
        Store encrypted credential.
        
        Args:
            key: Credential name (e.g., "anthropic_api_key")
            value: Credential value (will be encrypted)
            workspace: Workspace name (default: "default")
        """
        # Load existing credentials
        creds = self._load_credentials()
        
        # Ensure workspace exists
        if workspace not in creds:
            creds[workspace] = {}
        
        # Encrypt and store
        encrypted = self.cipher.encrypt(value.encode()).decode()
        creds[workspace][key] = encrypted
        
        # Save
        self._save_credentials(creds)
    
    def retrieve(self, key: str, workspace: str = "default") -> str:
        """
        Retrieve and decrypt credential.
        
        Args:
            key: Credential name
            workspace: Workspace name
            
        Returns:
            Decrypted credential value
            
        Raises:
            KeyError: If credential not found
        """
        creds = self._load_credentials()
        
        if workspace not in creds:
            raise KeyError(f"Workspace '{workspace}' not found")
        
        if key not in creds[workspace]:
            raise KeyError(f"Credential '{key}' not found in workspace '{workspace}'")
        
        encrypted = creds[workspace][key]
        return self.cipher.decrypt(encrypted.encode()).decode()
    
    def list_credentials(self, workspace: str = "default") -> list:
        """
        List credential keys (not values) in workspace.
        
        Args:
            workspace: Workspace name
            
        Returns:
            List of credential keys
        """
        creds = self._load_credentials()
        
        if workspace not in creds:
            return []
        
        return list(creds[workspace].keys())
    
    def delete(self, key: str, workspace: str = "default") -> None:
        """
        Delete credential.
        
        Args:
            key: Credential name
            workspace: Workspace name
        """
        creds = self._load_credentials()
        
        if workspace in creds and key in creds[workspace]:
            del creds[workspace][key]
            self._save_credentials(creds)
    
    def workspace_exists(self, workspace: str) -> bool:
        """Check if workspace exists"""
        creds = self._load_credentials()
        return workspace in creds
    
    def create_workspace(self, workspace: str) -> None:
        """Create new workspace"""
        creds = self._load_credentials()
        if workspace not in creds:
            creds[workspace] = {}
            self._save_credentials(creds)
    
    def _load_credentials(self) -> Dict:
        """Load credentials from encrypted file"""
        
        if not self.creds_file.exists():
            return {}
        
        try:
            with open(self.creds_file, "rb") as f:
                encrypted_data = f.read()
            
            # Decrypt
            decrypted = self.cipher.decrypt(encrypted_data)
            return json.loads(decrypted.decode())
        
        except Exception as e:
            # If decryption fails, return empty (corrupted vault)
            print(f"Warning: Could not decrypt vault. Creating new vault.")
            return {}
    
    def _save_credentials(self, creds: Dict) -> None:
        """Save credentials to encrypted file"""
        
        # Serialize
        json_data = json.dumps(creds, indent=2)
        
        # Encrypt
        encrypted = self.cipher.encrypt(json_data.encode())
        
        # Save
        with open(self.creds_file, "wb") as f:
            f.write(encrypted)
        
        # Set restrictive permissions
        if os.name != 'nt':  # Unix/Linux/Mac
            os.chmod(self.creds_file, 0o600)
    
    def export_for_env(self, workspace: str = "default") -> str:
        """
        Export credentials as environment variable format.
        
        Args:
            workspace: Workspace name
            
        Returns:
            String in .env format
        """
        creds = self._load_credentials()
        
        if workspace not in creds:
            return ""
        
        lines = []
        for key, encrypted in creds[workspace].items():
            value = self.cipher.decrypt(encrypted.encode()).decode()
            # Convert to uppercase and replace spaces
            env_key = key.upper().replace(" ", "_")
            lines.append(f"{env_key}={value}")
        
        return "\n".join(lines)
