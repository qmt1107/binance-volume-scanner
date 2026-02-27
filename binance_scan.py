import requests
import smtplib
import os
from email.mime.text import MIMEText
from datetime import datetime

EMAIL_ADDRESS = "wjddmlvk@gmail.com"
EMAIL_PASSWORD = os.getenv("EMAIL_PASS")
TO_EMAIL = "wjddmlvk@gmail.com"

TOP_N = 20


def scan_coinbase_hot():
    base_url = "https://api.exchange.coinbase.com"

    try:
        products = requests.get(f"{base_url}/products", timeout=10).json()

        usd_pairs = [
            p for p in products
            if p["quote_currency"] == "USD"
            and p["status"] == "online"
        ]

        results = []

        for product in usd_pairs:
            product_id = product["id"]

            stats = requests.get(
                f"{base_url}/products/{product_id}/stats",
                timeout=5
            )

            if stats.status_code != 200:
                continue

            s = stats.json()

            volume = float(s["volume"])
            high = float(s["high"])
            low = float(s["low"])

            if low == 0:
                continue

            change_pct = ((high - low) / low) * 100
            dollar_volume = volume * high

            score = dollar_volume * abs(change_pct)

            results.append({
                "symbol": product_id,
                "volume": dollar_volume,
                "change": change_pct,
                "score": score
            })

        # 거래대금 기준 상위 150개
        results = sorted(results, key=lambda x: x["volume"], reverse=True)[:150]

        hot_up = [
            r for r in results if r["change"] >= 4
        ]

        hot_down = [
            r for r in results if r["change"] <= -4
        ]

        hot_up = sorted(hot_up, key=lambda x: x["score"], reverse=True)[:TOP_N]
        hot_down = sorted(hot_down, key=lambda x: x["score"], reverse=True)[:TOP_N]

        return hot_up, hot_down, None

    except Exception as e:
        return None, None, str(e)


def send_email(hot_up, hot_down, error_msg):
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    if error_msg:
        body = f"❌ 오류 발생\n\n{error_msg}"
    else:
        body = f"🔥 Coinbase STRONG HOT COINS\n기준시각: {now}\n\n"

        body += "📈 상승 HOT TOP 20\n"
        body += "-" * 50 + "\n"
        for coin in hot_up:
            body += (
                f"{coin['symbol']}  "
                f"{coin['change']:+.2f}%  "
                f"${coin['volume']:,.0f}\n"
            )

        body += "\n📉 하락 HOT TOP 20\n"
        body += "-" * 50 + "\n"
        for coin in hot_down:
            body += (
                f"{coin['symbol']}  "
                f"{coin['change']:+.2f}%  "
                f"${coin['volume']:,.0f}\n"
            )

    msg = MIMEText(body)
    msg["Subject"] = "🔥 Coinbase HOT Top 20"
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = TO_EMAIL

    server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
    server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
    server.send_message(msg)
    server.quit()


if __name__ == "__main__":
    hot_up, hot_down, error_msg = scan_coinbase_hot()
    send_email(hot_up, hot_down, error_msg)
