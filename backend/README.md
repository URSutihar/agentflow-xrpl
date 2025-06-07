# XRPL DID Verification Module

A comprehensive DID (Decentralized Identity) verification system built for microfinance applications on the XRP Ledger.

## Features

- 🔐 **XRPL-based DID verification** with cryptographic challenge-response
- 📄 **W3C compliant DID documents** and verifiable credentials
- 🏦 **Microfinance-specific claims** (identity, age, credit score verification)
- 🌐 **XRPL Testnet integration** using `https://s.altnet.rippletest.net:51234/`
- ⚡ **FastAPI ready** for production deployment

## Quick Setup with Poetry

### 1. Install Poetry (if not already installed)
```bash
curl -sSL https://install.python-poetry.org | python3 -
# or
pip install poetry
```

### 2. Install Dependencies
```bash
# Navigate to the backend directory
cd backend

# Install all dependencies (this resolves conflicts automatically)
poetry install

# Install only production dependencies
poetry install --only=main
```

### 3. Activate Virtual Environment
```bash
poetry shell
```

### 4. Run the DID Verification Test
```bash
python did_verification_module.py
```

## Resolving Dependency Conflicts

Poetry automatically resolves the dependency conflicts you encountered with pip. The `pyproject.toml` file specifies:

- `httpx = "^0.27.0"` (compatible with e2b, langgraph-sdk, langgraph-api)
- `httpcore = "^1.0.5"` (compatible with e2b requirements)
- Proper version constraints for all XRPL dependencies

### If you still have conflicts:
```bash
# Clear Poetry cache
poetry cache clear --all pypi

# Update lock file
poetry lock --no-update

# Fresh install
poetry install
```

## Usage Examples

### Generate DID Challenge
```python
from did_verification_module import generate_signed_challenge

challenge = generate_signed_challenge(
    wallet_address="rYourXRPLAddress...",
    public_key="ED0279E1D277637CF5B75D1CEEDE9E1F92B3D8FA05D5DB9FB4F5C4F2D4B4D3C2F1A",
    private_key="sYourSeedPhrase...",
    challenge_data={
        "did_verification": True,
        "microfinance_application": True,
        "required_claims": ["identity", "age_verification", "credit_score"],
        "loan_amount": "1000_USD"
    }
)
```

### Verify DID Challenge
```python
from did_verification_module import verify_signed_challenge

result = verify_signed_challenge(
    challenge, 
    expected_address="rYourXRPLAddress..."
)

if result['verified']:
    print("✅ DID verification successful!")
    credential = result['verifiable_credential']
```

## API Integration

### FastAPI Endpoints (coming next)
- `POST /did/challenge` - Generate challenge
- `POST /did/verify` - Verify challenge  
- `GET /did/{address}` - Get DID document
- `POST /credentials/issue` - Issue verifiable credential

## Development

### Run Tests
```bash
poetry run pytest
```

### Code Formatting
```bash
poetry run black .
poetry run flake8 .
```

### Type Checking
```bash
poetry run mypy .
```

## XRPL Testnet Configuration

The module is pre-configured for XRPL Testnet:
- **Network**: `https://s.altnet.rippletest.net:51234/`
- **Faucet**: Use [XRPL Testnet Faucet](https://xrpl.org/xrp-testnet-faucet.html) for test XRP
- **Explorer**: [Testnet Explorer](https://testnet.xrpl.org/)

## Environment Variables

Create a `.env` file:
```env
XRPL_NETWORK_URL=https://s.altnet.rippletest.net:51234/
MICROFINANCE_DOMAIN=microfinance.xrpl.org
DID_CACHE_TTL=3600
```

## Microfinance Workflow Integration

This module integrates with your whiteboard orchestration tool:

```python
# Example workflow step
{
    "type": "did_verification",
    "config": {
        "provider": "XRPL",
        "required_claims": ["identity", "age_verification", "credit_score"],
        "xrpl_network": "testnet",
        "verification_method": "xrpl_did"
    },
    "next": "email_verification"
}
```

## Troubleshooting

### Poetry Issues
- **Lock file conflicts**: `poetry lock --no-update`
- **Cache issues**: `poetry cache clear --all pypi`
- **Environment issues**: `poetry env remove python && poetry install`

### XRPL Issues
- **Connection errors**: Verify testnet URL is accessible
- **Signing errors**: Ensure private key format is correct (starts with 's')
- **Account not found**: Create account using testnet faucet

## Next Steps

1. ✅ DID Verification Module (Complete)
2. 🔲 FastAPI endpoints creation
3. 🔲 Frontend integration
4. 🔲 Escrow account integration
5. 🔲 Complete workflow orchestration

---

**Ready for production?** Switch `XRPL_NETWORK_URL` to mainnet: `https://xrplcluster.com` 