"""
Authentication Module for PostgreSQL MCP Server
Supports both EntraID (Azure AD) and traditional PostgreSQL authentication
"""

import os
import logging
import asyncio
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from enum import Enum

try:
    from azure.identity.aio import DefaultAzureCredential, ClientSecretCredential
    AZURE_IDENTITY_AVAILABLE = True
except ImportError:
    AZURE_IDENTITY_AVAILABLE = False
    logging.warning("azure-identity not installed. EntraID authentication will not be available.")

logger = logging.getLogger("mcp-postgres-server")


class AuthenticationType(Enum):
    """Supported authentication types"""
    POSTGRESQL = "postgresql"  # Traditional username/password
    ENTRAID = "entraid"  # Azure AD / Microsoft Entra ID


class AuthenticationConfig:
    """Configuration for database authentication"""

    def __init__(self):
        """Initialize authentication configuration from environment variables"""
        # Authentication type
        auth_type_str = os.getenv("AUTH_TYPE", "postgresql").lower()
        self.auth_type = AuthenticationType.ENTRAID if auth_type_str == "entraid" else AuthenticationType.POSTGRESQL

        # PostgreSQL traditional authentication
        self.database_url = os.getenv("DATABASE_URL")

        # EntraID (Azure AD) authentication
        self.azure_tenant_id = os.getenv("AZURE_TENANT_ID")
        self.azure_client_id = os.getenv("AZURE_CLIENT_ID")
        self.azure_client_secret = os.getenv("AZURE_CLIENT_SECRET")

        # Azure PostgreSQL connection details (when using EntraID)
        self.pg_host = os.getenv("PG_HOST")
        self.pg_port = os.getenv("PG_PORT", "5432")
        self.pg_database = os.getenv("PG_DATABASE")
        self.pg_user = os.getenv("PG_USER")  # For EntraID, this is typically the Azure AD user/app name
        self.pg_sslmode = os.getenv("PG_SSLMODE", "require")

        # Token refresh settings
        self.token_refresh_margin = int(os.getenv("TOKEN_REFRESH_MARGIN", "300"))  # Refresh 5 minutes before expiry

        # Validate configuration
        self._validate_config()

    def _validate_config(self):
        """Validate that required configuration is present"""
        if self.auth_type == AuthenticationType.POSTGRESQL:
            if not self.database_url:
                raise ValueError("DATABASE_URL environment variable is required for PostgreSQL authentication")

        elif self.auth_type == AuthenticationType.ENTRAID:
            if not AZURE_IDENTITY_AVAILABLE:
                raise ValueError("azure-identity package is required for EntraID authentication. Install with: pip install azure-identity")

            missing_vars = []
            if not self.pg_host:
                missing_vars.append("PG_HOST")
            if not self.pg_database:
                missing_vars.append("PG_DATABASE")
            if not self.pg_user:
                missing_vars.append("PG_USER")

            # For service principal authentication
            if self.azure_client_id and not self.azure_client_secret:
                missing_vars.append("AZURE_CLIENT_SECRET")

            if missing_vars:
                raise ValueError(f"Missing required environment variables for EntraID authentication: {', '.join(missing_vars)}")

    def is_entraid(self) -> bool:
        """Check if EntraID authentication is enabled"""
        return self.auth_type == AuthenticationType.ENTRAID

    def is_postgresql(self) -> bool:
        """Check if traditional PostgreSQL authentication is enabled"""
        return self.auth_type == AuthenticationType.POSTGRESQL


class EntraIDTokenManager:
    """Manages EntraID access tokens for PostgreSQL authentication"""

    # Azure Database PostgreSQL resource scope
    POSTGRES_SCOPE = "https://ossrdbms-aad.database.windows.net/.default"

    def __init__(self, config: AuthenticationConfig):
        """Initialize EntraID token manager"""
        if not AZURE_IDENTITY_AVAILABLE:
            raise ImportError("azure-identity package is required for EntraID authentication")

        self.config = config
        self.credential = None
        self.current_token = None
        self.token_expires_at = None
        self._lock = asyncio.Lock()

        self._initialize_credential()

    def _initialize_credential(self):
        """Initialize Azure credential based on configuration"""
        if self.config.azure_client_id and self.config.azure_client_secret:
            # Service Principal (Client Credentials) authentication
            logger.info("Initializing EntraID authentication with Service Principal")
            self.credential = ClientSecretCredential(
                tenant_id=self.config.azure_tenant_id,
                client_id=self.config.azure_client_id,
                client_secret=self.config.azure_client_secret
            )
        else:
            # Default Azure credential (supports Managed Identity, Azure CLI, etc.)
            logger.info("Initializing EntraID authentication with DefaultAzureCredential")
            self.credential = DefaultAzureCredential()

    async def get_access_token(self) -> str:
        """Get a valid access token, refreshing if necessary"""
        async with self._lock:
            # Check if we need to refresh the token
            if self._needs_token_refresh():
                await self._refresh_token()

            return self.current_token

    def _needs_token_refresh(self) -> bool:
        """Check if the token needs to be refreshed"""
        if not self.current_token or not self.token_expires_at:
            return True

        # Refresh if token will expire within the margin
        time_until_expiry = (self.token_expires_at - datetime.now()).total_seconds()
        return time_until_expiry <= self.config.token_refresh_margin

    async def _refresh_token(self):
        """Refresh the access token"""
        try:
            logger.info("Refreshing EntraID access token for PostgreSQL")
            token = await self.credential.get_token(self.POSTGRES_SCOPE)

            self.current_token = token.token
            # Token expiry is in Unix timestamp
            self.token_expires_at = datetime.fromtimestamp(token.expires_on)

            logger.info(f"EntraID token refreshed. Expires at: {self.token_expires_at}")
        except Exception as e:
            logger.error(f"Failed to refresh EntraID token: {e}")
            raise

    async def close(self):
        """Close the credential and cleanup resources"""
        if self.credential:
            await self.credential.close()


class DatabaseAuthenticator:
    """Handles database authentication for both PostgreSQL and EntraID"""

    def __init__(self, config: Optional[AuthenticationConfig] = None):
        """Initialize database authenticator"""
        self.config = config or AuthenticationConfig()
        self.token_manager: Optional[EntraIDTokenManager] = None

        if self.config.is_entraid():
            self.token_manager = EntraIDTokenManager(self.config)
            logger.info("EntraID authentication configured")
        else:
            logger.info("PostgreSQL traditional authentication configured")

    async def get_connection_params(self, database_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get connection parameters for asyncpg based on authentication type

        Args:
            database_name: Optional database name to override default

        Returns:
            Dictionary of connection parameters for asyncpg.connect() or asyncpg.create_pool()
        """
        if self.config.is_entraid():
            return await self._get_entraid_connection_params(database_name)
        else:
            return self._get_postgresql_connection_params(database_name)

    def _get_postgresql_connection_params(self, database_name: Optional[str] = None) -> Dict[str, Any]:
        """Get connection parameters for traditional PostgreSQL authentication"""
        if database_name:
            # Parse DATABASE_URL and replace the database name
            dsn_parts = self.config.database_url.rsplit('/', 1)
            if len(dsn_parts) == 2:
                dsn = f"{dsn_parts[0]}/{database_name}"
            else:
                dsn = f"{self.config.database_url}/{database_name}"
        else:
            dsn = self.config.database_url

        return {"dsn": dsn}

    async def _get_entraid_connection_params(self, database_name: Optional[str] = None) -> Dict[str, Any]:
        """Get connection parameters for EntraID authentication"""
        # Get access token
        access_token = await self.token_manager.get_access_token()

        # Build connection parameters
        db = database_name or self.config.pg_database

        params = {
            "host": self.config.pg_host,
            "port": int(self.config.pg_port),
            "database": db,
            "user": self.config.pg_user,
            "password": access_token,  # Use access token as password
            "ssl": self.config.pg_sslmode,
        }

        logger.debug(f"Connecting to PostgreSQL with EntraID: {self.config.pg_user}@{self.config.pg_host}:{self.config.pg_port}/{db}")

        return params

    async def create_connection_pool(self, min_size: int = 2, max_size: int = 10,
                                    command_timeout: float = 60) -> 'asyncpg.Pool':
        """
        Create a connection pool with appropriate authentication

        Args:
            min_size: Minimum number of connections in the pool
            max_size: Maximum number of connections in the pool
            command_timeout: Command timeout in seconds

        Returns:
            asyncpg connection pool
        """
        import asyncpg

        conn_params = await self.get_connection_params()

        # For EntraID, we need to handle token refresh differently for connection pools
        # We'll use a shorter max_inactive_connection_lifetime to force reconnection
        if self.config.is_entraid():
            # Force reconnection every 30 minutes to refresh token
            pool = await asyncpg.create_pool(
                **conn_params,
                min_size=min_size,
                max_size=max_size,
                command_timeout=command_timeout,
                max_inactive_connection_lifetime=1800.0  # 30 minutes
            )
            logger.info("Created connection pool with EntraID authentication (30-minute connection lifetime)")
        else:
            pool = await asyncpg.create_pool(
                **conn_params,
                min_size=min_size,
                max_size=max_size,
                command_timeout=command_timeout
            )
            logger.info("Created connection pool with PostgreSQL authentication")

        return pool

    async def create_connection(self, database_name: Optional[str] = None) -> 'asyncpg.Connection':
        """
        Create a single database connection

        Args:
            database_name: Optional database name to connect to

        Returns:
            asyncpg connection
        """
        import asyncpg

        conn_params = await self.get_connection_params(database_name)
        conn = await asyncpg.connect(**conn_params)

        logger.debug(f"Created database connection using {self.config.auth_type.value} authentication")

        return conn

    async def close(self):
        """Close authenticator and cleanup resources"""
        if self.token_manager:
            await self.token_manager.close()

    def get_auth_info(self) -> Dict[str, Any]:
        """Get information about the current authentication configuration"""
        info = {
            "auth_type": self.config.auth_type.value,
            "azure_identity_available": AZURE_IDENTITY_AVAILABLE
        }

        if self.config.is_entraid():
            info.update({
                "pg_host": self.config.pg_host,
                "pg_port": self.config.pg_port,
                "pg_database": self.config.pg_database,
                "pg_user": self.config.pg_user,
                "pg_sslmode": self.config.pg_sslmode,
                "using_service_principal": bool(self.config.azure_client_id),
                "token_refresh_margin": self.config.token_refresh_margin
            })
        else:
            info.update({
                "database_url_configured": bool(self.config.database_url)
            })

        return info
