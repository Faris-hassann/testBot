import re
import json
import logging
import urllib.parse
from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import requests

logger = logging.getLogger(__name__)


@swagger_auto_schema(
    method='post',
    operation_description="Receive message from Bitrix24 webhook and send response back to the dialog.",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'data': openapi.Schema(
                type=openapi.TYPE_OBJECT,
                description='Webhook data from Bitrix24',
                properties={
                    'PARAMS': openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'MESSAGE': openapi.Schema(type=openapi.TYPE_STRING, description='Message text'),
                            'DIALOG_ID': openapi.Schema(type=openapi.TYPE_STRING, description='Dialog/Chat ID'),
                            'FROM_USER_ID': openapi.Schema(type=openapi.TYPE_STRING, description='User ID'),
                            'CHAT_ENTITY_DATA_1': openapi.Schema(type=openapi.TYPE_STRING, description='Entity data'),
                        }
                    ),
                    'BOT': openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        description='Bot data array',
                        items=openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'access_token': openapi.Schema(type=openapi.TYPE_STRING, description='Bot access token')
                            }
                        )
                    )
                }
            )
        }
    ),
    responses={
        200: openapi.Response(
            description='Success',
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'result': openapi.Schema(type=openapi.TYPE_STRING, example='ok')
                }
            )
        )
    },
    tags=['Messages']
)
@api_view(['POST'])
@permission_classes([AllowAny])
def webhook_handler(request):
    """
    Receive message from Bitrix24 webhook.
    Prints the message and sends a response back to the dialog.
    """
    try:
        # Parse incoming data
        body = request.body.decode('utf-8')
        parsed = urllib.parse.parse_qs(body)
        
        # Get data from parsed query string
        data_str = parsed.get('data', [None])[0]
        
        if not data_str:
            # Try to parse as JSON if query string parsing fails
            try:
                data = json.loads(body)
            except json.JSONDecodeError:
                logger.error("⚠️ Unexpected payload structure")
                logger.error(f"Body: {body}")
                return Response({"result": "ok"})
        else:
            # If data is a string, try to parse it as JSON
            try:
                data = json.loads(data_str) if isinstance(data_str, str) else data_str
            except (json.JSONDecodeError, TypeError):
                # If it's already a dict (from parse_qs), use it directly
                data = data_str if isinstance(data_str, dict) else {}
        
        # Ensure data is a dictionary
        if not isinstance(data, dict):
            logger.error("⚠️ Data is not a dictionary")
            logger.error(f"Data type: {type(data)}, Data: {data}")
            return Response({"result": "ok"})
        
        # Extract parameters
        params = data.get('PARAMS', {})
        message = params.get('MESSAGE', '')
        dialog_id = params.get('DIALOG_ID', '')
        user_id = params.get('FROM_USER_ID', '')
        entity_data1 = params.get('CHAT_ENTITY_DATA_1', '')
        
        # Extract links from message using regex
        link_pattern = r'https?://[^\s]+'
        found_links = re.findall(link_pattern, message)
        
        # Extract deal ID from CHAT_ENTITY_DATA_1
        deal_id = None
        if entity_data1:
            deal_match = re.search(r'DEAL\|(\d+)', entity_data1)
            if deal_match:
                deal_id = deal_match.group(1)
        
        # Extract access token from BOT section
        bot_data = data.get('BOT', [])
        access_token = ''
        bot_info = {}
        if isinstance(bot_data, list):
            for bot in bot_data:
                if isinstance(bot, dict):
                    if 'access_token' in bot:
                        access_token = bot['access_token']
                    # Store all bot information
                    bot_info = bot.copy()
                    break
        elif isinstance(bot_data, dict):
            bot_info = bot_data.copy()
            access_token = bot_data.get('access_token', '')
        
        # Log everything
        logger.info(f"User ID: {user_id}")
        logger.info(f"Dialog ID: {dialog_id}")
        logger.info(f"Message: {message}")
        logger.info(f"Links Found: {', '.join(found_links)}")
        logger.info(f"Deal ID: {deal_id}")
        logger.info(f"Access Token: {access_token[:10]}..." if access_token else "Access Token: (empty)")
        
        # Log bot information
        if bot_info:
            logger.info(f"Bot Information: {json.dumps(bot_info, indent=2)}")
        else:
            logger.info("Bot Information: (empty)")
        
        # Print to console
        print(f"\n{'='*50}")
        print(f"📨 MESSAGE RECEIVED")
        print(f"{'='*50}")
        print(f"User ID: {user_id}")
        print(f"Dialog ID: {dialog_id}")
        print(f"Message: {message}")
        print(f"Links Found: {', '.join(found_links) if found_links else 'None'}")
        print(f"Deal ID: {deal_id if deal_id else 'None'}")
        if bot_info:
            print(f"\n🤖 Bot Information:")
            for key, value in bot_info.items():
                if key == 'access_token' and value:
                    print(f"  {key}: {value[:20]}... (truncated)")
                else:
                    print(f"  {key}: {value}")
        else:
            print(f"Bot Information: None")
        print(f"{'='*50}\n")
        
        # Send response message back to dialog
        if access_token and dialog_id:
            send_message_to_dialog(dialog_id, access_token, message, found_links, deal_id)
        else:
            logger.warning("⚠️ Cannot send response: missing accessToken or dialogId")
        
        return Response({"result": "ok"})
        
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}", exc_info=True)
        return Response({"result": "ok"})


def send_message_to_dialog(dialog_id, access_token, user_message, links, deal_id):
    """
    Send a message back to the Bitrix24 chat dialog using settings from settings.py.
    
    Args:
        dialog_id: Dialog/Chat ID
        access_token: Bot access token
        user_message: Original message from user
        links: List of extracted links from message
        deal_id: Deal ID if available
    """
    # Build response message - echo the received message
    response_message = f"📨 Received: {user_message}"
    
    if links:
        response_message += f"\n\n🔗 Found {len(links)} link(s):\n"
        for link in links:
            response_message += f"• {link}\n"
    
    if deal_id:
        response_message += f"\n💼 Deal ID: {deal_id}"
    
    # Bitrix24 API endpoint for sending messages via bot (using BITRIX_DOMAIN from settings)
    url = f"https://{settings.BITRIX_DOMAIN}/rest/imbot.message.add.json?auth={access_token}"
    
    # Message payload
    message_data = {
        'DIALOG_ID': dialog_id,
        'MESSAGE': response_message
    }
    
    logger.info(f"📤 Sending message to dialog {dialog_id}")
    logger.info(f"📝 Message content: {response_message}")
    
    # Print to console
    print(f"\n{'='*50}")
    print(f"📤 SENDING MESSAGE")
    print(f"{'='*50}")
    print(f"Dialog ID: {dialog_id}")
    print(f"Message: {response_message}")
    print(f"{'='*50}\n")
    
    try:
        # Send POST request using requests library
        response = requests.post(
            url,
            data=message_data,
            timeout=10,
            verify=False  # Set to True in production with proper SSL
        )
        
        http_code = response.status_code
        
        if http_code == 200:
            logger.info(f"✅ Response message sent to dialog {dialog_id}")
            logger.info(f"API Response: {response.text}")
            print(f"✅ Message sent successfully! Response: {response.text[:100]}")
        else:
            logger.error(f"❌ API returned HTTP {http_code} when sending to dialog {dialog_id}")
            logger.error(f"Response: {response.text}")
            print(f"❌ Failed to send message. HTTP {http_code}: {response.text[:100]}")
            
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Error when sending message: {str(e)}")
        print(f"❌ Error sending message: {str(e)}")

