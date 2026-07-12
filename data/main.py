from etf_atr import Config, ETFATR
from kline import KLine
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def run():
    config = Config()
    os.makedirs(os.path.join(BASE_DIR, "dist", "data"), exist_ok=True)
    result = open(
        os.path.join(BASE_DIR, "dist", "data", "etf_atr.csv"), "w", encoding="utf-8-sig"
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


if __name__ == "__main__":
    run()
