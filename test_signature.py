"""
Quick test to verify the function signatures match
"""
import asyncio
import sys
import os

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

async def test_function_call():
    """Test that our function can be called with the right arguments"""
    try:
        from app.services.openai_service import generate_story
        
        # Test the function signature - this should work now
        # We're calling with word as positional and story_length as keyword
        result = await generate_story("test", story_length="brief")
        print("✅ Function call successful!")
        print(f"Result: {result[:100]}...")
        return True
        
    except TypeError as e:
        print(f"❌ Function signature error: {e}")
        return False
    except Exception as e:
        print(f"⚠️  Other error (expected in mock mode): {e}")
        return True  # This is OK, means signature is correct

if __name__ == "__main__":
    success = asyncio.run(test_function_call())
    if success:
        print("\n🎉 Function signature fix is working!")
    else:
        print("\n❌ Function signature still has issues")