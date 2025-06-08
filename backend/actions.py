#DID - > SUBMIT WALLET ADD and PUBLIC key and we verify it
MOCK_SEQUENCE = [
    {
        "type": "ui_form",
        "config": { 
            "fields": ["name", "email", "loan_amount", "wallet_address"] 
        },
        "next": "did_verification"
    },
    {
        "type": "did_verification", 
        "config": { 
            "provider": "XRPL", #only supported chain
            "required_claims": ["wallet_ownership"], #only supported claim
            "xrpl_network": "testnet",
            "verification_method": "xrpl_did"
        },
        "next": "escrow_accounts"
    },
    {
        "type": "escrow_accounts",
        "config": {
            "provider": "XRPL",
            "auto_release": False,
            "approval_required": True,
            "release_condition": "email_verification",
            "wallet_address": "rfftbnikaoHPW5HffRZjyZZHBs7BHUykuh",
            "wallet_secret": "sEd7DuCrruneYUG7qa2TPCktnKov4Uz",
            "email_address": "yuv2bindal@gmail.com",
            "currency_option": "XRP" #can be RLUSD as well
        },
        "next": "summarization"
    },
    {
        "type": "summarization",
        "config": {
            "generate_report": True,
            "metrics_string": "Help me understand my loan amount and what would be a recommended repayment schedule based on industry research of these microloan amounts?",
            "llm_provider": "openai",
            "web_search": True
        },
        "next": "END"
    }
    
]