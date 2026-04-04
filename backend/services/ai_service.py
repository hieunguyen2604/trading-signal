import os
import json
import httpx
import asyncio
from typing import Optional
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()

class AIService:
    """Tactical Reasoner for AETHER Terminal. Support for local (Ollama) and API (OpenAI)."""
    def __init__(self):
        self.gemini_key = os.getenv("GEMINI_API_KEY")
        
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
        """Generates a concise, professional trader justification for a signal."""
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
                return await self._get_gemini_response(prompt)
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
            print(f"Gemini API Error: {e}")
            raise e

    def _get_fallback_justification(self, signal: str, context: dict) -> str:
        """Deterministic professional justifications for offline mode."""
        if signal == "BUY":
            return "Multi-timeframe trend synchronization confirmed by liquidity accumulation."
        elif signal == "SELL":
            return "High-timeframe bearish divergence coupled with fading buyer volume."
        return "Tactical parameters within expected neutral volatility bands."

# Global singleton
ai_service = AIService()
