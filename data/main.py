from etf_atr import Config, ETFATR
from etf_stock import EmETF
from kline import KLine
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def calc_atr_of(result_file: str, target_list: list[tuple[str, str]]):
    os.makedirs(os.path.join(BASE_DIR, "dist", "data"), exist_ok=True)
    result = open(
        os.path.join(BASE_DIR, "dist", "data", result_file), "w", encoding="utf-8-sig"
    )
    print("代码,名称,ATR(14),ATR(60),最大回撤,当前回撤,来源", file=result)
    etf_list = []
    for code, name, source in target_list:
        kline = KLine(code)
        _, atr_ratio = kline.atr_ratio()
        _, atr_ratio2 = kline.atr_ratio(window=60)
        _, max_drawdown, current_drawdown = kline.drawdown(window=100)
        etf_list.append(
            ETFATR(
                code,
                name,
                atr_ratio,
                atr_ratio2,
                max_drawdown,
                current_drawdown,
                source,
            )
        )

    etf_list.sort(key=lambda x: x.atr_ratio, reverse=True)
    for etf in etf_list:
        print(etf, file=result)
    result.close()
    print(f"{len(etf_list)} 个 ETF atr 计算完毕")


def run_etf_atr():
    config = Config()
    target_list = [
        (e, config.etf_name_of(e), config.etf_category_of(e)) for e in config.etf()
    ]
    calc_atr_of("etf_atr.csv", target_list)


def run_stock_atr():
    config = Config()
    print(config.etf_stock_analysis())
    target_list = set()
    for etf, source in config.etf_stock_analysis():
        em_etf = EmETF(etf)
        stocks = em_etf.fetch_stocks()
        target_list.update([(code, name, source) for code, name, _ in stocks[:20]])

    calc_atr_of("stock_atr.csv", list(target_list))


if __name__ == "__main__":
    run_etf_atr()
    run_stock_atr()
