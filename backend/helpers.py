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
    
    # Get the templates directory
    templates_dir = Path(__file__).parent / "templates"
    
    # Read component files
    text_field_content = read_component_file(templates_dir / "text_field.html")
    password_field_content = read_component_file(templates_dir / "password_field.html")
    submit_button_content = read_component_file(templates_dir / "submit_button.html")
    
    # Extract CSS and JavaScript from components
    all_css = extract_css_from_components([text_field_content, password_field_content, submit_button_content])
    all_js = extract_js_from_components([text_field_content, password_field_content, submit_button_content])
    
    # Generate form fields HTML using simplified approach
    form_fields_html = generate_form_fields_simple(ui_form_step.form_config.fields)
    
    # Generate submit button HTML using simplified approach
    submit_button_html = generate_submit_button_simple()
    
    # Create complete HTML page
    html_page = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>XRPL Microfinance Form</title>
    <style>
        /* Global styles */
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Arial', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }}

        .form-container {{
            background: white;
            max-width: 600px;
            width: 100%;
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
            overflow: hidden;
            animation: slideUp 0.6s ease-out;
        }}

        @keyframes slideUp {{
            from {{
                opacity: 0;
                transform: translateY(30px);
            }}
            to {{
                opacity: 1;
                transform: translateY(0);
            }}
        }}

        .form-header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}

        .form-header h1 {{
            font-size: 1.8rem;
            margin-bottom: 10px;
        }}

        .form-header p {{
            opacity: 0.9;
            font-size: 1rem;
        }}

        .form-content {{
            padding: 40px;
        }}

        .workflow-form {{
            display: flex;
            flex-direction: column;
            gap: 20px;
        }}

        /* Component styles */
        {all_css}

        /* Mobile responsiveness */
        @media (max-width: 768px) {{
            .form-container {{
                margin: 10px;
                border-radius: 15px;
            }}

            .form-header h1 {{
                font-size: 1.5rem;
            }}

            .form-content {{
                padding: 30px 25px;
            }}
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
            <form class="workflow-form" id="workflowForm">
                {form_fields_html}
                
                {submit_button_html}
            </form>
        </div>
    </div>

    <script>
        {all_js}
        
        // Form-specific JavaScript
        document.addEventListener('DOMContentLoaded', function() {{
            console.log('XRPL Microfinance Form loaded successfully');
            
            // Initialize form validation
            const form = document.getElementById('workflowForm');
            form.addEventListener('submit', function(e) {{
                console.log('Form submitted');
            }});
        }});
    </script>
</body>
</html>"""
    
    return html_page


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