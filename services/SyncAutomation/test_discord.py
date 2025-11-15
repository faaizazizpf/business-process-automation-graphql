import requests

def notify_discord(message, webhook_url):
    data = {
        "content": message
    }
    response = requests.post(webhook_url, json=data)
    if response.status_code == 204:
        print("✅ Discord notification sent successfully")
    else:
        print(f"❌ Failed to send Discord notification: {response.status_code} - {response.text}")


discord_webhook_url = "https://discord.com/api/webhooks/1400432826020659200/YutmMifU_LNpdha7xiE6U2CQRdPrM2ZRe8Dc_71obtijl2EAG00uzfumKNbWGF1ZuNet"
notify_discord("📢 Monday board updated for markccman@gmail.com", discord_webhook_url)
