import requests
import pandas as pd
import smtplib
import os
from email.mime.text import MIMEText
from datetime import datetime

EMAIL_ADDRESS = "your_email@gmail.com"
EMAIL_PASSWORD = os.getenv("EMAIL_PASS")
TO_EMAIL = "your_email@gmail.com"

VOLUME_MULTIPLIER = 3
TOP_N = 10
INTERVAL = "1h"

def scan_volume():
    results = []
    exchange = requests.get("https://api.binance.com/api/v3/exchangeInfo").json()

    symbols = [
        s["symbol"] for s in exchange["symbols"]
        if s["quoteAsset"] == "USDT" and s["status"] == "TRADING"
    ]

    for symbol in symbols[:100]:  # 속도 안정 위해 100개만 테스트
        try:
            klines = requests.get(
                "https://api.binance.com/api/v3/klines",
                params={"symbol": symbol, "interval": INTERVAL, "limit": 50}
            ).json()

            volumes = [float(k[5]) for k in klines]
            avg_vol = sum(volumes[:-1]) / len(volumes[:-1])
            last_vol = volumes[-1]

            if last_vol > avg_vol * VOLUME_MULTIPLIER:
                ratio = last_vol / avg_vol
                results.append((symbol, ratio))
        except:
            continue

    results.sort(key=lambda x: x[1], reverse=True)
    return results[:TOP_N]

def send_email(results):
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    if not results:
        body = "거래량 급등 코인이 없습니다."
    else:
        body = "📈 Binance Volume Surge\n\n"
        for s in results:
            body += f"{s[0]} | {round(s[1],2)}x\n"

    msg = MIMEText(body)
    msg["Subject"] = f"Volume Report - {now}"
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = TO_EMAIL

    server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
    server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
    server.send_message(msg)
    server.quit()

if __name__ == "__main__":
    data = scan_volume()
    send_email(data)
