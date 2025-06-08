import os
import re
from pathlib import Path
from typing import Dict, List

from backend.states import UIFormStep


def generate_ui_form_html(ui_form_step: UIFormStep) -> str:
    """
    Generate complete HTML form page from UIFormStep using reusable components
    
    Args:
        ui_form_step: UIFormStep instance containing form configuration
    
    Returns:
        str: Complete HTML page as string
    """
    
    # Generate form fields HTML using enhanced approach
    form_fields_html = generate_form_fields_enhanced(ui_form_step.form_config.fields)
    
    # Create complete HTML page with embedded CSS
    html_page = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>XRPL Microfinance Application</title>
    <style>
        /* Global styles */
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Inter', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
            line-height: 1.6;
        }}

        .form-container {{
            background: white;
            max-width: 600px;
            width: 100%;
            border-radius: 20px;
            box-shadow: 0 25px 50px rgba(0, 0, 0, 0.15);
            overflow: hidden;
            animation: slideUp 0.8s ease-out;
            position: relative;
        }}

        .form-container::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(90deg, #667eea, #764ba2, #667eea);
            background-size: 200% 100%;
            animation: shimmer 3s infinite;
        }}

        @keyframes slideUp {{
            from {{
                opacity: 0;
                transform: translateY(40px) scale(0.98);
            }}
            to {{
                opacity: 1;
                transform: translateY(0) scale(1);
            }}
        }}

        @keyframes shimmer {{
            0% {{ background-position: -200% 0; }}
            100% {{ background-position: 200% 0; }}
        }}

        .form-header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px 30px;
            text-align: center;
            position: relative;
            overflow: hidden;
        }}

        .form-header::before {{
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
            animation: rotate 20s linear infinite;
        }}

        @keyframes rotate {{
            from {{ transform: rotate(0deg); }}
            to {{ transform: rotate(360deg); }}
        }}

        .form-header h1 {{
            font-size: 2rem;
            margin-bottom: 12px;
            font-weight: 700;
            position: relative;
            z-index: 1;
        }}

        .form-header p {{
            opacity: 0.95;
            font-size: 1.1rem;
            position: relative;
            z-index: 1;
            font-weight: 400;
        }}

        .form-content {{
            padding: 50px 40px;
            background: #fafafa;
        }}

        .workflow-form {{
            display: flex;
            flex-direction: column;
            gap: 25px;
        }}

        /* Enhanced Form Field Styles */
        .form-group {{
            position: relative;
            margin-bottom: 8px;
        }}

        .form-group.password-group {{
            position: relative;
        }}

        .field-label {{
            display: block;
            font-weight: 600;
            color: #374151;
            margin-bottom: 8px;
            font-size: 0.95rem;
            letter-spacing: 0.025em;
        }}

        .text-field, .password-field {{
            width: 100%;
            padding: 16px 20px;
            border: 2px solid #e5e7eb;
            border-radius: 12px;
            font-size: 1rem;
            font-family: inherit;
            background: white;
            transition: all 0.3s ease;
            color: #374151;
        }}

        .text-field:focus, .password-field:focus {{
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
            transform: translateY(-1px);
        }}

        .text-field:hover, .password-field:hover {{
            border-color: #9ca3af;
        }}

        .password-wrapper {{
            position: relative;
            display: flex;
            align-items: center;
        }}

        .password-toggle {{
            position: absolute;
            right: 15px;
            background: none;
            border: none;
            cursor: pointer;
            padding: 8px;
            border-radius: 6px;
            transition: background-color 0.2s ease;
            z-index: 2;
        }}

        .password-toggle:hover {{
            background-color: #f3f4f6;
        }}

        .eye-icon {{
            font-size: 1.2rem;
            color: #6b7280;
        }}

        .field-underline {{
            height: 2px;
            background: linear-gradient(90deg, #667eea, #764ba2);
            border-radius: 1px;
            transform: scaleX(0);
            transition: transform 0.3s ease;
            margin-top: -2px;
        }}

        .text-field:focus + .field-underline,
        .password-field:focus ~ .field-underline {{
            transform: scaleX(1);
        }}

        .password-strength {{
            margin-top: 8px;
            opacity: 0;
            transition: opacity 0.3s ease;
        }}

        .password-group:focus-within .password-strength {{
            opacity: 1;
        }}

        .strength-bar {{
            height: 4px;
            background: #e5e7eb;
            border-radius: 2px;
            overflow: hidden;
            margin-bottom: 6px;
        }}

        .strength-fill {{
            height: 100%;
            background: linear-gradient(90deg, #ef4444, #f59e0b, #10b981);
            width: 30%;
            border-radius: 2px;
            transition: width 0.3s ease;
        }}

        .strength-text {{
            font-size: 0.85rem;
            color: #6b7280;
            font-weight: 500;
        }}

        /* Enhanced Submit Button */
        .submit-group {{
            margin-top: 15px;
        }}

        .submit-button {{
            width: 100%;
            padding: 18px 30px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 12px;
            font-size: 1.1rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            outline: none;
            position: relative;
            overflow: hidden;
            font-family: inherit;
            letter-spacing: 0.025em;
        }}

        .submit-button::before {{
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
            transition: left 0.5s ease;
        }}

        .submit-button:hover::before {{
            left: 100%;
        }}

        .submit-button:hover {{
            transform: translateY(-2px);
            box-shadow: 0 15px 35px rgba(102, 126, 234, 0.4);
            background: linear-gradient(135deg, #5a67d8 0%, #6b46c1 100%);
        }}

        .submit-button:active {{
            transform: translateY(0);
            box-shadow: 0 8px 20px rgba(102, 126, 234, 0.3);
        }}

        .submit-button:disabled {{
            background: #d1d5db;
            color: #9ca3af;
            cursor: not-allowed;
            transform: none;
            box-shadow: none;
        }}

        .button-content {{
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 12px;
            position: relative;
            z-index: 1;
        }}

        .button-icon {{
            font-size: 1.3rem;
            transition: transform 0.3s ease;
        }}

        .submit-button:hover .button-icon {{
            transform: scale(1.1) rotate(5deg);
        }}

        .button-text {{
            font-weight: 600;
            letter-spacing: 0.5px;
        }}

        .loading-spinner {{
            display: none;
            align-items: center;
            justify-content: center;
            gap: 12px;
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: inherit;
            border-radius: inherit;
        }}

        .spinner {{
            width: 22px;
            height: 22px;
            border: 2.5px solid rgba(255, 255, 255, 0.3);
            border-top: 2.5px solid white;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }}

        @keyframes spin {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}

        .loading-text {{
            font-weight: 500;
            opacity: 0.95;
        }}

        .submit-feedback {{
            margin-top: 15px;
            padding: 12px 16px;
            border-radius: 8px;
            font-size: 0.9rem;
            font-weight: 500;
            text-align: center;
            opacity: 0;
            transform: translateY(-10px);
            transition: all 0.3s ease;
        }}

        .submit-feedback.show {{
            opacity: 1;
            transform: translateY(0);
        }}

        .submit-feedback.success {{
            background: #dcfce7;
            color: #166534;
            border: 1px solid #bbf7d0;
        }}

        .submit-feedback.error {{
            background: #fef2f2;
            color: #dc2626;
            border: 1px solid #fecaca;
        }}

        /* Input validation styles */
        .text-field:invalid, .password-field:invalid {{
            border-color: #ef4444;
        }}

        .text-field:valid, .password-field:valid {{
            border-color: #10b981;
        }}

        /* Floating label effect */
        .form-group.has-content .field-label,
        .form-group:focus-within .field-label {{
            color: #667eea;
            transform: translateY(-2px);
        }}

        /* Mobile responsiveness */
        @media (max-width: 768px) {{
            .form-container {{
                margin: 15px;
                border-radius: 16px;
            }}

            .form-header {{
                padding: 30px 25px;
            }}

            .form-header h1 {{
                font-size: 1.7rem;
            }}

            .form-header p {{
                font-size: 1rem;
            }}

            .form-content {{
                padding: 35px 25px;
            }}

            .text-field, .password-field {{
                padding: 14px 16px;
            }}

            .submit-button {{
                padding: 16px 25px;
                font-size: 1rem;
            }}
        }}

        @media (max-width: 480px) {{
            body {{
                padding: 10px;
            }}

            .form-container {{
                margin: 0;
                border-radius: 12px;
            }}

            .form-content {{
                padding: 25px 20px;
            }}

            .workflow-form {{
                gap: 20px;
            }}
        }}

        /* Dark mode support */
        @media (prefers-color-scheme: dark) {{
            .form-content {{
                background: #1f2937;
            }}

            .field-label {{
                color: #e5e7eb;
            }}

            .text-field, .password-field {{
                background: #374151;
                border-color: #4b5563;
                color: #e5e7eb;
            }}

            .text-field:focus, .password-field:focus {{
                border-color: #667eea;
                background: #374151;
            }}

            .strength-text {{
                color: #9ca3af;
            }}
        }}

        /* Accessibility improvements */
        @media (prefers-reduced-motion: reduce) {{
            * {{
                animation-duration: 0.01ms !important;
                animation-iteration-count: 1 !important;
                transition-duration: 0.01ms !important;
            }}
        }}

        /* Focus visible improvements */
        .submit-button:focus-visible {{
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.5);
        }}

        .text-field:focus-visible, .password-field:focus-visible {{
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.2);
        }}
    </style>
</head>
<body>
    <div class="form-container">
        <div class="form-header">
            <h1>📋 XRPL Microfinance Application</h1>
            <p>Please fill out the form below to proceed</p>
        </div>

        <div class="form-content">
            <form class="workflow-form" id="workflowForm" novalidate>
                {form_fields_html}
                
                <div class="submit-group">
                    <button type="submit" class="submit-button" id="submitButton">
                        <span class="button-content">
                            <span class="button-icon">🚀</span>
                            <span class="button-text">Submit & Continue</span>
                        </span>
                        <span class="loading-spinner">
                            <span class="spinner"></span>
                            <span class="loading-text">Processing & Advancing...</span>
                        </span>
                    </button>
                    <div class="submit-feedback"></div>
                </div>
            </form>
        </div>
    </div>

    <script>
        // Enhanced form functionality
        document.addEventListener('DOMContentLoaded', function() {{
            console.log('XRPL Microfinance Form loaded successfully');
            
            const form = document.getElementById('workflowForm');
            const submitButton = document.getElementById('submitButton');
            const buttonContent = submitButton.querySelector('.button-content');
            const loadingSpinner = submitButton.querySelector('.loading-spinner');
            
            // Add input event listeners for visual feedback
            const inputs = form.querySelectorAll('.text-field, .password-field');
            inputs.forEach(input => {{
                input.addEventListener('input', function() {{
                    const formGroup = this.closest('.form-group');
                    if (this.value.trim()) {{
                        formGroup.classList.add('has-content');
                    }} else {{
                        formGroup.classList.remove('has-content');
                    }}
                }});
                
                // Trigger on page load for pre-filled fields
                if (input.value.trim()) {{
                    input.closest('.form-group').classList.add('has-content');
                }}
            }});
            
            // Add email lookup for cached data
            const emailField = document.querySelector('input[name="email"]');
            if (emailField) {{
                emailField.addEventListener('blur', async function() {{
                    const email = this.value.trim();
                    if (email && email.includes('@')) {{
                        await loadCachedUserData(email);
                    }}
                }});
            }}
            
            // Password toggle functionality
            const passwordToggles = document.querySelectorAll('.password-toggle');
            passwordToggles.forEach(toggle => {{
                toggle.addEventListener('click', function() {{
                    const passwordField = this.parentElement.querySelector('.password-field');
                    const eyeIcon = this.querySelector('.eye-icon');
                    
                    if (passwordField.type === 'password') {{
                        passwordField.type = 'text';
                        eyeIcon.textContent = '🙈';
                    }} else {{
                        passwordField.type = 'password';
                        eyeIcon.textContent = '👁️';
                    }}
                }});
            }});
            
            // Form submission with enhanced feedback and caching
            form.addEventListener('submit', async function(e) {{
                e.preventDefault();
                
                // Show loading state
                buttonContent.style.display = 'none';
                loadingSpinner.style.display = 'flex';
                submitButton.disabled = true;
                
                try {{
                    // Collect form data
                    const formData = new FormData(form);
                    const data = Object.fromEntries(formData.entries());
                    
                    // Cache user data before submitting (if email exists)
                    if (data.email) {{
                        await cacheUserData(data);
                    }}
                    
                    // Call workflow advance endpoint
                    const response = await fetch('/workflow/advance', {{
                        method: 'POST',
                        headers: {{
                            'Content-Type': 'application/json',
                        }},
                        body: JSON.stringify(data)
                    }});
                    
                    if (response.ok) {{
                        showFeedback('success', 'Form submitted successfully! Proceeding...');
                        setTimeout(() => {{
                            window.location.reload(); // Or redirect to next step
                        }}, 1500);
                    }} else {{
                        throw new Error('Submission failed');
                    }}
                    
                }} catch (error) {{
                    console.error('Form submission error:', error);
                    showFeedback('error', 'Submission failed. Please try again.');
                }} finally {{
                    // Reset button state after delay
                    setTimeout(() => {{
                        buttonContent.style.display = 'flex';
                        loadingSpinner.style.display = 'none';
                        submitButton.disabled = false;
                    }}, 1000);
                }}
            }});
            
            async function cacheUserData(formData) {{
                try {{
                    // Build cache data dynamically from all form fields
                    const cacheData = {{
                        name: formData.name || '',
                        email: formData.email || '',
                        wallet_address: formData.wallet_address || ''
                    }};
                    
                    // Add any additional fields beyond the core three
                    for (const [fieldName, fieldValue] of Object.entries(formData)) {{
                        if (!['name', 'email', 'wallet_address'].includes(fieldName) && fieldValue) {{
                            cacheData[fieldName] = String(fieldValue);
                        }}
                    }}
                    
                    const response = await fetch('/api/cache-user-data', {{
                        method: 'POST',
                        headers: {{
                            'Content-Type': 'application/json',
                        }},
                        body: JSON.stringify(cacheData)
                    }});
                    
                    if (response.ok) {{
                        const result = await response.json();
                        console.log('✅ User data cached successfully', result);
                        showCacheNotification('Masked sensitive data and cached your profile in our system');
                    }} else {{
                        console.warn('⚠️ Failed to cache user data');
                    }}
                    
                }} catch (error) {{
                    console.error('Error caching user data:', error);
                }}
            }}
            
            async function loadCachedUserData(email) {{
                try {{
                    const response = await fetch(`/api/get-cached-data/${{encodeURIComponent(email)}}`);
                    const result = await response.json();
                    
                    if (result.found && result.data) {{
                        console.log('📋 Found cached data for:', email);
                        
                        // Auto-populate all form fields dynamically
                        let populatedCount = 0;
                        
                        for (const [fieldName, fieldValue] of Object.entries(result.data)) {{
                            // Skip timestamp field
                            if (fieldName === 'timestamp') continue;
                            
                            // Find form field by name attribute
                            const formField = document.querySelector(`input[name="${{fieldName}}"]`);
                            if (formField && fieldValue) {{
                                formField.value = fieldValue;
                                formField.closest('.form-group').classList.add('has-content');
                                populatedCount++;
                            }}
                        }}
                        
                        if (populatedCount > 0) {{
                            showCacheNotification(`Found saved data! ${{populatedCount}} fields auto-populated.`);
                        }}
                    }}
                    
                }} catch (error) {{
                    console.error('Error loading cached data:', error);
                }}
            }}
            
            function showFeedback(type, message) {{
                const feedback = document.querySelector('.submit-feedback');
                feedback.className = `submit-feedback show ${{type}}`;
                feedback.textContent = message;
                
                setTimeout(() => {{
                    feedback.classList.remove('show');
                }}, 5000);
            }}
            
            function showCacheNotification(message) {{
                // Create notification element if it doesn't exist
                let notification = document.getElementById('cacheNotification');
                if (!notification) {{
                    notification = document.createElement('div');
                    notification.id = 'cacheNotification';
                    notification.style.cssText = `
                        position: fixed;
                        top: 20px;
                        right: 20px;
                        background: #10b981;
                        color: white;
                        padding: 12px 20px;
                        border-radius: 8px;
                        font-weight: 500;
                        font-size: 0.9rem;
                        z-index: 1000;
                        transform: translateX(300px);
                        transition: transform 0.3s ease;
                        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
                    `;
                    document.body.appendChild(notification);
                }}
                
                notification.textContent = message;
                notification.style.transform = 'translateX(0)';
                
                setTimeout(() => {{
                    notification.style.transform = 'translateX(300px)';
                }}, 3000);
            }}
        }});
    </script>
</body>
</html>"""
    
    return html_page

def generate_form_fields_enhanced(fields: List[str]) -> str:
    """Generate enhanced form fields with modern styling"""
    
    field_html = []
    
    for field in fields:
        field_label = format_field_label(field)
        field_id = field.replace('_', '').replace(' ', '').lower()
        field_name = field
        
        # Determine if it's a password field
        password_fields = ['password', 'secret', 'wallet_secret', 'private_key', 'seed']
        is_password = any(pwd_field in field.lower() for pwd_field in password_fields)
        
        if is_password:
            # Create enhanced password field
            field_component = f'''
            <div class="form-group password-group">
                <label class="field-label" for="{field_id}">{field_label}</label>
                <div class="password-wrapper">
                    <input type="password" class="password-field" placeholder="Enter your {field_label.lower()}" id="{field_id}" name="{field_name}" required autocomplete="current-password">
                    <button type="button" class="password-toggle" aria-label="Toggle password visibility" tabindex="-1">
                        <span class="eye-icon">👁️</span>
                    </button>
                </div>
                <div class="field-underline"></div>
                <div class="password-strength">
                    <div class="strength-bar">
                        <div class="strength-fill"></div>
                    </div>
                    <span class="strength-text">Enter {field_label.lower()}</span>
                </div>
            </div>
            '''
        else:
            # Create enhanced text field
            input_type = get_input_type_for_field(field)
            autocomplete_attr = get_autocomplete_for_field(field)
            
            field_component = f'''
            <div class="form-group">
                <label class="field-label" for="{field_id}">{field_label}</label>
                <input type="{input_type}" class="text-field" placeholder="Enter your {field_label.lower()}" id="{field_id}" name="{field_name}" required {autocomplete_attr}>
                <div class="field-underline"></div>
            </div>
            '''
        
        field_html.append(field_component.strip())
    
    return "\n\n".join(field_html)

def get_autocomplete_for_field(field_name: str) -> str:
    """Get appropriate autocomplete attribute for field"""
    
    field_lower = field_name.lower()
    
    autocomplete_mapping = {
        'name': 'autocomplete="name"',
        'first_name': 'autocomplete="given-name"',
        'last_name': 'autocomplete="family-name"',
        'email': 'autocomplete="email"',
        'phone': 'autocomplete="tel"',
        'address': 'autocomplete="address-line1"',
        'wallet_address': 'autocomplete="off"',
        'amount': 'autocomplete="off"'
    }
    
    for key, value in autocomplete_mapping.items():
        if key in field_lower:
            return value
    
    return 'autocomplete="off"'

def read_component_file(file_path: Path) -> str:
    """Read component file content"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"Warning: Component file not found: {file_path}")
        return ""

def extract_css_from_components(component_contents: List[str]) -> str:
    """Extract all CSS from component files"""
    all_css = []
    
    for content in component_contents:
        # Extract CSS between <style> tags
        css_matches = re.findall(r'<style>(.*?)</style>', content, re.DOTALL)
        for match in css_matches:
            all_css.append(match.strip())
    
    return "\n\n".join(all_css)

def extract_js_from_components(component_contents: List[str]) -> str:
    """Extract all JavaScript from component files"""
    all_js = []
    
    for content in component_contents:
        # Extract JavaScript between <script> tags
        js_matches = re.findall(r'<script>(.*?)</script>', content, re.DOTALL)
        for match in js_matches:
            all_js.append(match.strip())
    
    return "\n\n".join(all_js)

def generate_form_fields_simple(fields: List[str]) -> str:
    """Generate form fields using simplified approach"""
    
    field_html = []
    
    for field in fields:
        field_label = format_field_label(field)
        field_id = field.replace('_', '').replace(' ', '').lower()
        field_name = field
        
        # Determine if it's a password field
        password_fields = ['password', 'secret', 'wallet_secret', 'private_key', 'seed']
        is_password = any(pwd_field in field.lower() for pwd_field in password_fields)
        
        if is_password:
            # Create password field
            field_component = f'''
            <div class="form-group password-group">
                <label class="field-label">{field_label}</label>
                <div class="password-wrapper">
                    <input type="password" class="password-field" placeholder="{field_label}" id="{field_id}" name="{field_name}" required>
                    <button type="button" class="password-toggle" aria-label="Toggle password visibility">
                        <span class="eye-icon">👁️</span>
                    </button>
                </div>
                <div class="field-underline"></div>
                <div class="password-strength">
                    <div class="strength-bar">
                        <div class="strength-fill"></div>
                    </div>
                    <span class="strength-text">Enter {field_label.lower()}</span>
                </div>
            </div>
            '''
        else:
            # Create text field
            input_type = get_input_type_for_field(field)
            field_component = f'''
            <div class="form-group">
                <label class="field-label">{field_label}</label>
                <input type="{input_type}" class="text-field" placeholder="{field_label}" id="{field_id}" name="{field_name}" required>
                <div class="field-underline"></div>
            </div>
            '''
        
        field_html.append(field_component.strip())
    
    return "\n\n".join(field_html)

def generate_submit_button_simple() -> str:
    """Generate submit button using simplified approach"""
    
    return '''
    <div class="submit-group">
        <button type="submit" class="submit-button" data-api-endpoint="/workflow/advance" data-method="POST">
            <span class="button-content">
                <span class="button-icon">🚀</span>
                <span class="button-text">Submit & Continue</span>
            </span>
            <span class="loading-spinner" style="display: none;">
                <span class="spinner"></span>
                <span class="loading-text">Processing & Advancing...</span>
            </span>
        </button>
        <div class="submit-feedback"></div>
    </div>
    '''.strip()

def format_field_label(field_name: str) -> str:
    """Convert field name to human-readable label"""
    
    # Replace underscores with spaces and title case
    label = field_name.replace('_', ' ').title()
    
    # Handle special cases
    label_mappings = {
        'Wallet Address': 'Wallet Address',
        'Email Address': 'Email Address',
        'Wallet Secret': 'Wallet Secret',
        'Private Key': 'Private Key',
        'Xrp': 'XRP',
        'Usd': 'USD'
    }
    
    for old, new in label_mappings.items():
        if old in label:
            label = label.replace(old, new)
    
    return label

def get_input_type_for_field(field_name: str) -> str:
    """Determine the appropriate HTML input type for a field"""
    
    field_lower = field_name.lower()
    
    if 'email' in field_lower:
        return 'email'
    elif 'phone' in field_lower or 'tel' in field_lower:
        return 'tel'
    elif 'amount' in field_lower or 'balance' in field_lower or 'price' in field_lower:
        return 'number'
    elif 'url' in field_lower or 'website' in field_lower:
        return 'url'
    else:
        return 'text'

def test_ui_form_generation():
    """Test function to demonstrate UI form generation"""
    
    # Create a test UIFormStep
    from backend.states import UIFormConfig, UIFormStep
    
    test_config = UIFormConfig(fields=["name", "email", "amount", "wallet_address", "wallet_secret"])
    test_step = UIFormStep(test_config, "did_verification")
    
    # Generate HTML
    html_content = generate_ui_form_html(test_step)
    
    # Save to file for testing
    output_file = Path(__file__).parent / "test_form_output.html"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ Test UI form generated successfully!")
    print(f"📄 Output saved to: {output_file}")
    print(f"🌐 You can open this file in a browser to see the form")
    
    return html_content

if __name__ == "__main__":
    test_ui_form_generation()
