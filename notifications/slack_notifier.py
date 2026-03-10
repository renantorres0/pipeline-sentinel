import requests
import os
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

def send_slack_alert(message: str, level: str = 'INFO', exception=None):
    webhook_url = os.getenv('SLACK_WEBHOOK_URL')
    if not webhook_url:
        print('AVISO: SLACK_WEBHOOK_URL não configurado')
        return

    emoji = {
        'INFO': ':information_source:',
        'SUCCESS': ':white_check_mark:',
        'ERROR': ':red_circle:',
        'WARNING': ':warning:'
    }.get(level, ':bell:')

    blocks = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": f"Pipeline Sentinel Alert"}
        },
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"{emoji} *{message}*"}
        },
        {
            "type": "context",
            "elements": [
                {"type": "mrkdwn", "text": f"*Timestamp:* {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC"}
            ]
        }
    ]

    if exception:
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*Erro:*\n```{str(exception)[:500]}```"}
        })

    response = requests.post(webhook_url, json={"blocks": blocks})
    response.raise_for_status()
    print(f"Slack notificado: {message}")

if __name__ == "__main__":
    send_slack_alert("✅ Pipeline Sentinel funcionando!", level="SUCCESS")