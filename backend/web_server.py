#!/usr/bin/env python3
"""
FastAPI Web Server for XRPL Microfinance Email Verification
Handles approve/reject endpoints for escrow verification emails
Plus summary generation and workflow management
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.states import (
    DIDVerificationConfig,
    DIDVerificationStep,
    EscrowAccountsConfig,
    EscrowAccountsStep,
    PlannedOrchestration,
    SummarizationConfig,
    SummarizationStep,
    UIFormConfig,
    UIFormStep,
    UserDataCache,
    WorkflowStep,
)

from .did_verification_module import verify_wallet_identity

# Import our email verification service and helpers
from .email_verification_module import (
    create_escrow_with_email_verification,
    email_service,
)
from .generation_agents.did_agents import generate_did_verification_form_html
from .generation_agents.escrow_agents import generate_escrow_accounts_form_html
from .generation_agents.ui_form_agents import generate_ui_form_html

# Import summary functionality
try:
    from .summary_module import SummaryNode, OrchestrationContext
    from .generation_agents.summary_agents import get_summary_display_html, get_summary_input_form_html
    SUMMARY_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Summary module not available: {e}")
    SUMMARY_AVAILABLE = False

# Pydantic models for request validation
class WorkflowSequenceRequest(BaseModel):
    sequence: List[Dict[str, Any]]

class IdentityVerificationRequest(BaseModel):
    wallet_address: str
    wallet_secret: str

class EscrowCreationRequest(BaseModel):
    sender_secret: str
    sender_wallet_address: str
    recipient_address: str
    sender_email: str
    loan_amount: float
    currency: str = "XRP"

# Global variables
planned_orchestration = PlannedOrchestration()
escrow_statuses = {}  # Track escrow statuses by escrow_id
escrow_creation_requests = {}  # Track escrow creation requests by sender email

def get_current_user_cache_data() -> UserDataCache:
    """
    Get cached user data for the current interacting user
    
    Returns:
        UserDataCache object with current user's cached data
    """
    
    current_email = planned_orchestration.get_current_user_email()
    if not current_email:
        # Return default empty cache data if no current user email
        return UserDataCache(
            name="",
            email="",
            wallet_address=""
        )
    
    try:
        cache_file = Path(__file__).parent / "current_cached_user_data.json"
        
        if not cache_file.exists():
            print(f"⚠️ Cache file not found, returning empty data for {current_email}")
            return UserDataCache(
                name="",
                email=current_email,
                wallet_address=""
            )
        
        with open(cache_file, 'r', encoding='utf-8') as f:
            cache_data = json.load(f)
        
        if current_email in cache_data:
            user_data = cache_data[current_email]
            print(f"✅ Found cached data for current user: {current_email}")
            
            # Create UserDataCache object from cached data
            return UserDataCache(**user_data)
        else:
            print(f"⚠️ No cached data found for current user: {current_email}")
            return UserDataCache(
                name="",
                email=current_email,
                wallet_address=""
            )
            
    except Exception as e:
        print(f"❌ Error retrieving cached data for {current_email}: {e}")
        return UserDataCache(
            name="",
            email=current_email or "",
            wallet_address=""
        )

# Helper function to create workflow steps from sequence data
def create_workflow_step_from_config(step_config: Dict[str, Any]) -> WorkflowStep:
    """Create a workflow step from configuration dictionary"""
    step_type = step_config.get("type")
    config_data = step_config.get("config", {})
    next_step = step_config.get("next", "END")
    
    if step_type == "ui_form":
        config = UIFormConfig(**config_data)
        return UIFormStep(config, next_step)
    
    elif step_type == "did_verification":
        config = DIDVerificationConfig(**config_data)
        return DIDVerificationStep(config, next_step)
    
    elif step_type == "escrow_accounts":
        config = EscrowAccountsConfig(**config_data)
        return EscrowAccountsStep(config, next_step)
    
    elif step_type == "summarization":
        config = SummarizationConfig(**config_data)
        return SummarizationStep(config, next_step)
    
    else:
        raise ValueError(f"Unknown workflow step type: {step_type}")

# Create FastAPI app
app = FastAPI(
    title="XRPL Microfinance Email Verification",
    description="Handles email verification for escrow approvals",
    version="1.0.0"
)

# Add CORS middleware to allow cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React development server
        "http://127.0.0.1:3000",  # Alternative localhost
        "http://localhost:5173",  # Vite development server
        "http://127.0.0.1:5173",  # Alternative Vite
        "http://localhost:8080",  # Other common dev ports
        "http://127.0.0.1:8080",
    ],
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Allow all headers
)

# Setup templates directory
templates_dir = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))

@app.get("/")
def root():
    """Root endpoint with API info"""
    return {
        "message": "XRPL Microfinance Email Verification API",
        "version": "1.0.0",
        "endpoints": {
            "verification": {
                "approve": "/verify/approve?token=<verification_token>",
                "reject": "/verify/reject?token=<verification_token>",
                "status": "/verify/status?token=<verification_token>"
            },
            "workflow": {
                "setup": "POST /workflow/setup - Setup workflow from sequence",
                "status": "GET /workflow/status - Get current workflow status", 
                "advance": "POST /workflow/advance - Advance to next step",
                "ui-form": "GET /workflow/ui-form - Get UI form for current step",
                "ui-form/demo": "GET /workflow/ui-form/demo - Get demo UI form",
                "did-verification": "GET /workflow/did-verification - Get DID verification form for current step",
                "did-verification/demo": "GET /workflow/did-verification/demo - Get demo DID verification form",
                "escrow-accounts": "GET /workflow/escrow-accounts - Get escrow accounts form for current step",
                "escrow-accounts/demo": "GET /workflow/escrow-accounts/demo - Get demo escrow accounts form",
                "display": "GET /workflow/display - Get dynamic workflow display",
                "display/content": "GET /workflow/display/content - Get current step info for auto-refresh"
            },
            "summary": {
                "input": "GET /summary - Simple form to input summary text",
                "display": "POST /api/display-summary - Display summary text beautifully", 
                "display_get": "GET /api/display-summary/{summary_text} - Display summary via URL",
                "generate": "POST /api/generate-summary - Generate AI-powered loan analysis",
                "providers": "GET /api/providers - Get available LLM providers"
            },
            "api": {
                "verify-identity": "POST /api/verify-identity - Verify wallet identity",
                "create-escrow": "POST /api/create-escrow - Create escrow with email verification",
                "escrow-status": "GET /api/escrow-status/{escrow_id} - Check escrow status",
                "cache-user-data": "POST /api/cache-user-data - Cache user form data",
                "get-cached-data": "GET /api/get-cached-data/{email} - Get cached user data",
                "list-cached-users": "GET /api/list-cached-users - List all cached users",
                "verification-tokens": "GET /api/verification-tokens/{email} - Get active verification tokens for user",
                "cleanup-tokens": "POST /api/cleanup-tokens/{email}?hours_old=24 - Clean up old verification tokens"
            },
            "debug": {
                "escrow-statuses": "GET /debug/escrow-statuses - View all escrow statuses",
                "escrow-creation-requests": "GET /debug/escrow-creation-requests - View escrow creation request tracking (duplicate prevention)",
                "workflow-state": "GET /debug/workflow-state - View current workflow state and user email",
                "time-info": "GET /debug/time-info - View server time vs XRPL time calculations",
                "verifications": "GET /debug/verifications - View loaded verifications vs file contents",
                "verification-tokens": "GET /debug/verification-tokens/{email} - Show cached vs filtered verification tokens for a user"
            },
            "health": "/health"
        },
        "summary_available": SUMMARY_AVAILABLE
    }

@app.get("/verify/approve", response_class=HTMLResponse)
def approve_escrow(request: Request, token: str):
    """
    Handle escrow approval from email link
    
    Args:
        token: Verification token from email
    
    Returns:
        HTML page showing approval result
    """
    
    if not token:
        raise HTTPException(status_code=400, detail="Verification token is required")
    
    # Debug: Check what tokens we have
    print(f"🔍 DEBUG: Received token: {token}")
    print(f"🔍 DEBUG: Available tokens: {list(email_service.pending_verifications.keys())}")
    print(f"🔍 DEBUG: Total pending verifications: {len(email_service.pending_verifications)}")
    
    # Call the email verification service to approve (now synchronous)
    result = email_service.verify_and_approve_escrow(token)
    
    print(f"🔍 DEBUG: Approval result: {result}")
    
    # Update escrow status if successful
    if result.get("success"):
        escrow_id = result.get("escrow_id")
        if escrow_id and escrow_id in escrow_statuses:
            escrow_statuses[escrow_id]["status"] = "approved"
            escrow_statuses[escrow_id]["updated_at"] = datetime.now(timezone.utc).isoformat()
            escrow_statuses[escrow_id]["approved_at"] = datetime.now(timezone.utc).isoformat()
            print(f"✅ Updated escrow status to approved for escrow_id: {escrow_id}")
    
    if not result.get("success"):
        error_msg = result.get('error', 'Unknown error occurred')
        print(f"❌ DEBUG: Approval failed with error: {error_msg}")
        
        # Return error page or redirect to error
        return HTMLResponse(
            content=f"""
            <html>
                <head><title>Approval Failed</title></head>
                <body style="font-family: Arial; text-align: center; padding: 50px;">
                    <h1>❌ Approval Failed</h1>
                    <p>{error_msg}</p>
                    <p><strong>Debug Info:</strong></p>
                    <p>Token: {token}</p>
                    <p>Available tokens: {len(email_service.pending_verifications)}</p>
                    <button onclick="window.close()">Close Window</button>
                </body>
            </html>
            """,
            status_code=400
        )
    
    # Prepare data for template
    escrow_data = result.get("escrow_data", {})
    template_data = {
        "request": request,
        "amount_xrp": result.get("amount_released", "N/A"),
        "application_id": escrow_data.get("application_id", "N/A"),
        "escrow_id": result.get("escrow_id", "N/A"),
        "recipient_address": result.get("recipient", "N/A"),
        "transaction_hash": result.get("transaction_hash", "N/A"),
        "approved_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    }
    
    # Render approved loan template
    return templates.TemplateResponse("approved_loan.html", template_data)

@app.get("/verify/reject", response_class=HTMLResponse)
def reject_escrow(request: Request, token: str):
    """
    Handle escrow rejection from email link
    
    Args:
        token: Verification token from email
    
    Returns:
        HTML page showing rejection result
    """
    
    if not token:
        raise HTTPException(status_code=400, detail="Verification token is required")
    
    # Debug: Check what tokens we have
    print(f"🔍 DEBUG REJECT: Received token: {token}")
    print(f"🔍 DEBUG REJECT: Available tokens: {list(email_service.pending_verifications.keys())}")
    print(f"🔍 DEBUG REJECT: Total pending verifications: {len(email_service.pending_verifications)}")
    
    # Call the email verification service to reject (now synchronous)
    result = email_service.verify_and_reject_escrow(token)
    
    print(f"🔍 DEBUG REJECT: Rejection result: {result}")
    
    # Update escrow status if successful
    if result.get("success"):
        escrow_id = result.get("escrow_id")
        if escrow_id and escrow_id in escrow_statuses:
            escrow_statuses[escrow_id]["status"] = "rejected"
            escrow_statuses[escrow_id]["updated_at"] = datetime.now(timezone.utc).isoformat()
            escrow_statuses[escrow_id]["rejected_at"] = datetime.now(timezone.utc).isoformat()
            print(f"❌ Updated escrow status to rejected for escrow_id: {escrow_id}")
    
    if not result.get("success"):
        error_msg = result.get('error', 'Unknown error occurred')
        print(f"❌ DEBUG REJECT: Rejection failed with error: {error_msg}")
        
        # Return error page
        return HTMLResponse(
            content=f"""
            <html>
                <head><title>Rejection Failed</title></head>
                <body style="font-family: Arial; text-align: center; padding: 50px;">
                    <h1>❌ Rejection Failed</h1>
                    <p>{error_msg}</p>
                    <p><strong>Debug Info:</strong></p>
                    <p>Token: {token}</p>
                    <p>Available tokens: {len(email_service.pending_verifications)}</p>
                    <button onclick="window.close()">Close Window</button>
                </body>
            </html>
            """,
            status_code=400
        )
    
    # Prepare data for template
    escrow_data = result.get("escrow_data", {})
    template_data = {
        "request": request,
        "amount_xrp": result.get("amount_xrp", "N/A"),
        "application_id": escrow_data.get("application_id", "N/A"),
        "escrow_id": result.get("escrow_id", "N/A"),
        "sender_address": result.get("sender_address", "N/A"),
        "transaction_hash": result.get("transaction_hash", "Auto-return within 72 hours"),
        "rejected_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "rejection_method": result.get("rejection_method", "immediate_recording"),
        "funds_return_method": result.get("funds_return_method", "auto_expiry_after_72_hours")
    }
    
    # Render rejected loan template
    return templates.TemplateResponse("rejected_loan.html", template_data)

@app.get("/verify/status")
def get_verification_status(token: str):
    """
    Get the current status of a verification token
    
    Args:
        token: Verification token
    
    Returns:
        JSON with verification status
    """
    
    if not token:
        raise HTTPException(status_code=400, detail="Verification token is required")
    
    # Reload verifications from file to get latest data
    email_service.pending_verifications = email_service._load_verifications()
    
    # Check if token exists in pending verifications
    if token not in email_service.pending_verifications:
        raise HTTPException(status_code=404, detail="Verification token not found")
    
    verification_data = email_service.pending_verifications[token]
    
    return {
        "token": token,
        "status": verification_data.get("status"),
        "created_at": verification_data.get("created_at"),
        "recipient_email": verification_data.get("recipient_email"),
        "escrow_id": verification_data.get("escrow_data", {}).get("escrow_id"),
        "amount_xrp": verification_data.get("escrow_data", {}).get("amount_xrp"),
        "approved_at": verification_data.get("approved_at"),
        "rejected_at": verification_data.get("rejected_at")
    }

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": "XRPL Microfinance Email Verification",
        "memory_address": hex(id(planned_orchestration)),
        "summary_available": SUMMARY_AVAILABLE
    }

# Summary Endpoints
@app.get("/summary", response_class=HTMLResponse)
async def get_summary_ui():
    """Serve a simple form to input summary text"""
    if not SUMMARY_AVAILABLE:
        return HTMLResponse(content="""
        <html>
            <head><title>Summary Unavailable</title></head>
            <body style="font-family: Arial; text-align: center; padding: 50px;">
                <h1>❌ Summary Module Unavailable</h1>
                <p>The summary module could not be loaded. Please check the server logs.</p>
                <a href="/">← Back to Home</a>
            </body>
        </html>
        """, status_code=503)
    
    return HTMLResponse(content=get_summary_input_form_html(), status_code=200)

@app.post("/api/display-summary", response_class=HTMLResponse)
async def display_summary_endpoint(title: str = "XRPL Loan Summary", summary_text: str = ""):
    """Display a summary using the summary agents display function"""
    if not SUMMARY_AVAILABLE:
        return HTMLResponse(content="Summary module not available", status_code=503)
    
    metadata = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "display_mode": "manual_input"
    }
    
    return HTMLResponse(content=get_summary_display_html(summary_text, title, metadata))

@app.post("/workflow/setup")
def setup_workflow(request_data: WorkflowSequenceRequest):
    """
    Setup workflow orchestration from a sequence of workflow steps
    
    Args:
        request_data: Contains sequence of workflow step configurations
    
    Returns:
        JSON with setup status and workflow details including redirect URL
    """
    
    try:
        # Clear existing workflow steps
        global planned_orchestration
        planned_orchestration = PlannedOrchestration()
        
        # Process each step in the sequence
        workflow_steps = []
        for step_config in request_data.sequence:
            try:
                step = create_workflow_step_from_config(step_config)
                workflow_steps.append(step)
            except Exception as step_error:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Invalid step configuration: {step_error}"
                )
        
        # Add all steps to orchestration
        planned_orchestration.add_steps(workflow_steps)
        
        # Construct the redirect URL for the workflow display
        base_url = "http://localhost:8000"  # Server deployment URL
        redirect_url = f"{base_url}/workflow/display"
        
        # Return success response with workflow details and redirect URL
        return {
            "success": True,
            "message": "Workflow orchestration setup successfully",
            "redirect_url": redirect_url,
            "workflow_details": {
                "total_steps": len(workflow_steps),
                "step_types": [step.step_type for step in workflow_steps],
                "current_step": planned_orchestration.get_current_step().step_type if planned_orchestration.get_current_step() else None,
                "all_steps": planned_orchestration.get_all_steps()
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to setup workflow: {str(e)}"
        )

@app.get("/workflow/status")
def get_workflow_status():
    """
    Get current workflow orchestration status
    
    Returns:
        JSON with current workflow status
    """
    
    current_step = planned_orchestration.get_current_step()
    
    return {
        "total_steps": len(planned_orchestration.workflow_steps),
        "current_step_index": planned_orchestration.current_step_index,
        "current_step_type": current_step.step_type if current_step else None,
        "current_step_config": current_step.config.__dict__ if current_step else None,
        "next_step": current_step.next if current_step else None,
        "all_steps": planned_orchestration.get_all_steps(),
        "is_complete": planned_orchestration.current_step_index >= len(planned_orchestration.workflow_steps)
    }

@app.post("/workflow/advance")
def advance_workflow(request: Request, form_data: dict = None):
    """
    Advance to the next workflow step
    
    Args:
        request: FastAPI request object
        form_data: Form data from current step
    
    Returns:
        JSON with advancement status
    """
    
    global planned_orchestration
    
    if not planned_orchestration:
        raise HTTPException(
            status_code=400,
            detail="No workflow orchestration is currently active. Please setup workflow first."
        )
    
    try:
        # Cache user data if it contains email
        if form_data and form_data.get('email'):
            try:
                # Set the current user email in the orchestration
                planned_orchestration.set_current_user_email(form_data.get('email'))
                
                # Create cache data with core fields
                cache_dict = {
                    'name': form_data.get('name', ''),
                    'email': form_data.get('email', ''),
                    'wallet_address': form_data.get('wallet_address', '')
                }
                
                # Add any additional fields (following the pattern firstword_secondword_...)
                for field_name, field_value in form_data.items():
                    if field_name not in ['name', 'email', 'wallet_address'] and field_value:
                        cache_dict[field_name] = str(field_value)
                
                # Create UserDataCache with dynamic fields
                cache_data = UserDataCache(**cache_dict)
                cache_user_data(cache_data)
                print(f"✅ Cached user data for email: {form_data.get('email')} with {len(cache_data.get_additional_fields())} additional fields")
            except Exception as cache_error:
                print(f"⚠️ Failed to cache user data: {cache_error}")
                # Don't fail the workflow advancement due to caching issues
        
        # Advance to next step
        current_step = planned_orchestration.get_current_step()
        if current_step:
            print(f"🔄 Advancing from step: {current_step.step_type}")
            planned_orchestration.advance_to_next_step()
            
            next_step = planned_orchestration.get_current_step()
            if next_step:
                return {
                    "success": True,
                    "message": "Workflow advanced successfully",
                    "previous_step": current_step.step_type,
                    "current_step": next_step.step_type,
                    "form_data_processed": bool(form_data),
                    "cached_email": form_data.get('email') if form_data else None
                }
            else:
                return {
                    "success": True,
                    "message": "Workflow completed successfully",
                    "previous_step": current_step.step_type,
                    "current_step": "COMPLETED",
                    "form_data_processed": bool(form_data),
                    "cached_email": form_data.get('email') if form_data else None
                }
        else:
            raise HTTPException(
                status_code=400,
                detail="Workflow has no current step to advance from"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to advance workflow: {str(e)}"
        )

@app.get("/workflow/ui-form", response_class=HTMLResponse)
def get_ui_form():
    """
    Generate and serve the UI form HTML for the current workflow step
    
    Returns:
        HTML page with the form based on current UIFormStep
    """
    
    current_step = planned_orchestration.get_current_step()
    
    if not current_step:
        raise HTTPException(status_code=404, detail="No current workflow step found")
    
    if current_step.step_type != "ui_form":
        raise HTTPException(
            status_code=400, 
            detail=f"Current step is not a UI form. Current step type: {current_step.step_type}"
        )
    
    try:
        # Generate HTML using the helper function
        html_content = generate_ui_form_html(current_step)
        return HTMLResponse(content=html_content)
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate UI form: {str(e)}"
        )

@app.get("/workflow/ui-form/demo", response_class=HTMLResponse)
def get_demo_ui_form():
    """
    Generate and serve a demo UI form with sample fields
    
    Returns:
        HTML page with a demo form
    """
    
    try:
        # Create a demo UIFormStep
        demo_config = UIFormConfig(fields=["name", "email", "amount", "wallet_address", "wallet_secret"])
        demo_step = UIFormStep(demo_config, "did_verification")
        
        # Generate HTML using the helper function
        html_content = generate_ui_form_html(demo_step)
        return HTMLResponse(content=html_content)
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate demo UI form: {str(e)}"
        )

@app.post("/api/verify-identity")
def verify_identity(request_data: IdentityVerificationRequest):
    """
    Verify wallet identity using wallet address and secret
    
    Args:
        request_data: Contains wallet_address and wallet_secret
    
    Returns:
        JSON with verification result
    """
    
    try:
        # Call the verification function
        result = verify_wallet_identity(
            wallet_address=request_data.wallet_address,
            secret=request_data.wallet_secret
        )
        
        return result
        
    except Exception as e:
        return {
            "identity_verified": False,
            "error": f"Verification error: {str(e)}",
            "status": "verification_error"
        }

@app.get("/workflow/did-verification", response_class=HTMLResponse)
def get_did_verification_form():
    """
    Generate and serve the DID verification form HTML for the current workflow step
    
    Returns:
        HTML page with the DID verification form based on current DIDVerificationStep
    """
    
    current_step = planned_orchestration.get_current_step()
    
    if not current_step:
        raise HTTPException(status_code=404, detail="No current workflow step found")
    
    if current_step.step_type != "did_verification":
        raise HTTPException(
            status_code=400, 
            detail=f"Current step is not a DID verification. Current step type: {current_step.step_type}"
        )
    
    try:
        # Generate HTML using the helper function
        html_content = generate_did_verification_form_html(current_step)
        return HTMLResponse(content=html_content)
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate DID verification form: {str(e)}"
        )

@app.get("/workflow/did-verification/demo", response_class=HTMLResponse)
def get_demo_did_verification_form():
    """
    Generate and serve a demo DID verification form
    
    Returns:
        HTML page with a demo DID verification form
    """
    
    try:
        # Create a demo DIDVerificationStep
        from backend.states import DIDVerificationConfig, DIDVerificationStep
        
        demo_config = DIDVerificationConfig(
            provider="XRPL",
            required_claims=["wallet_ownership"],
            xrpl_network="testnet"
        )
        demo_step = DIDVerificationStep(demo_config, "escrow_accounts")
        
        # Generate HTML using the helper function
        html_content = generate_did_verification_form_html(demo_step)
        return HTMLResponse(content=html_content)
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate demo DID verification form: {str(e)}"
        )

@app.get("/workflow/escrow-accounts", response_class=HTMLResponse)
def get_escrow_accounts_form():
    """
    Generate and serve the escrow accounts form HTML for the current workflow step
    
    Returns:
        HTML page with the escrow accounts form based on current EscrowAccountsStep
    """
    
    current_step = planned_orchestration.get_current_step()
    
    if not current_step:
        raise HTTPException(status_code=404, detail="No current workflow step found")
    
    if current_step.step_type != "escrow_accounts":
        raise HTTPException(
            status_code=400, 
            detail=f"Current step is not an escrow accounts step. Current step type: {current_step.step_type}"
        )
    
    try:
        # Get current user email from orchestration
        current_user_email = planned_orchestration.get_current_user_email()
        
        # Get cached user data for current user
        current_user_cache_details = get_current_user_cache_data()
        
        # Generate HTML using the helper function with current user email
        html_content = generate_escrow_accounts_form_html(current_step, current_user_cache_details)
        return HTMLResponse(content=html_content)
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate escrow accounts form: {str(e)}"
        )

@app.get("/workflow/escrow-accounts/demo", response_class=HTMLResponse)
def get_demo_escrow_accounts_form():
    """
    Generate and serve a demo escrow accounts form
    
    Returns:
        HTML page with a demo escrow accounts form
    """
    
    try:
        # Create a demo EscrowAccountsStep
        from backend.states import EscrowAccountsConfig, EscrowAccountsStep
        
        demo_config = EscrowAccountsConfig(
            provider="XRPL",
            auto_release=False,
            approval_required=True,
            wallet_address="rLU9sdfMkcqV9Pfaj6UePPdWGPMmEHFWcu",
            wallet_secret="sEdS5n9tQy9Suw9xVufH5eprfVhWZA3",
            email_address="yuv2bindal@gmail.com",
            currency_option="XRP"
        )
        demo_step = EscrowAccountsStep(demo_config, "summarization")
        
        # Use demo email for demo endpoint
        demo_user_email = "yuv2bindal@gmail.com"
        
        # Create demo cached user data
        demo_user_cache_details = UserDataCache(
            name="Demo User",
            email=demo_user_email,
            wallet_address="rsAievSV26WYo5KLSBwBQDyMb9tUSBbtdD",
            loan_amount="0.2"
        )

       
        # Generate HTML using the helper function with demo user email
        html_content = generate_escrow_accounts_form_html(demo_step, demo_user_cache_details)
        return HTMLResponse(content=html_content)
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate demo escrow accounts form: {str(e)}"
        )

@app.get("/workflow/display", response_class=HTMLResponse)
def get_workflow_display():
    """
    Dynamic workflow display that shows the current step's form/content
    Auto-refreshes every 5 seconds to check for step changes
    
    Returns:
        HTML page with current step content and auto-refresh functionality
    """
    
    try:
        current_step = planned_orchestration.get_current_step()
        
        if not current_step:
            # No current step - show workflow setup prompt
            return HTMLResponse(content="No current step found")
        
        # Get the appropriate content based on step type
        if current_step.step_type == "ui_form":
            step_content = generate_ui_form_html(current_step)
        elif current_step.step_type == "did_verification":
            step_content = generate_did_verification_form_html(current_step)
        elif current_step.step_type == "escrow_accounts":
            current_user_cache_details = get_current_user_cache_data()
            step_content = generate_escrow_accounts_form_html(current_step, current_user_cache_details)
        elif current_step.step_type == "summarization":
            # Get the summarization config
            summarization_config = current_step.config
            
            # Get user cache data without verification_tokens field
            current_user_cache_details = get_current_user_cache_data()
            user_cache_dict = current_user_cache_details.dict()
            
            # Remove verification_tokens if it exists
            if "verification_tokens" in user_cache_dict:
                del user_cache_dict["verification_tokens"]
            
            # Search for currency_option in previous workflow step configs
            currency_option = None
            for step in planned_orchestration.workflow_steps:
                if hasattr(step.config, 'currency_option') and step.config.currency_option:
                    currency_option = step.config.currency_option
                    break
            
            # Add currency_option to cache if found
            if currency_option:
                user_cache_dict["currency_option"] = currency_option
            
            # Set up OrchestrationContext
            orchestration_context = OrchestrationContext(
                high_level_steps=[step.step_type for step in planned_orchestration.workflow_steps],
                user_metrics_query=summarization_config.metrics_string,
                llm_provider=summarization_config.llm_provider,
                web_search_enabled=summarization_config.web_search,
                cache_user_data=user_cache_dict
            )
            
            # Generate summary using SummaryNode
            try:
                summary_node_instance = SummaryNode()
                summary_result = summary_node_instance.process_context(orchestration_context)
                
                # Extract summary text from result
                summary_text = summary_result.get("summary", "No summary generated")
                
                # Create metadata for display
                metadata = {
                    "provider_used": summary_result.get("provider_used", "unknown"),
                    "web_search_enabled": "Yes" if summary_result.get("web_search_enabled") else "No",
                    "generated_at": summary_result.get("timestamp", "unknown"),
                    "user_query": summary_result.get("user_query", "")
                }
                
                # Generate HTML using summary_agents
                step_content = get_summary_display_html(
                    summary_text=summary_text,
                    title="XRPL Loan Analysis Summary", 
                    metadata=metadata
                )
                
            except Exception as e:
                # Fallback error content
                error_summary = f"""
🏦 XRPL LOAN ANALYSIS - ERROR
============================

❌ Summary Generation Failed
Error: {str(e)}

Please check the configuration and try again.
"""
                step_content = get_summary_display_html(
                    summary_text=error_summary,
                    title="Summary Generation Error",
                    metadata={"error": str(e), "timestamp": datetime.now(timezone.utc).isoformat()}
                )
        else:
            step_content = generate_unknown_step_html(current_step)
        
        # Wrap the step content with polling functionality
        return HTMLResponse(content=wrap_with_polling_container(step_content, current_step))
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate workflow display: {str(e)}"
        )

@app.get("/workflow/display/content")
def get_workflow_display_content():
    """
    API endpoint for polling - returns current step info for auto-refresh
    
    Returns:
        JSON with current step information and whether content should refresh
    """
    
    try:
        current_step = planned_orchestration.get_current_step()
        
        if not current_step:
            return {
                "step_type": None,
                "step_index": -1,
                "total_steps": len(planned_orchestration.workflow_steps),
                "should_refresh": True,
                "is_complete": True
            }
        
        return {
            "step_type": current_step.step_type,
            "step_index": planned_orchestration.current_step_index,
            "total_steps": len(planned_orchestration.workflow_steps),
            "next_step": current_step.next,
            "should_refresh": False,  # Frontend will determine this based on step changes
            "is_complete": planned_orchestration.current_step_index >= len(planned_orchestration.workflow_steps)
        }
        
    except Exception as e:
        return {
            "error": str(e),
            "step_type": None,
            "should_refresh": True
        }

def wrap_with_polling_container(step_content: str, current_step) -> str:
    """
    Wraps step content with polling container and auto-refresh functionality
    """
    
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>XRPL Workflow Dashboard</title>
    <style>
        body {{
            margin: 0;
            padding: 0;
            font-family: 'Inter', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }}
        
        .workflow-header {{
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            padding: 15px 30px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            color: white;
            box-shadow: 0 2px 20px rgba(0, 0, 0, 0.1);
        }}
        
        .workflow-title {{
            font-size: 1.2rem;
            font-weight: 600;
        }}
        
        .workflow-progress {{
            display: flex;
            align-items: center;
            gap: 15px;
        }}
        
        .step-indicator {{
            background: rgba(255, 255, 255, 0.2);
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 0.9rem;
            font-weight: 500;
        }}
        
        .connection-status {{
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background: #10b981;
            animation: pulse 2s infinite;
        }}
        
        .connection-status.disconnected {{
            background: #ef4444;
            animation: none;
        }}
        
        @keyframes pulse {{
            0% {{ opacity: 1; }}
            50% {{ opacity: 0.5; }}
            100% {{ opacity: 1; }}
        }}
        
        .step-content {{
            position: relative;
            min-height: calc(100vh - 70px);
        }}
        
        .refresh-notification {{
            position: fixed;
            top: 20px;
            right: 20px;
            background: #10b981;
            color: white;
            padding: 12px 20px;
            border-radius: 8px;
            font-weight: 500;
            transform: translateX(300px);
            transition: transform 0.3s ease;
            z-index: 1000;
        }}
        
        .refresh-notification.show {{
            transform: translateX(0);
        }}
        
        .loading-overlay {{
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(102, 126, 234, 0.9);
            display: none;
            align-items: center;
            justify-content: center;
            z-index: 2000;
            backdrop-filter: blur(5px);
        }}
        
        .loading-content {{
            text-align: center;
            color: white;
        }}
        
        .loading-spinner {{
            width: 50px;
            height: 50px;
            border: 4px solid rgba(255, 255, 255, 0.3);
            border-top: 4px solid white;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin: 0 auto 20px;
        }}
        
        @keyframes spin {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}
    </style>
</head>
<body>
    <div class="workflow-header">
        <div class="workflow-title">🚀 XRPL Workflow Dashboard</div>
        <div class="workflow-progress">
            <div class="step-indicator" id="stepIndicator">
                Step {planned_orchestration.current_step_index + 1} of {len(planned_orchestration.workflow_steps)}: {current_step.step_type.replace('_', ' ').title()}
            </div>
            <div class="connection-status" id="connectionStatus"></div>
        </div>
    </div>
    
    <div class="step-content" id="stepContent">
        {step_content}
    </div>
    
    <div class="refresh-notification" id="refreshNotification">
        ✨ Step Updated!
    </div>
    
    <div class="loading-overlay" id="loadingOverlay">
        <div class="loading-content">
            <div class="loading-spinner"></div>
            <div>Loading next step...</div>
        </div>
    </div>
    
    <script>
        let currentStepType = '{current_step.step_type}';
        let currentStepIndex = {planned_orchestration.current_step_index};
        let isPolling = true;
        let pollInterval;
        
        // Start polling when page loads
        document.addEventListener('DOMContentLoaded', function() {{
            console.log('🚀 Workflow Dashboard loaded');
            startPolling();
            
            // Handle visibility change to pause/resume polling
            document.addEventListener('visibilitychange', function() {{
                if (document.hidden) {{
                    stopPolling();
                }} else {{
                    startPolling();
                }}
            }});
        }});
        
        function startPolling() {{
            if (pollInterval) clearInterval(pollInterval);
            
            pollInterval = setInterval(async () => {{
                await checkForStepChanges();
            }}, 5000); // Poll every 5 seconds
            
            // Update connection status
            document.getElementById('connectionStatus').classList.remove('disconnected');
        }}
        
        function stopPolling() {{
            if (pollInterval) {{
                clearInterval(pollInterval);
                pollInterval = null;
            }}
            
            // Update connection status
            document.getElementById('connectionStatus').classList.add('disconnected');
        }}
        
        async function checkForStepChanges() {{
            try {{
                const response = await fetch('/workflow/display/content');
                const data = await response.json();
                
                if (data.error) {{
                    console.error('Polling error:', data.error);
                    return;
                }}
                
                // Check if step has changed
                if (data.step_type !== currentStepType || data.step_index !== currentStepIndex) {{
                    console.log(`Step changed: ${{currentStepType}} -> ${{data.step_type}}`);
                    await refreshStepContent(data);
                }}
                
                // Update current tracking
                currentStepType = data.step_type;
                currentStepIndex = data.step_index;
                
                // Check if workflow is complete
                if (data.is_complete) {{
                    showWorkflowComplete();
                }}
                
            }} catch (error) {{
                console.error('Error checking for step changes:', error);
                document.getElementById('connectionStatus').classList.add('disconnected');
            }}
        }}
        
        async function refreshStepContent(stepData) {{
            try {{
                // Show loading overlay
                document.getElementById('loadingOverlay').style.display = 'flex';
                
                // Refresh the entire page to get new content
                setTimeout(() => {{
                    window.location.reload();
                }}, 1000);
                
            }} catch (error) {{
                console.error('Error refreshing content:', error);
                document.getElementById('loadingOverlay').style.display = 'none';
            }}
        }}
        
        function showRefreshNotification() {{
            const notification = document.getElementById('refreshNotification');
            notification.classList.add('show');
            
            setTimeout(() => {{
                notification.classList.remove('show');
            }}, 3000);
        }}
        
        function showWorkflowComplete() {{
            stopPolling();
            
            // Show completion message
            const stepContent = document.getElementById('stepContent');
            stepContent.innerHTML = `
                <div style="display: flex; align-items: center; justify-content: center; min-height: 70vh; text-align: center; color: white;">
                    <div>
                        <div style="font-size: 4rem; margin-bottom: 20px;">🎉</div>
                        <h1 style="font-size: 2.5rem; margin-bottom: 15px;">Workflow Complete!</h1>
                        <p style="font-size: 1.2rem; opacity: 0.9;">All steps have been successfully completed.</p>
                        <button onclick="window.location.href='/'" style="
                            margin-top: 30px;
                            padding: 15px 30px;
                            background: rgba(255, 255, 255, 0.2);
                            color: white;
                            border: 2px solid rgba(255, 255, 255, 0.3);
                            border-radius: 10px;
                            font-size: 1.1rem;
                            cursor: pointer;
                            transition: all 0.3s ease;
                        " onmouseover="this.style.background='rgba(255, 255, 255, 0.3)'" onmouseout="this.style.background='rgba(255, 255, 255, 0.2)'">
                            🏠 Return Home
                        </button>
                    </div>
                </div>
            `;
        }}
        
        // Handle window focus to resume polling
        window.addEventListener('focus', function() {{
            if (!pollInterval) {{
                startPolling();
            }}
        }});
        
        // Handle beforeunload to cleanup
        window.addEventListener('beforeunload', function() {{
            stopPolling();
        }});
    </script>
</body>
</html>"""


def generate_unknown_step_html(step) -> str:
    """Generate HTML for unknown step types"""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Unknown Step</title>
    <style>
        body {{
            font-family: 'Inter', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0;
            color: white;
        }}
        .step-container {{
            text-align: center;
            max-width: 600px;
            padding: 40px;
        }}
    </style>
</head>
<body>
    <div class="step-container">
        <div style="font-size: 4rem; margin-bottom: 20px;">❓</div>
        <h1>Unknown Step: {step.step_type}</h1>
        <p>This step type is not yet implemented in the display system.</p>
        <button onclick="fetch('/workflow/advance', {{method: 'POST'}}).then(() => location.reload())" 
                style="margin-top: 20px; padding: 15px 30px; background: rgba(255,255,255,0.2); color: white; border: none; border-radius: 10px; cursor: pointer;">
            Continue
        </button>
    </div>
</body>
</html>"""

@app.post("/api/cache-user-data")
def cache_user_data(user_data: UserDataCache):
    """
    Cache user form data to avoid re-entry
    
    Args:
        user_data: User data to cache (name, email, wallet_address, etc.)
    
    Returns:
        JSON with cache status
    """
    
    try:
        cache_file = Path(__file__).parent / "current_cached_user_data.json"
        
        # Validate field names
        validation_results = user_data.validate_all_fields()
        invalid_fields = [field for field, is_valid in validation_results.items() if not is_valid]
        
        if invalid_fields:
            return {
                "success": False,
                "error": "Invalid field names detected",
                "invalid_fields": invalid_fields,
                "message": f"Field names must follow pattern: firstword_secondword_... (all lowercase, separated by underscores). Invalid: {', '.join(invalid_fields)}"
            }
        
        # Add timestamp
        user_data.timestamp = datetime.now(timezone.utc).isoformat()
        
        # Load existing cache or create new one
        if cache_file.exists():
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
        else:
            cache_data = {}
        
        # Use email as the key and store user data
        cache_data[user_data.email] = user_data.dict()
        
        # Save back to file
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, indent=2, ensure_ascii=False)
        
        additional_fields = user_data.get_additional_fields()
        
        return {
            "success": True,
            "message": "User data cached successfully",
            "cached_email": user_data.email,
            "timestamp": user_data.timestamp,
            "core_fields": ["name", "email", "wallet_address"],
            "additional_fields": list(additional_fields.keys()),
            "total_fields": len(user_data.dict()) - 1,  # Exclude timestamp
            "field_validation": "All fields valid ✅"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to cache user data: {str(e)}"
        )

@app.get("/api/get-cached-data/{email}")
def get_cached_user_data(email: str):
    """
    Retrieve cached user data by email
    
    Args:
        email: User's email address to lookup cached data
    
    Returns:
        JSON with cached user data or empty if not found
    """
    
    try:
        cache_file = Path(__file__).parent / "current_cached_user_data.json"
        
        if not cache_file.exists():
            return {
                "found": False,
                "data": None,
                "message": "No cache file exists"
            }
        
        with open(cache_file, 'r', encoding='utf-8') as f:
            cache_data = json.load(f)
        
        if email in cache_data:
            return {
                "found": True,
                "data": cache_data[email],
                "message": "Cached data found"
            }
        else:
            return {
                "found": False,
                "data": None,
                "message": "No cached data for this email"
            }
            
    except Exception as e:
        return {
            "found": False,
            "data": None,
            "error": str(e)
        }

@app.get("/api/list-cached-users")
def list_cached_users():
    """
    List all cached user emails (for debugging/admin purposes)
    
    Returns:
        JSON with list of cached emails and their timestamps
    """
    
    try:
        cache_file = Path(__file__).parent / "current_cached_user_data.json"
        
        if not cache_file.exists():
            return {
                "cached_users": [],
                "total_count": 0,
                "message": "No cache file exists"
            }
        
        with open(cache_file, 'r', encoding='utf-8') as f:
            cache_data = json.load(f)
        
        cached_users = []
        for email, data in cache_data.items():
            cached_users.append({
                "email": email,
                "name": data.get("name", "Unknown"),
                "wallet_address": data.get("wallet_address", "Unknown"),
                "timestamp": data.get("timestamp", "Unknown"),
                "cached_fields": list(data.keys())
            })
        
        return {
            "cached_users": cached_users,
            "total_count": len(cached_users),
            "message": f"Found {len(cached_users)} cached users"
        }
        
    except Exception as e:
        return {
            "cached_users": [],
            "total_count": 0,
            "error": str(e)
        }

@app.post("/api/create-escrow")
def create_escrow(request_data: EscrowCreationRequest):
    """
    Create an escrow account with email verification
    
    Args:
        request_data: Contains sender_secret, recipient_address, sender_email, loan_amount, currency
    
    Returns:
        JSON with escrow creation result and email verification status
    """
    
    try:
        # Check for duplicate creation request for the same sender email
        sender_email = request_data.sender_email
        current_time = datetime.now(timezone.utc)
        
        # Check if there's a recent creation request for this email (within last 5 minutes)
        if sender_email in escrow_creation_requests:
            last_request_time = datetime.fromisoformat(escrow_creation_requests[sender_email]["timestamp"])
            time_diff = (current_time - last_request_time).total_seconds()
            
            if time_diff < 300:  # 5 minutes = 300 seconds
                # Return the existing escrow data instead of creating a new one
                existing_escrow_id = escrow_creation_requests[sender_email]["escrow_id"]
                print(f"🚫 Duplicate escrow creation request for {sender_email}, returning existing escrow {existing_escrow_id}")
                
                return {
                    "success": True,
                    "message": "Escrow already exists for this email (duplicate prevention)",
                    "escrow_data": escrow_creation_requests[sender_email]["escrow_data"],
                    "email_verification": escrow_creation_requests[sender_email]["email_verification"],
                    "workflow_step": "awaiting_verification",
                    "duplicate_prevented": True
                }
        
        # Call the escrow creation function with conditional escrow (default)
        result = create_escrow_with_email_verification(
            sender_secret=request_data.sender_secret,
            recipient_address=request_data.recipient_address,
            amount_xrp=request_data.loan_amount,
            sender_email=request_data.sender_email,
            application_id=f"loan_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}",
            hold_hours=0,  # Ignored for conditional escrows
            use_conditional=True  # Use conditional escrow: instant approval, immediate rejection recording with 72h auto-return
        )
        
        if result.get("success"):
            # Store escrow status for tracking
            escrow_id = result.get("escrow_data", {}).get("escrow_id")
            if escrow_id:
                escrow_statuses[escrow_id] = {
                    "status": "pending",
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "sender_email": request_data.sender_email,
                    "loan_amount": request_data.loan_amount,
                    "currency": request_data.currency,
                    "recipient_address": request_data.recipient_address
                }
                
                # Track this creation request to prevent duplicates
                escrow_creation_requests[sender_email] = {
                    "escrow_id": escrow_id,
                    "timestamp": current_time.isoformat(),
                    "escrow_data": result.get("escrow_data"),
                    "email_verification": result.get("email_verification")
                }
            
            return {
                "success": True,
                "message": "Escrow created successfully and verification email sent",
                "escrow_data": result.get("escrow_data"),
                "email_verification": result.get("email_verification"),
                "workflow_step": "awaiting_verification"
            }
        else:
            return {
                "success": False,
                "error": result.get("error", "Failed to create escrow"),
                "details": result
            }
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create escrow: {str(e)}"
        )

@app.get("/api/escrow-status/{escrow_id}")
def get_escrow_status(escrow_id: str):
    """
    Get the current status of an escrow
    
    Args:
        escrow_id: The escrow ID to check status for
    
    Returns:
        JSON with escrow status information
    """
    
    try:
        if escrow_id not in escrow_statuses:
            return {
                "found": False,
                "error": "Escrow ID not found",
                "escrow_id": escrow_id
            }
        
        escrow_data = escrow_statuses[escrow_id]
        
        return {
            "found": True,
            "escrow_id": escrow_id,
            "status": escrow_data.get("status", "unknown"),
            "created_at": escrow_data.get("created_at"),
            "sender_email": escrow_data.get("sender_email"),
            "loan_amount": escrow_data.get("loan_amount"),
            "currency": escrow_data.get("currency"),
            "recipient_address": escrow_data.get("recipient_address"),
            "updated_at": escrow_data.get("updated_at")
        }
        
    except Exception as e:
        return {
            "found": False,
            "error": str(e),
            "escrow_id": escrow_id
        }

@app.get("/api/verification-tokens/{email}")
def get_user_verification_tokens(email: str):
    """
    Get all active verification tokens and their statuses for a specific user email
    Only returns pending tokens or recent decisions (within last hour)
    
    Args:
        email: User's email address to lookup verification tokens
    
    Returns:
        JSON with active verification tokens and their current statuses
    """
    
    try:
        cache_file = Path(__file__).parent / "current_cached_user_data.json"
        
        if not cache_file.exists():
            return {
                "found": False,
                "tokens": [],
                "message": "No cache file exists"
            }
        
        with open(cache_file, 'r', encoding='utf-8') as f:
            cache_data = json.load(f)
        
        if email in cache_data and "verification_tokens" in cache_data[email]:
            all_tokens = cache_data[email]["verification_tokens"]
            
            # Filter tokens to only include active ones or recent decisions
            active_tokens = []
            current_time = datetime.now(timezone.utc)
            
            for token in all_tokens:
                token_status = token.get("status", "pending")
                updated_at = token.get("updated_at")
                
                # Always include pending tokens
                if token_status == "pending":
                    active_tokens.append(token)
                    continue
                
                # For approved/rejected tokens, only include if recent (within last hour)
                if token_status in ["approved", "rejected"] and updated_at:
                    try:
                        token_time = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
                        time_diff = (current_time - token_time).total_seconds()
                        
                        # Include if within last hour (3600 seconds)
                        if time_diff <= 3600:
                            active_tokens.append(token)
                    except Exception as e:
                        print(f"⚠️ Error parsing token timestamp: {e}")
                        continue
            
            # Find the most recent token with a decision status
            latest_decision_token = None
            for token in active_tokens:
                if token.get("status") in ["approved", "rejected"]:
                    if not latest_decision_token or token.get("updated_at", "") > latest_decision_token.get("updated_at", ""):
                        latest_decision_token = token
            
            return {
                "found": len(active_tokens) > 0,
                "email": email,
                "tokens": active_tokens,
                "latest_status_token": latest_decision_token,
                "total_tokens": len(active_tokens),
                "total_historical_tokens": len(all_tokens),
                "has_decision": latest_decision_token is not None,
                "decision_status": latest_decision_token.get("status") if latest_decision_token else None,
                "filtered_info": {
                    "active_tokens": len(active_tokens),
                    "filtered_out": len(all_tokens) - len(active_tokens),
                    "filter_reason": "Excluded old resolved tokens (>1 hour old)"
                }
            }
        else:
            return {
                "found": False,
                "tokens": [],
                "message": "No verification tokens for this email"
            }
            
    except Exception as e:
        return {
            "found": False,
            "tokens": [],
            "error": str(e)
        }

@app.post("/api/cleanup-tokens/{email}")
def cleanup_old_verification_tokens(email: str, hours_old: int = 24):
    """
    Clean up old verification tokens for a user (removes tokens older than specified hours)
    
    Args:
        email: User's email address
        hours_old: Remove tokens older than this many hours (default: 24)
    
    Returns:
        JSON with cleanup results
    """
    
    try:
        cache_file = Path(__file__).parent / "current_cached_user_data.json"
        
        if not cache_file.exists():
            return {
                "success": False,
                "message": "No cache file exists"
            }
        
        with open(cache_file, 'r', encoding='utf-8') as f:
            cache_data = json.load(f)
        
        if email not in cache_data or "verification_tokens" not in cache_data[email]:
            return {
                "success": True,
                "message": "No verification tokens found for this user",
                "tokens_removed": 0
            }
        
        original_tokens = cache_data[email]["verification_tokens"]
        current_time = datetime.now(timezone.utc)
        cutoff_seconds = hours_old * 3600
        
        # Filter out old tokens
        remaining_tokens = []
        removed_count = 0
        
        for token in original_tokens:
            token_status = token.get("status", "pending")
            updated_at = token.get("updated_at")
            
            should_keep = True
            
            # Always keep pending tokens
            if token_status == "pending":
                should_keep = True
            elif token_status in ["approved", "rejected"] and updated_at:
                try:
                    token_time = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
                    time_diff = (current_time - token_time).total_seconds()
                    
                    # Remove if older than cutoff
                    if time_diff > cutoff_seconds:
                        should_keep = False
                        removed_count += 1
                except Exception:
                    # If we can't parse timestamp, keep the token to be safe
                    should_keep = True
            
            if should_keep:
                remaining_tokens.append(token)
        
        # Update cache with cleaned tokens
        cache_data[email]["verification_tokens"] = remaining_tokens
        
        # Save back to file
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, indent=2, ensure_ascii=False)
        
        return {
            "success": True,
            "message": f"Cleaned up verification tokens for {email}",
            "tokens_removed": removed_count,
            "tokens_remaining": len(remaining_tokens),
            "cutoff_hours": hours_old,
            "cleanup_timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@app.get("/debug/escrow-statuses")
def debug_escrow_statuses():
    """
    Debug endpoint to view all escrow statuses
    
    Returns:
        JSON with all escrow statuses
    """
    
    return {
        "escrow_statuses": escrow_statuses,
        "total_escrows": len(escrow_statuses),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@app.get("/debug/escrow-creation-requests")
def debug_escrow_creation_requests():
    """
    Debug endpoint to view escrow creation request tracking (duplicate prevention)
    
    Returns:
        JSON with escrow creation request tracking
    """
    
    return {
        "escrow_creation_requests": escrow_creation_requests,
        "total_requests": len(escrow_creation_requests),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@app.get("/debug/workflow-state")
def debug_workflow_state():
    """
    Debug endpoint to view current workflow state and user email
    
    Returns:
        JSON with workflow state information
    """
    
    current_step = planned_orchestration.get_current_step()
    return {
        "current_user_email": planned_orchestration.get_current_user_email(),
        "current_step": current_step.step_type if current_step else None,
        "current_step_index": planned_orchestration.current_step_index,
        "total_steps": len(planned_orchestration.workflow_steps),
        "all_steps": planned_orchestration.get_all_steps(),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@app.get("/debug/time-info")
def debug_time_info():
    """
    Debug endpoint to view server time vs XRPL time calculations
    
    Returns:
        JSON with time information for debugging
    """
    
    import time
    current_unix_time = time.time()
    current_ripple_time = int(current_unix_time - 946684800)
    
    return {
        "server_time": {
            "unix_timestamp": current_unix_time,
            "iso_format": datetime.fromtimestamp(current_unix_time).isoformat(),
            "utc_format": datetime.fromtimestamp(current_unix_time, tz=timezone.utc).isoformat()
        },
        "ripple_time": {
            "ripple_timestamp": current_ripple_time,
            "conversion_offset": 946684800,
            "description": "Ripple epoch starts Jan 1, 2000 vs Unix epoch Jan 1, 1970"
        },
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@app.get("/debug/verification-tokens/{email}")
def debug_verification_tokens(email: str):
    """
    Debug endpoint to show cached vs filtered verification tokens for a user
    
    Args:
        email: User's email address
    
    Returns:
        JSON with detailed token comparison
    """
    
    try:
        cache_file = Path(__file__).parent / "current_cached_user_data.json"
        
        if not cache_file.exists():
            return {
                "email": email,
                "cache_file_exists": False,
                "message": "No cache file exists"
            }
        
        with open(cache_file, 'r', encoding='utf-8') as f:
            cache_data = json.load(f)
        
        if email not in cache_data:
            return {
                "email": email,
                "user_in_cache": False,
                "message": "User not found in cache"
            }
        
        user_data = cache_data[email]
        all_tokens = user_data.get("verification_tokens", [])
        
        # Apply same filtering logic as the main endpoint
        active_tokens = []
        filtered_tokens = []
        current_time = datetime.now(timezone.utc)
        
        for token in all_tokens:
            token_status = token.get("status", "pending")
            updated_at = token.get("updated_at")
            
            is_active = False
            filter_reason = ""
            
            # Always include pending tokens
            if token_status == "pending":
                is_active = True
                filter_reason = "pending_status"
            # For approved/rejected tokens, only include if recent (within last hour)
            elif token_status in ["approved", "rejected"] and updated_at:
                try:
                    token_time = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
                    time_diff = (current_time - token_time).total_seconds()
                    
                    if time_diff <= 3600:  # 1 hour
                        is_active = True
                        filter_reason = f"recent_decision_({time_diff:.0f}s_ago)"
                    else:
                        filter_reason = f"too_old_({time_diff:.0f}s_ago)"
                except Exception as e:
                    filter_reason = f"timestamp_parse_error: {e}"
            else:
                filter_reason = "no_timestamp_or_unknown_status"
            
            token_with_debug = {
                **token,
                "is_active": is_active,
                "filter_reason": filter_reason
            }
            
            if is_active:
                active_tokens.append(token_with_debug)
            else:
                filtered_tokens.append(token_with_debug)
        
        return {
            "email": email,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "user_in_cache": True,
            "total_cached_tokens": len(all_tokens),
            "active_tokens_count": len(active_tokens),
            "filtered_tokens_count": len(filtered_tokens),
            "cached_tokens": all_tokens,
            "active_tokens": active_tokens,
            "filtered_out_tokens": filtered_tokens,
            "filter_criteria": {
                "include_pending": True,
                "include_recent_decisions": "within_1_hour",
                "exclude_old_decisions": "older_than_1_hour"
            }
        }
        
    except Exception as e:
        return {
            "email": email,
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

@app.get("/debug/verifications")
def debug_verifications():
    """
    Debug endpoint to compare loaded verifications with file contents
    
    Returns:
        JSON with loaded vs file verification comparison for troubleshooting
    """
    
    try:
        # Get currently loaded verifications
        loaded_tokens = list(email_service.pending_verifications.keys())
        loaded_count = len(loaded_tokens)
        
        # Reload from file to get latest
        file_verifications = email_service._load_verifications()
        file_tokens = list(file_verifications.keys())
        file_count = len(file_tokens)
        
        # Find differences
        missing_in_memory = [token for token in file_tokens if token not in loaded_tokens]
        extra_in_memory = [token for token in loaded_tokens if token not in file_tokens]
        
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "loaded_in_memory": {
                "count": loaded_count,
                "tokens": loaded_tokens
            },
            "stored_in_file": {
                "count": file_count,
                "tokens": file_tokens
            },
            "differences": {
                "missing_in_memory": missing_in_memory,
                "extra_in_memory": extra_in_memory,
                "sync_status": "in_sync" if not missing_in_memory and not extra_in_memory else "out_of_sync"
            },
            "file_path": email_service.verifications_file,
            "recommendations": {
                "reload_needed": len(missing_in_memory) > 0,
                "cleanup_needed": len(extra_in_memory) > 0
            }
        }
        
    except Exception as e:
        return {
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "debug_failed"
        }

# Summary-related Pydantic models
class OrchestrationContextRequest(BaseModel):
    high_level_steps: List[str]
    user_metrics_query: str
    llm_provider: str = "openai"
    web_search_enabled: bool = False
    cache_user_data: Dict[str, Any] = {}

class SummaryResponse(BaseModel):
    summary: str
    provider_used: str
    web_search_enabled: bool
    user_query: str
    timestamp: str
    context_data: Dict[str, Any]
    error: Optional[str] = None

class DisplaySummaryRequest(BaseModel):
    title: str = "XRPL Loan Summary"
    summary_text: str
    metadata: Optional[Dict[str, str]] = None

# Initialize the summary node if available
if SUMMARY_AVAILABLE:
    summary_node = SummaryNode()
    print("✅ Summary node initialized")
else:
    summary_node = None
    print("❌ Summary node not available")

if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Starting XRPL Microfinance Email Verification Server...")
    print("📧 Handles approve/reject links from verification emails")
    print("🌐 Server will be available at: http://localhost:8000")
    print("📋 API docs at: http://localhost:8000/docs")
    
    uvicorn.run(
        "web_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 