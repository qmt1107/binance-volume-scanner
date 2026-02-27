import requests
import smtplib
import os
from email.mime.text import MIMEText
from datetime import datetime
import time

EMAIL_ADDRESS = "your_email@gmail.com"
EMAIL_PASSWORD = os.getenv("EMAIL_PASS")
TO_EMAIL = "your_email@gmail.com"

VOLUME_MULTIPLIER = 3
TOP_N = 10
INTERVAL = "1h"

def scan_volume():
    results = []

    url = "https://api.binance.com/api/v3/exchangeInfo"
    response = requests.get(url)

    if response.status_code != 200:
        print("ExchangeInfo API failed")
        return []

    exchange = response.json()

    if "symbols" not in exchange:
        print("Symbols key not found:", exchange)
        return []

    symbols = [
        s["symbol"] for s in exchange["symbols"]
        if s["quoteAsset"] == "USDT" and s["status"] == "TRADING"
    ]

    for symbol in symbols[:50]:  # 안정성 위해 50개만 테스트
        try:
            klines = requests.get(
                "https://api.binance.com/api/v3/klines",
                params={"symbol": symbol, "interval": INTERVAL, "limit": 50}
            )

            if klines.status_code != 200:
                continue

            data = klines.json()
            volumes = [float(k[5]) for k in data]

            avg_vol = sum(volumes[:-1]) / len(volumes[:-1])
            last_vol = volumes[-1]

            if last_vol > avg_vol * VOLUME_MULTIPLIER:
                ratio = last_vol / avg_vol
                results.append((symbol, ratio))

            time.sleep(0.1)

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
    msg["From"] = "wjddmlvk@gmail.com"
    msg["To"] = "wjddmlvk@gmail.com"

    server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
    server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
    server.send_message(msg)
    server.quit()

if __name__ == "__main__":
    data = scan_volume()
    send_email(data)
