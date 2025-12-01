import json
import yaml
import requests
from typing import Dict, Any, Optional
from functools import lru_cache
from requests.auth import HTTPBasicAuth


class ConsulConfigLoader:
    def __init__(self, consul_addr: str, user: Optional[str] = None, password: Optional[str] = None):
        """
        Initialize Consul config loader
        
        Args:
            consul_addr: Consul server address (e.g., "https://consul.cegove.cloud")
            user: Basic auth username
            password: Basic auth password
        """
        self.consul_addr = consul_addr.rstrip('/')
        self.auth = HTTPBasicAuth(user, password) if user and password else None
    
    def load_config(self, key: str) -> Dict[str, Any]:
        """
        Load config from Consul KV store
        
        Args:
            key: Consul KV key path (e.g., "service/movie-service.json")
            
        Returns:
            Dictionary containing configuration
        """
        # Construct Consul KV API URL
        url = f"{self.consul_addr}/v1/kv/{key}"
        
        # Make request with basic auth
        response = requests.get(url, auth=self.auth, verify=True)
        
        if response.status_code == 401:
            raise ValueError("Authentication failed. Check CONSUL_USER and CONSUL_PASSWORD")
        elif response.status_code == 404:
            raise ValueError(f"Key {key} not found in Consul")
        elif response.status_code != 200:
            raise ValueError(f"Failed to load config from Consul: {response.status_code} - {response.text}")
        
        # Parse response
        data = response.json()
        if not data or len(data) == 0:
            raise ValueError(f"Key {key} not found in Consul")
        
        # Decode base64 value
        import base64
        value = base64.b64decode(data[0]['Value']).decode('utf-8')
        
        # Determine format by extension
        if key.endswith('.json'):
            return json.loads(value)
        elif key.endswith(('.yaml', '.yml')):
            return yaml.safe_load(value)
        elif key.endswith('.env'):
            return self._parse_env(value)
        else:
            # Try JSON first, then YAML
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                try:
                    return yaml.safe_load(value)
                except:
                    # Return as single key-value
                    return {key: value}
    
    def _parse_env(self, content: str) -> Dict[str, str]:
        """Parse .env file content"""
        config = {}
        for line in content.split('\n'):
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                config[key.strip()] = value.strip()
        return config
    
    def load_configs(self, *keys: str) -> Dict[str, Any]:
        """
        Load multiple configs from Consul
        
        Args:
            *keys: Multiple Consul KV key paths
            
        Returns:
            Merged dictionary containing all configurations
        """
        merged_config = {}
        for key in keys:
            config = self.load_config(key)
            merged_config.update(config)
        return merged_config


@lru_cache()
def get_consul_loader(consul_addr: str, user: str = None, password: str = None) -> ConsulConfigLoader:
    """Get cached Consul loader instance"""
    return ConsulConfigLoader(consul_addr, user, password)