 
"""
Discord Webhook Client
"""
import os
from discord_webhook import DiscordWebhook
from dotenv import load_dotenv

class DiscordClient:
    def __init__(self):
        load_dotenv()
        self.webhook_url = os.getenv('DISCORD_WEBHOOK_URL')
        
    def send_text_message(self, content: str):
        """Send text message to Discord"""
        if not self.webhook_url:
            print("Discord webhook URL not found in .env file")
            print("Message content:")
            print(content)
            return
            
        try:
            webhook = DiscordWebhook(url=self.webhook_url, content=content)
            response = webhook.execute()
            print("Message sent to Discord successfully")
        except Exception as e:
            print(f"Failed to send Discord message: {e}")
            print("Message content:")
            print(content)