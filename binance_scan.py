import requests
import smtplib
import os
from email.mime.text import MIMEText
from datetime import datetime

EMAIL_ADDRESS = "wjddmlvk@gmail.com"
EMAIL_PASSWORD = os.getenv("EMAIL_PASS")
TO_EMAIL = "wjddmlvk@gmail.com"

TOP_N = 20


def scan_futures_hot():
    url = "https://fapi.binance.com/fapi/v1/ticker/24hr"

    response = requests.get(url, timeout=10)

    if response.status_code != 200:
        return None, None, f"API 실패: {response.status_code}"

    data = response.json()

    usdt_pairs = [
        d for d in data
        if d["symbol"].endswith("USDT")
    ]

    # 1️⃣ 거래대금 기준 정렬
    sorted_by_volume = sorted(
        usdt_pairs,
        key=lambda x: float(x["quoteVolume"]),
        reverse=True
    )

    top_150 = sorted_by_volume[:150]

    hot_up = []
    hot_down = []

    for coin in top_150:
        volume = float(coin["quoteVolume"])
        change = float(coin["priceChangePercent"])

        score = volume * abs(change)

        coin_data = {
            "symbol": coin["symbol"],
            "volume": volume,
            "change": change,
            "score": score
        }

        if change >= 4:
            hot_up.append(coin_data)
        elif change <= -4:
            hot_down.append(coin_data)

    hot_up = sorted(hot_up, key=lambda x: x["score"], reverse=True)[:TOP_N]
    hot_down = sorted(hot_down, key=lambda x: x["score"], reverse=True)[:TOP_N]

    return hot_up, hot_down, None


def send_email(hot_up, hot_down, error_msg):
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    if error_msg:
        body = f"❌ 오류 발생\n\n{error_msg}"
    else:
        body = f"🔥 Binance FUTURES STRONG HOT\n기준시각: {now}\n\n"

        body += "📈 상승 HOT TOP 20 (선물)\n"
        body += "-" * 50 + "\n"
        for coin in hot_up:
            body += (
                f"{coin['symbol']}  "
                f"{coin['change']:+.2f}%  "
                f"${coin['volume']:,.0f}\n"
            )

        body += "\n📉 하락 HOT TOP 20 (선물)\n"
        body += "-" * 50 + "\n"
        for coin in hot_down:
            body += (
                f"{coin['symbol']}  "
                f"{coin['change']:+.2f}%  "
                f"${coin['volume']:,.0f}\n"
            )

    msg = MIMEText(body)
    msg["Subject"] = "🔥 Binance Futures HOT Top 20"
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = TO_EMAIL

    server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
    server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
    server.send_message(msg)
    server.quit()


if __name__ == "__main__":
    hot_up, hot_down, error_msg = scan_futures_hot()
    send_email(hot_up, hot_down, error_msg)
