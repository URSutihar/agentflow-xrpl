"""
DID Verification Agents
Handles generation of DID verification forms and UI components
"""

import re
from pathlib import Path
from typing import List

from backend.states import DIDVerificationStep


def generate_did_verification_form_html(did_verification_step: DIDVerificationStep) -> str:
    """
    Generate complete HTML form page for DID verification
    
    Args:
        did_verification_step: DIDVerificationStep instance containing verification configuration
    
    Returns:
        str: Complete HTML page as string
    """
    
    # Get the templates directory
    templates_dir = Path(__file__).parent.parent / "templates"
    
    # Read component files
    text_field_content = read_component_file(templates_dir / "text_field.html")
    password_field_content = read_component_file(templates_dir / "password_field.html")
    # Note: We don't include submit_button_content since we have custom handling
    
    # Extract CSS and JavaScript from components (excluding submit button to avoid conflicts)
    all_css = extract_css_from_components([text_field_content, password_field_content])
    all_js = extract_js_from_components([text_field_content, password_field_content])
    
    # Generate wallet address field
    wallet_address_field = '''
    <div class="form-group">
        <label class="field-label">Wallet Address</label>
        <input type="text" class="text-field" placeholder="Enter your XRPL wallet address" id="walletaddress" name="wallet_address" required>
        <div class="field-underline"></div>
    </div>
    '''
    
    # Generate wallet secret field
    wallet_secret_field = '''
    <div class="form-group password-group">
        <label class="field-label">Wallet Secret</label>
        <div class="password-wrapper">
            <input type="password" class="password-field" placeholder="Enter your wallet secret" id="walletsecret" name="wallet_secret" required>
            <button type="button" class="password-toggle" aria-label="Toggle password visibility">
                <span class="eye-icon">👁️</span>
            </button>
        </div>
        <div class="field-underline"></div>
        <div class="password-strength">
            <div class="strength-bar">
                <div class="strength-fill"></div>
            </div>
            <span class="strength-text">Enter wallet secret</span>
        </div>
    </div>
    '''
    
    # Generate verification submit button (custom implementation without component conflicts)
    verification_button = '''
    <div class="submit-group">
        <button type="button" class="submit-button" id="verifyButton">
            <span class="button-content">
                <span class="button-icon">🔐</span>
                <span class="button-text">Verify Identity</span>
            </span>
            <span class="loading-spinner" style="display: none;">
                <span class="spinner"></span>
                <span class="loading-text">Verifying Identity...</span>
            </span>
        </button>
        <div class="submit-feedback"></div>
    </div>
    '''
    
    # Create complete HTML page
    html_page = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>XRPL Identity Verification</title>
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

        /* Popup styles */
        .popup-overlay {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.5);
            display: none;
            justify-content: center;
            align-items: center;
            z-index: 1000;
        }}

        .popup {{
            background: white;
            border-radius: 15px;
            padding: 30px;
            max-width: 400px;
            width: 90%;
            text-align: center;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.2);
            animation: popupSlideIn 0.3s ease-out;
        }}

        @keyframes popupSlideIn {{
            from {{
                opacity: 0;
                transform: scale(0.8) translateY(-20px);
            }}
            to {{
                opacity: 1;
                transform: scale(1) translateY(0);
            }}
        }}

        .popup-success {{
            border-top: 5px solid #4CAF50;
        }}

        .popup-error {{
            border-top: 5px solid #f44336;
        }}

        .popup-icon {{
            font-size: 3rem;
            margin-bottom: 15px;
        }}

        .popup-title {{
            font-size: 1.5rem;
            margin-bottom: 10px;
            font-weight: bold;
        }}

        .popup-message {{
            font-size: 1rem;
            margin-bottom: 20px;
            color: #666;
        }}

        .popup-button {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 8px;
            font-size: 1rem;
            cursor: pointer;
            transition: transform 0.2s ease;
        }}

        .popup-button:hover {{
            transform: translateY(-2px);
        }}

        /* Component styles */
        {all_css}

        /* Custom submit button styles (to replace component styles) */
        .submit-group {{
            position: relative;
            margin: 25px 0;
            width: 100%;
        }}

        .submit-button {{
            width: 100%;
            padding: 15px 25px;
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
            font-family: 'Arial', sans-serif;
            min-height: 55px;
            display: flex;
            align-items: center;
            justify-content: center;
        }}

        .submit-button:hover {{
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);
            background: linear-gradient(135deg, #5a67d8 0%, #6b46c1 100%);
        }}

        .submit-button:disabled {{
            background: #cbd5e0;
            color: #a0aec0;
            cursor: not-allowed;
            transform: none;
            box-shadow: none;
        }}

        .button-content {{
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
            transition: all 0.3s ease;
        }}

        .button-icon {{
            font-size: 1.2rem;
            transition: transform 0.3s ease;
        }}

        .submit-button:hover .button-icon {{
            transform: scale(1.1);
        }}

        .button-text {{
            font-weight: 600;
            letter-spacing: 0.5px;
        }}

        .loading-spinner {{
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: inherit;
            border-radius: inherit;
        }}

        .spinner {{
            width: 20px;
            height: 20px;
            border: 2px solid rgba(255, 255, 255, 0.3);
            border-top: 2px solid white;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }}

        @keyframes spin {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}

        .loading-text {{
            font-weight: 500;
            opacity: 0.9;
        }}

        .submit-feedback {{
            margin-top: 10px;
            padding: 10px;
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
            background: #e8f5e8;
            color: #2e7d32;
            border: 1px solid #4caf50;
        }}

        .submit-feedback.error {{
            background: #ffebee;
            color: #c62828;
            border: 1px solid #f44336;
        }}

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

            .popup {{
                padding: 25px;
            }}

            .submit-button {{
                padding: 12px 20px;
                font-size: 1rem;
                min-height: 50px;
            }}
            
            .button-icon {{
                font-size: 1.1rem;
            }}
        }}
    </style>
</head>
<body>
    <div class="form-container">
        <div class="form-header">
            <h1>🔐 Identity Verification</h1>
            <p>Verify your XRPL wallet ownership to continue</p>
        </div>

        <div class="form-content">
            <form class="workflow-form" id="verificationForm" action="" method="post" onsubmit="return false;">
                {wallet_address_field}
                {wallet_secret_field}
                {verification_button}
            </form>
        </div>
    </div>

    <!-- Success Popup -->
    <div class="popup-overlay" id="successPopup">
        <div class="popup popup-success">
            <div class="popup-icon">✅</div>
            <div class="popup-title">Identity Verified!</div>
            <div class="popup-message">Your wallet ownership has been successfully verified. Proceeding to the next step...</div>
            <button class="popup-button" onclick="closePopup('successPopup')">Continue</button>
        </div>
    </div>

    <!-- Error Popup -->
    <div class="popup-overlay" id="errorPopup">
        <div class="popup popup-error">
            <div class="popup-icon">❌</div>
            <div class="popup-title">Verification Failed</div>
            <div class="popup-message" id="errorMessage">Identity verification failed. Please check your wallet address and secret, then try again.</div>
            <button class="popup-button" onclick="closePopup('errorPopup')">Try Again</button>
        </div>
    </div>

    <script>
        {all_js}
        
        // DID Verification specific JavaScript
        document.addEventListener('DOMContentLoaded', function() {{
            console.log('XRPL Identity Verification Form loaded successfully');
            
            const form = document.getElementById('verificationForm');
            const submitButton = document.getElementById('verifyButton');
            const buttonContent = submitButton.querySelector('.button-content');
            const loadingSpinner = submitButton.querySelector('.loading-spinner');
            
            // Prevent any form submission
            form.addEventListener('submit', function(e) {{
                e.preventDefault();
                e.stopPropagation();
                return false;
            }});
            
            // Handle button click specifically
            submitButton.addEventListener('click', async function(e) {{
                e.preventDefault();
                e.stopPropagation();
                
                // Get form data
                const walletAddress = document.getElementById('walletaddress').value.trim();
                const walletSecret = document.getElementById('walletsecret').value.trim();
                
                // Basic validation
                if (!walletAddress || !walletSecret) {{
                    document.getElementById('errorMessage').textContent = 'Please fill in both wallet address and secret.';
                    showPopup('errorPopup');
                    return;
                }}
                
                // Show loading state
                buttonContent.style.display = 'none';
                loadingSpinner.style.display = 'flex';
                submitButton.disabled = true;
                
                try {{
                    console.log('Calling verification API...');
                    
                    // Call verification endpoint
                    const response = await fetch('/api/verify-identity', {{
                        method: 'POST',
                        headers: {{
                            'Content-Type': 'application/json',
                        }},
                        body: JSON.stringify({{
                            wallet_address: walletAddress,
                            wallet_secret: walletSecret
                        }})
                    }});
                    
                    console.log('API response status:', response.status);
                    
                    const result = await response.json();
                    console.log('Verification result:', result);
                    
                    // Reset button state
                    buttonContent.style.display = 'flex';
                    loadingSpinner.style.display = 'none';
                    submitButton.disabled = false;
                    
                    if (result.identity_verified) {{
                        // Show success popup
                        showPopup('successPopup');
                        
                        // Auto-advance workflow after 2 seconds
                        setTimeout(async () => {{
                            try {{
                                console.log('Advancing workflow...');
                                const advanceResponse = await fetch('/workflow/advance', {{
                                    method: 'POST'
                                }});
                                console.log('Workflow advance response:', advanceResponse.status);
                                
                                if (advanceResponse.ok) {{
                                    // Redirect or reload as needed
                                    window.location.reload();
                                }} else {{
                                    console.error('Failed to advance workflow');
                                }}
                            }} catch (error) {{
                                console.error('Error advancing workflow:', error);
                            }}
                        }}, 2000);
                        
                    }} else {{
                        // Show error popup
                        const errorMessage = result.error || 'Verification failed. Please try again.';
                        document.getElementById('errorMessage').textContent = errorMessage;
                        showPopup('errorPopup');
                    }}
                    
                }} catch (error) {{
                    console.error('Verification error:', error);
                    
                    // Reset button state
                    buttonContent.style.display = 'flex';
                    loadingSpinner.style.display = 'none';
                    submitButton.disabled = false;
                    
                    // Show error popup
                    document.getElementById('errorMessage').textContent = 'Network error. Please check your connection and try again.';
                    showPopup('errorPopup');
                }}
            }});
        }});
        
        function showPopup(popupId) {{
            document.getElementById(popupId).style.display = 'flex';
        }}
        
        function closePopup(popupId) {{
            document.getElementById(popupId).style.display = 'none';
        }}
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


def test_did_verification_generation():
    """Test function to demonstrate DID verification form generation"""
    
    # Create a test DIDVerificationStep
    from backend.states import DIDVerificationConfig, DIDVerificationStep
    
    test_config = DIDVerificationConfig(
        provider="XRPL",
        required_claims=["wallet_ownership"],
        xrpl_network="testnet"
    )
    test_step = DIDVerificationStep(test_config, "escrow_accounts")
    
    # Generate HTML
    html_content = generate_did_verification_form_html(test_step)
    
    # Save to file for testing
    output_file = Path(__file__).parent.parent / "test_did_verification_output.html"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ Test DID verification form generated successfully!")
    print(f"📄 Output saved to: {output_file}")
    print(f"🌐 You can open this file in a browser to see the form")
    
    return html_content


if __name__ == "__main__":
    test_did_verification_generation()
