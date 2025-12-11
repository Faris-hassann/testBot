# Bot Registration Guide

## Registration Endpoint

Register your bot with Bitrix24 using the following structure:

```
https://cultiv.bitrix24.com/rest/imbot.register?auth=<YOUR_AUTH_TOKEN>
```

## Registration Payload

The bot registration uses the following JSON structure:

```json
{
    "CODE": "cultiv_bot_001",
    "TYPE": "B",
    "EVENT_MESSAGE_ADD": "https://testbot-2x1r.onrender.com/bot/message",
    "EVENT_WELCOME_MESSAGE": "https://testbot-2x1r.onrender.com/bot/welcome",
    "EVENT_BOT_DELETE": "https://testbot-2x1r.onrender.com/bot/delete",
    "OPENLINE": "N",
    "PROPERTIES": {
        "NAME": "Faris Bot",
        "COLOR": "GREEN",
        "EMAIL": "bot@cultiv.ai",
        "PERSONAL_GENDER": "M",
        "WORK_POSITION": "AI Assistant"
    }
}
```

## cURL Command

Replace `<YOUR_AUTH_TOKEN>` with your actual Bitrix24 access token:

```bash
curl -X POST "https://cultiv.bitrix24.com/rest/imbot.register?auth=<YOUR_AUTH_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "CODE": "cultiv_bot_001",
    "TYPE": "B",
    "EVENT_MESSAGE_ADD": "https://testbot-2x1r.onrender.com/bot/message",
    "EVENT_WELCOME_MESSAGE": "https://testbot-2x1r.onrender.com/bot/welcome",
    "EVENT_BOT_DELETE": "https://testbot-2x1r.onrender.com/bot/delete",
    "OPENLINE": "N",
    "PROPERTIES": {
        "NAME": "Faris Bot",
        "COLOR": "GREEN",
        "EMAIL": "bot@cultiv.ai",
        "PERSONAL_GENDER": "M",
        "WORK_POSITION": "AI Assistant"
    }
}'
```

## Example with Auth Token

```bash
curl -X POST "https://cultiv.bitrix24.com/rest/imbot.register?auth=b3a93a690078737d006d9cc5000003a6000007c81893f9279ecafe6ec0ffb070573c35" \
  -H "Content-Type: application/json" \
  -d '{
    "CODE": "cultiv_bot_001",
    "TYPE": "B",
    "EVENT_MESSAGE_ADD": "https://testbot-2x1r.onrender.com/bot/message",
    "EVENT_WELCOME_MESSAGE": "https://testbot-2x1r.onrender.com/bot/welcome",
    "EVENT_BOT_DELETE": "https://testbot-2x1r.onrender.com/bot/delete",
    "OPENLINE": "N",
    "PROPERTIES": {
        "NAME": "Faris Bot",
        "COLOR": "GREEN",
        "EMAIL": "bot@cultiv.ai",
        "PERSONAL_GENDER": "M",
        "WORK_POSITION": "AI Assistant"
    }
}'
```

## Using Python Script

You can also use the provided Python script:

```bash
python bot/register_bot.py <YOUR_AUTH_TOKEN>
```

Or set the environment variable:

```bash
export BITRIX_AUTH_TOKEN="b3a93a690078737d006d9cc5000003a6000007c81893f9279ecafe6ec0ffb070573c35"
python bot/register_bot.py
```

## Endpoints

After registration, Bitrix24 will send events to these endpoints:

- **EVENT_MESSAGE_ADD**: `https://testbot-2x1r.onrender.com/bot/message` - When a new message is sent to the bot
- **EVENT_WELCOME_MESSAGE**: `https://testbot-2x1r.onrender.com/bot/welcome` - When a user first interacts with the bot
- **EVENT_BOT_DELETE**: `https://testbot-2x1r.onrender.com/bot/delete` - When the bot is deleted

## Field Explanations

- **CODE**: Unique bot identifier (`cultiv_bot_001`)
- **TYPE**: Bot type (`B` = Bot)
- **EVENT_MESSAGE_ADD**: Webhook URL for new messages
- **EVENT_WELCOME_MESSAGE**: Webhook URL for welcome messages
- **EVENT_BOT_DELETE**: Webhook URL for bot deletion
- **OPENLINE**: `N` = Regular chat only, `Y` = Open Channels support
- **PROPERTIES**: Bot display settings (name, color, email, etc.)

