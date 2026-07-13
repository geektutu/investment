import os
import requests
from urllib.parse import urlencode
from diskcache import Cache

from etf_atr import Config, ETFATR
from kline import KLine

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE = Cache(os.path.join(BASE_DIR, ".cache"))


class EmETF(object):
    def __init__(self, etf_code: str):
        base_url = "https://datacenter.eastmoney.com/securities/api/data/v1/get"
        columns = ["STOCK_SECURITY_CODE", "MARKET_RATIO", "STOCK_NAME_ABBR"]
        params = {
            "reportName": "RPT_POFD_TS_ETFREDEMPTION_LIST",
            "columns": ",".join(columns),
            "filter": f"(SECURITY_CODE={etf_code})",
        }
        query = urlencode(params, safe=")(")

        self.etf_code = etf_code
        self.url = base_url + "?" + query

    @CACHE.memoize(expire=3600 * 12)
    def __fetch(self, code):
        print(f"fetch remote {code}")
        res = requests.get(self.url)
        if res.status_code == 200:
            obj = res.json()
            return obj

        return None

    def fetch_stocks(self):
        stocks = []
        obj = self.__fetch(self.etf_code)
        if not obj:
            print(self.etf_code, "Not Found")
            return stocks

        data = obj["result"]["data"]
        for item in data:
            name = item["STOCK_NAME_ABBR"]
            code = item["STOCK_SECURITY_CODE"]
            weight = float(item["MARKET_RATIO"].strip("%")) / 100.0
            # 占比小于万5的公司忽略，排除退市，ST 等公司，避免除0异常
            if weight <= 0.0005:
                continue
            stocks.append((code, name, weight))

        stocks.sort(key=lambda x: x[2], reverse=True)

        return stocks
