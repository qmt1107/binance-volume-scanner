import requests
import smtplib
import os
from email.mime.text import MIMEText
from datetime import datetime

EMAIL_ADDRESS = "wjddmlvk@gmail.com"
EMAIL_PASSWORD = os.getenv("EMAIL_PASS")
TO_EMAIL = "wjddmlvk@gmail.com"

TOP_N = 20

def scan_top_volume():
    url = "https://api.binance.com/api/v3/ticker/24hr"
    response = requests.get(url)

    if response.status_code != 200:
        print("24hr API failed")
        return []

    data = response.json()

    usdt_pairs = [
        d for d in data
        if d["symbol"].endswith("USDT")
    ]

    # 거래대금 기준 정렬 (quoteVolume)
    sorted_pairs = sorted(
        usdt_pairs,
        key=lambda x: float(x["quoteVolume"]),
        reverse=True
    )

    return sorted_pairs[:TOP_N]


def send_email(results):
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    body = f"📊 Binance 24H Trading Value Top {TOP_N}\n\n"

    for i, coin in enumerate(results, 1):
        symbol = coin["symbol"]
        quote_volume = float(coin["quoteVolume"])
        price_change = float(coin["priceChangePercent"])

        body += (
            f"{i}. {symbol}\n"
            f"   거래대금: ${quote_volume:,.0f}\n"
            f"   24h 변동률: {price_change:.2f}%\n\n"
        )

    msg = MIMEText(body)
    msg["Subject"] = f"Binance 24H Volume Top {TOP_N}"
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = TO_EMAIL

    server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
    server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
    server.send_message(msg)
    server.quit()


if __name__ == "__main__":
    results = scan_top_volume()
    send_email(results)
