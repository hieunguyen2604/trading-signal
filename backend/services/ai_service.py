import os
import json
import httpx
import asyncio
import time
from typing import Optional, Dict
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

class AIService:
    """Provides AI-driven tactical justifications and reasoning for trading signals."""
    ACTIVE_MODE = "AETHER"
    
    def __init__(self):
        self.gemini_key = os.getenv("GEMINI_API_KEY")
        self.justification_cache: Dict[str, dict] = {}
        self.CACHE_TTL = 300
        self.last_429_time = 0.0
        self.COOLDOWN_PERIOD = 60
        
        if self.gemini_key:
            self.provider = "GEMINI"
            self.model = "gemini-2.0-flash"
            genai.configure(api_key=self.gemini_key)
            self.client = genai.GenerativeModel(self.model)
        else:
            self.provider = "OFFLINE"
            self.model = "N/A"
            self.client = None

    async def get_tactical_justification(self, symbol: str, signal: str, score: int, context: dict) -> str:
        """Generates a professional trader justification for a signal with caching."""
        cache_key = f"{symbol}_{signal}_{score // 5}"
        now = time.time()
        
        if cache_key in self.justification_cache:
            entry = self.justification_cache[cache_key]
            if now - entry["timestamp"] < self.CACHE_TTL:
                return entry["text"]

        if now - self.last_429_time < self.COOLDOWN_PERIOD:
            return self._get_fallback_justification(signal, context)

        prompt = f"""
        Analyze this {self.ACTIVE_MODE} Signal: {symbol} {signal} (Score: {score}/100)
        
        Context:
        - Trend (1H/4H/1D): {context.get('trend_1st', 'N/A')} / {context.get('trend_2nd', 'N/A')} / {context.get('btc_trend', 'N/A')}
        - Market Sentiment: {context.get('sentiment_alignment', 'NEUTRAL')}
        
        Task: Provide a sharp, data-driven tactical justification.
        Constraints: 10-12 words max. No emojis. Tone: Institutional, professional, precise.
        """
        
        try:
            if self.provider == "GEMINI" and self.client:
                text = await self._get_gemini_response(prompt)
                self.justification_cache[cache_key] = {"text": text, "timestamp": now}
                return text
            else:
                return self._get_fallback_justification(signal, context)
        except Exception as e:
            print(f"AI Service Error: {e}")
            return self._get_fallback_justification(signal, context)

    async def _get_gemini_response(self, prompt: str) -> str:
        try:
            response = await self.client.generate_content_async(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=40,
                    temperature=0.2,
                )
            )
            return response.text.replace('"', '').strip()
        except Exception as e:
            if "429" in str(e) or "ResourceExhausted" in str(e):
                self.last_429_time = time.time()
            raise e

    async def chat(self, messages: list) -> str:
        """Handles general conversation with the trading assistant."""
        if self.provider != "GEMINI" or not self.client:
            return "AI Service is currently offline. Please check your Gemini API key."
            
        try:
            history = [{"role": "user" if m["role"] == "user" else "model", "parts": [m["content"]]} for m in messages[:-1]]
            chat_session = self.client.start_chat(history=history)
            
            system_context = "You are an elite crypto trading assistant. Tone: Professional, data-driven, precise."
            response = await chat_session.send_message_async(
                f"{system_context}\n\nUser: {messages[-1]['content']}",
                generation_config=genai.types.GenerationConfig(max_output_tokens=800, temperature=0.7)
            )
            return response.text.strip()
        except Exception as e:
            if "429" in str(e) or "ResourceExhausted" in str(e):
                self.last_429_time = time.time()
                return "Gemini API Quota Exceeded. Service temporarily busy."
            return "I encountered an error processing your request."

    def _get_fallback_justification(self, signal: str, context: dict) -> str:
        trend = context.get('trend_1st', 'NEUTRAL')
        if signal == "BUY":
            if trend == "UP": return "Bullish trend amplification confirmed by liquidity depth."
            return "Mean reversion setup detected at key volatility support."
        elif signal == "SELL":
            if trend == "DOWN": return "Bearish momentum expansion validated by order book imbalance."
            return "Tactical short entry identified at structural resistance."
        return "Market parameters maintaining neutrality within expected range."

ai_service = AIService()
