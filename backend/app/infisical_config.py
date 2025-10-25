"""
Infisical Configuration
Centralized secret management using Infisical with OAuth and fallback to .env
"""

import os
from typing import Optional
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env first (for Infisical credentials)
# Check both backend/.env and backend/app/.env
backend_dir = Path(__file__).parent.parent
env_file = backend_dir / ".env"
if env_file.exists():
    load_dotenv(env_file)
else:
    load_dotenv()  # Load from current directory

# Try to import Infisical SDK
try:
    from infisical_client import InfisicalClient, ClientSettings, AuthenticationOptions, UniversalAuthMethod
    INFISICAL_AVAILABLE = True
    print("✅ Infisical SDK imported successfully")
except ImportError:
    try:
        # Try alternative import
        from infisical_python import InfisicalClient
        INFISICAL_AVAILABLE = True
        print("✅ Infisical SDK (alternative) imported successfully")
    except ImportError:
        INFISICAL_AVAILABLE = False
        InfisicalClient = None
        print("⚠️  infisical-python not installed - using .env fallback")

class SecretManager:
    """
    Unified secret manager that uses Infisical if available,
    falls back to .env file otherwise
    """
    
    def __init__(self):
        self.client: Optional[InfisicalClient] = None
        self.use_infisical = False
        self.project_id = None
        
        if INFISICAL_AVAILABLE:
            # Try OAuth method first (preferred for production)
            client_id = os.getenv("INFISICAL_CLIENT_ID")
            client_secret = os.getenv("INFISICAL_CLIENT_SECRET")
            project_id = os.getenv("INFISICAL_PROJECT_ID")
            
            # Try token method as fallback
            infisical_token = os.getenv("INFISICAL_TOKEN")
            
            if client_id and client_secret and project_id:
                try:
                    self.client = InfisicalClient(
                        ClientSettings(
                            auth=AuthenticationOptions(
                                universal_auth=UniversalAuthMethod(
                                    client_id=client_id,
                                    client_secret=client_secret
                                )
                            )
                        )
                    )
                    self.project_id = project_id
                    self.use_infisical = True
                    print("✅ Infisical client initialized with OAuth")
                except Exception as e:
                    print(f"⚠️  Failed to initialize Infisical with OAuth: {e}")
                    print("⚠️  Falling back to .env file")
            elif infisical_token:
                try:
                    # Fallback to token-based authentication
                    self.client = InfisicalClient(token=infisical_token)
                    self.use_infisical = True
                    print("✅ Infisical client initialized with token")
                except Exception as e:
                    print(f"⚠️  Failed to initialize Infisical with token: {e}")
                    print("⚠️  Falling back to .env file")
            else:
                print("⚠️  INFISICAL credentials not found in environment")
                print("⚠️  Need either:")
                print("     - INFISICAL_CLIENT_ID, INFISICAL_CLIENT_SECRET, INFISICAL_PROJECT_ID (OAuth)")
                print("     - INFISICAL_TOKEN (Service Token)")
                print("⚠️  Using .env file for secrets")
        else:
            print("⚠️  Using .env file for secrets")
    
    def get_secret(
        self, 
        secret_name: str, 
        default: Optional[str] = None,
        environment: str = "dev",
        project_id: Optional[str] = None
    ) -> Optional[str]:
        """
        Get a secret from Infisical or .env file
        
        Args:
            secret_name: Name of the secret (e.g., "SUPABASE_URL")
            default: Default value if secret not found
            environment: Infisical environment (dev, staging, prod)
            project_id: Infisical project ID (optional, uses self.project_id if not provided)
        
        Returns:
            Secret value or default
        """
        if self.use_infisical and self.client:
            try:
                # Use instance project_id if not provided
                pid = project_id or self.project_id
                
                # Get secret from Infisical
                secret = self.client.getSecret(
                    options={
                        "environment": environment,
                        "projectId": pid,
                        "secretName": secret_name,
                    }
                )
                value = secret.secretValue
                print(f"✅ Retrieved {secret_name} from Infisical")
                return value
            except Exception as e:
                print(f"⚠️  Failed to get {secret_name} from Infisical: {e}")
                # Fall back to environment variable
                env_value = os.getenv(secret_name, default)
                if env_value:
                    print(f"✅ Using {secret_name} from .env fallback")
                return env_value
        else:
            # Use standard environment variable
            env_value = os.getenv(secret_name, default)
            if env_value:
                print(f"✅ Using {secret_name} from .env file")
            return env_value
    
    def get_all_secrets(
        self, 
        environment: str = "dev",
        project_id: Optional[str] = None
    ) -> dict:
        """
        Get all secrets from Infisical or environment
        
        Args:
            environment: Infisical environment (dev, staging, prod)
            project_id: Infisical project ID (optional, uses self.project_id if not provided)
        
        Returns:
            Dictionary of all secrets
        """
        if self.use_infisical and self.client:
            try:
                # Use instance project_id if not provided
                pid = project_id or self.project_id
                
                secrets = self.client.listSecrets(
                    options={
                        "environment": environment,
                        "projectId": pid,
                    }
                )
                result = {secret.secretKey: secret.secretValue for secret in secrets}
                print(f"✅ Retrieved {len(result)} secrets from Infisical")
                return result
            except Exception as e:
                print(f"⚠️  Failed to get all secrets from Infisical: {e}")
                return dict(os.environ)
        else:
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

