#!/usr/bin/env python3
"""
Voice Agent Test Runner

Usage:
    python test_runner.py              # Run all tests
    python test_runner.py --rest       # Run only REST tests
    python test_runner.py --ws         # Run only WebSocket tests
    python test_runner.py --voices     # Run only voice listing test
"""

import asyncio
import argparse
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tests.test_voice_agent import VoiceAgentTester

async def main():
    parser = argparse.ArgumentParser(description='Voice Agent Test Runner')
    parser.add_argument('--rest', action='store_true', help='Run only REST endpoint tests')
    parser.add_argument('--ws', action='store_true', help='Run only WebSocket tests')
    parser.add_argument('--voices', action='store_true', help='Run only voice listing test')
    
    args = parser.parse_args()
    
    print("🎙️ Voice Agent Test Runner")
    print("=" * 40)
    
    # Check server connectivity first
    import aiohttp
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:8000/") as response:
                if response.status == 200:
                    print("✅ Server is running")
                else:
                    print("❌ Server returned error status")
                    return
    except Exception as e:
        print(f"❌ Cannot connect to server: {e}")
        print("Please start the server with: python main.py")
        return
    
    async with VoiceAgentTester() as tester:
        
        if args.voices or not any([args.rest, args.ws, args.voices]):
            await tester.test_voice_list()
        
        if args.rest or not any([args.rest, args.ws, args.voices]):
            await tester.test_rest_endpoint()
        
        if args.ws or not any([args.rest, args.ws, args.voices]):
            await tester.test_websocket_endpoint()
    
    print("\n🎉 Testing completed!")
    print("Check 'test_responses' folder for audio files")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n❌ Tests interrupted")
    except Exception as e:
        print(f"\n❌ Error: {e}")
