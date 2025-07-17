"""
Centralized API client manager module.
All external API integrations should be handled through this module.
"""
import logging
from typing import Dict, Any, Optional, Union

from app.core.delta_exchange import DeltaExchangeClient, DeltaExchangeConfig

logger = logging.getLogger(__name__)

class ApiManager:
    """
    Manages all API connections and client instances.
    This is a singleton class that provides access to various API clients.
    """
    _instance = None
    _clients: Dict[str, Any] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ApiManager, cls).__new__(cls)
            cls._instance._clients = {}
        return cls._instance

    def register_client(self, name: str, client: Any) -> None:
        """
        Register a new API client
        
        Args:
            name: A unique identifier for the client
            client: The client instance
        """
        self._clients[name] = client
        logger.info(f"Registered client: {name}")

    def get_client(self, name: str) -> Optional[Any]:
        """
        Get a registered client by name
        
        Args:
            name: The client identifier
            
        Returns:
            The client instance or None if not found
        """
        client = self._clients.get(name)
        if client is None:
            logger.warning(f"Client not found: {name}")
        return client

    def remove_client(self, name: str) -> None:
        """
        Remove a registered client
        
        Args:
            name: The client identifier
        """
        if name in self._clients:
            del self._clients[name]
            logger.info(f"Removed client: {name}")
        else:
            logger.warning(f"Cannot remove client (not found): {name}")

    def clear_clients(self) -> None:
        """Remove all registered clients"""
        self._clients.clear()
        logger.info("Cleared all API clients")

    # Delta Exchange specific methods
    def register_delta_client(self, api_key: str, api_secret: str, user_id: str = None) -> str:
        """
        Register a Delta Exchange client
        
        Args:
            api_key: Delta Exchange API key
            api_secret: Delta Exchange API secret
            user_id: Optional user ID to associate with this client
            
        Returns:
            The client name/ID
        """
        client_name = f"delta_exchange_{user_id}" if user_id else "delta_exchange"
        config = DeltaExchangeConfig(
            api_key=api_key,
            api_secret=api_secret
        )
        client = DeltaExchangeClient(config)
        self.register_client(client_name, client)
        return client_name

    def get_delta_client(self, user_id: str = None) -> Optional[DeltaExchangeClient]:
        """
        Get a Delta Exchange client
        
        Args:
            user_id: Optional user ID to get a specific client
            
        Returns:
            The Delta Exchange client instance
        """
        client_name = f"delta_exchange_{user_id}" if user_id else "delta_exchange"
        return self.get_client(client_name)

# Create a singleton instance
api_manager = ApiManager()
