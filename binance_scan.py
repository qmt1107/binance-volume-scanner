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
    url = "https://api.binance.us/api/v3/ticker/24hr"

    try:
        response = requests.get(url, timeout=10)

        if response.status_code != 200:
            return [], f"API 실패: 상태코드 {response.status_code}"

        data = response.json()

        if not isinstance(data, list):
            return [], f"API 응답 이상: {data}"

        usdt_pairs = [
            d for d in data
            if d.get("symbol", "").endswith("USDT")
        ]

        if len(usdt_pairs) == 0:
            return [], "USDT 페어 없음"

        sorted_pairs = sorted(
            usdt_pairs,
            key=lambda x: float(x.get("quoteVolume", 0)),
            reverse=True
        )

        return sorted_pairs[:TOP_N], None

    except Exception as e:
        return [], f"에러 발생: {str(e)}"


def send_email(results, error_msg):
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    if error_msg:
        body = f"❌ 오류 발생\n\n{error_msg}"
    elif not results:
        body = "⚠ 결과가 비어있습니다."
    else:
        body = f"📊 Binance 24H Trading Value Top {TOP_N}\n\n"

        for i, coin in enumerate(results, 1):
            symbol = coin.get("symbol", "N/A")
            quote_volume = float(coin.get("quoteVolume", 0))
            price_change = float(coin.get("priceChangePercent", 0))

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
    results, error_msg = scan_top_volume()
    send_email(results, error_msg)
