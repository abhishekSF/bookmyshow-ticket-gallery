"""
Configuration management for the BookMyShow Ticket Gallery project.
Loads settings from environment variables.
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Project settings from environment variables."""
    
    # Gmail API
    gmail_project_id: Optional[str] = None
    gmail_client_id: Optional[str] = None
    gmail_client_secret: Optional[str] = None
    gmail_token_file: str = "./tokens/token.json"
    gmail_enabled: bool = False
    
    # Ollama
    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1:8b"
    ollama_timeout_ms: int = 60000
    ollama_enable: bool = False  # Must be enabled for enrichment to work
    
    # TMDb API
    tmdb_api_key: Optional[str] = None
    tmdb_enable: bool = True  # Enabled for poster fallback
    
    # Salesforce (Headless 360)
    sf_url: str = "https://test-dev-ed.sfdc.us"
    sf_client_id: Optional[str] = None
    sf_client_secret: Optional[str] = None
    sf_client_secret_username: Optional[str] = None
    sf_refresh_token: Optional[str] = None
    sf_api_url: str = f"{sf_url}/services/data/v61.0"
    sf_enabled: bool = False  # Must be enabled for push to work
    sf_tenant_id: Optional[str] = None
    
    # Application
    app_name: str = "bookmyshow-ticket-gallery"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
    
    @property
    def is_ready(self) -> bool:
        """Check if all enabled services are properly configured."""
        ready = True
        
        if self.gmail_enabled and not self.gmail_client_id:
            ready = False
        if self.ollama_enable and self.ollama_url != "http://localhost:11434":
            # Check if Ollama is reachable
            import httpx
            try:
                httpx.get(self.ollama_url, timeout=2.0)
            except:
                ready = False
        if self.tmdb_enable and not self.tmdb_api_key:
            ready = False
        if self.sf_enabled and (not self.sf_client_id or not self.sf_refresh_token):
            ready = False
        
        return ready
    
    def print_status(self):
        """Print configuration status for debugging."""
        print(f"\n{'='*50}")
        print(f"{'Configuration Status':^50}")
        print(f"{'='*50}")
        
        print(f"Gmail API:          {'✓' if self.gmail_enabled else '✗'} (enabled={self.gmail_enabled})")
        print(f"  Client ID:        {self.gmail_client_id[:20]}..." if self.gmail_client_id else "  Client ID:      NOT SET")
        print(f"  Token file:       {self.gmail_token_file}")
        
        print(f"\nOllama:             {'✓' if self.ollama_enable else '✗'} (enabled={self.ollama_enable})")
        print(f"  Model:            {self.ollama_model}")
        print(f"  URL:              {self.ollama_url}")
        
        print(f"\nTMDb API:           {'✓' if self.tmdb_enable else '✗'} (enabled={self.tmdb_enable})")
        print(f"  API Key:          {self.tmdb_api_key[:15]}..." if self.tmdb_api_key else "  API Key:       NOT SET")
        
        print(f"\nSalesforce:         {'✓' if self.sf_enabled else '✗'} (enabled={self.sf_enabled})")
        print(f"  URL:              {self.sf_url}")
        print(f"  Tenant ID:        {self.sf_tenant_id[:15]}..." if self.sf_tenant_id else "  Tenant ID:   NOT SET")
        
        print(f"\n{'✓ READY' if self.is_ready else '✗ NOT READY (use --force to proceed)'}")
        print(f"{'='*50}\n")
    
    @property
    def ollama_available(self) -> bool:
        """Check if Ollama is actually running."""
        try:
            import httpx
            response = httpx.get(f"{self.ollama_url}/api/tags", timeout=2.0)
            return response.status_code == 200
        except:
            return False


settings = Settings()