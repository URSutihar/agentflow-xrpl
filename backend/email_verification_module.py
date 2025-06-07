import hashlib
import json
import os
import secrets
import smtplib
import time
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from urllib.parse import urlencode
from pathlib import Path

from dotenv import load_dotenv
from xrpl.wallet import Wallet

# Import escrow module for integration
try:
    from .escrow_module import (
        XRPLEscrowService,
        create_microfinance_escrow,
        escrow_service,
        CryptoConditions,  # Import crypto-conditions support
    )
    ESCROW_AVAILABLE = True
except ImportError:
    print("⚠️  Warning: Escrow module not available")
    ESCROW_AVAILABLE = False

load_dotenv()

class EmailVerificationService:
    """
    Email verification service for microfinance escrow approvals
    """
    
    def __init__(self, smtp_server="smtp.gmail.com", smtp_port=587):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        # In production, these should be environment variables
        self.sender_email =  os.getenv("SENDER_EMAIL")  # Replace with your email
        self.sender_password = os.getenv("SENDER_PASSWORD")  # Replace with app password
        self.verification_base_url = "http://localhost:8000/verify"  # Your backend URL
        
        # File to store pending verifications (for persistence between processes)
        self.verifications_file = os.path.join(os.path.dirname(__file__), "pending_verifications.json")
        
        # Load existing verifications from file
        self.pending_verifications = self._load_verifications()
    
    def _load_verifications(self):
        """Load pending verifications from file"""
        try:
            # Get absolute path for debugging
            abs_path = os.path.abspath(self.verifications_file)
            print(f"🔍 DEBUG: Loading verifications from: {abs_path}")
            print(f"🔍 DEBUG: File exists: {os.path.exists(self.verifications_file)}")
            
            if os.path.exists(self.verifications_file):
                with open(self.verifications_file, 'r') as f:
                    data = json.load(f)
                    print(f"🔍 DEBUG: Loaded {len(data)} verifications from file")
                    print(f"🔍 DEBUG: Token keys: {list(data.keys())}")
                    return data
            else:
                print(f"🔍 DEBUG: Verifications file does not exist, returning empty dict")
                return {}
        except Exception as e:
            print(f"⚠️  Warning: Could not load verifications file: {e}")
            return {}
    
    def _save_verifications(self):
        """Save pending verifications to file"""
        try:
            abs_path = os.path.abspath(self.verifications_file)
            print(f"🔍 DEBUG: Saving verifications to: {abs_path}")
            print(f"🔍 DEBUG: Saving {len(self.pending_verifications)} verifications")
            
            os.makedirs(os.path.dirname(self.verifications_file), exist_ok=True)
            with open(self.verifications_file, 'w') as f:
                json.dump(self.pending_verifications, f, indent=2)
                
            print(f"✅ DEBUG: Successfully saved verifications to file")
        except Exception as e:
            print(f"⚠️  Warning: Could not save verifications file: {e}")
    
    def _cache_user_verification_token(self, user_email, verification_token, status):
        """
        Cache verification token for user polling by email
        
        Args:
            user_email (str): User's email address
            verification_token (str): Verification token from escrow creation
            status (str): approval status ("approved" or "rejected")
        """
        
        try:
            cache_file = Path(__file__).parent / "current_cached_user_data.json"
            
            # Load existing cache or create new one
            if cache_file.exists():
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
            else:
                cache_data = {}
            
            # Ensure user entry exists
            if user_email not in cache_data:
                cache_data[user_email] = {}
            
            # Initialize verification_tokens list if not exists
            if "verification_tokens" not in cache_data[user_email]:
                cache_data[user_email]["verification_tokens"] = []
            
            # Add new token with status and timestamp
            token_entry = {
                "token": verification_token,
                "status": status,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            
            # Check if token already exists, if so update it
            existing_index = None
            for i, existing_token in enumerate(cache_data[user_email]["verification_tokens"]):
                if existing_token.get("token") == verification_token:
                    existing_index = i
                    break
            
            if existing_index is not None:
                cache_data[user_email]["verification_tokens"][existing_index] = token_entry
                print(f"🔄 Updated existing verification token status for {user_email}: {status}")
            else:
                cache_data[user_email]["verification_tokens"].append(token_entry)
                print(f"➕ Added new verification token for {user_email}: {status}")
            
            # Save back to file
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)
                
            print(f"✅ Cached verification token {verification_token[:8]}... for {user_email}")
            
        except Exception as e:
            print(f"⚠️  Warning: Could not cache verification token: {e}")
    
    def generate_verification_token(self, escrow_data):
        """
        Generate a secure verification token for escrow approval
        
        Args:
            escrow_data (dict): Escrow information
        
        Returns:
            str: Verification token
        """
        token_data = f"{escrow_data.get('escrow_id')}_{escrow_data.get('sender_address')}_{int(time.time())}"
        token = hashlib.sha256(token_data.encode()).hexdigest()[:32]
        return token
    
    def send_escrow_verification_email(self, recipient_email, escrow_data, sender_secret):
        """
        Send email verification for escrow approval
        
        Args:
            recipient_email (str): Email address to send verification to
            escrow_data (dict): Escrow details from escrow creation
            sender_secret (str): Sender's XRPL secret for escrow operations
        
        Returns:
            dict: Email sending result with verification token
        """
        
        # Generate verification token
        verification_token = self.generate_verification_token(escrow_data)
        
        # Store verification data (including fulfillment for conditional escrows)
        verification_entry = {
            "escrow_data": escrow_data,
            "sender_secret": sender_secret,
            "recipient_email": recipient_email,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "status": "pending"
        }
        
        # If this is a conditional escrow, store the fulfillment securely
        if escrow_data.get("escrow_type") == "conditional" or escrow_data.get("condition"):
            verification_entry["condition"] = escrow_data.get("condition")
            verification_entry["fulfillment"] = escrow_data.get("fulfillment")
            verification_entry["escrow_type"] = "conditional"
            print(f"🔐 Stored conditional escrow verification with fulfillment")
        else:
            verification_entry["escrow_type"] = "time_based"
            print(f"⏰ Stored time-based escrow verification")
        
        self.pending_verifications[verification_token] = verification_entry
        
        # Cache verification token for user polling (pending status initially)
        self._cache_user_verification_token(
            user_email=recipient_email,
            verification_token=verification_token,
            status="pending"
        )
        
        # Save to file for persistence
        self._save_verifications()
        print(f"💾 Saved verification token to file: {verification_token}")
        
        # Create verification URLs
        approve_url = f"{self.verification_base_url}/approve?{urlencode({'token': verification_token})}"
        reject_url = f"{self.verification_base_url}/reject?{urlencode({'token': verification_token})}"
        
        # Create email content with conditional escrow information
        escrow_type = verification_entry["escrow_type"]
        subject = f"🏦 Microfinance Escrow Approval Required - {escrow_data.get('amount_xrp', 0)} XRP ({escrow_type.replace('_', ' ').title()})"
        
        # Email sending logic
        email_sent = False
        email_error = None
        
        if self.sender_email and self.sender_password:
            # Try to send actual email
            try:
                # Create HTML email content
                html_body = self._create_html_email_body(escrow_data, verification_token, approve_url, reject_url, recipient_email, escrow_type)
                text_body = self._create_text_email_body(escrow_data, verification_token, approve_url, reject_url, escrow_type)
                
                # Create and send email
                msg = MIMEMultipart('alternative')
                msg['Subject'] = subject
                msg['From'] = self.sender_email
                msg['To'] = recipient_email
                
                msg.attach(MIMEText(text_body, 'plain'))
                msg.attach(MIMEText(html_body, 'html'))
                
                # Send via SMTP
                server = smtplib.SMTP(self.smtp_server, self.smtp_port)
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.sendmail(self.sender_email, recipient_email, msg.as_string())
                server.quit()
                
                email_sent = True
                print(f"✅ Email successfully sent to: {recipient_email}")
                
            except Exception as e:
                email_error = str(e)
                print(f"❌ Failed to send email: {email_error}")
        else:
            print("⚠️  Email credentials not configured. Using mock email.")
        
        # Display email info (whether sent or mock)
        print(f"📧 Subject: {subject}")
        print(f"✅ Approve URL: {approve_url}")
        print(f"❌ Reject URL: {reject_url}")
        
        # Return result
        return {
            "success": True,
            "verification_token": verification_token,
            "approve_url": approve_url,
            "reject_url": reject_url,
            "recipient_email": recipient_email,
            "escrow_id": escrow_data.get('escrow_id'),
            "escrow_type": escrow_type,
            "status": "email_sent" if email_sent else "mock_email",
            "email_error": email_error
        }
    
    def _create_html_email_body(self, escrow_data, verification_token, approve_url, reject_url, recipient_email, escrow_type):
        """Create HTML email body"""
        
        # Conditional escrow specific information
        escrow_explanation = ""
        timing_info = ""
        
        if escrow_type == "conditional":
            escrow_explanation = """
            <div style="background-color: #e8f5e8; border: 1px solid #4CAF50; padding: 15px; border-radius: 5px; margin: 15px 0;">
                <h4 style="margin-top: 0; color: #2e7d32;">🔐 Conditional Escrow</h4>
                <p><strong>This is a conditional escrow</strong> - the funds are immediately available for release upon your approval.</p>
                <p>✅ <strong>Approval:</strong> Instant release when you click "Approve"</p>
                <p>❌ <strong>Rejection:</strong> Immediate rejection recording - funds return within 72 hours</p>
                <p>🔒 <strong>Secure crypto-condition</strong> - only your email approval can release the funds</p>
            </div>
            """
            timing_info = f"""
            <tr style="border-bottom: 1px solid #ddd;">
                <td style="padding: 8px; font-weight: bold;">Escrow Type:</td>
                <td style="padding: 8px; color: #4CAF50; font-weight: bold;">Conditional (Immediate Release)</td>
            </tr>
            <tr style="border-bottom: 1px solid #ddd;">
                <td style="padding: 8px; font-weight: bold;">Expires After:</td>
                <td style="padding: 8px;">{escrow_data.get('can_cancel_at', 'N/A')}</td>
            </tr>
            """
        else:
            escrow_explanation = """
            <div style="background-color: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 5px; margin: 15px 0;">
                <h4 style="margin-top: 0; color: #856404;">⏰ Time-Based Escrow</h4>
                <p><strong>This is a time-based escrow</strong> - the funds will be available for release after a specific time.</p>
                <p>🕒 <strong>Release time:</strong> {escrow_data.get('can_finish_at', 'N/A')}</p>
            </div>
            """
            timing_info = f"""
            <tr style="border-bottom: 1px solid #ddd;">
                <td style="padding: 8px; font-weight: bold;">Escrow Type:</td>
                <td style="padding: 8px; color: #ff9800; font-weight: bold;">Time-Based</td>
            </tr>
            <tr style="border-bottom: 1px solid #ddd;">
                <td style="padding: 8px; font-weight: bold;">Can Release After:</td>
                <td style="padding: 8px;">{escrow_data.get('can_finish_at', 'N/A')}</td>
            </tr>
            """
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #4CAF50; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background-color: #f9f9f9; }}
                .escrow-details {{ background-color: white; padding: 15px; border-radius: 5px; margin: 15px 0; }}
                .button {{ display: inline-block; padding: 12px 24px; margin: 10px; text-decoration: none; border-radius: 5px; font-weight: bold; text-align: center; }}
                .approve {{ background-color: #4CAF50; color: white; }}
                .reject {{ background-color: #f44336; color: white; }}
                .warning {{ background-color: #fff3cd; border: 1px solid #ffeaa7; padding: 10px; border-radius: 5px; margin: 15px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🏦 Microfinance Escrow Approval</h1>
                    <p>XRPL Testnet - {escrow_type.replace('_', ' ').title()} Escrow</p>
                </div>
                
                <div class="content">
                    <h2>Escrow Verification Required</h2>
                    <p>A microfinance escrow has been created and requires your approval to release funds.</p>
                    
                    {escrow_explanation}
                    
                    <div class="escrow-details">
                        <h3>📋 Escrow Details</h3>
                        <table style="width: 100%; border-collapse: collapse;">
                            <tr style="border-bottom: 1px solid #ddd;">
                                <td style="padding: 8px; font-weight: bold;">Escrow ID:</td>
                                <td style="padding: 8px;">{escrow_data.get('escrow_id', 'N/A')}</td>
                            </tr>
                            <tr style="border-bottom: 1px solid #ddd;">
                                <td style="padding: 8px; font-weight: bold;">Amount:</td>
                                <td style="padding: 8px; color: #4CAF50; font-weight: bold;">{escrow_data.get('amount_xrp', 0)} XRP</td>
                            </tr>
                            <tr style="border-bottom: 1px solid #ddd;">
                                <td style="padding: 8px; font-weight: bold;">Sender:</td>
                                <td style="padding: 8px; font-family: monospace;">{escrow_data.get('sender_address', 'N/A')}</td>
                            </tr>
                            <tr style="border-bottom: 1px solid #ddd;">
                                <td style="padding: 8px; font-weight: bold;">Recipient:</td>
                                <td style="padding: 8px; font-family: monospace;">{escrow_data.get('recipient_address', 'N/A')}</td>
                            </tr>
                            <tr style="border-bottom: 1px solid #ddd;">
                                <td style="padding: 8px; font-weight: bold;">Application ID:</td>
                                <td style="padding: 8px;">{escrow_data.get('application_id', 'N/A')}</td>
                            </tr>
                            {timing_info}
                            <tr>
                                <td style="padding: 8px; font-weight: bold;">Transaction Hash:</td>
                                <td style="padding: 8px; font-family: monospace; font-size: 12px;">{escrow_data.get('transaction_hash', 'N/A')}</td>
                            </tr>
                        </table>
                    </div>
                    
                    <div class="warning">
                        <strong>⚠️ Important:</strong> The funds have already been deducted from your wallet and are held in escrow. 
                        Approving will release them to the recipient. Rejecting will return them to you.
                    </div>
                    
                    <h3>Choose an Action:</h3>
                    <div style="text-align: center; margin: 20px 0;">
                        <a href="{approve_url}" class="button approve">✅ Approve & Release Funds</a>
                        <a href="{reject_url}" class="button reject">❌ Reject & Return Funds</a>
                    </div>
                    
                    <div style="margin-top: 30px; padding: 15px; background-color: #e3f2fd; border-radius: 5px;">
                        <h4>🔍 Verification Details</h4>
                        <p><strong>Verification Token:</strong> <code>{verification_token}</code></p>
                        <p><strong>Created:</strong> {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
                        <p><strong>Network:</strong> XRPL Testnet</p>
                        <p><strong>Escrow Type:</strong> {escrow_type.replace('_', ' ').title()}</p>
                    </div>
                    
                    <div style="margin-top: 20px; font-size: 12px; color: #666;">
                        <p><strong>Security Note:</strong> This email was sent to {recipient_email}. 
                        If you did not initiate this escrow, please do not click any links and contact support.</p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
    
    def _create_text_email_body(self, escrow_data, verification_token, approve_url, reject_url, escrow_type):
        """Create plain text email body"""
        
        escrow_type_info = ""
        if escrow_type == "conditional":
            escrow_type_info = f"""
CONDITIONAL ESCROW - APPROVAL: INSTANT | REJECTION: IMMEDIATE
✅ Approval: Instant release when you click the approval link
❌ Rejection: Immediate rejection recording - funds return within 72 hours
🔒 Secure crypto-condition - only your email approval can release funds
            """
        else:
            escrow_type_info = f"""
TIME-BASED ESCROW
🕒 Release time: {escrow_data.get('can_finish_at', 'N/A')}
            """
        
        return f"""
        MICROFINANCE ESCROW APPROVAL REQUIRED
        
        Escrow Type: {escrow_type.replace('_', ' ').title()}
        {escrow_type_info}
        
        Escrow Details:
        - Escrow ID: {escrow_data.get('escrow_id', 'N/A')}
        - Amount: {escrow_data.get('amount_xrp', 0)} XRP
        - Sender: {escrow_data.get('sender_address', 'N/A')}
        - Recipient: {escrow_data.get('recipient_address', 'N/A')}
        - Application ID: {escrow_data.get('application_id', 'N/A')}
        
        Actions:
        Approve: {approve_url}
        Reject: {reject_url}
        
        Verification Token: {verification_token}
        Network: XRPL Testnet
        """
    
    def get_account_balance(self, wallet_address):
        """
        Get current XRP balance for an account
        
        Args:
            wallet_address (str): XRPL wallet address
        
        Returns:
            dict: Balance information
        """
        if not ESCROW_AVAILABLE:
            return {"balance_xrp": 0, "balance_drops": "0", "error": "XRPL not available"}
        
        try:
            from xrpl.clients import JsonRpcClient
            from xrpl.models.requests import AccountInfo
            from xrpl.utils import drops_to_xrp
            
            client = JsonRpcClient("https://s.altnet.rippletest.net:51234/")
            account_info = AccountInfo(account=wallet_address)
            
            # Use synchronous request to avoid event loop conflicts
            try:
                response = client.request(account_info)
            except Exception as request_error:
                # If the request method has issues, return a simpler response
                print(f"⚠️  Balance check failed: {request_error}")
                return {"balance_xrp": "Unknown", "balance_drops": "Unknown", "error": "Balance check failed"}
            
            if response.is_successful():
                balance_drops = response.result['account_data']['Balance']
                balance_xrp = float(drops_to_xrp(balance_drops))
                return {
                    "balance_xrp": balance_xrp,
                    "balance_drops": balance_drops,
                    "success": True
                }
            else:
                return {"balance_xrp": 0, "balance_drops": "0", "error": "Account not found"}
                
        except Exception as e:
            print(f"⚠️  Balance check error: {e}")
            return {"balance_xrp": "Unknown", "balance_drops": "Unknown", "error": str(e)}
    
    def log_balance_changes(self, escrow_data, transaction_type, transaction_hash=None):
        """
        Log balance changes before and after escrow operations
        
        Args:
            escrow_data (dict): Escrow information
            transaction_type (str): "approve" or "reject"
            transaction_hash (str, optional): XRPL transaction hash
        
        Returns:
            dict: Balance change log
        """
        sender_address = escrow_data.get("sender_address")
        recipient_address = escrow_data.get("recipient_address")
        amount_xrp = escrow_data.get("amount_xrp", 0)
        
        # Get current balances (now synchronous)
        sender_balance = self.get_account_balance(sender_address)
        recipient_balance = self.get_account_balance(recipient_address)
        
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "transaction_type": transaction_type,
            "application_id": escrow_data.get("application_id"),
            "escrow_id": escrow_data.get("escrow_id"),
            "amount_xrp": amount_xrp,
            "transaction_hash": transaction_hash,
            "balances": {
                "sender": {
                    "address": sender_address,
                    "balance_xrp": sender_balance.get("balance_xrp", 0),
                    "balance_drops": sender_balance.get("balance_drops", "0")
                },
                "recipient": {
                    "address": recipient_address,
                    "balance_xrp": recipient_balance.get("balance_xrp", 0),
                    "balance_drops": recipient_balance.get("balance_drops", "0")
                }
            }
        }
        
        # Log to console (in production, save to database/file)
        print("\n" + "="*60)
        print(f"📊 BALANCE UPDATE LOG - {transaction_type.upper()}")
        print("="*60)
        print(f"⏰ Timestamp: {log_entry['timestamp']}")
        print(f"🆔 Application ID: {log_entry['application_id']}")
        print(f"🔐 Escrow ID: {log_entry['escrow_id']}")
        print(f"💰 Amount: {amount_xrp} XRP")
        print(f"🔗 Transaction Hash: {transaction_hash or 'N/A'}")
        print(f"\n💳 CURRENT BALANCES:")
        print(f"   Sender ({sender_address}): {sender_balance.get('balance_xrp', 0)} XRP")
        print(f"   Recipient ({recipient_address}): {recipient_balance.get('balance_xrp', 0)} XRP")
        
        if transaction_type == "approve":
            print(f"\n✅ FUNDS RELEASED:")
            print(f"   → {amount_xrp} XRP transferred from escrow to {recipient_address}")
        else:
            print(f"\n🔄 FUNDS RETURNED:")
            print(f"   → {amount_xrp} XRP returned from escrow to {sender_address}")
        
        print("="*60 + "\n")
        
        return log_entry
    
    def verify_and_approve_escrow(self, verification_token):
        """
        Verify token and approve/release escrow
        
        Args:
            verification_token (str): Verification token from email
            
        Returns:
            dict: Approval result with transaction details
        """
        
        print(f"🔍 Attempting to verify and approve escrow with token: {verification_token}")
        
        # Reload verifications from file to get latest data
        self.pending_verifications = self._load_verifications()
        
        # Check if token exists
        if verification_token not in self.pending_verifications:
            print(f"❌ Token not found: {verification_token}")
            return {
                "success": False,
                "error": "Invalid or expired verification token",
                "token": verification_token
            }
        
        verification_data = self.pending_verifications[verification_token]
        
        # Check if already processed
        if verification_data.get("status") != "pending":
            print(f"❌ Token already processed: {verification_data.get('status')}")
            return {
                "success": False,
                "error": f"Verification already processed with status: {verification_data.get('status')}",
                "token": verification_token
            }
        
        # Get escrow data
        escrow_data = verification_data["escrow_data"]
        sender_secret = verification_data["sender_secret"]
        escrow_type = verification_data.get("escrow_type", "time_based")
        
        print(f"🏦 Processing {escrow_type} escrow approval")
        print(f"🆔 Escrow ID: {escrow_data.get('escrow_id')}")
        
        # Handle conditional vs time-based escrows differently
        try:
            if escrow_type == "conditional":
                # For conditional escrows, use the stored fulfillment
                condition = verification_data.get("condition")
                fulfillment = verification_data.get("fulfillment")
                
                if not condition or not fulfillment:
                    print(f"❌ Missing condition/fulfillment for conditional escrow")
                    return {
                        "success": False,
                        "error": "Missing crypto-condition data for conditional escrow",
                        "token": verification_token
                    }
                
                print(f"🔐 Using conditional escrow release with fulfillment")
                
                # Create wallet from secret for conditional escrow finish
                sender_wallet = Wallet.from_seed(sender_secret)
                
                result = escrow_service.finish_conditional_escrow(
                    sender_wallet=sender_wallet,  # Use wallet object, not secret string
                    recipient_address=escrow_data.get('recipient_address'),
                    escrow_sequence=escrow_data.get('escrow_id'),  # Use escrow_sequence parameter name
                    condition=condition,  # Include condition parameter
                    fulfillment=fulfillment
                )
                
            else:
                # For time-based escrows, use the standard finish method
                print(f"⏰ Using time-based escrow release")
                
                # Create wallet from secret for time-based escrow finish
                sender_wallet = Wallet.from_seed(sender_secret)
                
                result = escrow_service.finish_escrow(
                    sender_wallet=sender_wallet,  # Use wallet object, not secret string
                    recipient_address=escrow_data.get('recipient_address'),
                    escrow_sequence=escrow_data.get('escrow_id')  # Use escrow_sequence parameter name
                )
            
            if result.get('success'):
                # Mark as approved
                verification_data["status"] = "approved"
                verification_data["approval_status"] = "approved"  # New tracking field
                verification_data["approved_at"] = datetime.now(timezone.utc).isoformat()
                verification_data["finish_result"] = result
                
                # Cache verification token for user polling
                self._cache_user_verification_token(
                    user_email=verification_data.get("recipient_email"),
                    verification_token=verification_token,
                    status="approved"
                )
                
                # Save to file
                self._save_verifications()
                
                print(f"✅ Escrow successfully approved and released!")
                print(f"💰 Amount: {escrow_data.get('amount_xrp')} XRP")
                print(f"📊 Transaction Hash: {result.get('transaction_hash')}")
                
                return {
                    "success": True,
                    "message": "Escrow successfully approved and funds released!",
                    "escrow_id": escrow_data.get('escrow_id'),
                    "escrow_type": escrow_type,
                    "amount_xrp": escrow_data.get('amount_xrp'),
                    "transaction_hash": result.get('transaction_hash'),
                    "recipient_address": escrow_data.get('recipient_address'),
                    "approved_at": verification_data["approved_at"],
                    "token": verification_token
                }
            else:
                print(f"❌ Escrow release failed: {result.get('error')}")
                return {
                    "success": False,
                    "error": f"Failed to release escrow: {result.get('error')}",
                    "escrow_id": escrow_data.get('escrow_id'),
                    "escrow_type": escrow_type,
                    "token": verification_token
                }
                
        except Exception as e:
            print(f"❌ Error during escrow approval: {str(e)}")
            verification_data["status"] = "error"
            verification_data["error"] = str(e)
            verification_data["error_at"] = datetime.now(timezone.utc).isoformat()
            self._save_verifications()
            
            return {
                "success": False,
                "error": f"Error during escrow approval: {str(e)}",
                "escrow_id": escrow_data.get('escrow_id'),
                "escrow_type": escrow_type,
                "token": verification_token
            }
    
    def verify_and_reject_escrow(self, verification_token):
        """
        Verify token and reject/cancel escrow
        
        Args:
            verification_token (str): Verification token from email
            
        Returns:
            dict: Rejection result with transaction details
        """
        
        print(f"🔍 Attempting to verify and reject escrow with token: {verification_token}")
        
        # Reload verifications from file to get latest data
        self.pending_verifications = self._load_verifications()
        
        # Check if token exists
        if verification_token not in self.pending_verifications:
            print(f"❌ Token not found: {verification_token}")
            return {
                "success": False,
                "error": "Invalid or expired verification token",
                "token": verification_token
            }
        
        verification_data = self.pending_verifications[verification_token]
        
        # Check if already processed
        if verification_data.get("status") != "pending":
            print(f"❌ Token already processed: {verification_data.get('status')}")
            return {
                "success": False,
                "error": f"Verification already processed with status: {verification_data.get('status')}",
                "token": verification_token
            }
        
        # Get escrow data
        escrow_data = verification_data["escrow_data"]
        sender_secret = verification_data["sender_secret"]
        escrow_type = verification_data.get("escrow_type", "time_based")
        
        print(f"🏦 Processing {escrow_type} escrow rejection")
        print(f"🆔 Escrow ID: {escrow_data.get('escrow_id')}")
        
        # Handle conditional vs time-based escrows differently
        try:
            # For both escrow types, we'll mark as rejected but not immediately cancel
            # The escrow will auto-expire after the CancelAfter time (72 hours)
            print(f"🔐 Recording rejection for {escrow_type} escrow (funds will return after auto-expiry)")
            
            # Mark as rejected immediately (don't wait for actual cancellation)
            verification_data["status"] = "rejected"
            verification_data["approval_status"] = "rejected"  # New tracking field
            verification_data["rejected_at"] = datetime.now(timezone.utc).isoformat()
            verification_data["rejection_method"] = "email_rejection_immediate"
            verification_data["funds_return_info"] = {
                "return_method": "auto_expiry",
                "estimated_return_time": escrow_data.get('can_cancel_at'),
                "return_hours": escrow_data.get('expires_in_hours', 72)
            }
            
            # Cache verification token for user polling
            self._cache_user_verification_token(
                user_email=verification_data.get("recipient_email"),
                verification_token=verification_token,
                status="rejected"
            )
            
            # Save to file
            self._save_verifications()
            
            print(f"✅ Rejection recorded successfully!")
            print(f"💰 Amount: {escrow_data.get('amount_xrp')} XRP will return via auto-expiry")
            print(f"⏰ Estimated return time: {escrow_data.get('can_cancel_at')}")
            
            return {
                "success": True,
                "message": "Rejection recorded successfully! Funds will return to sender within 72 hours.",
                "escrow_id": escrow_data.get('escrow_id'),
                "escrow_type": escrow_type,
                "amount_xrp": escrow_data.get('amount_xrp'),
                "rejection_method": "immediate_recording",
                "funds_return_method": "auto_expiry_after_72_hours",
                "estimated_return_time": escrow_data.get('can_cancel_at'),
                "sender_address": escrow_data.get('sender_address'),
                "rejected_at": verification_data["rejected_at"],
                "token": verification_token
            }
                
        except Exception as e:
            print(f"❌ Error during escrow rejection: {str(e)}")
            verification_data["status"] = "error"
            verification_data["error"] = str(e)
            verification_data["error_at"] = datetime.now(timezone.utc).isoformat()
            self._save_verifications()
            
            return {
                "success": False,
                "error": f"Error during escrow rejection: {str(e)}",
                "escrow_id": escrow_data.get('escrow_id'),
                "escrow_type": escrow_type,
                "token": verification_token
            }

# Global email verification service
email_service = EmailVerificationService()

# Integration function for microfinance workflow
def create_escrow_with_email_verification(sender_secret, recipient_address, amount_xrp, 
                                        sender_email, application_id=None, hold_hours=0, use_conditional=True):
    """
    Create escrow and send email verification
    
    Args:
        sender_secret (str): Sender's XRPL secret
        recipient_address (str): Recipient's wallet address
        amount_xrp (float): Amount in XRP
        sender_email (str): Email for verification
        application_id (str, optional): Application ID
        hold_hours (int): Hold duration (default: 0 = immediate release for time-based, ignored for conditional)
        use_conditional (bool): Whether to use conditional escrow (default: True)
    
    Returns:
        dict: Combined escrow creation and email verification result
    """
    
    print(f"🏦 Creating escrow with email verification...")
    print(f"📧 Email: {sender_email}")
    print(f"💰 Amount: {amount_xrp} XRP")
    print(f"📍 Recipient: {recipient_address}")
    print(f"🔐 Escrow type: {'Conditional' if use_conditional else 'Time-based'}")
    
    try:
        if use_conditional:
            # Create conditional escrow (immediate release with crypto-condition)
            print(f"🔐 Creating conditional escrow with 72-hour auto-expiry...")
            
            # Create wallet from secret for conditional escrow
            sender_wallet = Wallet.from_seed(sender_secret)
            
            escrow_result = escrow_service.create_conditional_escrow(
                sender_wallet=sender_wallet,  # Use wallet object, not secret string
                recipient_address=recipient_address,
                amount_xrp=amount_xrp,
                cancel_hours=72,  # 72 hours for auto-expiry (rejections recorded immediately)
                memo=f"Microfinance loan: {application_id}" if application_id else None
            )
        else:
            # Create time-based escrow (backward compatibility)
            print(f"⏰ Creating time-based escrow with {hold_hours} hour hold...")
            escrow_result = create_microfinance_escrow(
                sender_secret=sender_secret,
                recipient_address=recipient_address,
                amount_xrp=amount_xrp,
                application_id=application_id,
                hold_hours=hold_hours
            )
        
        if not escrow_result.get("success"):
            return {
                "success": False,
                "error": f"Escrow creation failed: {escrow_result.get('error', 'Unknown error')}",
                "escrow_result": escrow_result
            }
        
        print(f"✅ Escrow created successfully!")
        print(f"🆔 Escrow ID: {escrow_result.get('escrow_id')}")
        print(f"📊 Transaction Hash: {escrow_result.get('transaction_hash')}")
        
        # Send email verification
        email_service = EmailVerificationService()
        email_result = email_service.send_escrow_verification_email(
            recipient_email=sender_email,
            escrow_data=escrow_result,
            sender_secret=sender_secret
        )
        
        if email_result.get("success"):
            print(f"✅ Email verification sent successfully!")
            return {
                "success": True,
                "message": "Escrow created and email verification sent!",
                "escrow_result": escrow_result,
                "email_result": email_result,
                "escrow_id": escrow_result.get('escrow_id'),
                "escrow_type": "conditional" if use_conditional else "time_based",
                "verification_token": email_result.get('verification_token'),
                "approve_url": email_result.get('approve_url'),
                "reject_url": email_result.get('reject_url')
            }
        else:
            return {
                "success": False,
                "error": "Escrow created but email verification failed",
                "escrow_result": escrow_result,
                "email_result": email_result
            }
            
    except Exception as e:
        print(f"❌ Error in escrow creation with email verification: {str(e)}")
        return {
            "success": False,
            "error": f"Escrow creation failed: {str(e)}"
        }

if __name__ == "__main__":
    def main():
        print("=== Email Verification Module Test ===\n")
        
        # Test parameters
        sender_secret = os.getenv("TEST_SENDER_SECRET")
        sender_address = os.getenv("TEST_SENDER_WALLET_ADDRESS")
        recipient_address = os.getenv("TEST_RECIPIENT_WALLET_ADDRESS")
        sender_email = os.getenv("SENDER_EMAIL")
        loan_amount = 0.1  # Reduced from 3.0 to 0.1 for testing
        
        print("📧 Email Verification Test Parameters:")
        print(f"  Sender: {sender_address}")
        print(f"  Recipient: {recipient_address}")
        print(f"  Amount: {loan_amount} XRP")
        print(f"  Email: {sender_email}")
        
        print("Creating escrow with email verification...")
        result = create_escrow_with_email_verification(
            sender_secret=sender_secret,
            recipient_address=recipient_address,
            amount_xrp=loan_amount,
            sender_email=sender_email,
            application_id="MF2024002",
            hold_hours=0,  # Ignored for conditional escrows
            use_conditional=True  # Test conditional escrow (default)
        )
        
        if result.get("success"):
            print("✅ Escrow created and email sent!")
            print(f"  Escrow ID: {result.get('escrow_id')}")
            print(f"  Escrow Type: {result.get('escrow_type')}")
            print(f"  Verification Token: {result.get('verification_token')}")
            print(f"  Approve URL: {result.get('approve_url')}")
            print(f"  Reject URL: {result.get('reject_url')}")
            print(f"  Transaction Hash: {result.get('escrow_result', {}).get('transaction_hash')}")
        else:
            print("❌ Process failed:")
            print(f"  Error: {result.get('error')}")
        
        print("\n=== Complete Workflow Integration ===")
        print("1. ✅ XRPL Wallet Verification")
        print("2. ✅ Escrow Creation (funds locked)")
        print("3. ✅ Email Verification Sent")
        print("4. 🔲 User clicks approve/reject in email")
        print("5. 🔲 Funds released or returned automatically")

    # Run the main function (no longer async)
    main() 