from dataclasses import dataclass
from typing import Any, Dict, List

from pydantic import BaseModel

# Available workflow step types
OPTIONS = ["ui_form", "did_verification", "escrow_accounts", "summarization", "END"]

# Configuration classes
@dataclass
class BaseConfig:
    """Base configuration class for all workflow steps"""
    pass

@dataclass
class UIFormConfig(BaseConfig):
    """Configuration for UI Form workflow step"""
    fields: List[str]

@dataclass
class DIDVerificationConfig(BaseConfig):
    """Configuration for DID Verification workflow step"""
    provider: str = "XRPL"
    required_claims: List[str] = None
    xrpl_network: str = "testnet"
    verification_method: str = "xrpl_did"
    
    def __post_init__(self):
        if self.required_claims is None:
            self.required_claims = ["wallet_ownership"]

@dataclass
class EscrowAccountsConfig(BaseConfig):
    """Configuration for Escrow Accounts workflow step"""
    provider: str = "XRPL"
    auto_release: bool = False
    approval_required: bool = True
    release_condition: str = "email_verification"
    wallet_address: str = ""
    wallet_secret: str = ""
    email_address: str = ""
    currency_option: str = "XRP"

@dataclass
class SummarizationConfig(BaseConfig):
    """Configuration for Summarization workflow step"""
    generate_report: bool = True
    metrics_string: str = ""
    llm_provider: str = "openai"
    web_search: bool = True

# Base WorkflowStep class
class WorkflowStep:
    """Base class for all workflow steps"""
    
    def __init__(self, step_type: str, config: BaseConfig, next_step: str):
        self.step_type = step_type
        self.config = config
        self.next = next_step
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert step to dictionary representation"""
        return {
            "type": self.step_type,
            "config": self.config.__dict__,
            "next": self.next
        }

# Specific WorkflowStep implementations
class UIFormStep(WorkflowStep):
    """UI Form workflow step"""
    
    def __init__(self, config: UIFormConfig, next_step: str = "did_verification"):
        super().__init__("ui_form", config, next_step)
        self.form_config = config

class DIDVerificationStep(WorkflowStep):
    """DID Verification workflow step"""
    
    def __init__(self, config: DIDVerificationConfig, next_step: str = "escrow_accounts"):
        super().__init__("did_verification", config, next_step)
        self.verification_config = config

class EscrowAccountsStep(WorkflowStep):
    """Escrow Accounts workflow step"""
    
    def __init__(self, config: EscrowAccountsConfig, next_step: str = "summarization"):
        super().__init__("escrow_accounts", config, next_step)
        self.escrow_config = config

class SummarizationStep(WorkflowStep):
    """Summarization workflow step"""
    
    def __init__(self, config: SummarizationConfig, next_step: str = "END"):
        super().__init__("summarization", config, next_step)
        self.summary_config = config

# Simple workflow container
class PlannedOrchestration:
    """Simple container for workflow steps"""
    
    def __init__(self, workflow_steps: List[WorkflowStep] = None):
        self.workflow_steps = workflow_steps if workflow_steps is not None else []
        self.current_step_index = 0
        self.current_interacting_user_mail = None  # Track the current user's email
    
    def add_step(self, step: WorkflowStep):
        """Add a workflow step to the orchestration"""
        self.workflow_steps.append(step)
    
    def add_steps(self, steps: List[WorkflowStep]):
        """Add multiple workflow steps to the orchestration"""
        self.workflow_steps.extend(steps)
    
    def get_current_step(self) -> WorkflowStep:
        """Get the current workflow step"""
        if self.current_step_index < len(self.workflow_steps):
            return self.workflow_steps[self.current_step_index]
        return None
    
    def advance_to_next_step(self):
        """Move to the next step"""
        if self.current_step_index < len(self.workflow_steps) - 1:
            self.current_step_index += 1
    
    def set_current_user_email(self, email: str):
        """Set the current interacting user's email"""
        self.current_interacting_user_mail = email
        print(f"📧 Set current user email: {email}")
    
    def get_current_user_email(self) -> str:
        """Get the current interacting user's email"""
        return self.current_interacting_user_mail
    
    def get_all_steps(self) -> List[Dict[str, Any]]:
        """Get all steps as dictionaries"""
        return [step.to_dict() for step in self.workflow_steps]




class UserDataCache(BaseModel):
    # Required core fields that are always present
    name: str
    email: str  # Used as the key in the cache
    wallet_address: str
    
    # Optional timestamp field (automatically added)
    timestamp: str = None
    
    class Config:
        # Allow additional fields beyond the defined ones
        extra = "allow"
        
    def get_additional_fields(self) -> Dict[str, str]:
        """
        Get all additional fields beyond the core required ones
        
        Returns:
            Dict of additional field names and values
        """
        core_fields = {"name", "email", "wallet_address", "timestamp"}
        additional = {}
        
        for field_name, field_value in self.dict().items():
            if field_name not in core_fields and field_value is not None:
                additional[field_name] = str(field_value)
        
        return additional
    
    def get_all_form_fields(self) -> Dict[str, str]:
        """
        Get all fields formatted for form data (excluding timestamp)
        
        Returns:
            Dict of all field names and values suitable for forms
        """
        all_fields = {}
        
        for field_name, field_value in self.dict().items():
            if field_name != "timestamp" and field_value is not None:
                all_fields[field_name] = str(field_value)
        
        return all_fields
    
    @staticmethod
    def validate_field_name(field_name: str) -> bool:
        """
        Validate that a field name follows the pattern: firstword_secondword_...
        (all lowercase words separated by underscores)
        
        Args:
            field_name: Field name to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        import re

        # Core fields are always valid
        if field_name in {"name", "email", "wallet_address", "timestamp"}:
            return True
        
        # Pattern: starts with lowercase letter, followed by lowercase letters/numbers,
        # then optionally more groups of _lowercase_letters/numbers
        pattern = r'^[a-z][a-z0-9]*(?:_[a-z][a-z0-9]*)*$'
        return bool(re.match(pattern, field_name))
    
    def validate_all_fields(self) -> Dict[str, bool]:
        """
        Validate all field names in this instance
        
        Returns:
            Dict mapping field names to their validation status
        """
        validation_results = {}
        
        for field_name in self.dict().keys():
            validation_results[field_name] = self.validate_field_name(field_name)
        
        return validation_results