/**
 * Configuration Manager for Frontend
 * Fetches configuration from API and applies it to the UI
 */

class ConfigManager {
    constructor() {
        this.config = null;
        this.defaultConfig = {
            ui: {
                // API-only color system - no defaults
                font_size: {
                    small: "12px",
                    medium: "14px",
                    large: "16px",
                    extra_large: "18px"
                },
                font_family: "Segoe UI, sans-serif"
            },
            screenshot: {
                interval_seconds: 60,
                quality: 85,
                format: "JPEG"
            },
            features: {
                ai_analysis: true,
                auto_categorization: true,
                idle_detection: true,
                program_tracking: true,
                email_notifications: false
            }
        };
    }

    /**
     * Fetch styling configuration directly from DDS API
     * @returns {Promise<Object>} Configuration object
     */
    async fetchDDSApiConfiguration() {
        try {
            console.log('🎨 Fetching styling from DDS API...');
            
            const response = await fetch(this.ddsApiUrl, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'User-Agent': 'DDS-FocusPro/1.3'
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const apiResponse = await response.json();
            
            console.log('🔍 DDS API Response:', apiResponse); // Debug logging
            
            if (apiResponse.status === 'success' && apiResponse.data) {
                const stylingData = apiResponse.data;
                
                    // Transform DDS API response to our config format, focusing on all colors including header, footer, button-text
                    const transformedConfig = {
                        ui: {
                            primary_color: stylingData.primary_color || this.defaultConfig.ui.primary_color,
                            secondary_color: stylingData.secondary_color || this.defaultConfig.ui.secondary_color,
                            background_color: stylingData.background_color || this.defaultConfig.ui.background_color,
                            button_color: stylingData.button_color || this.defaultConfig.ui.button_color,
                            text_color: stylingData.text_color || this.defaultConfig.ui.text_color,
                            // 🎨 NEW: Additional specific color fields
                            header_color: stylingData['header-color'] || stylingData.header_color,
                            footer_color: stylingData['footer-color'] || stylingData.footer_color,
                            button_text_color: stylingData['button-text_color'] || stylingData.button_text_color,
                            font_family: stylingData.font_family || this.defaultConfig.ui.font_family,
                            font_size: {
                                heading: stylingData.heading_font_size || '18px',
                                body: stylingData.body_font_size || '14px',
                                small: "12px",
                                medium: "14px",
                                large: "16px",
                                extra_large: "18px"
                            },
                            border_radius: stylingData.border_radius || '8px'
                        },
                        theme_info: {
                            theme_name: stylingData.theme_name || 'Default Theme',
                            description: stylingData.description || '',
                            version: stylingData.version || '1.0',
                            is_active: stylingData.is_active || true
                        },
                        screenshot: this.defaultConfig.screenshot,
                        features: this.defaultConfig.features
                    };
                    
                    console.log('✅ DDS styling loaded successfully');
                    console.log(`🎨 Theme: ${stylingData.theme_name}`);
                    console.log(`🎨 Primary Color: ${stylingData.primary_color}`);
                    console.log(`🎨 Secondary Color: ${stylingData.secondary_color}`);
                    console.log(`🎨 Background Color: ${stylingData.background_color}`);
                    console.log(`🎨 Button Color: ${stylingData.button_color}`);
                    console.log(`🎨 Text Color: ${stylingData.text_color}`);
                    console.log(`🎨 Header Color: ${stylingData['header-color'] || stylingData.header_color}`);
                    console.log(`🎨 Footer Color: ${stylingData['footer-color'] || stylingData.footer_color}`);
                    console.log(`🎨 Button Text Color: ${stylingData['button-text_color'] || stylingData.button_text_color}`);
                    
                return transformedConfig;
            } else {
                console.error('❌ Invalid DDS API response structure:', apiResponse);
                throw new Error(`Invalid DDS API response format. Expected: {status: 'success', data: {...}}, Got: ${JSON.stringify(apiResponse)}`);
            }
        } catch (error) {
            console.warn('⚠️ Failed to fetch from DDS API:', error.message);
            console.error('🔍 Full error details:', error);
            return null;
        }
    }

    /**
     * Fetch configuration from APIs with fallback strategy
     * 1. Try DDS styling API first (for primary/secondary colors)
     * 2. Try local backend API 
     * 3. Fall back to defaults
     * @returns {Promise<Object>} Configuration object
     */
    async fetchConfiguration() {
        try {
            console.log('🔄 Loading configuration...');
            
            // First, try to get styling from DDS API
            let config = await this.fetchDDSApiConfiguration();
            
            if (config) {
                // Got DDS styling, now try to merge with local backend config
                try {
                    const backendResponse = await fetch('/api/config', {
                        method: 'GET',
                        headers: {
                            'Content-Type': 'application/json'
                        }
                    });

                    if (backendResponse.ok) {
                        const backendData = await backendResponse.json();
                        if (backendData.success && backendData.config) {
                            // Merge DDS styling with backend config, DDS styling takes priority for UI
                            config.screenshot = backendData.config.screenshot || config.screenshot;
                            config.features = backendData.config.features || config.features;
                            console.log('✅ Merged DDS styling with backend config');
                        }
                    }
                } catch (backendError) {
                    console.warn('⚠️ Backend config unavailable, using DDS styling only:', backendError.message);
                }
                
                this.config = config;
                return this.config;
            }
            
            // If DDS API failed, try backend only
            console.log('🔄 DDS API unavailable, trying backend...');
            const response = await fetch('/api/config', {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            
            if (data.success) {
                this.config = data.config;
                console.log('✅ Configuration loaded from backend:', data.source);
                console.log('📋 Config:', this.config);
                return this.config;
            } else {
                throw new Error(data.error || 'Failed to fetch configuration');
            }
        } catch (error) {
            console.warn('⚠️ All APIs failed, using default configuration:', error.message);
            this.config = this.defaultConfig;
            return this.config;
        }
    }

    /**
     * Refresh configuration from API
     * @returns {Promise<Object>} Updated configuration
     */
    async refreshConfiguration() {
        try {
            console.log('🔄 Refreshing configuration...');
            
            const response = await fetch('/api/config/refresh', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            const data = await response.json();
            
            if (data.success) {
                this.config = data.config;
                console.log('✅ Configuration refreshed successfully');
                this.applyConfiguration();
                return this.config;
            } else {
                throw new Error(data.error || 'Failed to refresh configuration');
            }
        } catch (error) {
            console.error('❌ Failed to refresh configuration:', error.message);
            throw error;
        }
    }

    /**
     * Get screenshot interval from API
     * @returns {Promise<number>} Interval in seconds
     */
    async getScreenshotInterval() {
        try {
            const response = await fetch('/api/config/screenshot-interval');
            const data = await response.json();
            
            if (data.success) {
                return data.interval_seconds;
            } else {
                return this.defaultConfig.screenshot.interval_seconds;
            }
        } catch (error) {
            console.warn('⚠️ Failed to get screenshot interval:', error.message);
            return this.defaultConfig.screenshot.interval_seconds;
        }
    }

    /**
     * Apply configuration to the UI
     */
    applyConfiguration() {
        if (!this.config) {
            console.warn('⚠️ No configuration to apply');
            return;
        }

        console.log('🎨 Applying configuration to UI...');

        // Apply CSS variables
        this.applyCSSVariables();
        
        // Apply font settings
        this.applyFontSettings();
        
        // Update UI elements
        this.updateUIElements();
        
        console.log('✅ Configuration applied successfully');
    }

    /**
     * Apply CSS custom properties from configuration
     * Apply all colors from DDS API: primary, secondary, background, button, text
     */
    applyCSSVariables() {
        const root = document.documentElement;
        const ui = this.config.ui || {};

        console.log('🎨 Applying CSS variables from DDS API...');

        // Apply primary color and its variations
        if (ui.primary_color) {
            root.style.setProperty('--primary-color', ui.primary_color);
            root.style.setProperty('--primary-hover', this.darkenColor(ui.primary_color, 10));
            root.style.setProperty('--primary-active', this.darkenColor(ui.primary_color, 20));
            root.style.setProperty('--primary-light', this.lightenColor(ui.primary_color, 40));
            root.style.setProperty('--primary-dark', this.darkenColor(ui.primary_color, 30));
            root.style.setProperty('--primary-darker', this.darkenColor(ui.primary_color, 40));
            console.log(`🎨 Primary color set to: ${ui.primary_color}`);
        }

        // Apply secondary color and its variations
        if (ui.secondary_color) {
            root.style.setProperty('--secondary-color', ui.secondary_color);
            root.style.setProperty('--secondary-hover', this.darkenColor(ui.secondary_color, 10));
            root.style.setProperty('--secondary-active', this.darkenColor(ui.secondary_color, 20));
            root.style.setProperty('--secondary-light', this.lightenColor(ui.secondary_color, 40));
            root.style.setProperty('--secondary-dark', this.darkenColor(ui.secondary_color, 30));
            console.log(`🎨 Secondary color set to: ${ui.secondary_color}`);
        }

        // Apply background color and its variations
        if (ui.background_color) {
            root.style.setProperty('--background-color', ui.background_color);
            root.style.setProperty('--background-hover', this.darkenColor(ui.background_color, 5));
            root.style.setProperty('--background-active', this.darkenColor(ui.background_color, 10));
            root.style.setProperty('--background-light', this.lightenColor(ui.background_color, 20));
            root.style.setProperty('--background-dark', this.darkenColor(ui.background_color, 15));
            
            // Set background-related variables
            root.style.setProperty('--bg-primary', ui.background_color);
            root.style.setProperty('--bg-secondary', this.lightenColor(ui.background_color, 10));
            root.style.setProperty('--bg-tertiary', this.darkenColor(ui.background_color, 10));
            root.style.setProperty('--bg-glass', `rgba(${this.hexToRgb(ui.background_color)}, 0.95)`);
            root.style.setProperty('--bg-blur', `rgba(${this.hexToRgb(ui.background_color)}, 0.8)`);
            
            console.log(`🎨 Background color set to: ${ui.background_color}`);
        }

        // Apply button color and its variations
        if (ui.button_color) {
            root.style.setProperty('--button-color', ui.button_color, 'important');
            root.style.setProperty('--button-hover', this.darkenColor(ui.button_color, 10), 'important');
            root.style.setProperty('--button-active', this.darkenColor(ui.button_color, 20), 'important');
            root.style.setProperty('--button-light', this.lightenColor(ui.button_color, 40), 'important');
            root.style.setProperty('--button-dark', this.darkenColor(ui.button_color, 30), 'important');
            
            // Set warning color based on button color
            root.style.setProperty('--warning-color', ui.button_color, 'important');
            root.style.setProperty('--warning-light', this.lightenColor(ui.button_color, 20), 'important');
            root.style.setProperty('--warning-dark', this.darkenColor(ui.button_color, 20), 'important');
            
            console.log(`🎨 Button color set to: ${ui.button_color}`);
        }

        // Apply text color and its variations
        if (ui.text_color) {
            root.style.setProperty('--text-color', ui.text_color);
            root.style.setProperty('--text-hover', this.lightenColor(ui.text_color, 10));
            root.style.setProperty('--text-active', this.darkenColor(ui.text_color, 10));
            root.style.setProperty('--text-light', this.lightenColor(ui.text_color, 30));
            root.style.setProperty('--text-dark', this.darkenColor(ui.text_color, 20));
            
            // Set background dark based on text color
            root.style.setProperty('--bg-dark', ui.text_color);
            
            console.log(`🎨 Text color set to: ${ui.text_color}`);
        }

        // 🎨 NEW: Apply header color and variations
        if (ui.header_color) {
            root.style.setProperty('--header-color', ui.header_color);
            root.style.setProperty('--header-background', ui.header_color);
            root.style.setProperty('--header-hover', this.darkenColor(ui.header_color, 10));
            root.style.setProperty('--header-active', this.darkenColor(ui.header_color, 20));
            console.log(`🎨 Header color set to: ${ui.header_color}`);
        }

        // 🎨 NEW: Apply footer color and variations
        if (ui.footer_color) {
            root.style.setProperty('--footer-color', ui.footer_color);
            root.style.setProperty('--footer-background', ui.footer_color);
            root.style.setProperty('--footer-hover', this.darkenColor(ui.footer_color, 10));
            root.style.setProperty('--footer-active', this.darkenColor(ui.footer_color, 20));
            console.log(`🎨 Footer color set to: ${ui.footer_color}`);
        }

        // 🎨 NEW: Apply button text color
        if (ui.button_text_color) {
            root.style.setProperty('--button-text-color', ui.button_text_color);
            root.style.setProperty('--button-text-hover', this.lightenColor(ui.button_text_color, 10));
            root.style.setProperty('--button-text-active', this.darkenColor(ui.button_text_color, 10));
            console.log(`🎨 Button text color set to: ${ui.button_text_color}`);
        }

        // Set derived colors based on API colors
        if (ui.primary_color) {
            root.style.setProperty('--border-color', this.lightenColor(ui.primary_color, 60));
            root.style.setProperty('--hover-color', this.darkenColor(ui.primary_color, 10));
            root.style.setProperty('--hover-light', `rgba(${this.hexToRgb(ui.primary_color)}, 0.1)`);
            root.style.setProperty('--hover-overlay', `rgba(${this.hexToRgb(ui.primary_color)}, 0.05)`);
            root.style.setProperty('--active-color', this.darkenColor(ui.primary_color, 20));
            root.style.setProperty('--active-light', `rgba(${this.hexToRgb(ui.primary_color)}, 0.15)`);
            root.style.setProperty('--focus-shadow', `0 0 0 0.2rem rgba(${this.hexToRgb(ui.primary_color)}, 0.25)`);
        }

        if (ui.secondary_color) {
            root.style.setProperty('--success-color', ui.secondary_color);
            root.style.setProperty('--success-light', this.lightenColor(ui.secondary_color, 20));
            root.style.setProperty('--success-dark', this.darkenColor(ui.secondary_color, 20));
            root.style.setProperty('--accent-color', ui.secondary_color);
            root.style.setProperty('--accent-light', this.lightenColor(ui.secondary_color, 20));
            root.style.setProperty('--accent-dark', this.darkenColor(ui.secondary_color, 20));
            root.style.setProperty('--info-color', ui.secondary_color);
            root.style.setProperty('--info-light', this.lightenColor(ui.secondary_color, 20));
            root.style.setProperty('--info-dark', this.darkenColor(ui.secondary_color, 20));
            root.style.setProperty('--focus-color', ui.secondary_color);
            root.style.setProperty('--loading-color', ui.secondary_color);
            root.style.setProperty('--loading-bg', `rgba(${this.hexToRgb(ui.secondary_color)}, 0.1)`);
        }

        // Set system defaults for disabled states
        root.style.setProperty('--disabled-color', '#6c757d');
        root.style.setProperty('--disabled-bg', '#e9ecef');
        root.style.setProperty('--disabled-border', '#dee2e6');
        root.style.setProperty('--disabled-text', '#adb5bd');
        
        // Set error color as system default
        root.style.setProperty('--error-color', '#dc3545');
        root.style.setProperty('--error-light', '#e15868');
        root.style.setProperty('--error-dark', '#c82333');
        root.style.setProperty('--danger-color', '#dc3545');
        root.style.setProperty('--danger-dark', '#c82333');

        // Generate gray scale from background and text colors
        if (ui.background_color && ui.text_color) {
            // Generate light grays from background color
            root.style.setProperty('--gray-50', this.lightenColor(ui.background_color, 3));
            root.style.setProperty('--gray-100', this.lightenColor(ui.background_color, 1));
            root.style.setProperty('--gray-200', this.darkenColor(ui.background_color, 2));
            
            // Generate mid grays blending background and text
            const midGray = this.blendColors(ui.background_color, ui.text_color, 0.3);
            root.style.setProperty('--gray-300', midGray);
            root.style.setProperty('--gray-400', this.darkenColor(midGray, 10));
            root.style.setProperty('--gray-500', this.darkenColor(midGray, 20));
            
            // Generate dark grays from text color
            root.style.setProperty('--gray-600', this.lightenColor(ui.text_color, 30));
            root.style.setProperty('--gray-700', this.lightenColor(ui.text_color, 20));
            root.style.setProperty('--gray-800', this.lightenColor(ui.text_color, 10));
            root.style.setProperty('--gray-900', ui.text_color);
        }

        // Create gradients from API colors
        if (ui.primary_color && ui.secondary_color) {
            root.style.setProperty('--gradient-primary', 
                `linear-gradient(135deg, ${ui.primary_color} 0%, ${this.darkenColor(ui.primary_color, 20)} 50%, ${this.darkenColor(ui.primary_color, 40)} 100%)`);
            root.style.setProperty('--gradient-secondary', 
                `linear-gradient(135deg, ${ui.background_color || '#ffffff'} 0%, ${ui.secondary_color} 50%, ${ui.background_color || '#ffffff'} 100%)`);
            
            // Generate shadow colors from primary color
            root.style.setProperty('--shadow-primary', 
                `0 0 50px rgba(${this.hexToRgb(ui.primary_color)}, 0.15)`);
            root.style.setProperty('--shadow-primary-lg', 
                `20px 0 60px rgba(${this.hexToRgb(ui.primary_color)}, 0.2)`);
        }
        
        if (ui.background_color) {
            root.style.setProperty('--gradient-glass', 
                `linear-gradient(135deg, rgba(${this.hexToRgb(ui.background_color)}, 0.95) 0%, rgba(${this.hexToRgb(ui.background_color)}, 0.9) 100%)`);
        }

        // Apply font settings
        if (ui.font_family) {
            root.style.setProperty('--font-family-primary', ui.font_family);
            document.body.style.fontFamily = ui.font_family;
        }
        if (ui.border_radius) {
            root.style.setProperty('--border-radius', ui.border_radius);
        }

        // Apply font sizes
        const fontSize = ui.font_size || {};
        if (fontSize.heading) {
            root.style.setProperty('--font-size-heading', fontSize.heading);
        }
        if (fontSize.body) {
            root.style.setProperty('--font-size-body', fontSize.body);
            root.style.setProperty('--font-size-medium', fontSize.body);
        }
        if (fontSize.small) {
            root.style.setProperty('--font-size-small', fontSize.small);
        }
        if (fontSize.large) {
            root.style.setProperty('--font-size-large', fontSize.large);
        }
        if (fontSize.extra_large) {
            root.style.setProperty('--font-size-extra-large', fontSize.extra_large);
        }

        // Apply colors to specific elements immediately
        this.applyColorsToElements();

        console.log('✅ All CSS variables applied successfully from DDS API');
    }

    /**
     * Apply colors directly to specific elements for immediate effect
     * Apply all DDS API colors: primary, secondary, background, button, text
     */
    applyColorsToElements() {
        const ui = this.config.ui || {};

        console.log('🎨 Applying colors to specific elements...');

        // Apply secondary color to drawer elements
        if (ui.secondary_color) {
            // Update drawer header with secondary color
            const drawerHeaders = document.querySelectorAll('.drawer-header');
            drawerHeaders.forEach(header => {
                header.style.background = ui.secondary_color;
            });

            // Update primary buttons
            const primaryButtons = document.querySelectorAll('.btn-primary, .submit-btn');
            primaryButtons.forEach(button => {
                button.style.backgroundColor = ui.primary_color;
                button.style.borderColor = ui.primary_color;
            });

            // Update section headers
            const sectionHeaders = document.querySelectorAll('.drawer-section-header');
            sectionHeaders.forEach(header => {
                header.style.borderLeftColor = ui.primary_color;
            });

            // Update drawer arrow button
            const drawerArrowBtn = document.querySelector('.drawer-arrow-btn');
            if (drawerArrowBtn) {
                drawerArrowBtn.style.backgroundColor = ui.primary_color;
                drawerArrowBtn.style.borderColor = ui.primary_color;
            }
        }

        // Apply secondary color
        if (ui.secondary_color) {
            const secondaryElements = document.querySelectorAll('.btn-secondary');
            secondaryElements.forEach(element => {
                element.style.backgroundColor = ui.secondary_color;
                element.style.borderColor = ui.secondary_color;
            });
        }

        // Apply button color to specific button elements
        if (ui.button_color) {
            const buttonElements = document.querySelectorAll('button:not(.btn-primary):not(.btn-secondary), .modal-btn');
            buttonElements.forEach(button => {
                if (!button.classList.contains('cancel-btn')) {
                    button.style.backgroundColor = ui.button_color;
                    button.style.borderColor = ui.button_color;
                }
            });
        }

        // Apply background color
        if (ui.background_color) {
            // Apply to main content areas (but not drawer-content)
            const contentAreas = document.querySelectorAll('.main-content');
            contentAreas.forEach(area => {
                area.style.backgroundColor = ui.background_color;
            });
        }

        // Apply secondary color to all drawer elements
        if (ui.secondary_color) {
            // Apply secondary color to drawer content
            const drawerContent = document.querySelectorAll('.drawer-content');
            drawerContent.forEach(content => {
                content.style.backgroundColor = ui.secondary_color;
            });

            // Apply to drawer sections
            const drawerSections = document.querySelectorAll('.drawer-section');
            drawerSections.forEach(section => {
                section.style.backgroundColor = ui.secondary_color;
            });
        }

        // Apply text color
        if (ui.text_color) {
            // Apply to main text elements
            const textElements = document.querySelectorAll('.project-name, .task-name, .drawer-item-text');
            textElements.forEach(element => {
                element.style.color = ui.text_color;
            });

            // Apply to all drawer text elements
            const drawerTextElements = document.querySelectorAll('.drawer-header, .drawer-section-header, .drawer-item');
            drawerTextElements.forEach(element => {
                element.style.color = ui.text_color;
            });

            // Update body text color
            document.body.style.color = ui.text_color;
        }

        // 🎨 NEW: Apply header color to header elements
        if (ui.header_color) {
            const headerElements = document.querySelectorAll('header, .header, .top-header, .window-header, .navbar');
            headerElements.forEach(element => {
                element.style.backgroundColor = ui.header_color;
            });
            console.log('🎨 Applied header color to header elements');
        }

        // 🎨 NEW: Apply footer color to footer elements
        if (ui.footer_color) {
            const footerElements = document.querySelectorAll('footer, .footer, .bottom-footer');
            footerElements.forEach(element => {
                element.style.backgroundColor = ui.footer_color;
            });
            console.log('🎨 Applied footer color to footer elements');
        }

        // 🎨 NEW: Apply button text color to button text
        if (ui.button_text_color) {
            const buttonElements = document.querySelectorAll('button, .btn, .modal-btn, .submit-btn');
            buttonElements.forEach(button => {
                button.style.color = ui.button_text_color;
            });
            console.log('🎨 Applied button text color to all buttons');
        }

        console.log('✅ Colors applied to specific elements');
    }

    /**
     * Utility function to darken a color by a percentage
     */
    darkenColor(color, percent) {
        const num = parseInt(color.replace("#", ""), 16);
        const amt = Math.round(2.55 * percent);
        const R = (num >> 16) - amt;
        const G = (num >> 8 & 0x00FF) - amt;
        const B = (num & 0x0000FF) - amt;
        return "#" + (0x1000000 + (R < 255 ? R < 1 ? 0 : R : 255) * 0x10000 +
            (G < 255 ? G < 1 ? 0 : G : 255) * 0x100 +
            (B < 255 ? B < 1 ? 0 : B : 255)).toString(16).slice(1);
    }

    /**
     * Utility function to lighten a color by a percentage
     */
    lightenColor(color, percent) {
        const num = parseInt(color.replace("#", ""), 16);
        const amt = Math.round(2.55 * percent);
        const R = (num >> 16) + amt;
        const G = (num >> 8 & 0x00FF) + amt;
        const B = (num & 0x0000FF) + amt;
        return "#" + (0x1000000 + (R < 255 ? R < 1 ? 0 : R : 255) * 0x10000 +
            (G < 255 ? G < 1 ? 0 : G : 255) * 0x100 +
            (B < 255 ? B < 1 ? 0 : B : 255)).toString(16).slice(1);
    }

    /**
     * Utility function to convert hex color to RGB string
     */
    hexToRgb(hex) {
        const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
        return result ? 
            `${parseInt(result[1], 16)}, ${parseInt(result[2], 16)}, ${parseInt(result[3], 16)}` : 
            '255, 255, 255';
    }

    /**
     * Utility function to blend two colors
     */
    blendColors(color1, color2, ratio) {
        const hex1 = parseInt(color1.replace("#", ""), 16);
        const hex2 = parseInt(color2.replace("#", ""), 16);
        
        const r1 = (hex1 >> 16) & 255;
        const g1 = (hex1 >> 8) & 255;
        const b1 = hex1 & 255;
        
        const r2 = (hex2 >> 16) & 255;
        const g2 = (hex2 >> 8) & 255;
        const b2 = hex2 & 255;
        
        const r = Math.round(r1 * (1 - ratio) + r2 * ratio);
        const g = Math.round(g1 * (1 - ratio) + g2 * ratio);
        const b = Math.round(b1 * (1 - ratio) + b2 * ratio);
        
        return "#" + ((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1);
    }

    /**
     * Apply font settings to body
     */
    applyFontSettings() {
        const ui = this.config.ui || {};
        
        if (ui.font_family) {
            document.body.style.fontFamily = ui.font_family;
        }
    }

    /**
     * Update specific UI elements based on configuration
     */
    updateUIElements() {
        // Update screenshot interval display if exists
        const intervalDisplay = document.getElementById('screenshot-interval-display');
        if (intervalDisplay && this.config.screenshot) {
            intervalDisplay.textContent = `${this.config.screenshot.interval_seconds}s`;
        }

        // Update feature toggles
        this.updateFeatureToggles();
    }

    /**
     * Update feature toggle states
     */
    updateFeatureToggles() {
        const features = this.config.features || {};
        
        Object.entries(features).forEach(([feature, enabled]) => {
            const toggle = document.getElementById(`feature-${feature.replace('_', '-')}`);
            if (toggle) {
                toggle.checked = enabled;
                toggle.dispatchEvent(new Event('change'));
            }
        });
    }

    /**
     * Get configuration value by path
     * @param {string} path - Dot notation path (e.g., 'ui.primary_color')
     * @param {*} defaultValue - Default value if path not found
     * @returns {*} Configuration value
     */
    getValue(path, defaultValue = null) {
        if (!this.config) return defaultValue;
        
        return path.split('.').reduce((obj, key) => {
            return obj && obj[key] !== undefined ? obj[key] : defaultValue;
        }, this.config);
    }

    /**
     * Initialize configuration system
     */
    async initialize() {
        console.log('🚀 Initializing Configuration Manager...');
        
        try {
            await this.fetchConfiguration();
            this.applyConfiguration();
            
            // For login pages, force immediate color application after a short delay
            if (window.location.pathname.includes('login') || document.querySelector('.login-button, .login-btn')) {
                console.log('🔑 Login page detected - ensuring button colors are applied');
                setTimeout(() => {
                    this.forceButtonColorApplication();
                }, 500);
            }
            
            // Set up periodic refresh (every 5 minutes)
            setInterval(() => {
                this.refreshConfiguration().catch(console.error);
            }, 5 * 60 * 1000);
            
            console.log('✅ Configuration Manager initialized');
        } catch (error) {
            console.error('❌ Failed to initialize Configuration Manager:', error);
        }
    }

    /**
     * Force button color application for login pages
     */
    forceButtonColorApplication() {
        const ui = this.config?.ui || {};
        
        console.log('🔘 Force applying button colors for login page...');
        console.log('🔘 Available button color:', ui.button_color);
        
        if (ui.button_color) {
            // Apply CSS variables with !important
            const root = document.documentElement;
            root.style.setProperty('--button-color', ui.button_color, 'important');
            root.style.setProperty('--button-hover', this.darkenColor(ui.button_color, 10), 'important');
            
            // Apply to login buttons specifically with direct style override
            const loginButtons = document.querySelectorAll('.login-button, .login-btn, .guest-button');
            loginButtons.forEach(button => {
                button.style.setProperty('background-color', ui.button_color, 'important');
                button.style.setProperty('border-color', ui.button_color, 'important');
                console.log(`🎨 Applied button color ${ui.button_color} to`, button.className || button.tagName);
            });
            
            // Apply hover effects with proper cleanup
            const hoverColor = this.darkenColor(ui.button_color, 10);
            loginButtons.forEach(button => {
                // Remove existing event listeners
                button.removeEventListener('mouseenter', button._hoverHandler);
                button.removeEventListener('mouseleave', button._leaveHandler);
                
                // Add new event listeners
                button._hoverHandler = () => {
                    button.style.setProperty('background-color', hoverColor, 'important');
                };
                button._leaveHandler = () => {
                    button.style.setProperty('background-color', ui.button_color, 'important');
                };
                
                button.addEventListener('mouseenter', button._hoverHandler);
                button.addEventListener('mouseleave', button._leaveHandler);
            });
            
            console.log('✅ Button colors force-applied for login page with !important');
        } else {
            console.warn('⚠️ No button color available to apply');
            console.warn('⚠️ Config state:', this.config);
        }
    }
}

// Global instance
window.configManager = new ConfigManager();

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.configManager.initialize();
    });
} else {
    window.configManager.initialize();
}

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ConfigManager;
}
