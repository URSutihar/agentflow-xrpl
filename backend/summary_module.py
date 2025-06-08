from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import openai
import requests
from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv()


class MarketRatesAnalysis(BaseModel):
    """Market rates and standards analysis"""
    xrp_current_value: float = Field(description="Current XRP value in USD")
    lending_rates_range: str = Field(description="Interest rate range for microloans")
    market_volatility_assessment: str = Field(description="Assessment of market volatility")
    industry_standards: List[str] = Field(description="List of industry standards")


class RiskAssessment(BaseModel):
    """Risk assessment for the microloan"""
    risk_level: str = Field(description="Overall risk level (Low, Medium, High)")
    risk_score: int = Field(description="Risk score from 1-10", ge=1, le=10)
    risk_factors: List[str] = Field(description="List of identified risk factors")
    mitigation_strategies: List[str] = Field(description="Risk mitigation strategies")


class RepaymentSchedule(BaseModel):
    """Recommended repayment schedule"""
    loan_amount_usd: float = Field(description="Loan amount in USD")
    interest_rate_annual: float = Field(description="Annual interest rate percentage")
    repayment_term_months: int = Field(description="Repayment term in months")
    monthly_payment_usd: float = Field(description="Monthly payment amount in USD")
    total_repayment_usd: float = Field(description="Total amount to be repaid in USD")
    payment_frequency: str = Field(description="Payment frequency (weekly, monthly, etc.)")


class MarketTrends(BaseModel):
    """Market trends affecting the loan"""
    price_predictions: Dict[str, float] = Field(description="Price predictions by timeframe")
    regulatory_outlook: str = Field(description="Regulatory environment outlook")
    institutional_adoption_impact: str = Field(description="Impact of institutional adoption")
    market_sentiment: str = Field(description="Current market sentiment")


class NextStepsRecommendations(BaseModel):
    """Next steps and management recommendations"""
    immediate_actions: List[str] = Field(description="Immediate actions to take")
    ongoing_monitoring: List[str] = Field(description="Ongoing monitoring requirements")
    risk_management: List[str] = Field(description="Risk management recommendations")
    communication_plan: List[str] = Field(description="Communication plan with borrower")


class UserProfileAnalysis(BaseModel):
    """User profile analysis"""
    profile_completeness: str = Field(description="Profile completeness assessment")
    verification_status: str = Field(description="Verification status")
    creditworthiness_factors: List[str] = Field(description="Factors affecting creditworthiness")
    recommended_actions: List[str] = Field(description="Recommended actions for user")


class RejectionAnalysis(BaseModel):
    """Detailed analysis for rejected loans"""
    rejection_factors: List[str] = Field(description="Specific factors that led to rejection")
    data_quality_issues: List[str] = Field(description="Issues with data quality or completeness")
    regulatory_concerns: List[str] = Field(description="Regulatory or compliance issues")
    market_conditions_impact: str = Field(description="How market conditions influenced rejection")
    improvement_recommendations: List[str] = Field(description="Specific steps to improve for reapplication")
    reapplication_timeline: str = Field(description="Recommended timeline for reapplication")
    success_probability_factors: List[str] = Field(description="Factors that would increase success chances")


class StructuredLoanSummary(BaseModel):
    """Complete structured loan summary"""
    user_profile: UserProfileAnalysis
    market_analysis: MarketRatesAnalysis
    risk_assessment: RiskAssessment
    repayment_schedule: RepaymentSchedule
    market_trends: MarketTrends
    next_steps: NextStepsRecommendations
    rejection_analysis: Optional[RejectionAnalysis] = Field(None, description="Detailed rejection analysis (only for rejected loans)")
    summary_metadata: Dict[str, Any] = Field(description="Metadata about the summary")
    key_recommendations: List[str] = Field(description="Top 3-5 key recommendations")


@dataclass
class OrchestrationContext:
    high_level_steps: List[str]
    user_metrics_query: str
    llm_provider: str = "openai"  # "openai", "perplexity", "gemini"
    web_search_enabled: bool = False
    cache_user_data: Dict[str, Any] = None
    
    def __post_init__(self):
        """Initialize cache_user_data as empty dict if None"""
        if self.cache_user_data is None:
            self.cache_user_data = {}


class LLMProvider:
    """Base class for LLM providers"""
    
    def __init__(self):
        self.api_key = None
    
    def generate_summary(self, context: OrchestrationContext) -> str:
        raise NotImplementedError


class OpenAIProvider(LLMProvider):
    """OpenAI GPT provider"""
    
    def __init__(self):
        super().__init__()
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        
        # Initialize OpenAI client with API key
        self.client = openai.OpenAI(api_key=self.api_key)
    
    def generate_summary(self, context: OrchestrationContext) -> str:
        prompt = self._create_prompt(context)
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert XRPL microfinance analyst. Generate comprehensive, detailed loan analysis reports with professional formatting."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2000,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            return f"❌ OpenAI API Error: {str(e)}\n\n" + self._create_fallback_summary(context)
    
    def _create_prompt(self, context: OrchestrationContext) -> str:
        loan_amount = context.cache_user_data.get('loan_amount', 0)
        currency = context.cache_user_data.get('currency_used', 'XRP')
        loan_status = context.cache_user_data.get('loan_status', 'pending')
        
        # Create rejection analysis instruction if status is rejected
        rejection_focus = ""
        if loan_status.lower() == "rejected":
            rejection_focus = """
🚨 CRITICAL FOCUS - REJECTION ANALYSIS:
Since this loan was REJECTED, provide detailed analysis of WHY the rejection occurred:
- Specific rejection factors from the user data
- Risk factors that led to rejection
- Data quality issues or missing information
- Regulatory or compliance concerns
- Market conditions that influenced the decision
- Detailed recommendations for future loan approval
- Step-by-step improvement plan for the user
"""
        
        # Include ALL cache_data fields in the prompt
        cache_data_str = json.dumps(context.cache_user_data, indent=2)
        
        return f"""
Analyze this XRPL microloan application and provide a comprehensive detailed summary:

COMPLETE USER DATA (ALL FIELDS):
{cache_data_str}

LOAN DETAILS:
- Requested Amount: {loan_amount} {currency}
- Currency: {currency}
- Current Status: {loan_status}

WORKFLOW STEPS COMPLETED: {', '.join(context.high_level_steps)}

USER QUERY: "{context.user_metrics_query}"

{rejection_focus}

Please provide a comprehensive analysis covering:

1. **USER PROFILE ANALYSIS**
   - Profile completeness assessment
   - Verification status evaluation
   - Creditworthiness factors analysis

2. **MARKET ANALYSIS**
   - Current XRP market conditions
   - Industry lending rates for {loan_amount} {currency}
   - Market volatility assessment
   - Industry standards comparison

3. **RISK ASSESSMENT**
   - Overall risk level and score (1-10)
   - Specific risk factors identified
   - Risk mitigation strategies

4. **REPAYMENT ANALYSIS**
   - Recommended repayment schedule
   - Interest rate suggestions
   - Payment frequency recommendations
   - Total cost analysis

5. **MARKET TRENDS & PREDICTIONS**
   - XRP price predictions (3, 6, 12 months)
   - Regulatory outlook
   - Market sentiment analysis

6. **NEXT STEPS & RECOMMENDATIONS**
   - Immediate actions required
   - Long-term monitoring needs
   - Risk management strategies
   - Communication plan

{"7. **DETAILED REJECTION ANALYSIS** (Focus heavily on this since loan is REJECTED)" if loan_status.lower() == "rejected" else ""}

Format this as a professional, comprehensive report suitable for loan decision making.
Analyze ALL user data fields provided, not just the basic ones.
"""
    
    def _create_fallback_summary(self, context: OrchestrationContext) -> str:
        """Create a fallback text summary when API fails"""
        
        loan_amount = context.cache_user_data.get("loan_amount", 0)
        currency = context.cache_user_data.get("currency_used", "XRP")
        loan_status = context.cache_user_data.get("loan_status", "pending")
        
        return f"""
🏦 XRPL MICROLOAN ANALYSIS (Fallback Mode)
==========================================

👤 USER PROFILE:
   Name: {context.cache_user_data.get('name', 'Unknown')}
   Email: {context.cache_user_data.get('email', 'Unknown')}
   Wallet: {context.cache_user_data.get('wallet_address', 'Unknown')}

💰 LOAN DETAILS:
   Amount: {loan_amount} {currency}
   Status: {loan_status.upper()}
   
⚠️ BASIC ASSESSMENT:
   Risk Level: Medium
   Estimated Interest: 10-15% annually
   
📋 RECOMMENDATIONS:
   - Complete full verification process
   - Provide additional documentation
   - Consider smaller initial loan amount
   - Review application in 30 days

❌ Note: Full analysis unavailable due to API service issues.
Please retry analysis or contact technical support.
"""


class PerplexityProvider(LLMProvider):
    """Perplexity Sonar Pro provider with web search"""
    
    def __init__(self):
        super().__init__()
        self.api_key = os.getenv("PERPLEXITY_API_KEY")
        if not self.api_key:
            raise ValueError("PERPLEXITY_API_KEY environment variable not set")
    
    def generate_summary(self, context: OrchestrationContext) -> str:
        prompt = self._create_prompt(context)
        
        try:
            print(f"🔍 Perplexity API call starting...")
            print(f"🔍 API Key present: {bool(self.api_key)}")
            
            url = "https://api.perplexity.ai/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": "llama-3.1-sonar-large-128k-online",
                "messages": [
                    {"role": "system", "content": "You are an expert XRPL microfinance analyst with access to real-time market data. Generate comprehensive, detailed loan analysis reports with professional formatting using current market data."},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 2000,
                "temperature": 0.7
            }
            
            print(f"🔍 Making API request to: {url}")
            response = requests.post(url, headers=headers, json=data, timeout=30)
            print(f"🔍 Response status: {response.status_code}")
            
            response.raise_for_status()
            
            result = response.json()
            print(f"✅ Perplexity API call successful!")
            return result["choices"][0]["message"]["content"].strip()
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Perplexity API request error: {e}")
            return f"❌ Perplexity API Error: {str(e)}\n\n" + self._create_fallback_summary(context)
        except KeyError as e:
            print(f"❌ Unexpected response format: {e}")
            return f"❌ Perplexity Response Error: {str(e)}\n\n" + self._create_fallback_summary(context)
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return f"❌ Perplexity Error: {str(e)}\n\n" + self._create_fallback_summary(context)
    
    def _create_prompt(self, context: OrchestrationContext) -> str:
        loan_amount = context.cache_user_data.get('loan_amount', 0)
        currency = context.cache_user_data.get('currency_used', 'XRP')
        loan_status = context.cache_user_data.get('loan_status', 'pending')
        
        # Create rejection analysis instruction if status is rejected
        rejection_focus = ""
        if loan_status.lower() == "rejected":
            rejection_focus = """
🚨 CRITICAL FOCUS - REJECTION ANALYSIS (Use web search for industry data):
Since this loan was REJECTED, research and analyze:
- Common reasons for crypto microloan rejections in current market
- Industry standards that this application may have failed to meet
- Regulatory requirements that weren't satisfied
- Current market conditions that influenced the rejection
- Best practices for reapplying after rejection in crypto lending
- Real-time data on successful vs rejected microloan profiles
- Steps to improve creditworthiness in crypto lending market
"""
        
        # Include ALL cache_data fields in the prompt
        cache_data_str = json.dumps(context.cache_user_data, indent=2)
        
        return f"""
Research and analyze this XRPL microloan application using current market data and provide a comprehensive detailed summary:

COMPLETE USER DATA (ALL FIELDS):
{cache_data_str}

LOAN DETAILS:
- Requested Amount: {loan_amount} {currency}
- Currency: {currency}
- Current Status: {loan_status}

WORKFLOW STEPS COMPLETED: {', '.join(context.high_level_steps)}

USER QUERY: "{context.user_metrics_query}"

{rejection_focus}

Use web search to research current market conditions and provide a comprehensive analysis covering:

1. **REAL-TIME MARKET RESEARCH**
   - Current XRP price and market conditions
   - Latest crypto lending rates and standards
   - Recent regulatory developments affecting microloans

2. **USER PROFILE ANALYSIS** 
   - Complete assessment using ALL provided user data fields
   - Verification status evaluation
   - Profile strengths and weaknesses

3. **INDUSTRY COMPARISON**
   - How this application compares to current market standards
   - Benchmark against successful {loan_amount} {currency} loans
   - Industry best practices analysis

4. **RISK ASSESSMENT WITH MARKET DATA**
   - Current market volatility impact
   - Crypto-specific risk factors
   - Real-time risk mitigation strategies

5. **MARKET-INFORMED REPAYMENT ANALYSIS**
   - Current industry rates for {loan_amount} {currency}
   - Competitive repayment schedules
   - Market-based recommendations

6. **CURRENT TRENDS & PREDICTIONS**
   - Latest XRP price predictions and analysis
   - Regulatory outlook with recent developments
   - Market sentiment from recent news

7. **DATA-BACKED RECOMMENDATIONS**
   - Immediate actions based on current market
   - Industry-standard next steps
   - Market-informed improvement strategies

{"8. **COMPREHENSIVE REJECTION ANALYSIS** (Research why similar loans are rejected currently)" if loan_status.lower() == "rejected" else ""}

Provide a detailed, professional report with real-time market insights and data-backed recommendations.
Use web search extensively to provide current, accurate market information.
"""
    
    def _create_fallback_summary(self, context: OrchestrationContext) -> str:
        """Create a fallback text summary when API fails"""
        
        loan_amount = context.cache_user_data.get("loan_amount", 0)
        currency = context.cache_user_data.get("currency_used", "XRP")
        loan_status = context.cache_user_data.get("loan_status", "pending")
        
        return f"""
🏦 XRPL MICROLOAN ANALYSIS (Web Search Unavailable)
=================================================

👤 USER PROFILE:
   Name: {context.cache_user_data.get('name', 'Unknown')}
   Email: {context.cache_user_data.get('email', 'Unknown')}
   Wallet: {context.cache_user_data.get('wallet_address', 'Unknown')}

💰 LOAN DETAILS:
   Amount: {loan_amount} {currency}
   Status: {loan_status.upper()}
   
📊 ESTIMATED MARKET CONDITIONS:
   XRP Value: ~$2.20 (estimate)
   Crypto Lending Rates: 8-25% annually
   Market Volatility: High
   
⚠️ BASIC ASSESSMENT:
   Risk Level: Medium-High (crypto volatility)
   Estimated Interest: 12-18% annually
   
📋 RECOMMENDATIONS:
   - Verify current XRP market conditions
   - Research latest crypto lending standards
   - Consider collateral requirements
   - Monitor regulatory developments
   - Implement real-time risk management

❌ Note: Real-time market data unavailable due to API issues.
Please retry with working web search for current market analysis.
"""


class GeminiProvider(LLMProvider):
    """Google Gemini 2.5 Flash provider"""
    
    def __init__(self):
        super().__init__()
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")
    
    def generate_summary(self, context: OrchestrationContext) -> str:
        prompt = self._create_prompt(context)
        
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent?key={self.api_key}"
            headers = {"Content-Type": "application/json"}
            
            data = {
                "contents": [{
                    "parts": [{
                        "text": f"You are an expert XRPL microfinance analyst with advanced reasoning capabilities. Generate comprehensive, detailed loan analysis reports with professional formatting and deep analytical insights. {prompt}"
                    }]
                }],
                "generationConfig": {
                    "temperature": 0.7,
                    "maxOutputTokens": 2000
                }
            }
            
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            
            result = response.json()
            return result["candidates"][0]["content"]["parts"][0]["text"].strip()
            
        except Exception as e:
            return f"❌ Gemini API Error: {str(e)}\n\n" + self._create_fallback_summary(context)
    
    def _create_prompt(self, context: OrchestrationContext) -> str:
        loan_amount = context.cache_user_data.get('loan_amount', 0)
        currency = context.cache_user_data.get('currency_used', 'XRP')
        loan_status = context.cache_user_data.get('loan_status', 'pending')
        
        # Create rejection analysis instruction if status is rejected
        rejection_focus = ""
        if loan_status.lower() == "rejected":
            rejection_focus = """
🚨 CRITICAL FOCUS - ADVANCED REJECTION ANALYSIS:
Since this loan was REJECTED, use your advanced reasoning to analyze:
- Multi-factor analysis of why this specific application was rejected
- Pattern recognition from the user data that indicates rejection factors
- Complex interactions between data fields that led to rejection
- Predictive analysis of what changes would improve approval chances
- Systematic evaluation of gaps in the application
- Advanced recommendations for profile optimization
- Probability modeling for successful reapplication
"""
        
        # Include ALL cache_data fields in the prompt
        cache_data_str = json.dumps(context.cache_user_data, indent=2)
        
        return f"""
Analyze this XRPL microloan application with your advanced reasoning capabilities and provide a comprehensive detailed summary:

COMPLETE USER DATA (ALL FIELDS):
{cache_data_str}

LOAN DETAILS:
- Requested Amount: {loan_amount} {currency}
- Currency: {currency}
- Current Status: {loan_status}

WORKFLOW STEPS COMPLETED: {', '.join(context.high_level_steps)}

USER QUERY: "{context.user_metrics_query}"

{rejection_focus}

Apply advanced multi-variable analysis and provide a comprehensive assessment covering:

1. **ADVANCED USER PROFILE ANALYSIS**
   - Deep assessment using ALL provided user data fields
   - Pattern recognition in user behavior/data
   - Complex creditworthiness modeling

2. **SOPHISTICATED MARKET ANALYSIS**
   - Multi-dimensional market condition assessment
   - Advanced risk-adjusted lending rates for {loan_amount} {currency}
   - Predictive market volatility modeling

3. **COMPLEX RISK ASSESSMENT**
   - Multi-factor risk scoring with advanced algorithms
   - Cross-correlation analysis of risk factors
   - Dynamic risk mitigation strategies

4. **OPTIMIZED REPAYMENT MODELING**
   - AI-optimized repayment schedules
   - Adaptive interest rate recommendations
   - Predictive payment behavior analysis

5. **ADVANCED MARKET PREDICTIONS**
   - Multi-model XRP price forecasting
   - Regulatory impact analysis
   - Institutional behavior predictions

6. **INTELLIGENT RECOMMENDATIONS**
   - Machine learning-informed next steps
   - Predictive optimization strategies
   - Advanced risk management protocols

{"7. **DEEP REJECTION ANALYSIS** (Apply advanced pattern recognition to understand rejection factors)" if loan_status.lower() == "rejected" else ""}

Provide a sophisticated, data-driven analysis that demonstrates advanced reasoning and predictive capabilities.
Consider edge cases and complex interactions between all data fields.
Use pattern recognition and predictive modeling for comprehensive assessment.
"""
    
    def _create_fallback_summary(self, context: OrchestrationContext) -> str:
        """Create a fallback text summary when API fails"""
        
        loan_amount = context.cache_user_data.get("loan_amount", 0)
        currency = context.cache_user_data.get("currency_used", "XRP")
        loan_status = context.cache_user_data.get("loan_status", "pending")
        
        return f"""
🏦 XRPL MICROLOAN ANALYSIS (Advanced AI Unavailable)
==================================================

👤 USER PROFILE:
   Name: {context.cache_user_data.get('name', 'Unknown')}
   Email: {context.cache_user_data.get('email', 'Unknown')}
   Wallet: {context.cache_user_data.get('wallet_address', 'Unknown')}

💰 LOAN DETAILS:
   Amount: {loan_amount} {currency}
   Status: {loan_status.upper()}
   
🤖 AI-OPTIMIZED ESTIMATES:
   XRP Value: ~$2.20 (model estimate)
   AI-Suggested Rates: 9-16% annually
   ML Risk Score: Medium (6/10)
   
⚠️ BASIC ASSESSMENT:
   Risk Level: Medium (requires advanced analysis)
   Estimated Interest: 10-15% annually
   
📋 RECOMMENDATIONS:
   - Apply advanced AI risk modeling
   - Use multi-factor verification systems
   - Implement predictive analytics
   - Consider adaptive loan terms
   - Deploy behavioral pattern analysis

❌ Note: Advanced AI analysis unavailable due to API issues.
Please retry for sophisticated multi-dimensional assessment.
"""


class SummaryNode:
    """
    Summary node that processes OrchestrationContext and generates 
    comprehensive summaries using LLM providers.
    """
    
    def __init__(self):
        self.providers = {
            "openai": OpenAIProvider,
            "perplexity": PerplexityProvider, 
            "gemini": GeminiProvider
        }
    
    def process_context(self, context: OrchestrationContext) -> Dict[str, Any]:
        """
        Process the orchestration context and generate a comprehensive summary using LLMs
        
        Args:
            context: OrchestrationContext with user data and workflow info
            
        Returns:
            Dictionary with LLM-generated summary information
        """
        
        # Determine which provider to use
        provider_name = self._select_provider(context)
        print(f"🎯 Selected provider: {provider_name}")
        
        try:
            # Initialize the selected provider
            provider_class = self.providers[provider_name]
            print(f"🔧 Initializing {provider_name} provider...")
            
            try:
                provider = provider_class()
                print(f"✅ {provider_name} provider initialized successfully")
            except ValueError as e:
                print(f"❌ {provider_name} provider initialization failed: {e}")
                return self._generate_fallback_response(context, f"{provider_name} initialization error: {e}")
            
            # Generate summary using LLM
            print(f"🚀 Generating summary with {provider_name}...")
            summary_text = provider.generate_summary(context)
            
            # Return as dictionary with additional metadata
            return {
                "summary": summary_text,
                "provider_used": provider_name,
                "web_search_enabled": context.web_search_enabled,
                "user_query": context.user_metrics_query,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "context_data": {
                    "user_name": context.cache_user_data.get("name", "Unknown"),
                    "loan_amount": context.cache_user_data.get("loan_amount", 0),
                    "currency": context.cache_user_data.get("currency_used", "XRP"),
                    "loan_status": context.cache_user_data.get("loan_status", "pending"),
                    "workflow_steps": context.high_level_steps
                }
            }
            
        except Exception as e:
            # Fallback to basic summary if LLM fails
            print(f"⚠️ LLM generation failed: {e}")
            return self._generate_fallback_response(context, str(e))
    
    def get_summary_text(self, context: OrchestrationContext) -> str:
        """
        Get the summary text directly
        
        Args:
            context: OrchestrationContext with user data and workflow info
            
        Returns:
            Summary text string
        """
        
        provider_name = self._select_provider(context)
        
        try:
            provider_class = self.providers[provider_name]
            provider = provider_class()
            return provider.generate_summary(context)
            
        except Exception as e:
            print(f"⚠️ LLM generation failed: {e}")
            return f"❌ Summary Generation Error: {str(e)}\n\n" + self._create_basic_fallback_summary(context, str(e))
    
    def _select_provider(self, context: OrchestrationContext) -> str:
        """
        Select the appropriate LLM provider based on context
        
        Args:
            context: OrchestrationContext
            
        Returns:
            String name of the provider to use
        """
        
        # If web search is enabled, always use Perplexity
        if context.web_search_enabled:
            return "perplexity"
        
        # Otherwise use the specified provider
        provider = context.llm_provider.lower()
        if provider in self.providers:
            return provider
        else:
            print(f"⚠️ Unknown provider '{provider}', defaulting to OpenAI")
            return "openai"
    
    def _generate_fallback_response(self, context: OrchestrationContext, error: str) -> Dict[str, Any]:
        """Generate a fallback response when LLM calls fail"""
        
        fallback_summary = self._create_basic_fallback_summary(context, error)
        
        return {
            "summary": fallback_summary,
            "provider_used": "fallback",
            "error": error,
            "web_search_enabled": context.web_search_enabled,
            "user_query": context.user_metrics_query,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "context_data": {
                "user_name": context.cache_user_data.get("name", "Unknown"),
                "loan_amount": context.cache_user_data.get("loan_amount", 0),
                "currency": context.cache_user_data.get("currency_used", "XRP"),
                "loan_status": context.cache_user_data.get("loan_status", "pending"),
                "workflow_steps": context.high_level_steps
            }
        }
    
    def _create_basic_fallback_summary(self, context: OrchestrationContext, error: str) -> str:
        """Create a basic fallback text summary"""
        
        loan_amount = context.cache_user_data.get("loan_amount", 0)
        currency = context.cache_user_data.get("currency_used", "XRP")
        loan_status = context.cache_user_data.get("loan_status", "pending")
        
        return f"""
🏦 XRPL MICROLOAN ANALYSIS (System Fallback)
============================================

👤 USER PROFILE:
   Name: {context.cache_user_data.get('name', 'Unknown')}
   Email: {context.cache_user_data.get('email', 'Unknown')}
   Wallet: {context.cache_user_data.get('wallet_address', 'Unknown')}

💰 LOAN DETAILS:
   Amount: {loan_amount} {currency}
   Status: {loan_status.upper()}
   
⚠️ BASIC ASSESSMENT:
   Risk Level: Medium (requires full analysis)
   Estimated Interest: 10-15% annually
   
📋 RECOMMENDATIONS:
   - Complete full verification process
   - Provide additional documentation
   - Consider smaller initial loan amount
   - Review application in 30 days
   - Contact technical support for full analysis

❌ Error Details: {error}

Note: Full analysis unavailable due to system issues.
Please retry analysis or contact technical support.
"""
    

if __name__ == "__main__":
    # Example usage
    user_metrics_query = "Help me understand my loan amount and what would be a recommended repayment schedule based on industry research of these microloan amounts?"
    web_search_enabled = True
    
    # Sample cache data matching the user's format
    sample_cache_data = {
        "name": "Yuv Bindal",
        "email": "yuv2bindal@gmail.com", 
        "wallet_address": "rsAievSV26WYo5KLSBwBQDyMb9tUSBbtdD",
        "timestamp": "2025-06-07T19:19:11.865757+00:00",
        "loan_amount": "1",
        "currency_used": "XRP",
        "loan_status": "rejected"
    }
    
    orchestration_context = OrchestrationContext(
        high_level_steps=["ui_form", "did_verification", "escrow_accounts", "summarization"],
        user_metrics_query=user_metrics_query,
        llm_provider="openai",
        web_search_enabled=web_search_enabled,
        cache_user_data=sample_cache_data
    )
    
    # Create summary node and process context
    summary_node = SummaryNode()
    summary_result = summary_node.process_context(orchestration_context)
    
    print("🏦 LLM-GENERATED SUMMARY")
    print("=" * 50)
    print(f"Provider Used: {summary_result['provider_used']}")
    print(f"Web Search: {'Enabled' if summary_result['web_search_enabled'] else 'Disabled'}")
    print("=" * 50)
    
    # Display summary in readable format
    summary_text = summary_result["summary"]
    print(summary_text)
    
    print("\n" + "=" * 50)
    print("📊 FULL SUMMARY JSON")
    print("=" * 50)
    print(json.dumps(summary_result, indent=2))
