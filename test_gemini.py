#!/usr/bin/env python3
"""
Quick test of Gemini integration
"""

import sys
import json
from loguru import logger
from llm import create_llm_client

# Configure logger
logger.remove()
logger.add(sys.stdout, level="INFO")

def test_gemini():
    """Test Gemini client functionality."""

    print("\n" + "="*80)
    print("🚀 TESTING GEMINI INTEGRATION")
    print("="*80 + "\n")

    # Create Gemini client configuration
    config = {
        'provider': 'gemini',
        'api_key': 'AIzaSyDsOf-eFFQUOgfPWYBl2vHOUW9XFIFpFaE',
        'model': 'gemini-1.5-flash-002',
        'max_tokens': 4000,
        'temperature': 0.7
    }

    # Create client
    print("1️⃣  Creating Gemini client...")
    client = create_llm_client(config)
    print(f"   ✅ Client created: {client.provider_name}")
    print(f"   📝 Model: {client.model}\n")

    # Test 1: Simple text generation
    print("2️⃣  Testing text generation...")
    response = client.generate(
        prompt="Write a brief professional summary for a Python developer with 3 years of experience in web development and machine learning.",
        temperature=0.7
    )
    print(f"   ✅ Generated {len(response.content)} characters")
    print(f"   💰 Cost: ${response.cost_usd:.6f}")
    print(f"   📊 Tokens: {response.input_tokens} in, {response.output_tokens} out")
    print(f"   📝 Response preview:\n")
    print(f"   {response.content[:200]}...\n")

    # Test 2: JSON generation
    print("3️⃣  Testing JSON generation...")
    job_data = {
        "title": "Senior Python Developer",
        "company": "TechCorp Slovakia",
        "description": "We are seeking an experienced Python developer to join our team. You'll work on backend systems, APIs, and data processing pipelines."
    }

    json_response = client.generate_json(
        prompt=f"Analyze this job posting and extract key requirements as JSON:\n{json.dumps(job_data, indent=2)}\n\nReturn a JSON object with: required_skills (list), experience_level (string), and key_responsibilities (list).",
        temperature=0.3
    )
    print(f"   ✅ JSON parsed successfully")
    print(f"   📝 Result:\n")
    print(f"   {json.dumps(json_response, indent=2)}\n")

    # Test 3: Token counting
    print("4️⃣  Testing token counting...")
    test_text = "This is a test sentence for token counting in Gemini."
    token_count = client.count_tokens(test_text)
    print(f"   ✅ Text: '{test_text}'")
    print(f"   📊 Tokens: {token_count}\n")

    # Test 4: Cost estimation
    print("5️⃣  Testing cost estimation...")
    estimated_cost = client.estimate_cost(input_tokens=1000, output_tokens=500)
    print(f"   ✅ Estimated cost for 1,000 input + 500 output tokens:")
    print(f"   💰 ${estimated_cost:.6f}\n")

    print("="*80)
    print("✨ ALL TESTS PASSED! Gemini is working perfectly!")
    print("="*80)
    print("\n🎉 You're ready to use Gemini for CV tailoring and job matching!\n")

if __name__ == "__main__":
    try:
        test_gemini()
    except Exception as e:
        logger.error(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
