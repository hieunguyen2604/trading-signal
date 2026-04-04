import os
import asyncio
from services.ai_service import ai_service
from dotenv import load_dotenv

load_dotenv()

async def test_prompts():
    print("--- 🧪 Testing AI Terminal Prompts ---")
    
    # 1. Test Tactical Justification (The Background Assistant)
    scenarios = [
        {
            "symbol": "BTCUSDT",
            "signal": "BUY",
            "score": 85,
            "context": {
                "trend_1st": "UP",
                "trend_2nd": "UP",
                "btc_trend": "UP",
                "sentiment_alignment": "BULLISH"
            }
        },
        {
            "symbol": "ETHUSDT",
            "signal": "SELL",
            "score": 72,
            "context": {
                "trend_1st": "DOWN",
                "trend_2nd": "NEUTRAL",
                "btc_trend": "DOWN",
                "sentiment_alignment": "BEARISH"
            }
        },
        {
            "symbol": "SOLUSDT",
            "signal": "WATCH",
            "score": 45,
            "context": {
                "trend_1st": "UP",
                "trend_2nd": "DOWN",
                "btc_trend": "NEUTRAL",
                "sentiment_alignment": "NEUTRAL"
            }
        }
    ]

    print("\n[A] Testing Tactical Justifications:")
    for i, s in enumerate(scenarios):
        print(f"\nScenario {i+1}: {s['symbol']} {s['signal']} (Score: {s['score']})")
        justification = await ai_service.get_tactical_justification(
            s['symbol'], s['signal'], s['score'], s['context']
        )
        print(f"-> Output: \"{justification}\"")
        # Check if it was cached (only for the same one)
    
    # 2. Test Chatbot Response (Manual interaction)
    print("\n[B] Testing Chatbot Response:")
    messages = [
        {"role": "user", "content": "What is the outlook for BTC right now?"}
    ]
    print(f"User: {messages[0]['content']}")
    response = await ai_service.chat(messages)
    print(f"Chatbot: \"{response}\"")

if __name__ == "__main__":
    if not os.getenv("GEMINI_API_KEY"):
        print("❌ Error: GEMINI_API_KEY not found in .env")
    else:
        asyncio.run(test_prompts())
