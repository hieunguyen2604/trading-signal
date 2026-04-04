import os
import json
import httpx
import asyncio
import time
from typing import Optional, Dict
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()

class AIService:
    """Tactical Reasoner for AETHER Terminal. Support for local (Ollama) and API (OpenAI)."""
    def __init__(self):
        self.gemini_key = os.getenv("GEMINI_API_KEY")
        self.justification_cache: Dict[str, dict] = {} # Key: symbol+signal, Value: {"text": str, "timestamp": float}
        self.CACHE_TTL = 300 # 5 minutes
        self.last_429_time = 0.0 # Circuit breaker for 429 errors
        self.COOLDOWN_PERIOD = 60 # Stop background AI for 60s on quota hit
        
        if self.gemini_key:
            self.provider = "GEMINI"
            self.model = "gemini-2.0-flash" # Default to 2.0-flash
            genai.configure(api_key=self.gemini_key)
            self.client = genai.GenerativeModel(self.model)
            print(f"AI Service: Initialized with GEMINI ({self.model})")
        else:
            self.provider = "OFFLINE"
            self.model = "N/A"
            self.client = None
            print("AI Service: Initialized in OFFLINE mode (No Gemini Key)")

    async def get_tactical_justification(self, symbol: str, signal: str, score: int, context: dict) -> str:
        """Generates a concise, professional trader justification for a signal with caching."""
        
        # 1. Check Cache first to save quota
        cache_key = f"{symbol}_{signal}_{score // 5}" # Round score to nearest 5 for better cache reuse
        now = time.time()
        
        if cache_key in self.justification_cache:
            entry = self.justification_cache[cache_key]
            if now - entry["timestamp"] < self.CACHE_TTL:
                return entry["text"]

        # 2. Circuit Breaker: Check if we are in 429 cooldown
        if now - self.last_429_time < self.COOLDOWN_PERIOD:
            return self._get_fallback_justification(signal, context)

        prompt = f"""
        Act as an institutional quantitative trader. 
        Analyze this signal: {symbol} {signal} (Score: {score}/100)
        Market Context:
        - 15M Trend: {context.get('trend_1st', 'N/A')}
        - 1H Trend: {context.get('trend_2nd', 'N/A')}
        - BTC Trend: {context.get('btc_trend', 'N/A')}
        - Sentiment: {context.get('sentiment_alignment', 'NEUTRAL')}
        
        Provide a concise, professional justification for this trade. 
        Limit to 10-12 words. Do NOT use emojis. Tone: Elite, Data-driven.
        """
        
        try:
            if self.provider == "GEMINI" and self.client:
                text = await self._get_gemini_response(prompt)
                
                # Cache the new justification
                self.justification_cache[cache_key] = {
                    "text": text,
                    "timestamp": now
                }
                return text
            else:
                return self._get_fallback_justification(signal, context)
        except Exception as e:
            # Silent fallback to professional mock to prevent dashboard lag on connection failure
            print(f"AI Reasoner Error: {e}")
            return self._get_fallback_justification(signal, context)

    async def _get_gemini_response(self, prompt: str) -> str:
        """Call Google Gemini API."""
        try:
            # Using generate_content_async for non-blocking call
            response = await self.client.generate_content_async(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=30,
                    temperature=0.3,
                )
            )
            return response.text.strip()
        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "ResourceExhausted" in error_str:
                self.last_429_time = time.time()
                print("!!! AI QUOTA HIT: Activating circuit breaker (60s cooldown) !!!")
            
            print(f"Gemini API Error: {e}")
            raise e

    async def chat(self, messages: list) -> str:
        """General AI conversation with market awareness."""
        if self.provider != "GEMINI" or not self.client:
            return "AI Service is currently offline. Please check your Gemini API key."
            
        try:
            # Convert simple message format to Gemini's history format
            history = []
            for msg in messages[:-1]:
                role = "user" if msg["role"] == "user" else "model"
                history.append({"role": role, "parts": [msg["content"]]})
            
            chat_session = self.client.start_chat(history=history)
            last_message = messages[-1]["content"]
            
            # System prompt for context-aware chatting
            system_context = """
            You are AETHER AI, an elite crypto trading assistant. 
            Tone: Professional, data-driven, concise. 
            Assist users with signals, risk management, and market outlook.
            """
            
            response = await chat_session.send_message_async(
                f"{system_context}\n\nUser: {last_message}",
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=500,
                    temperature=0.7,
                )
            )
            return response.text.strip()
        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "ResourceExhausted" in error_str:
                self.last_429_time = time.time() # Also trigger cooldown from chat hits
                return "Gemini API Quota Exceeded. The background assistant is currently busy. Please wait a moment before trying again."
            
            print(f"AI Chat Error: {e}")
            return "I encountered an error processing your request. Please try again."

    def _get_fallback_justification(self, signal: str, context: dict) -> str:
        """Deterministic professional justifications for offline mode."""
        if signal == "BUY":
            return "Multi-timeframe trend synchronization confirmed by liquidity accumulation."
        elif signal == "SELL":
            return "High-timeframe bearish divergence coupled with fading buyer volume."
        return "Tactical parameters within expected neutral volatility bands."

# Global singleton
ai_service = AIService()
