# -*- coding: utf-8 -*-
"""
Configuration Manager for DDS FocusPro
Fetches configuration from API with fallback to default values
"""

import requests
import json
import os
from typing import Dict, Any, Optional
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class ConfigManager:
    def __init__(self):
        # External API disabled to prevent hanging
        self.config_api_url = None  # Removed: 'https://dxdtime.ddsolutions.io/api/styling/global/'
        self.api_timeout = 10  # seconds
        self.config_cache = None
        self.logger = logging.getLogger(__name__)
        
        # Default configuration values
        self.default_config = {
            "ui": {
                "primary_color": "#006039",
                "secondary_color": "#004d2e", 
                "background_color": "#ffffff",
                "text_color": "#333333",
                "font_size": {
                    "small": "12px",
                    "medium": "14px", 
                    "large": "16px",
                    "extra_large": "18px"
                },
                "font_family": "Inter, sans-serif"
            },
            "credentials": {
                "s3": {
                    "access_key": os.getenv('S3_ACCESS_KEY', ''),
                    "secret_key": os.getenv('S3_SECRET_KEY', ''),
                    "bucket_name": os.getenv('S3_BUCKET_NAME', 'ddsfocustime'),
                    "region": os.getenv('S3_REGION', 'us-east-1')
                },
                "openai": {
                    "api_key": os.getenv('OPENAI_API_KEY', ''),
                    "model": "gpt-3.5-turbo",
                    "max_tokens": 150
                },
                "database": {
                    "host": os.getenv('DB_HOST', '92.113.22.65'),
                    "user": os.getenv('DB_USER', 'root'),
                    "password": os.getenv('DB_PASSWORD', ''),
                    "database": os.getenv('DB_NAME', 'ddsfocus_db'),
                    "port": int(os.getenv('DB_PORT', 3306))
                },
                "auth_token": os.getenv('AUTH_TOKEN', '')
            },
            "screenshot": {
                "interval_seconds": int(os.getenv('SCREENSHOT_INTERVAL', 60)),
                "quality": 85,
                "format": "JPEG",
                "auto_upload": True,
                "folder_structure": "users_screenshots/{date}/{email}/{task}/"
            },
            "features": {
                "ai_analysis": True,
                "auto_categorization": True,
                "idle_detection": True,
                "program_tracking": True,
                "email_notifications": False
            }
        }
    
    def fetch_config_from_api(self) -> Optional[Dict[str, Any]]:
        """
        Fetch configuration from DDS styling API endpoint
        Returns None if API call fails
        """
        try:
            self.logger.info(f"Fetching styling configuration from DDS API: {self.config_api_url}")
            
            headers = {
                'Content-Type': 'application/json',
                'User-Agent': 'DDS-FocusPro/1.3'
            }
            
            response = requests.get(
                self.config_api_url, 
                headers=headers,
                timeout=self.api_timeout
            )
            
            if response.status_code == 200:
                api_response = response.json()
                self.logger.info("[SUCCESS] Successfully fetched styling configuration from DDS API")
                
                # Check if response has the expected structure
                if api_response.get('status') == 'success' and 'data' in api_response:
                    styling_data = api_response['data']
                    
                    # Transform DDS API response to our config format
                    transformed_config = {
                        "ui": {
                            "primary_color": styling_data.get('primary_color', self.default_config['ui']['primary_color']),
                            "secondary_color": styling_data.get('secondary_color', self.default_config['ui']['secondary_color']),
                            "background_color": styling_data.get('background_color', self.default_config['ui']['background_color']),
                            "text_color": styling_data.get('text_color', self.default_config['ui']['text_color']),
                            "font_family": styling_data.get('font_family', self.default_config['ui']['font_family']),
                            "font_size": {
                                "heading": styling_data.get('heading_font_size', '18px'),
                                "body": styling_data.get('body_font_size', '14px'),
                                "small": "12px",
                                "medium": "14px",
                                "large": "16px",
                                "extra_large": "18px"
                            },
                            "border_radius": styling_data.get('border_radius', '8px')
                        },
                        "theme_info": {
                            "theme_name": styling_data.get('theme_name', 'Default Theme'),
                            "description": styling_data.get('description', ''),
                            "version": styling_data.get('version', '1.0'),
                            "is_active": styling_data.get('is_active', True)
                        }
                    }
                    
                    self.logger.info(f"[THEME] Loaded theme: {styling_data.get('theme_name', 'Unknown')}")
                    self.logger.info(f"[THEME] Primary color: {styling_data.get('primary_color')}")
                    self.logger.info(f"[THEME] Secondary color: {styling_data.get('secondary_color')}")
                    
                    return transformed_config
                else:
                    self.logger.warning(f"[WARNING] Unexpected API response format")
                    return None
            else:
                self.logger.warning(f"[WARNING] DDS API returned status code: {response.status_code}")
                return None
                
        except requests.exceptions.Timeout:
            self.logger.error("[ERROR] DDS API request timed out")
            return None
        except requests.exceptions.ConnectionError:
            self.logger.error("[ERROR] Failed to connect to DDS styling API")
            return None
        except Exception as e:
            self.logger.error(f"[ERROR] Error fetching styling configuration: {str(e)}")
            return None
    
    def merge_configs(self, api_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge API configuration with default values
        API values override defaults, but defaults fill in missing values
        """
        merged_config = self.default_config.copy()
        
        def deep_merge(default_dict, api_dict):
            """Recursively merge dictionaries"""
            for key, value in api_dict.items():
                if key in default_dict and isinstance(default_dict[key], dict) and isinstance(value, dict):
                    deep_merge(default_dict[key], value)
                else:
                    default_dict[key] = value
        
        deep_merge(merged_config, api_config)
        return merged_config
    
    def get_config(self, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Get complete configuration with API-first, fallback-to-default strategy
        
        Args:
            force_refresh: If True, bypass cache and fetch fresh config
            
        Returns:
            Complete configuration dictionary
        """
        if self.config_cache and not force_refresh:
            return self.config_cache
        
        self.logger.info("[DEBUG] Loading configuration...")
        
        # Try to fetch from API first
        api_config = self.fetch_config_from_api()
        
        if api_config:
            # Merge API config with defaults
            final_config = self.merge_configs(api_config)
            self.logger.info("[SUCCESS] Using API configuration with default fallbacks")
        else:
            # Use default configuration
            final_config = self.default_config
            self.logger.info("[WARNING] Using default configuration (API unavailable)")
        
        # Cache the configuration
        self.config_cache = final_config
        return final_config
    
    def get_ui_config(self) -> Dict[str, Any]:
        """Get UI-specific configuration"""
        config = self.get_config()
        return config.get('ui', {})
    
    def get_credentials(self) -> Dict[str, Any]:
        """Get credentials configuration"""
        config = self.get_config()
        return config.get('credentials', {})
    
    def get_screenshot_config(self) -> Dict[str, Any]:
        """Get screenshot configuration"""
        config = self.get_config()
        return config.get('screenshot', {})
    
    def get_s3_credentials(self) -> Dict[str, str]:
        """Get S3 credentials specifically"""
        credentials = self.get_credentials()
        return credentials.get('s3', {})
    
    def get_database_credentials(self) -> Dict[str, Any]:
        """Get database credentials specifically"""
        credentials = self.get_credentials()
        return credentials.get('database', {})
    
    def get_openai_config(self) -> Dict[str, str]:
        """Get OpenAI configuration"""
        credentials = self.get_credentials()
        return credentials.get('openai', {})
    
    def get_screenshot_interval(self) -> int:
        """Get screenshot capture interval in seconds"""
        screenshot_config = self.get_screenshot_config()
        return screenshot_config.get('interval_seconds', 60)
    
    def update_config_cache(self, new_config: Dict[str, Any]):
        """Update the cached configuration"""
        self.config_cache = new_config
        self.logger.info("[SUCCESS] Configuration cache updated")
    
    def get_config_for_frontend(self) -> Dict[str, Any]:
        """
        Get safe configuration for frontend (without sensitive credentials)
        """
        config = self.get_config()
        
        # Create a safe copy without sensitive data
        safe_config = {
            "ui": config.get('ui', {}),
            "screenshot": {
                "interval_seconds": config.get('screenshot', {}).get('interval_seconds', 60),
                "quality": config.get('screenshot', {}).get('quality', 85),
                "format": config.get('screenshot', {}).get('format', 'JPEG')
            },
            "features": config.get('features', {})
        }
        
        return safe_config

# Global configuration manager instance
config_manager = ConfigManager()
