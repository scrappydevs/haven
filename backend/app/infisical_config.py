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
        # Check if running with Infisical CLI
        if os.getenv("INFISICAL_PROJECT_ID"):
            print("✅ Running with Infisical CLI")
        else:
            print("⚠️  Not using Infisical CLI - reading from environment")
    
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
            print(f"✅ Loaded {secret_name}")
        else:
            print(f"⚠️  {secret_name} not found")
        return value
    
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

