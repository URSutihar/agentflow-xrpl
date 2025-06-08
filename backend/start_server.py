#!/usr/bin/env python3
"""
Startup script for XRPL Microfinance Email Verification Server
"""

import uvicorn

if __name__ == "__main__":
    print("🚀 Starting XRPL Microfinance Email Verification Server...")
    print("📧 Handles approve/reject links from verification emails")
    print("🌐 Server will be available at: http://localhost:8000")
    print("📋 API docs at: http://localhost:8000/docs")
    print("✅ Approve endpoint: http://localhost:8000/verify/approve?token=<token>")
    print("❌ Reject endpoint: http://localhost:8000/verify/reject?token=<token>")
    print("\nPress Ctrl+C to stop the server")
    print("-" * 60)
    
    uvicorn.run(
        "backend.web_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 