import json
import os
from pathlib import Path
from typing import Dict, List

from backend.states import EscrowAccountsStep, UserDataCache


def generate_escrow_accounts_form_html(escrow_accounts_step: EscrowAccountsStep, current_user_cache_details: UserDataCache) -> str:
    """
    Generate escrow accounts status page that automatically creates escrow using pre-populated data
    
    Args:
        escrow_accounts_step: EscrowAccountsStep instance containing escrow configuration
    
    Returns:
        str: Complete HTML page as string
    """
    
    # Extract configuration data for automatic escrow creation
    config = escrow_accounts_step.escrow_config
    
    # All data should be available from previous steps
    sender_wallet_address = config.wallet_address or ""
    sender_secret = config.wallet_secret or ""
    sender_email = config.email_address or ""
    recipient_address = current_user_cache_details.wallet_address or ""
    recipient_email = current_user_cache_details.email or ""
    currency_selected = config.currency_option or "XRP"
    loan_amount = current_user_cache_details.get_additional_fields().get('loan_amount', '0.1')
    loan_amount = float(loan_amount)

    
    # Create complete HTML page that automatically creates escrow
    html_page = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>XRPL Escrow Processing - Loan Application</title>
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
            padding: 20px;
            line-height: 1.6;
        }}

        .escrow-container {{
            background: white;
            max-width: 800px;
            width: 100%;
            margin: 0 auto;
            border-radius: 20px;
            box-shadow: 0 25px 50px rgba(0, 0, 0, 0.15);
            overflow: hidden;
            animation: slideUp 0.8s ease-out;
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

        .escrow-header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px 30px;
            text-align: center;
            position: relative;
            overflow: hidden;
        }}

        .escrow-header h1 {{
            font-size: 2rem;
            margin-bottom: 12px;
            font-weight: 700;
        }}

        .escrow-header p {{
            opacity: 0.95;
            font-size: 1.1rem;
            font-weight: 400;
        }}

        .progress-bar {{
            background: rgba(255, 255, 255, 0.2);
            height: 6px;
            border-radius: 3px;
            margin-top: 20px;
            overflow: hidden;
        }}

        .progress-fill {{
            background: #10b981;
            height: 100%;
            width: 80%;
            border-radius: 3px;
            transition: width 0.3s ease;
        }}

        .escrow-content {{
            padding: 0;
        }}

        /* Status Section */
        .status-section {{
            padding: 40px;
            text-align: center;
        }}

        .status-icon {{
            font-size: 4rem;
            margin-bottom: 20px;
            animation: pulse 2s infinite;
        }}

        @keyframes pulse {{
            0% {{ transform: scale(1); }}
            50% {{ transform: scale(1.05); }}
            100% {{ transform: scale(1); }}
        }}

        .status-title {{
            font-size: 1.8rem;
            font-weight: 700;
            color: #374151;
            margin-bottom: 15px;
        }}

        .status-description {{
            font-size: 1.1rem;
            color: #6b7280;
            margin-bottom: 30px;
        }}

        .status-badge {{
            display: inline-block;
            padding: 10px 20px;
            background: #fef3c7;
            color: #d97706;
            border-radius: 20px;
            font-weight: 600;
            margin-bottom: 30px;
        }}

        .status-badge.approved {{
            background: #dcfce7;
            color: #16a34a;
        }}

        .status-badge.rejected {{
            background: #fef2f2;
            color: #dc2626;
        }}

        .status-badge.processing {{
            background: #dbeafe;
            color: #2563eb;
        }}

        /* Loading spinner */
        .loading-spinner {{
            display: inline-block;
            width: 30px;
            height: 30px;
            border: 3px solid rgba(102, 126, 234, 0.3);
            border-top: 3px solid #667eea;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin-right: 15px;
        }}

        @keyframes spin {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}

        /* Email Preview Section */
        .email-preview {{
            background: #f9fafb;
            border: 1px solid #e5e7eb;
            border-radius: 12px;
            padding: 20px;
            margin-top: 30px;
        }}

        .email-preview h3 {{
            font-size: 1.2rem;
            font-weight: 600;
            color: #374151;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
            gap: 10px;
        }}

        .email-content {{
            background: white;
            border: 1px solid #d1d5db;
            border-radius: 8px;
            padding: 15px;
            max-height: 300px;
            overflow-y: auto;
            font-size: 0.9rem;
        }}

        /* Final Action Section */
        .final-action {{
            padding: 40px;
            text-align: center;
            background: #f9fafb;
            display: none;
        }}

        .final-action.show {{
            display: block;
        }}

        .advance-button {{
            padding: 18px 40px;
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
            color: white;
            border: none;
            border-radius: 12px;
            font-size: 1.1rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
        }}

        .advance-button:hover {{
            transform: translateY(-2px);
            box-shadow: 0 15px 35px rgba(16, 185, 129, 0.4);
        }}
    </style>
</head>
<body>
    <div class="escrow-container">
        <div class="escrow-header">
            <h1>🏦 Escrow Account Created</h1>
            <p>Processing your loan application securely</p>
            <div class="progress-bar">
                <div class="progress-fill" id="progressFill"></div>
            </div>
        </div>

        <div class="escrow-content">
            <!-- Status Section -->
            <div class="status-section" id="statusSection">
                <div class="status-icon" id="statusIcon">
                    <span class="loading-spinner"></span>
                </div>
                <h2 class="status-title" id="statusTitle">Creating Escrow Account...</h2>
                <p class="status-description" id="statusDescription">
                    Please wait while we set up your secure escrow account and send the verification email.
                </p>
                <div class="status-badge processing" id="statusBadge">Processing</div>

                <div class="email-preview" id="emailPreview" style="display: none;">
                    <h3>📧 Verification Email Sent</h3>
                    <div class="email-content" id="emailContent">
                        <!-- Email content will be populated here -->
                    </div>
                </div>
            </div>

            <!-- Final Action Section -->
            <div class="final-action" id="finalAction">
                <h2 id="finalTitle">Loan Approved!</h2>
                <p id="finalDescription">Would you like to see the summary of your loan terms?</p>
                <button class="advance-button" onclick="advanceWorkflow()">
                    View Loan Summary
                </button>
            </div>
        </div>
    </div>

    <script>
        let escrowId = null;
        let pollInterval = null;
        let escrowCreationInProgress = false; // Flag to prevent duplicate calls
        let escrowAlreadyCreated = false; // Flag to track if escrow was already created
        
        document.addEventListener('DOMContentLoaded', function() {{
            console.log('🏦 Escrow processing page loaded');
            
            // Check if escrow was already created in this session
            const sessionEscrowId = sessionStorage.getItem('escrowId_"{sender_email}"');
            if (sessionEscrowId) {{
                console.log('🔍 Escrow already exists in session:', sessionEscrowId);
                escrowId = sessionEscrowId;
                escrowAlreadyCreated = true;
                showEscrowCreated({{
                    success: true,
                    escrow_data: {{ escrow_id: sessionEscrowId }},
                    email_verification: {{ email_body: "Previously created escrow found." }}
                }});
                startStatusPolling();
                return;
            }}
            
            // Automatically create escrow on page load if not already created
            setTimeout(() => {{
                if (!escrowCreationInProgress && !escrowAlreadyCreated) {{
                    createEscrowAutomatically();
                }}
            }}, 1500); // Small delay for visual effect
        }});

        async function createEscrowAutomatically() {{
            // Prevent duplicate calls
            if (escrowCreationInProgress || escrowAlreadyCreated) {{
                console.log('🚫 Escrow creation already in progress or completed');
                return;
            }}
            
            escrowCreationInProgress = true;
            
            try {{
                // Get loan amount from cached data
                const loanAmount = await getLoanAmountFromCache();
                const recipientAddress = await getRecipientFromCache();
                
                if (!loanAmount) {{
                    showError("Loan amount not found. Please complete previous steps.");
                    return;
                }}

                // Create escrow data from configuration
                const escrowData = {{
                    sender_secret: "{sender_secret}",
                    sender_wallet_address: "{sender_wallet_address}",
                    recipient_address: "{recipient_address}", // Use configured recipient address
                    sender_email: "{sender_email}",
                    loan_amount: "{loan_amount}",
                    currency: "{currency_selected}"
                }};

                console.log('📤 Creating escrow automatically');

                // Submit to escrow creation endpoint
                const response = await fetch('/api/create-escrow', {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/json',
                    }},
                    body: JSON.stringify(escrowData)
                }});

                const result = await response.json();

                if (result.success) {{
                    escrowId = result.escrow_data?.escrow_id;
                    escrowAlreadyCreated = true;
                    
                    // Store in session to prevent recreation
                    if (escrowId) {{
                        sessionStorage.setItem('escrowId_"{sender_email}"', escrowId);
                    }}
                    
                    showEscrowCreated(result);
                    startStatusPolling();
                }} else {{
                    showError(`Failed to create escrow: ${{result.error || 'Unknown error'}}`);
                }}

            }} catch (error) {{
                console.error('Escrow creation error:', error);
                showError(`Error creating escrow: ${{error.message}}`);
            }} finally {{
                escrowCreationInProgress = false;
            }}
        }}

        async function getLoanAmountFromCache() {{
            try {{
                const response = await fetch(`/api/get-cached-data/${{encodeURIComponent("{sender_email}")}}`);
                const result = await response.json();
                
                if (result.found && result.data) {{
                    return result.data.loan_amount || result.data.amount;
                }}
                return 100; // Default fallback amount
            }} catch (error) {{
                console.error('Error getting loan amount:', error);
                return 100;
            }}
        }}

        async function getRecipientFromCache() {{
            try {{
                const response = await fetch(`/api/get-cached-data/${{encodeURIComponent("{sender_email}")}}`);
                const result = await response.json();
                
                if (result.found && result.data) {{
                    return result.data.recipient_address;
                }}
                return null;
            }} catch (error) {{
                console.error('Error getting recipient:', error);
                return null;
            }}
        }}

        function showEscrowCreated(escrowResult) {{
            // Update status
            document.getElementById('statusIcon').innerHTML = '⏳';
            document.getElementById('statusTitle').textContent = 'Escrow Created Successfully!';
            document.getElementById('statusDescription').textContent = 'Your loan request has been submitted and verification email sent. Please wait for financial institution approval.';
            document.getElementById('statusBadge').textContent = 'In Review';
            document.getElementById('statusBadge').className = 'status-badge';
            
            // Cache verification token for polling
            if (escrowResult.verification_token || escrowResult.email_verification?.verification_token) {{
                const verificationToken = escrowResult.verification_token || escrowResult.email_verification.verification_token;
                cacheVerificationToken(verificationToken);
                console.log('📝 Cached verification token for polling:', verificationToken);
            }}
            
            // Update progress bar
            document.getElementById('progressFill').style.width = '90%';
            
            // Display email content if available
            if (escrowResult.email_verification?.email_body) {{
                document.getElementById('emailContent').innerHTML = escrowResult.email_verification.email_body;
                document.getElementById('emailPreview').style.display = 'block';
            }}
        }}

        async function cacheVerificationToken(verificationToken) {{
            try {{
                // Get current user data
                const response = await fetch(`/api/get-cached-data/${{encodeURIComponent("{sender_email}")}}`);
                const result = await response.json();
                
                let userData = result.found ? result.data : {{}};
                userData.email = "{sender_email}";
                userData.name = userData.name || "User";
                userData.wallet_address = userData.wallet_address || "";
                
                // Initialize verification_tokens array if not exists
                if (!userData.verification_tokens) {{
                    userData.verification_tokens = [];
                }}
                
                // Add verification token (with pending status initially)
                const tokenEntry = {{
                    token: verificationToken,
                    status: "pending",
                    updated_at: new Date().toISOString()
                }};
                
                // Check if token already exists
                const existingIndex = userData.verification_tokens.findIndex(t => t.token === verificationToken);
                if (existingIndex !== -1) {{
                    userData.verification_tokens[existingIndex] = tokenEntry;
                }} else {{
                    userData.verification_tokens.push(tokenEntry);
                }}
                
                // Cache the updated user data
                await fetch('/api/cache-user-data', {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/json',
                    }},
                    body: JSON.stringify(userData)
                }});
                
                console.log('✅ Verification token cached successfully');
                
            }} catch (error) {{
                console.error('❌ Error caching verification token:', error);
            }}
        }}

        function showError(message) {{
            document.getElementById('statusIcon').innerHTML = '❌';
            document.getElementById('statusTitle').textContent = 'Escrow Creation Failed';
            document.getElementById('statusDescription').textContent = message;
            document.getElementById('statusBadge').textContent = 'Error';
            document.getElementById('statusBadge').className = 'status-badge rejected';
        }}

        function startStatusPolling() {{
            if (pollInterval) clearInterval(pollInterval);
            
            pollInterval = setInterval(async () => {{
                await checkEscrowStatus();
            }}, 5000); // Poll every 5 seconds
        }}

        async function checkEscrowStatus() {{
            try {{
                // Directly check user cache for verification tokens
                const response = await fetch(`/api/get-cached-data/${{encodeURIComponent("{sender_email}")}}`);
                const result = await response.json();
                
                if (!result.found || !result.data || !result.data.verification_tokens) {{
                    console.log('🔍 No verification tokens found for user, continuing to poll...');
                    return;
                }}
                
                const verificationTokens = result.data.verification_tokens;
                
                if (verificationTokens.length === 0) {{
                    console.log('🔍 No verification tokens in array, continuing to poll...');
                    return;
                }}
                
                // Sort tokens by updated_at field (latest first)
                const sortedTokens = [...verificationTokens].sort((a, b) => {{
                    const dateA = new Date(a.updated_at || '1970-01-01');
                    const dateB = new Date(b.updated_at || '1970-01-01');
                    return dateB - dateA; // Descending order (latest first)
                }});
                
                const latestToken = sortedTokens[0];
                const tokenStatus = latestToken.status;
                
                console.log(`🔍 Latest verification token status: ${{tokenStatus}} (updated: ${{latestToken.updated_at}})`);
                
                // Check status and trigger appropriate UI flow
                if (tokenStatus === 'approved') {{
                    console.log('✅ Loan approved! Switching to approval flow...');
                    showApprovalSection();
                    stopPolling();
                }} else if (tokenStatus === 'rejected') {{
                    console.log('❌ Loan rejected! Switching to rejection flow...');
                    showRejectionSection();
                    stopPolling();
                }} else {{
                    // Status is 'pending' or something else - remain where we are
                    console.log(`⏳ Token status is '${{tokenStatus}}', continuing to poll...`);
                }}
                
            }} catch (error) {{
                console.error('Error checking escrow status from cache:', error);
                // Continue polling even if there's an error
            }}
        }}

        function showApprovalSection() {{
            // Bright and nice green theme for approval
            document.body.style.background = 'linear-gradient(135deg, #4CAF50 0%, #8BC34A 100%)';
            
            document.getElementById('statusIcon').innerHTML = '🎉';
            document.getElementById('statusTitle').textContent = '🎊 Loan Approved! 🎊';
            document.getElementById('statusDescription').innerHTML = `
                <div style="background: rgba(255,255,255,0.9); padding: 20px; border-radius: 15px; margin: 20px 0; box-shadow: 0 4px 15px rgba(0,0,0,0.1);">
                    <h3 style="color: #2E7D32; margin: 0 0 10px 0;">🎯 Congratulations!</h3>
                    <p style="color: #1B5E20; margin: 0; font-size: 1.1rem; font-weight: 500;">
                        Your microfinance loan application has been <strong>APPROVED</strong> by the financial institution!
                    </p>
                    <p style="color: #2E7D32; margin: 10px 0 0 0; font-size: 0.95rem;">
                        ✅ Funds have been successfully released to your wallet<br>
                        ✅ Transaction has been confirmed on XRPL blockchain<br>
                        ✅ Your loan terms are now active
                    </p>
                </div>
            `;
            document.getElementById('statusBadge').textContent = '✅ APPROVED';
            document.getElementById('statusBadge').className = 'status-badge approved';
            document.getElementById('statusBadge').style.background = '#4CAF50';
            document.getElementById('statusBadge').style.color = 'white';
            document.getElementById('statusBadge').style.fontWeight = 'bold';
            document.getElementById('statusBadge').style.fontSize = '1.1rem';
            document.getElementById('statusBadge').style.padding = '12px 24px';
            document.getElementById('statusBadge').style.borderRadius = '25px';
            document.getElementById('statusBadge').style.boxShadow = '0 4px 15px rgba(76, 175, 80, 0.4)';
            
            document.getElementById('progressFill').style.width = '100%';
            document.getElementById('progressFill').style.background = '#4CAF50';
            
            // Update final action section
            document.getElementById('finalTitle').textContent = '📋 Ready to Review Terms';
            document.getElementById('finalTitle').style.color = '#2E7D32';
            document.getElementById('finalDescription').textContent = 'Your loan has been approved! Review the detailed terms and conditions of your microfinance loan.';
            document.getElementById('finalDescription').style.color = '#1B5E20';
            
            const button = document.querySelector('.advance-button');
            button.textContent = '📋 Summarise Loan Terms';
            button.style.background = 'linear-gradient(135deg, #4CAF50 0%, #8BC34A 100%)';
            button.style.boxShadow = '0 6px 20px rgba(76, 175, 80, 0.4)';
            button.style.fontSize = '1.2rem';
            button.style.padding = '18px 35px';
            
            document.getElementById('finalAction').classList.add('show');
            
            // Add celebration animation
            createCelebrationAnimation();
        }}

        function showRejectionSection() {{
            // Red theme for rejection
            document.body.style.background = 'linear-gradient(135deg, #f44336 0%, #d32f2f 100%)';
            
            document.getElementById('statusIcon').innerHTML = '😞';
            document.getElementById('statusTitle').textContent = '❌ Loan Application Rejected';
            document.getElementById('statusDescription').innerHTML = `
                <div style="background: rgba(255,255,255,0.9); padding: 20px; border-radius: 15px; margin: 20px 0; box-shadow: 0 4px 15px rgba(0,0,0,0.1);">
                    <h3 style="color: #d32f2f; margin: 0 0 10px 0;">📋 Application Status</h3>
                    <p style="color: #b71c1c; margin: 0; font-size: 1.1rem; font-weight: 500;">
                        Unfortunately, your microfinance loan application has been <strong>REJECTED</strong> by the financial institution.
                    </p>
                    <p style="color: #d32f2f; margin: 10px 0 0 0; font-size: 0.95rem;">
                        🔄 Analyse why your loan was rejected and with our models that can suggest improvements<br>
                        📧 Don't worry, you can try again!<br>
                        💡 Consider reviewing and improving your application
                    </p>
                </div>
            `;
            document.getElementById('statusBadge').textContent = '❌ REJECTED';
            document.getElementById('statusBadge').className = 'status-badge rejected';
            document.getElementById('statusBadge').style.background = '#f44336';
            document.getElementById('statusBadge').style.color = 'white';
            document.getElementById('statusBadge').style.fontWeight = 'bold';
            document.getElementById('statusBadge').style.fontSize = '1.1rem';
            document.getElementById('statusBadge').style.padding = '12px 24px';
            document.getElementById('statusBadge').style.borderRadius = '25px';
            document.getElementById('statusBadge').style.boxShadow = '0 4px 15px rgba(244, 67, 54, 0.4)';
            
            document.getElementById('progressFill').style.width = '100%';
            document.getElementById('progressFill').style.background = '#f44336';
            
            // Update final action section
            document.getElementById('finalTitle').textContent = '🔍 Understand Rejection';
            document.getElementById('finalTitle').style.color = '#d32f2f';
            document.getElementById('finalDescription').textContent = 'Learn why your application was rejected and get insights on how to improve your next application.';
            document.getElementById('finalDescription').style.color = '#b71c1c';
            
            const button = document.querySelector('.advance-button');
            button.textContent = '🔍 Analyse Why Loan Was Rejected';
            button.style.background = 'linear-gradient(135deg, #f44336 0%, #d32f2f 100%)';
            button.style.boxShadow = '0 6px 20px rgba(244, 67, 54, 0.4)';
            button.style.fontSize = '1.2rem';
            button.style.padding = '18px 35px';
            
            document.getElementById('finalAction').classList.add('show');
        }}

        function createCelebrationAnimation() {{
            // Add some celebration effects for approval
            const container = document.querySelector('.escrow-container');
            
            // Create floating particles
            for (let i = 0; i < 20; i++) {{
                const particle = document.createElement('div');
                particle.innerHTML = ['🎉', '🎊', '✨', '⭐', '🌟'][Math.floor(Math.random() * 5)];
                particle.style.position = 'fixed';
                particle.style.fontSize = '20px';
                particle.style.left = Math.random() * window.innerWidth + 'px';
                particle.style.top = '-20px';
                particle.style.zIndex = '1000';
                particle.style.pointerEvents = 'none';
                particle.style.animation = `fall ${{2 + Math.random() * 3}}s linear forwards`;
                
                document.body.appendChild(particle);
                
                setTimeout(() => {{
                    particle.remove();
                }}, 5000);
            }}
            
            // Add keyframe animation if not exists
            if (!document.getElementById('celebration-styles')) {{
                const style = document.createElement('style');
                style.id = 'celebration-styles';
                style.textContent = `
                    @keyframes fall {{
                        to {{
                            transform: translateY(${{window.innerHeight + 50}}px) rotate(360deg);
                            opacity: 0;
                        }}
                    }}
                `;
                document.head.appendChild(style);
            }}
        }}

        function stopPolling() {{
            if (pollInterval) {{
                clearInterval(pollInterval);
                pollInterval = null;
            }}
        }}

        async function advanceWorkflow() {{
            try {{
                // Get current verification token status for context
                let escrowContext = {{ escrow_completed: true, escrow_id: escrowId }};
                
                try {{
                    // Use the dedicated verification tokens endpoint
                    const tokensResponse = await fetch(`/api/verification-tokens/${{encodeURIComponent("{sender_email}")}}`);
                    const tokensResult = await tokensResponse.json();
                    
                    if (tokensResult.found && tokensResult.latest_status_token) {{
                        const latestToken = tokensResult.latest_status_token;
                        
                        escrowContext.approval_status = latestToken.status;
                        escrowContext.verification_token = latestToken.token;
                        escrowContext.status_updated_at = latestToken.updated_at;
                        
                        // Add context for next step
                        if (latestToken.status === 'approved') {{
                            escrowContext.next_action = 'summarise_loan_terms';
                            escrowContext.workflow_outcome = 'approved';
                        }} else if (latestToken.status === 'rejected') {{
                            escrowContext.next_action = 'analyse_rejection_reasons';
                            escrowContext.workflow_outcome = 'rejected';
                        }}
                    }}
                }} catch (contextError) {{
                    console.warn('Could not get escrow context:', contextError);
                }}

                const response = await fetch('/workflow/advance', {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/json',
                    }},
                    body: JSON.stringify(escrowContext)
                }});
                
                if (response.ok) {{
                    console.log('✅ Workflow advanced with context:', escrowContext);
                    window.location.reload();
                }} else {{
                    console.error('Failed to advance workflow');
                    alert('Failed to advance workflow. Please try again.');
                }}
                
            }} catch (error) {{
                console.error('Error advancing workflow:', error);
                alert('Error advancing workflow. Please try again.');
            }}
        }}

        window.addEventListener('beforeunload', function() {{
            stopPolling();
        }});
    </script>
</body>
</html>"""
    
    return html_page


def test_escrow_form_generation():
    """Test function to demonstrate escrow form generation"""
    
    # Create a test EscrowAccountsStep
    from backend.states import EscrowAccountsConfig, EscrowAccountsStep
    
    test_config = EscrowAccountsConfig(
        provider="XRPL",
        auto_release=False,
        approval_required=True,
        wallet_address="rTestWallet123...",
        wallet_secret="sTestSecret123...",
        email_address="test@example.com",
        currency_option="XRP"
    )
    test_step = EscrowAccountsStep(test_config, "summarization")
    
    # Generate HTML
    html_content = generate_escrow_accounts_form_html(test_step)
    
    # Save to file for testing
    output_file = Path(__file__).parent / "test_escrow_output.html"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ Test escrow form generated successfully!")
    print(f"📄 Output saved to: {output_file}")
    print(f"🌐 You can open this file in a browser to see the form")
    
    return html_content


if __name__ == "__main__":
    test_escrow_form_generation()
