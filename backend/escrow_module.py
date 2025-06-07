import json
import secrets
import time
import hashlib
from datetime import datetime, timedelta, timezone

import xrpl
from xrpl.clients import JsonRpcClient
from xrpl.models.requests import AccountInfo, AccountTx
from xrpl.models.transactions import EscrowCancel, EscrowCreate, EscrowFinish
from xrpl.transaction import sign, submit_and_wait
from xrpl.utils import drops_to_xrp, xrp_to_drops
from xrpl.wallet import Wallet

try:
    XRPL_AVAILABLE = True
    print("✅ XRPL library loaded for escrow operations")
except ImportError as e:
    print(f"⚠️  Warning: XRPL library import failed: {e}")
    print("Install with: poetry add xrpl-py")
    XRPL_AVAILABLE = False
except Exception as e:
    print(f"⚠️  Warning: XRPL library loaded but initialization failed: {e}")
    XRPL_AVAILABLE = False

class CryptoConditions:
    """
    Crypto-conditions implementation for XRPL escrows
    Implements PREIMAGE-SHA-256 crypto-conditions
    """
    
    @staticmethod
    def generate_condition_and_fulfillment():
        """
        Generate a PREIMAGE-SHA-256 crypto-condition and its fulfillment
        
        Returns:
            dict: Contains condition, fulfillment, and preimage_data
        """
        
        # Generate 32 random bytes for the preimage
        preimage_data = secrets.token_bytes(32)
        
        # Calculate SHA-256 hash of the preimage
        condition_hash = hashlib.sha256(preimage_data).digest()
        
        # Create condition in ASN.1 DER format for PREIMAGE-SHA-256
        # Format: A0258020 + <32-byte hash> + 810120
        condition = "A0258020" + condition_hash.hex().upper() + "810120"
        
        # Create fulfillment in ASN.1 DER format for PREIMAGE-SHA-256
        # Format: A0228020 + <32-byte preimage>
        fulfillment = "A0228020" + preimage_data.hex().upper()
        
        return {
            "condition": condition,
            "fulfillment": fulfillment,
            "preimage_data": preimage_data.hex().upper(),
            "condition_hash": condition_hash.hex().upper()
        }
    
    @staticmethod
    def validate_fulfillment(condition, fulfillment):
        """
        Validate that a fulfillment satisfies a condition
        
        Args:
            condition (str): The condition string
            fulfillment (str): The fulfillment string
        
        Returns:
            bool: True if fulfillment satisfies condition
        """
        
        try:
            # Extract hash from condition (skip A0258020, take 32 bytes, skip 810120)
            if not condition.startswith("A0258020") or not condition.endswith("810120"):
                return False
            
            expected_hash = condition[8:72]  # 32 bytes = 64 hex chars
            
            # Extract preimage from fulfillment (skip A0228020, take 32 bytes)
            if not fulfillment.startswith("A0228020"):
                return False
            
            preimage = fulfillment[8:72]  # 32 bytes = 64 hex chars
            
            # Calculate hash of preimage
            preimage_bytes = bytes.fromhex(preimage)
            calculated_hash = hashlib.sha256(preimage_bytes).hexdigest().upper()
            
            return calculated_hash == expected_hash
            
        except Exception as e:
            print(f"⚠️ Validation error: {e}")
            return False

class XRPLEscrowService:
    """
    XRPL Escrow Service for microfinance applications with crypto-conditions support
    """
    
    def __init__(self, network_url="https://s.altnet.rippletest.net:51234/"):
        self.network_url = network_url
        self.client = None
        if XRPL_AVAILABLE:
            self.client = JsonRpcClient(network_url)
    
    def create_conditional_escrow(self, sender_wallet, recipient_address, amount_xrp, 
                                cancel_hours=72, memo=None):
        """
        Create a conditional escrow that can only be released with the correct fulfillment
        
        Args:
            sender_wallet (Wallet): XRPL wallet object for the sender (escrow creator)
            recipient_address (str): Recipient's XRPL wallet address
            amount_xrp (float): Amount in XRP to escrow
            cancel_hours (float): Hours after which escrow auto-expires (default: 72 hours)
            memo (str, optional): Optional memo for the escrow
        
        Returns:
            dict: Escrow creation result with condition and fulfillment details
        """
        
        if not XRPL_AVAILABLE or not self.client:
            return {
                "success": False,
                "error": "XRPL client not available",
                "mock_data": {
                    "escrow_id": f"MOCK_CONDITIONAL_ESCROW_{secrets.token_hex(8)}",
                    "amount": amount_xrp,
                    "recipient": recipient_address,
                    "status": "mock_conditional_created"
                }
            }
        
        try:
            # Generate crypto-condition and fulfillment
            crypto_data = CryptoConditions.generate_condition_and_fulfillment()
            
            # Calculate cancel time (72 hours from now by default)
            # Ripple Epoch = Unix Epoch - 946684800 (Jan 1, 2000 vs Jan 1, 1970)
            current_unix_time = time.time()
            cancel_unix_time = current_unix_time + (cancel_hours * 3600)
            cancel_after = int(cancel_unix_time - 946684800)
            
            # Debug prints to verify calculations
            print(f"🔍 DEBUG CONDITIONAL ESCROW:")
            print(f"   Current Unix time: {current_unix_time}")
            print(f"   Cancel hours: {cancel_hours}")
            print(f"   Cancel after (Ripple format): {cancel_after}")
            print(f"   Cancel time: {datetime.fromtimestamp(cancel_unix_time).strftime('%Y-%m-%d %H:%M:%S UTC')}")
            print(f"   Condition: {crypto_data['condition']}")
            print(f"   Fulfillment: {crypto_data['fulfillment'][:20]}...")
            
            # Convert XRP to drops (1 XRP = 1,000,000 drops)
            amount_drops = xrp_to_drops(amount_xrp)
            
            # Create memo if provided
            memos = []
            if memo:
                from xrpl.models.transactions import Memo
                memos = [Memo(memo_data=memo.encode().hex().upper())]
            
            # Create the conditional escrow transaction
            escrow_tx = EscrowCreate(
                account=sender_wallet.address,
                destination=recipient_address,
                amount=amount_drops,
                condition=crypto_data['condition'],  # Use crypto-condition instead of time
                cancel_after=cancel_after,  # Can be cancelled after this time
                memos=memos if memos else None
            )
            
            # Submit the transaction
            response = submit_and_wait(escrow_tx, self.client, sender_wallet)
            
            if response.is_successful():
                # Extract escrow sequence number (used as escrow ID)
                escrow_sequence = response.result.get('Sequence', 0)
                
                return {
                    "success": True,
                    "escrow_id": escrow_sequence,
                    "transaction_hash": response.result.get('hash'),
                    "sender_address": sender_wallet.address,
                    "recipient_address": recipient_address,
                    "amount_xrp": amount_xrp,
                    "amount_drops": amount_drops,
                    "condition": crypto_data['condition'],
                    "fulfillment": crypto_data['fulfillment'],
                    "preimage_data": crypto_data['preimage_data'],
                    "cancel_after_timestamp": cancel_after,
                    "cancel_after_datetime": datetime.fromtimestamp(cancel_unix_time).isoformat(),
                    "cancel_hours": cancel_hours,
                    "memo": memo,
                    "status": "conditional_escrow_created",
                    "escrow_type": "conditional",
                    "can_cancel_at": datetime.fromtimestamp(cancel_unix_time).strftime("%Y-%m-%d %H:%M:%S UTC"),
                    "immediately_releasable": True,  # With correct fulfillment
                    "expires_in_hours": cancel_hours,
                    "expires_in_days": round(cancel_hours / 24, 1),  # More meaningful for longer durations
                    "rejection_available_after": datetime.fromtimestamp(cancel_unix_time).strftime("%Y-%m-%d %H:%M:%S UTC")
                }
            else:
                return {
                    "success": False,
                    "error": f"Transaction failed: {response.result}",
                    "transaction_response": response.result
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Conditional escrow creation failed: {str(e)}"
            }
    
    def finish_conditional_escrow(self, sender_wallet, recipient_address, escrow_sequence, 
                                condition, fulfillment):
        """
        Finish (release) a conditional escrow transaction using the fulfillment
        
        Args:
            sender_wallet (Wallet): Original escrow creator's wallet
            recipient_address (str): Recipient's address
            escrow_sequence (int): Escrow sequence number (ID)
            condition (str): The condition used in escrow creation
            fulfillment (str): The fulfillment that satisfies the condition
        
        Returns:
            dict: Escrow finish result
        """
        
        if not XRPL_AVAILABLE or not self.client:
            return {
                "success": False,
                "error": "XRPL client not available",
                "mock_data": {
                    "escrow_id": escrow_sequence,
                    "status": "mock_conditional_finished"
                }
            }
        
        try:
            # Validate fulfillment before submitting
            if not CryptoConditions.validate_fulfillment(condition, fulfillment):
                return {
                    "success": False,
                    "error": "Invalid fulfillment for the given condition"
                }
            
            # Create the escrow finish transaction with condition and fulfillment
            finish_tx = EscrowFinish(
                account=sender_wallet.address,
                owner=sender_wallet.address,
                offer_sequence=escrow_sequence,
                condition=condition,
                fulfillment=fulfillment
            )
            
            print(f"🔍 DEBUG FINISH CONDITIONAL ESCROW:")
            print(f"   Account: {sender_wallet.address}")
            print(f"   Escrow sequence: {escrow_sequence}")
            print(f"   Condition: {condition}")
            print(f"   Fulfillment: {fulfillment[:20]}...")
            
            # Submit the transaction
            response = submit_and_wait(finish_tx, self.client, sender_wallet)
            
            if response.is_successful():
                return {
                    "success": True,
                    "escrow_id": escrow_sequence,
                    "transaction_hash": response.result.get('hash'),
                    "status": "conditional_escrow_finished",
                    "funds_released": True,
                    "finished_at": datetime.now(timezone.utc).isoformat(),
                    "condition_satisfied": True
                }
            else:
                return {
                    "success": False,
                    "error": f"Conditional escrow finish failed: {response.result}",
                    "transaction_response": response.result
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Conditional escrow finish failed: {str(e)}"
            }
    
    def create_escrow(self, sender_wallet, recipient_address, amount_xrp, 
                     hold_duration_hours=72, memo=None):
        """
        Create an escrow transaction that holds XRP until conditions are met
        (Backwards compatibility - now creates conditional escrows by default)
        
        Args:
            sender_wallet (Wallet): XRPL wallet object for the sender (escrow creator)
            recipient_address (str): Recipient's XRPL wallet address
            amount_xrp (float): Amount in XRP to escrow
            hold_duration_hours (int): How long to hold the escrow (now used as cancel time)
            memo (str, optional): Optional memo for the escrow
        
        Returns:
            dict: Escrow creation result with transaction details
        """
        
        # For backwards compatibility, create conditional escrow with cancel time
        return self.create_conditional_escrow(
            sender_wallet=sender_wallet,
            recipient_address=recipient_address,
            amount_xrp=amount_xrp,
            cancel_hours=hold_duration_hours,
            memo=memo
        )
    
    def finish_escrow(self, sender_wallet, recipient_address, escrow_sequence, 
                     condition=None, fulfillment=None):
        """
        Finish (release) an escrow transaction
        (Backwards compatibility - handles both conditional and time-based escrows)
        
        Args:
            sender_wallet (Wallet): Original escrow creator's wallet
            recipient_address (str): Recipient's address
            escrow_sequence (int): Escrow sequence number (ID)
            condition (str, optional): The condition (for conditional escrows)
            fulfillment (str, optional): The fulfillment (for conditional escrows)
        
        Returns:
            dict: Escrow finish result
        """
        
        if condition and fulfillment:
            # Handle conditional escrow
            return self.finish_conditional_escrow(
                sender_wallet=sender_wallet,
                recipient_address=recipient_address,
                escrow_sequence=escrow_sequence,
                condition=condition,
                fulfillment=fulfillment
            )
        else:
            # Handle time-based escrow (original implementation)
            if not XRPL_AVAILABLE or not self.client:
                return {
                    "success": False,
                    "error": "XRPL client not available",
                    "mock_data": {
                        "escrow_id": escrow_sequence,
                        "status": "mock_finished"
                    }
                }
            
            try:
                # Create the escrow finish transaction
                finish_tx = EscrowFinish(
                    account=sender_wallet.address,
                    owner=sender_wallet.address,
                    offer_sequence=escrow_sequence
                )
                
                # Submit the transaction synchronously
                response = submit_and_wait(finish_tx, self.client, sender_wallet)
                
                if response.is_successful():
                    return {
                        "success": True,
                        "escrow_id": escrow_sequence,
                        "transaction_hash": response.result.get('hash'),
                        "status": "escrow_finished",
                        "funds_released": True,
                        "finished_at": datetime.now(timezone.utc).isoformat()
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Escrow finish failed: {response.result}",
                        "transaction_response": response.result
                    }
                    
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Escrow finish failed: {str(e)}"
                }

    def cancel_escrow(self, sender_wallet, recipient_address, escrow_sequence):
        """
        Cancel an escrow transaction (returns funds to sender)
        
        Args:
            sender_wallet (Wallet): Original escrow creator's wallet
            recipient_address (str): Recipient's address  
            escrow_sequence (int): Escrow sequence number (ID)
        
        Returns:
            dict: Escrow cancel result
        """
        
        if not XRPL_AVAILABLE or not self.client:
            return {
                "success": False,
                "error": "XRPL client not available",
                "mock_data": {
                    "escrow_id": escrow_sequence,
                    "status": "mock_cancelled"
                }
            }
        
        try:
            # Create the escrow cancel transaction
            cancel_tx = EscrowCancel(
                account=sender_wallet.address,  # The escrow creator cancels
                owner=sender_wallet.address,  # The original escrow creator  
                offer_sequence=escrow_sequence  # Sequence number of the EscrowCreate
            )
            
            print(f"🔍 DEBUG CANCEL: Created EscrowCancel transaction:")
            print(f"   Account: {sender_wallet.address}")
            print(f"   Owner: {sender_wallet.address}")  
            print(f"   OfferSequence: {escrow_sequence}")
            
            # Submit the transaction synchronously
            response = submit_and_wait(cancel_tx, self.client, sender_wallet)
            
            print(f"🔍 DEBUG CANCEL: Transaction response: {response.result if hasattr(response, 'result') else 'No result'}")
            print(f"🔍 DEBUG CANCEL: Is successful: {response.is_successful() if hasattr(response, 'is_successful') else 'No method'}")
            
            if response.is_successful():
                return {
                    "success": True,
                    "escrow_id": escrow_sequence,
                    "transaction_hash": response.result.get('hash'),
                    "status": "escrow_cancelled",
                    "funds_returned": True,
                    "cancelled_at": datetime.now(timezone.utc).isoformat()
                }
            else:
                return {
                    "success": False,
                    "error": f"Escrow cancel failed: {response.result}",
                    "transaction_response": response.result
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Escrow cancel failed: {str(e)}"
            }
    
    def get_account_escrows(self, wallet_address):
        """
        Get all escrows for a specific account
        
        Args:
            wallet_address (str): XRPL wallet address
        
        Returns:
            dict: List of escrows for the account
        """
        
        if not XRPL_AVAILABLE or not self.client:
            return {
                "success": False,
                "error": "XRPL client not available",
                "mock_escrows": []
            }
        
        try:
            # Get account transactions to find escrows
            account_tx_request = AccountTx(
                account=wallet_address,
                limit=50  # Adjust as needed
            )
            
            response = self.client.request(account_tx_request)
            
            if response.is_successful():
                transactions = response.result.get('transactions', [])
                escrows = []
                
                for tx_data in transactions:
                    tx = tx_data.get('tx', {})
                    if tx.get('TransactionType') == 'EscrowCreate':
                        escrows.append({
                            "escrow_sequence": tx.get('Sequence'),
                            "destination": tx.get('Destination'),
                            "amount_drops": tx.get('Amount'),
                            "amount_xrp": drops_to_xrp(tx.get('Amount', '0')),
                            "finish_after": tx.get('FinishAfter'),
                            "cancel_after": tx.get('CancelAfter'),
                            "condition": tx.get('Condition'),
                            "transaction_hash": tx_data.get('hash'),
                            "status": "active",  # Would need additional logic to determine actual status
                            "escrow_type": "conditional" if tx.get('Condition') else "time_based"
                        })
                
                return {
                    "success": True,
                    "escrows": escrows,
                    "count": len(escrows)
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to get account transactions: {response.result}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to get escrows: {str(e)}"
            }

# Create global escrow service instance
escrow_service = XRPLEscrowService()

# Convenience function for microfinance workflow
def create_microfinance_escrow(sender_secret, recipient_address, amount_xrp, 
                              application_id=None, hold_hours=72):
    """
    Create an escrow for microfinance application (now creates conditional escrows)
    
    Args:
        sender_secret (str): Sender's XRPL secret/seed
        recipient_address (str): Recipient's wallet address
        amount_xrp (float): Amount in XRP to escrow
        application_id (str, optional): Microfinance application ID
        hold_hours (int): Hours until escrow can be cancelled (default: 72)
    
    Returns:
        dict: Escrow creation result
    """
    
    if not XRPL_AVAILABLE:
        return {
            "success": False,
            "error": "XRPL not available",
            "mock_result": {
                "escrow_id": f"MOCK_{secrets.token_hex(8)}",
                "amount": amount_xrp,
                "recipient": recipient_address,
                "application_id": application_id
            }
        }
    
    try:
        # Create wallet from secret
        sender_wallet = Wallet.from_seed(sender_secret)
        
        # Create memo with application info
        memo = f"Microfinance escrow"
        if application_id:
            memo += f" - App ID: {application_id}"
        
        # Create the conditional escrow
        result = escrow_service.create_conditional_escrow(
            sender_wallet=sender_wallet,
            recipient_address=recipient_address,
            amount_xrp=amount_xrp,
            cancel_hours=hold_hours,
            memo=memo
        )
        
        # Add microfinance-specific fields
        if result.get("success"):
            result["application_id"] = application_id
            result["escrow_type"] = "microfinance_conditional"
            result["workflow_step"] = "conditional_escrow_created"
        
        return result
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Microfinance escrow creation failed: {str(e)}"
        }
