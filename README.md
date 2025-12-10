# Bitrix24 Bot - Django Implementation

This Django project replicates the PHP Bitrix24 bot functionality for receiving and sending messages.

## Features

- **Webhook Handler**: Receives messages from Bitrix24
- **Message Processing**: Extracts links, deal IDs, and other data from messages
- **Response Sending**: Sends formatted responses back to Bitrix24 dialogs
- **Bot Registration**: Handles bot installation and registration with Bitrix24
- **Console Logging**: Prints received and sent messages to console
- **Swagger/OpenAPI Documentation**: Interactive API documentation available at `/swagger/`
- **Auto-redirect**: Root URL automatically redirects to Swagger documentation

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run migrations (if needed):
```bash
python manage.py migrate
```

3. Configure settings in `bitrix_bot/settings.py` or use environment variables:
   - `BITRIX_DOMAIN`: Your Bitrix24 domain (default: cultiv.bitrix24.com)
   - `BITRIX_CLIENT_ID`: Your Bitrix24 client ID
   - `BITRIX_CLIENT_SECRET`: Your Bitrix24 client secret
   - `BITRIX_EVENT_HANDLER`: Your webhook URL (e.g., https://your-domain.com/b24-hook.php)

## Running the Server

```bash
python manage.py runserver
```

The server will run on `http://127.0.0.1:8000/`

**Note**: When you visit the root URL (`http://127.0.0.1:8000/`), you'll be automatically redirected to the Swagger documentation at `/swagger/`

## API Documentation

- **Swagger UI**: `http://127.0.0.1:8000/swagger/` - Interactive API documentation
- **ReDoc**: `http://127.0.0.1:8000/redoc/` - Alternative API documentation
- **OpenAPI Schema**: `http://127.0.0.1:8000/swagger.json` or `/swagger.yaml`

## Endpoints

- `/b24-hook.php` - Webhook endpoint for receiving messages from Bitrix24
- `/register-bot/` - Register bot using client ID and secret
- `/install/` - Handle app installation and bot registration

## How It Works

1. **Receiving Messages**: When Bitrix24 sends a message to your bot, it hits the `/b24-hook.php` endpoint
2. **Processing**: The webhook handler extracts:
   - Message text
   - Dialog ID
   - User ID
   - Links from the message
   - Deal ID (if available)
   - Access token
3. **Logging**: All received data is printed to console and logged
4. **Sending Response**: A formatted response message is sent back to the dialog

## Example Usage

When a message is received, you'll see output like:
```
==================================================
📨 MESSAGE RECEIVED
==================================================
User ID: 123
Dialog ID: chat456
Message: Hello! Check this link: https://example.com
Links Found: https://example.com
Deal ID: None
==================================================
```

## Notes

- The webhook endpoint uses `@csrf_exempt` to allow POST requests from Bitrix24
- SSL verification is disabled for development (set `verify=True` in production)
- Make sure your webhook URL is publicly accessible for Bitrix24 to send requests

