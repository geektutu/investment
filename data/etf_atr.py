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
        return list(self.__etfs.keys())

    def etf_category_of(self, code: str):
        return self.__etf_categories.get(code, "")

    def etf_name_of(self, code):
        return self.__etfs.get(code, "")


class ETFATR(object):
    def __init__(
        self,
        config: Config,
        code: int,
        atr_ratio: float,
        max_drawdown: float,
        current_drawdown: float,
    ) -> None:
        self.config = config
        self.code = code
        self.atr_ratio = atr_ratio
        self.max_drawdown = max_drawdown
        self.current_drawdown = current_drawdown

    def __str__(self):
        return f"{self.code},{self.config.etf_name_of(self.code)},{self.atr_ratio:.2%},{self.max_drawdown:.1%},{self.current_drawdown:.1%}"


if __name__ == "__main__":
    config = Config()
    os.makedirs(os.path.join(BASE_DIR, "dist"), exist_ok=True)
    result = open(
        os.path.join(BASE_DIR, "dist", "etf_atr.csv"), "w", encoding="utf-8-sig"
    )
    print("代码,名称,ATR波动率,最大回撤,当前回撤", file=result)
    etf_list = []
    for code in config.etf():
        kline = KLine(code)
        _, atr_ratio = kline.atr_ratio()
        _, max_drawdown, current_drawdown = kline.drawdown(window=100)
        etf_list.append(ETFATR(config, code, atr_ratio, max_drawdown, current_drawdown))

    etf_list.sort(key=lambda x: x.atr_ratio, reverse=True)
    for etf in etf_list:
        print(etf, file=result)
    result.close()
    print(f"{len(etf_list)} 个 ETF atr 计算完毕")
