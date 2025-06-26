import requests

def get_usdt_uah_rate():
    try:
        response = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=USDTUAH")
        data = response.json()
        return round(float(data['price']), 2)
    except:
        return "ошибка при получении курса"