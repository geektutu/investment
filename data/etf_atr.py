import os
import yaml
from kline import KLine

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class Config(object):
    def __init__(self, config_file=os.path.join(BASE_DIR, "config.yaml")) -> None:
        with open(config_file, "r", encoding="utf-8-sig") as f:
            self.config = yaml.safe_load(f)
        etf_keys = [key for key in self.config.keys() if "ETF" in key]
        self.__etfs = {}
        self.__etf_categories = {}
        for key in etf_keys:
            print(f"添加 {key}")
            for code in self.config[key]:
                self.__etfs[str(code)] = self.config[key][code]
                self.__etf_categories[str(code)] = key

    def etf(self):
        return list[str](self.__etfs.keys())

    def etf_category_of(self, code: str):
        return self.__etf_categories.get(code, "")

    def etf_name_of(self, code):
        return self.__etfs.get(code, "")

    def etf_stock_analysis(self):
        return self.config.get("成分股分析", {}).items()


class ETFATR(object):
    def __init__(
        self,
        code: int,
        name: str,
        atr_ratio: float,
        max_drawdown: float,
        current_drawdown: float,
        source: str,
    ) -> None:
        self.code = code
        self.name = name
        self.atr_ratio = atr_ratio
        self.max_drawdown = max_drawdown
        self.current_drawdown = current_drawdown
        self.source = source

    def __str__(self):
        return f"{self.code},{self.name},{self.atr_ratio:.2%},{self.max_drawdown:.1%},{self.current_drawdown:.1%},{self.source}"
