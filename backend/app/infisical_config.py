"""
Infisical Configuration
Centralized secret management using Infisical CLI (no credentials needed)
Secrets are injected via: infisical run -- <command>
"""

import os
from typing import Optional

class SecretManager:
    """
    Simple secret manager that reads from environment variables.
    Secrets are injected via Infisical CLI: infisical run -- <command>
    No SDK or credentials needed!
    """
    
    def __init__(self):
        self.loaded_secrets = []
        self.missing_secrets = []
        
        # Check if running with Infisical CLI
        self.using_infisical = os.getenv("INFISICAL_PROJECT_ID") is not None
    
    def get_secret(
        self, 
        secret_name: str, 
        default: Optional[str] = None,
        environment: str = "dev",
        project_id: Optional[str] = None
    ) -> Optional[str]:
        """
        Get a secret from environment (injected by Infisical CLI)
        
        Args:
            secret_name: Name of the secret (e.g., "SUPABASE_URL")
            default: Default value if secret not found
            environment: Not used (for backwards compatibility)
            project_id: Not used (for backwards compatibility)
        
        Returns:
            Secret value or default
        """
        value = os.getenv(secret_name, default)
        if value:
            if secret_name not in self.loaded_secrets:
                self.loaded_secrets.append(secret_name)
        else:
            if secret_name not in self.missing_secrets:
                self.missing_secrets.append(secret_name)
        return value
    
    def print_status(self):
        """Print a summary of loaded secrets"""
        print("\n" + "="*60)
        if self.using_infisical:
            print("✅ Secrets loaded from Infisical CLI")
        else:
            print("📋 Secrets loaded from environment")
        print("="*60)
        
        if self.loaded_secrets:
            print("\n✅ Loaded secrets:")
            for secret in self.loaded_secrets:
                print(f"   • {secret}")
        
        if self.missing_secrets:
            print("\n⚠️  Missing secrets (optional):")
            for secret in self.missing_secrets:
                print(f"   • {secret}")
        
        print("="*60 + "\n")
    
    def get_all_secrets(
        self, 
        environment: str = "dev",
        project_id: Optional[str] = None
    ) -> dict:
        """
        Get all secrets from environment
        
        Returns:
            Dictionary of all secrets
        """
        return dict(os.environ)


# Global secret manager instance
secret_manager = SecretManager()


def get_secret(secret_name: str, default: Optional[str] = None) -> Optional[str]:
    """
    Convenience function to get a secret
    
    Args:
        secret_name: Name of the secret
        default: Default value if not found
    
    Returns:
        Secret value or default
    """
    return secret_manager.get_secret(secret_name, default)

