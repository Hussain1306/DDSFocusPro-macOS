#!/usr/bin/env python3
"""
DDS Theme Manager - Backend Implementation
Handles theme creation, management, and API endpoints for frontend consumption
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from flask import Flask, request, jsonify, render_template
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ThemeConfig:
    """Data class for theme configuration"""
    theme_name: str
    description: str
    header_color: str = "#ffffff"
    footer_color: str = "#ffffff"
    text_color: str = "#000000"
    background_color: str = "#ffffff"
    button_color: str = "#007bff"
    button_text_color: str = "#ffffff"
    submit_button_bg_color: str = "#006039"
    submit_button_text_color: str = "#ffffff"
    primary_button_bg_color: str = "#007bff"
    primary_button_text_color: str = "#ffffff"
    secondary_button_bg_color: str = "#6c757d"
    secondary_button_text_color: str = "#ffffff"
    drawer_background_color: str = "#f8f9fa"
    drawer_text_color: str = "#212529"
    icon_color: str = "#6c757d"
    top_color: str = "#ffffff"
    heading_font_size: str = "24px"
    body_font_size: str = "16px"
    font_family: str = "Arial, sans-serif"
    border_radius: str = "4px"
    created_at: str = ""
    updated_at: str = ""
    is_active: bool = False
    version: str = "1.0"
    
    @classmethod
    def from_api_data(cls, api_data: Dict[str, Any]) -> 'ThemeConfig':
        """Create ThemeConfig from API data (handles hyphen/underscore conversion)"""
        
        # Handle field name conversion from API format (hyphens) to Python format (underscores)
        field_mapping = {
            'header-color': 'header_color',
            'footer-color': 'footer_color',
            'button-text_color': 'button_text_color'
        }
        
        # Convert API data to Python field names
        converted_data = {}
        for key, value in api_data.items():
            # Convert hyphenated keys to underscored keys
            python_key = field_mapping.get(key, key.replace('-', '_'))
            converted_data[python_key] = value
        
        # Ensure required fields are present
        if 'theme_name' not in converted_data:
            converted_data['theme_name'] = converted_data.get('name', 'Untitled Theme')
        
        if 'description' not in converted_data:
            converted_data['description'] = 'Theme created via API'
        
        return cls(**converted_data)
    
    def to_api_format(self) -> Dict[str, Any]:
        """Convert to API format (underscores to hyphens where needed)"""
        
        # Field mapping from Python format to API format
        reverse_mapping = {
            'header_color': 'header-color',
            'footer_color': 'footer-color',
            'button_text_color': 'button-text_color'
        }
        
        api_data = {}
        for field in self.__dataclass_fields__:
            if field in ['created_at', 'updated_at', 'is_active', 'version']:
                continue  # Skip internal fields
            
            value = getattr(self, field)
            # Convert to API format if needed
            api_key = reverse_mapping.get(field, field)
            api_data[api_key] = value
        
        return api_data

class ThemeManager:
    """Main theme management class"""
    
    def __init__(self, storage_path: str = "themes.json"):
        self.storage_path = storage_path
        self.themes: Dict[str, ThemeConfig] = {}
        self.active_theme: Optional[str] = None
        self.load_themes()
    
    def load_themes(self) -> None:
        """Load themes from storage file"""
        try:
            if os.path.exists(self.storage_path):
                with open(self.storage_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                # Convert dict data back to ThemeConfig objects
                for theme_id, theme_data in data.get('themes', {}).items():
                    self.themes[theme_id] = ThemeConfig(**theme_data)
                
                self.active_theme = data.get('active_theme')
                logger.info(f" Loaded {len(self.themes)} themes from {self.storage_path}")
            else:
                logger.info(" No existing themes file, starting fresh")
                self.create_default_themes()
        except Exception as e:
            logger.error(f" Error loading themes: {e}")
            self.create_default_themes()
    
    def save_themes(self) -> None:
        """Save themes to storage file"""
        try:
            data = {
                'themes': {theme_id: asdict(theme) for theme_id, theme in self.themes.items()},
                'active_theme': self.active_theme,
                'last_updated': datetime.now().isoformat()
            }
            
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f" Saved {len(self.themes)} themes to {self.storage_path}")
        except Exception as e:
            logger.error(f" Error saving themes: {e}")
    
    def create_default_themes(self) -> None:
        """Create default themes"""
        logger.info(" Creating default themes...")
        
        # Default Light Theme
        default_theme = ThemeConfig(
            theme_name="Default Light Theme",
            description="Clean and modern light theme",
            header_color="#ffffff",
            footer_color="#f8f9fa",
            text_color="#212529",
            background_color="#ffffff",
            button_color="#007bff",
            button_text_color="#ffffff",
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            is_active=True
        )
        
        # Postman Test Theme (from user request)
        postman_theme = ThemeConfig(
            theme_name="Postman Test Theme",
            description="A beautiful theme created via Postman",
            header_color="#8E44AD",
            footer_color="#3498DB",
            text_color="#2C3E50",
            background_color="#ECF0F1",
            button_color="transpsrant",
            button_text_color="#2C3E50",
            submit_button_bg_color="#006039",
            submit_button_text_color="#ffffff",
            primary_button_bg_color="#007bff",
            primary_button_text_color="#ffffff",
            secondary_button_bg_color="#6c757d",
            secondary_button_text_color="#ffffff",
            drawer_background_color="#f8f9fa",
            drawer_text_color="#212529",
            icon_color="#6c757d",
            top_color="#ffffff",
            heading_font_size="36px",
            body_font_size="18px",
            font_family="Segoe UI, sans-serif",
            border_radius="10px",
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            is_active=False
        )
        
        # Modern Dark Theme
        dark_theme = ThemeConfig(
            theme_name="Modern Dark Theme",
            description="Sleek dark theme for better focus",
            header_color="#111827",
            footer_color="#1f2937",
            text_color="#f3f4f6",
            background_color="#1f2937",
            button_color="#3b82f6",
            button_text_color="#ffffff",
            submit_button_bg_color="#059669",
            submit_button_text_color="#ffffff",
            primary_button_bg_color="#2563eb",
            primary_button_text_color="#ffffff",
            secondary_button_bg_color="#6b7280",
            secondary_button_text_color="#ffffff",
            drawer_background_color="#374151",
            drawer_text_color="#f3f4f6",
            icon_color="#9ca3af",
            top_color="#111827",
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            is_active=False
        )
        
        self.themes = {
            "default_light": default_theme,
            "postman_test": postman_theme,
            "modern_dark": dark_theme
        }
        self.active_theme = "default_light"
        self.save_themes()
    
    def create_theme(self, theme_data: Dict[str, Any]) -> str:
        """Create a new theme"""
        try:
            # Generate theme ID
            theme_id = theme_data.get('theme_name', 'custom').lower().replace(' ', '_')
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            if theme_id in self.themes:
                theme_id = f"{theme_id}_{timestamp}"
            
            # Create theme config using from_api_data method to handle field conversion
            theme_config = ThemeConfig.from_api_data(theme_data)
            
            # Set metadata
            theme_config.created_at = datetime.now().isoformat()
            theme_config.updated_at = datetime.now().isoformat()
            
            self.themes[theme_id] = theme_config
            self.save_themes()
            
            logger.info(f" Created theme: {theme_id}")
            return theme_id
            
        except Exception as e:
            logger.error(f" Error creating theme: {e}")
            raise
    
    def get_theme(self, theme_id: str) -> Optional[ThemeConfig]:
        """Get a specific theme"""
        return self.themes.get(theme_id)
    
    def get_active_theme(self) -> Optional[ThemeConfig]:
        """Get the currently active theme"""
        if self.active_theme and self.active_theme in self.themes:
            return self.themes[self.active_theme]
        return None
    
    def set_active_theme(self, theme_id: str) -> bool:
        """Set a theme as active"""
        if theme_id in self.themes:
            # Deactivate current theme
            if self.active_theme:
                self.themes[self.active_theme].is_active = False
            
            # Activate new theme
            self.themes[theme_id].is_active = True
            self.active_theme = theme_id
            self.save_themes()
            
            logger.info(f" Activated theme: {theme_id}")
            return True
        return False
    
    def list_themes(self) -> List[Dict[str, Any]]:
        """List all available themes"""
        return [
            {
                'id': theme_id,
                'name': theme.theme_name,
                'description': theme.description,
                'is_active': theme.is_active,
                'created_at': theme.created_at
            }
            for theme_id, theme in self.themes.items()
        ]
    
    def delete_theme(self, theme_id: str) -> bool:
        """Delete a theme"""
        if theme_id in self.themes:
            if self.active_theme == theme_id:
                # Set default theme as active if deleting active theme
                self.set_active_theme("default_light")
            
            del self.themes[theme_id]
            self.save_themes()
            logger.info(f" Deleted theme: {theme_id}")
            return True
        return False
    
    def export_theme_for_api(self, theme_id: Optional[str] = None) -> Dict[str, Any]:
        """Export theme in API format for frontend consumption"""
        theme = self.get_theme(theme_id) if theme_id else self.get_active_theme()
        
        if not theme:
            theme = self.themes.get("default_light") or list(self.themes.values())[0]
        
        # Convert to API format (matching the expected structure)
        api_format = {
            "status": "success",
            "message": "Active styling configuration retrieved successfully",
            "data": {
                "theme_name": theme.theme_name,
                "description": theme.description,
                "header-color": theme.header_color,
                "footer-color": theme.footer_color,
                "text_color": theme.text_color,
                "background_color": theme.background_color,
                "button_color": theme.button_color,
                "button-text_color": theme.button_text_color,
                "submit_button_bg_color": theme.submit_button_bg_color,
                "submit_button_text_color": theme.submit_button_text_color,
                "primary_button_bg_color": theme.primary_button_bg_color,
                "primary_button_text_color": theme.primary_button_text_color,
                "secondary_button_bg_color": theme.secondary_button_bg_color,
                "secondary_button_text_color": theme.secondary_button_text_color,
                "drawer_background_color": theme.drawer_background_color,
                "drawer_text_color": theme.drawer_text_color,
                "icon_color": theme.icon_color,
                "top_color": theme.top_color,
                "heading_font_size": theme.heading_font_size,
                "body_font_size": theme.body_font_size,
                "font_family": theme.font_family,
                "border_radius": theme.border_radius,
                "version": theme.version,
                "is_active": theme.is_active
            }
        }
        
        return api_format

# Global theme manager instance
theme_manager = ThemeManager()

def create_theme_app():
    """Create Flask app with theme management endpoints"""
    app = Flask(__name__)
    
    @app.route('/api/themes', methods=['GET'])
    def get_themes():
        """Get all themes"""
        try:
            themes = theme_manager.list_themes()
            return jsonify({
                'status': 'success',
                'themes': themes,
                'count': len(themes)
            })
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500
    
    @app.route('/api/themes/<theme_id>', methods=['GET'])
    def get_theme(theme_id):
        """Get specific theme"""
        try:
            theme_data = theme_manager.export_theme_for_api(theme_id)
            if theme_data['data']:
                return jsonify(theme_data)
            else:
                return jsonify({
                    'status': 'error',
                    'message': 'Theme not found'
                }), 404
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500
    
    @app.route('/api/themes/active', methods=['GET'])
    def get_active_theme():
        """Get active theme (compatible with existing API)"""
        try:
            return jsonify(theme_manager.export_theme_for_api())
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500
    
    @app.route('/api/themes', methods=['POST'])
    def create_theme():
        """Create new theme"""
        try:
            theme_data = request.get_json()
            if not theme_data:
                return jsonify({
                    'status': 'error',
                    'message': 'No theme data provided'
                }), 400
            
            theme_id = theme_manager.create_theme(theme_data)
            return jsonify({
                'status': 'success',
                'message': 'Theme created successfully',
                'theme_id': theme_id
            }), 201
            
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500
    
    @app.route('/api/themes/<theme_id>/activate', methods=['POST'])
    def activate_theme(theme_id):
        """Activate a theme"""
        try:
            if theme_manager.set_active_theme(theme_id):
                return jsonify({
                    'status': 'success',
                    'message': f'Theme {theme_id} activated successfully'
                })
            else:
                return jsonify({
                    'status': 'error',
                    'message': 'Theme not found'
                }), 404
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500
    
    @app.route('/api/themes/<theme_id>', methods=['DELETE'])
    def delete_theme(theme_id):
        """Delete a theme"""
        try:
            if theme_manager.delete_theme(theme_id):
                return jsonify({
                    'status': 'success',
                    'message': f'Theme {theme_id} deleted successfully'
                })
            else:
                return jsonify({
                    'status': 'error',
                    'message': 'Theme not found'
                }), 404
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500
    
    @app.route('/api/themes/postman-test/apply', methods=['POST'])
    def apply_postman_test_theme():
        """Apply the Postman Test Theme specifically"""
        try:
            success = theme_manager.set_active_theme('postman_test')
            if success:
                return jsonify({
                    'status': 'success',
                    'message': 'Postman Test Theme applied successfully',
                    'theme_data': theme_manager.export_theme_for_api('postman_test')
                })
            else:
                return jsonify({
                    'status': 'error',
                    'message': 'Failed to apply Postman Test Theme'
                }), 500
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500
    
    return app

if __name__ == '__main__':
    # Test the theme manager
    print(" DDS Theme Manager Test")
    print("=" * 50)
    
    # Test creating Postman theme
    postman_theme_data = {
        "theme_name": "Postman Test Theme",
        "description": "A beautiful theme created via Postman",
        "header_color": "#8E44AD",
        "footer_color": "#3498DB",
        "text_color": "#2C3E50",
        "background_color": "#ECF0F1",
        "button_color": "transpsrant",
        "button_text_color": "#2C3E50",
        "submit_button_bg_color": "#006039",
        "submit_button_text_color": "#ffffff",
        "primary_button_bg_color": "#007bff",
        "primary_button_text_color": "#ffffff",
        "secondary_button_bg_color": "#6c757d",
        "secondary_button_text_color": "#ffffff",
        "drawer_background_color": "#f8f9fa",
        "drawer_text_color": "#212529",
        "icon_color": "#6c757d",
        "top_color": "#ffffff",
        "heading_font_size": "36px",
        "body_font_size": "18px",
        "font_family": "Segoe UI, sans-serif",
        "border_radius": "10px"
    }
    
    print(" Created themes:")
    for theme_id, theme in theme_manager.themes.items():
        print(f"   - {theme_id}: {theme.theme_name}")
    
    print(f"\n Active theme: {theme_manager.active_theme}")
    
    # Test API export
    api_data = theme_manager.export_theme_for_api()
    print(f"\n📡 API Export Preview:")
    print(f"   Theme: {api_data['data']['theme_name']}")
    print(f"   Status: {api_data['status']}")
    
    # Run Flask app
    print(f"\n Starting Flask theme server...")
    app = create_theme_app()
    app.run(debug=True, port=5001)
