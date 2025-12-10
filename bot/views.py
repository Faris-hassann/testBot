import re
import json
import logging
import urllib.parse
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import requests

logger = logging.getLogger(__name__)


@swagger_auto_schema(
    method='post',
    operation_description="Handle incoming webhook from Bitrix24. Receives messages and sends response back.",
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
    tags=['Webhook']
)
@csrf_exempt
@require_http_methods(["POST"])
def webhook_handler(request):
    """
    Handle incoming webhook from Bitrix24.
    Receives messages and sends response back.
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
                return JsonResponse({"result": "ok"})
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
            return JsonResponse({"result": "ok"})
        
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
        if isinstance(bot_data, list):
            for bot in bot_data:
                if isinstance(bot, dict) and 'access_token' in bot:
                    access_token = bot['access_token']
                    break
        
        # Log everything
        logger.info(f"User ID: {user_id}")
        logger.info(f"Dialog ID: {dialog_id}")
        logger.info(f"Message: {message}")
        logger.info(f"Links Found: {', '.join(found_links)}")
        logger.info(f"Deal ID: {deal_id}")
        logger.info(f"Access Token: {access_token[:10]}..." if access_token else "Access Token: (empty)")
        
        # Print to console
        print(f"\n{'='*50}")
        print(f"📨 MESSAGE RECEIVED")
        print(f"{'='*50}")
        print(f"User ID: {user_id}")
        print(f"Dialog ID: {dialog_id}")
        print(f"Message: {message}")
        print(f"Links Found: {', '.join(found_links) if found_links else 'None'}")
        print(f"Deal ID: {deal_id if deal_id else 'None'}")
        print(f"{'='*50}\n")
        
        # Send response message back to dialog
        if access_token and dialog_id:
            send_message_to_dialog(dialog_id, access_token, message, found_links, deal_id)
        else:
            logger.warning("⚠️ Cannot send response: missing accessToken or dialogId")
        
        return JsonResponse({"result": "ok"})
        
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}", exc_info=True)
        return JsonResponse({"result": "ok"})


def send_message_to_dialog(dialog_id, access_token, user_message, links, deal_id):
    """
    Send a message back to the Bitrix24 chat dialog.
    
    Args:
        dialog_id: Dialog/Chat ID
        access_token: Bot access token
        user_message: Original message from user
        links: List of extracted links from message
        deal_id: Deal ID if available
    """
    # Build response message
    response_message = "✅ Message received!\n"
    response_message += f"Original message: {user_message[:100]}"
    
    if links:
        response_message += f"\n\n🔗 Found {len(links)} link(s):\n"
        for link in links:
            response_message += f"• {link}\n"
    
    if deal_id:
        response_message += f"\n💼 Deal ID: {deal_id}"
    
    # Bitrix24 API endpoint for sending messages via bot
    url = f"https://{settings.BITRIX_DOMAIN}/rest/imbot.message.add.json?auth={access_token}"
    
    # Message payload
    message_data = {
        'DIALOG_ID': dialog_id,
        'MESSAGE': response_message
    }
    
    logger.info(f"📤 Sending message to dialog {dialog_id} with token: {access_token[:10]}...")
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


@swagger_auto_schema(
    method='post',
    operation_description="Handle app installation from Bitrix24. Receives auth token and registers the bot.",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'auth': openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'access_token': openapi.Schema(type=openapi.TYPE_STRING, description='Access token from Bitrix24')
                }
            )
        }
    ),
    responses={
        200: openapi.Response(description='Bot registration response from Bitrix24'),
        400: openapi.Response(description='AUTH_ID missing'),
        500: openapi.Response(description='Bot registration failed')
    },
    tags=['Bot Registration']
)
@swagger_auto_schema(
    method='get',
    operation_description="Handle app installation from Bitrix24 (GET method).",
    manual_parameters=[
        openapi.Parameter('access_token', openapi.IN_QUERY, description="Access token", type=openapi.TYPE_STRING),
    ],
    responses={
        200: openapi.Response(description='Bot registration response from Bitrix24'),
        400: openapi.Response(description='AUTH_ID missing'),
        500: openapi.Response(description='Bot registration failed')
    },
    tags=['Bot Registration']
)
@csrf_exempt
@require_http_methods(["POST", "GET"])
def install_app(request):
    """
    Handle app installation from Bitrix24.
    Receives auth token and registers the bot.
    """
    try:
        if request.method == 'POST':
            body = request.body.decode('utf-8')
            data = json.loads(body) if body else {}
        else:
            # For GET requests, check query parameters
            data = request.GET.dict()
        
        # Extract AUTH_ID from the payload
        auth_id = None
        if 'auth' in data and isinstance(data['auth'], dict):
            auth_id = data['auth'].get('access_token')
        elif 'auth' in data:
            auth_id = data.get('auth')
        elif 'access_token' in data:
            auth_id = data.get('access_token')
        
        if not auth_id:
            logger.error("❌ No AUTH_ID received.")
            return JsonResponse({"error": "AUTH_ID missing"}, status=400)
        
        # Register bot
        event_handler = settings.BITRIX_EVENT_HANDLER
        url = f"https://{settings.BITRIX_DOMAIN}/rest/imbot.register.json?auth={auth_id}"
        
        bot_data = {
            'CODE': 'inbox_bot',
            'TYPE': 'B',
            'OPENLINE': 'Y',
            'EVENT_HANDLER': event_handler,
            'PROPERTIES': {
                'NAME': 'Inbox Bot',
                'COLOR': 'GREEN'
            }
        }
        
        logger.info("🔄 Sending bot registration request to Bitrix24...")
        print(f"\n🔄 Registering bot with Bitrix24...")
        print(f"Event Handler: {event_handler}")
        
        try:
            response = requests.post(
                url,
                data=bot_data,
                timeout=30,
                verify=False
            )
            
            if response.status_code == 200:
                logger.info(f"✅ Bot registration response: {response.text}")
                print(f"✅ Bot registered successfully!")
                print(f"Response: {response.text[:200]}")
                return HttpResponse(response.text, content_type='application/json')
            else:
                logger.error(f"❌ Bot registration failed: HTTP {response.status_code}")
                logger.error(f"Response: {response.text}")
                print(f"❌ Registration failed. HTTP {response.status_code}: {response.text[:200]}")
                return JsonResponse({"error": "Bot registration failed"}, status=response.status_code)
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Bot registration failed: {str(e)}")
            print(f"❌ Registration error: {str(e)}")
            return JsonResponse({"error": f"Bot registration failed: {str(e)}"}, status=500)
            
    except Exception as e:
        logger.error(f"Error in install_app: {str(e)}", exc_info=True)
        return JsonResponse({"error": str(e)}, status=500)


@swagger_auto_schema(
    method='post',
    operation_description="Register bot using client ID and secret. Alternative registration method.",
    responses={
        200: openapi.Response(description='Bot registration response from Bitrix24'),
        500: openapi.Response(description='Bot registration failed')
    },
    tags=['Bot Registration']
)
@swagger_auto_schema(
    method='get',
    operation_description="Register bot using client ID and secret (GET method).",
    responses={
        200: openapi.Response(description='Bot registration response from Bitrix24'),
        500: openapi.Response(description='Bot registration failed')
    },
    tags=['Bot Registration']
)
@csrf_exempt
@require_http_methods(["POST", "GET"])
def register_bot(request):
    """
    Register bot using client ID and secret.
    Alternative registration method.
    """
    try:
        client_id = settings.BITRIX_CLIENT_ID
        client_secret = settings.BITRIX_CLIENT_SECRET
        domain = settings.BITRIX_DOMAIN
        event_handler = settings.BITRIX_EVENT_HANDLER
        
        url = f"https://{domain}/rest/{client_id}/{client_secret}/imbot.register.json"
        
        bot_data = {
            'CODE': 'open_channel_inbox_bot',
            'TYPE': 'B',  # Bot
            'EVENT_HANDLER': event_handler,
            'OPENLINE': 'Y',
            'PROPERTIES': {
                'NAME': 'Inbox Bot',
                'COLOR': 'GREEN'
            }
        }
        
        logger.info(f"🔄 Registering bot via client credentials...")
        print(f"\n🔄 Registering bot with client ID/Secret...")
        print(f"URL: {url}")
        print(f"Event Handler: {event_handler}")
        
        try:
            response = requests.post(
                url,
                data=bot_data,
                timeout=30,
                verify=False
            )
            
            logger.info(f"Bot registration response: {response.text}")
            print(f"✅ Registration response: {response.text[:200]}")
            return HttpResponse(response.text, content_type='application/json')
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Bot registration failed: {str(e)}")
            print(f"❌ Registration error: {str(e)}")
            return JsonResponse({"error": str(e)}, status=500)
            
    except Exception as e:
        logger.error(f"Error in register_bot: {str(e)}", exc_info=True)
        return JsonResponse({"error": str(e)}, status=500)

