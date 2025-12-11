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
    operation_description="Handle incoming message from Bitrix24 bot (EVENT_MESSAGE_ADD).",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        description='Message event data from Bitrix24'
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
    tags=['Bot Events']
)
@api_view(['POST'])
@permission_classes([AllowAny])
def bot_message(request):
    """
    Handle EVENT_MESSAGE_ADD - when a new message is sent to the bot.
    This is the main message handler endpoint.
    """
    return process_message(request)


@swagger_auto_schema(
    method='post',
    operation_description="Handle welcome message event from Bitrix24 bot (EVENT_WELCOME_MESSAGE).",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        description='Welcome message event data from Bitrix24'
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
    tags=['Bot Events']
)
@api_view(['POST'])
@permission_classes([AllowAny])
def bot_welcome(request):
    """
    Handle EVENT_WELCOME_MESSAGE - when a user first interacts with the bot.
    """
    try:
        # Parse incoming data
        body = request.body.decode('utf-8')
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            # Try parsing as query string
            parsed = urllib.parse.parse_qs(body)
            data_str = parsed.get('data', [None])[0]
            if data_str:
                try:
                    data = json.loads(data_str) if isinstance(data_str, str) else data_str
                except (json.JSONDecodeError, TypeError):
                    data = data_str if isinstance(data_str, dict) else {}
            else:
                data = {}
        
        logger.info("🎉 Welcome message event received")
        logger.info(f"Welcome data: {json.dumps(data, indent=2)}")
        
        print(f"\n{'='*50}")
        print(f"🎉 WELCOME MESSAGE EVENT")
        print(f"{'='*50}")
        print(f"Data: {json.dumps(data, indent=2)}")
        print(f"{'='*50}\n")
        
        return Response({"result": "ok"})
        
    except Exception as e:
        logger.error(f"Error processing welcome message: {str(e)}", exc_info=True)
        return Response({"result": "ok"})


@swagger_auto_schema(
    method='post',
    operation_description="Handle bot delete event from Bitrix24 (EVENT_BOT_DELETE).",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        description='Bot delete event data from Bitrix24'
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
    tags=['Bot Events']
)
@api_view(['POST'])
@permission_classes([AllowAny])
def bot_delete(request):
    """
    Handle EVENT_BOT_DELETE - when the bot is deleted from Bitrix24.
    """
    try:
        # Parse incoming data
        body = request.body.decode('utf-8')
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            # Try parsing as query string
            parsed = urllib.parse.parse_qs(body)
            data_str = parsed.get('data', [None])[0]
            if data_str:
                try:
                    data = json.loads(data_str) if isinstance(data_str, str) else data_str
                except (json.JSONDecodeError, TypeError):
                    data = data_str if isinstance(data_str, dict) else {}
            else:
                data = {}
        
        logger.info("🗑️ Bot delete event received")
        logger.info(f"Delete data: {json.dumps(data, indent=2)}")
        
        print(f"\n{'='*50}")
        print(f"🗑️ BOT DELETE EVENT")
        print(f"{'='*50}")
        print(f"Data: {json.dumps(data, indent=2)}")
        print(f"{'='*50}\n")
        
        return Response({"result": "ok"})
        
    except Exception as e:
        logger.error(f"Error processing bot delete: {str(e)}", exc_info=True)
        return Response({"result": "ok"})


def process_message(request):
    """
    Process incoming message from Bitrix24.
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
        
        # Log the received message
        logger.info("=" * 60)
        logger.info("📨 NEW MESSAGE RECEIVED")
        logger.info("=" * 60)
        logger.info(f"User ID: {user_id}")
        logger.info(f"Dialog ID: {dialog_id}")
        logger.info(f"Message: {message}")
        logger.info(f"Links Found: {', '.join(found_links) if found_links else 'None'}")
        logger.info(f"Deal ID: {deal_id if deal_id else 'None'}")
        logger.info(f"Access Token: {access_token[:10]}..." if access_token else "Access Token: (empty)")
        
        # Log bot information
        if bot_info:
            logger.info(f"Bot Information: {json.dumps(bot_info, indent=2)}")
        else:
            logger.info("Bot Information: (empty)")
        logger.info("=" * 60)
        
        # Print to console
        print(f"\n{'='*50}")
        print(f"📨 NEW MESSAGE RECEIVED")
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
        
        # Send the same message back to the user
        if access_token and dialog_id and message:
            send_message_to_dialog(dialog_id, access_token, message)
            logger.info(f"✅ Echoed message back to user: {message}")
        else:
            if not access_token:
                logger.warning("⚠️ Cannot send response: missing accessToken")
            if not dialog_id:
                logger.warning("⚠️ Cannot send response: missing dialogId")
            if not message:
                logger.warning("⚠️ Cannot send response: message is empty")
        
        return Response({"result": "ok"})
        
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}", exc_info=True)
        return Response({"result": "ok"})


def send_message_to_dialog(dialog_id, access_token, user_message):
    """
    Send a message back to the Bitrix24 chat dialog using settings from settings.py.
    Echoes back the exact same message the user sent.
    
    Args:
        dialog_id: Dialog/Chat ID
        access_token: Bot access token
        user_message: Original message from user (will be echoed back)
    """
    # Echo the exact same message back
    response_message = user_message
    
    # Bitrix24 API endpoint for sending messages via bot (using BITRIX_DOMAIN from settings)
    url = f"https://{settings.BITRIX_DOMAIN}/rest/imbot.message.add.json?auth={access_token}"
    
    # Message payload
    message_data = {
        'DIALOG_ID': dialog_id,
        'MESSAGE': response_message
    }
    
    logger.info(f"📤 Sending message to dialog {dialog_id}")
    logger.info(f"📝 Echoing message: {response_message}")
    
    # Print to console
    print(f"\n{'='*50}")
    print(f"📤 SENDING MESSAGE (ECHO)")
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
            logger.info(f"✅ Message echoed successfully to dialog {dialog_id}")
            logger.info(f"API Response: {response.text}")
            print(f"✅ Message sent successfully! Response: {response.text[:100]}")
        else:
            logger.error(f"❌ API returned HTTP {http_code} when sending to dialog {dialog_id}")
            logger.error(f"Response: {response.text}")
            print(f"❌ Failed to send message. HTTP {http_code}: {response.text[:100]}")
            
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Error when sending message: {str(e)}")
        print(f"❌ Error sending message: {str(e)}")

