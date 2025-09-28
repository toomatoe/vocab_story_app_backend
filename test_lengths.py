"""
Test script to demonstrate the flexible story length feature
"""
import requests
import json

# Server URL
BASE_URL = "http://127.0.0.1:8001"

def test_story_lengths():
    """Test all available story length options"""
    
    test_word = "adventure"
    length_options = ["brief", "short", "medium", "long"]
    
    print(f"Testing story generation for word: '{test_word}'\n")
    
    for length in length_options:
        print(f"🔍 Testing {length.upper()} story...")
        
        # Prepare request
        payload = {
            "word": test_word,
            "length": length
        }
        
        try:
            # Make request
            response = requests.post(f"{BASE_URL}/generate_story", json=payload)
            
            if response.status_code == 200:
                data = response.json()
                word_count = len(data["story"].split())
                
                print(f"✅ {length.capitalize()} story generated successfully!")
                print(f"   📝 Word count: {word_count}")
                print(f"   🤖 Mock mode: {data['mock']}")
                print(f"   📖 Story preview: {data['story'][:100]}...")
                print()
            else:
                print(f"❌ Error: {response.status_code} - {response.text}")
                print()
                
        except requests.exceptions.ConnectionError:
            print("❌ Cannot connect to server. Make sure it's running on port 8001")
            break
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            print()

def test_invalid_length():
    """Test invalid length parameter"""
    print("🔍 Testing invalid length parameter...")
    
    payload = {
        "word": "test",
        "length": "invalid"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/generate_story", json=payload)
        print(f"Response: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 FLEXIBLE STORY LENGTH TESTING")
    print("=" * 60)
    
    test_story_lengths()
    
    print("=" * 60)
    print("🔍 TESTING ERROR HANDLING")
    print("=" * 60)
    
    test_invalid_length()
    
    print("\n🎉 Testing complete!")
    print("💡 Try the interactive docs at: http://127.0.0.1:8001/docs")