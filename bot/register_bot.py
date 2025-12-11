"""
Bot registration script for Bitrix24.
This script registers the bot using the new event-based structure.
"""
import os
import json
import requests
from django.conf import settings

def register_bot_with_events(auth_token):
    """
    Register bot with Bitrix24 using the new event-based structure.
    
    Args:
        auth_token: Access token from Bitrix24 (from ?auth= parameter)
    
    Returns:
        Response from Bitrix24 API
    """
    # Get base URL from settings
    base_url = f"https://{settings.BITRIX_DOMAIN}"
    
    # Get webhook base URL (your Render domain)
    webhook_base = os.environ.get('BITRIX_EVENT_HANDLER', settings.BITRIX_EVENT_HANDLER)
    # Extract base URL (remove /b24-hook.php if present)
    if '/b24-hook.php' in webhook_base:
        webhook_base = webhook_base.replace('/b24-hook.php', '')
    elif '/bot/' in webhook_base:
        webhook_base = webhook_base.rsplit('/bot/', 1)[0]
    
    # Bot registration payload matching the new structure
    bot_data = {
        "CODE": "cultiv_bot_001",
        "TYPE": "B",
        "EVENT_MESSAGE_ADD": f"{webhook_base}/bot/message",
        "EVENT_WELCOME_MESSAGE": f"{webhook_base}/bot/welcome",
        "EVENT_BOT_DELETE": f"{webhook_base}/bot/delete",
        "OPENLINE": "N",
        "PROPERTIES": {
            "NAME": "Faris Bot",
            "COLOR": "GREEN",
            "EMAIL": "bot@cultiv.ai",
            "PERSONAL_GENDER": "M",
            "WORK_POSITION": "AI Assistant"
        }
    }
    
    # Registration URL
    url = f"{base_url}/rest/imbot.register?auth={auth_token}"
    
    print(f"\n🔄 Registering bot with Bitrix24...")
    print(f"URL: {url}")
    print(f"Bot Data: {json.dumps(bot_data, indent=2)}")
    
    try:
        response = requests.post(
            url,
            json=bot_data,
            timeout=30,
            verify=False
        )
        
        print(f"\n✅ Registration Response (HTTP {response.status_code}):")
        print(response.text)
        
        if response.status_code == 200:
            try:
                result = response.json()
                print(f"\n✅ Bot registered successfully!")
                return result
            except json.JSONDecodeError:
                print(f"\n⚠️ Response is not JSON: {response.text}")
                return {"response": response.text}
        else:
            print(f"\n❌ Registration failed with HTTP {response.status_code}")
            return {"error": response.text}
            
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Error during registration: {str(e)}")
        return {"error": str(e)}


# Example usage (can be run as a Django management command or standalone)
if __name__ == "__main__":
    import django
    import sys
    
    # Setup Django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bitrix_bot.settings')
    django.setup()
    
    # Get auth token from command line or environment
    if len(sys.argv) > 1:
        auth_token = sys.argv[1]
    else:
        auth_token = os.environ.get('BITRIX_AUTH_TOKEN')
        if not auth_token:
            print("Usage: python register_bot.py <auth_token>")
            print("Or set BITRIX_AUTH_TOKEN environment variable")
            sys.exit(1)
    
    result = register_bot_with_events(auth_token)
    print(f"\nResult: {json.dumps(result, indent=2)}")

