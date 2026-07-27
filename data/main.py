from etf_atr import Config, ETFATR
from etf_stock import EmETF
from kline import KLine
import os
import shutil
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def calc_atr_of(result_file: str, target_list: list[tuple[str, str]]):
    os.makedirs(os.path.join(BASE_DIR, "dist", "data"), exist_ok=True)
    result = open(
        os.path.join(BASE_DIR, "dist", "data", result_file), "w", encoding="utf-8-sig"
    )
    print("代码,名称,ATR(14),ATR(50),BIAS(50),最大回撤,当前回撤,来源", file=result)
    etf_list = []
    for code, name, source in target_list:
        kline = KLine(code)
        _, atr_ratio = kline.atr_ratio()
        _, atr_ratio2 = kline.atr_ratio(window=50)
        _, max_drawdown, current_drawdown = kline.drawdown(window=100)
        bias_ratio = kline.bias(window=50)
        etf_list.append(
            ETFATR(
                code,
                name,
                atr_ratio,
                atr_ratio2,
                max_drawdown,
                current_drawdown,
                source,
                bias_ratio,
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


def run_correlation():
    """计算 ETF 之间的相关性矩阵并输出 CSV"""
    config = Config()
    etf_codes = config.etf()
    etf_names = {code: config.etf_name_of(code) for code in etf_codes}

    # 获取所有 ETF 的涨跌幅数据
    klines = {}
    for code in etf_codes:
        kline = KLine(code)
        df = kline._KLine__pct_change(20)
        if not df.empty:
            klines[code] = df[["trade_date", "涨幅"]].rename(columns={"涨幅": code})

    # 计算相关性矩阵
    codes = sorted(klines.keys())
    n = len(codes)
    corr_matrix = [[0.0] * n for _ in range(n)]

    for i in range(n):
        for j in range(n):
            if i == j:
                corr_matrix[i][j] = 1.0
            elif i < j:
                df1 = klines[codes[i]]
                df2 = klines[codes[j]]
                merged = pd.merge(df1, df2, on="trade_date", how="inner")
                if not merged.empty:
                    corr = merged[codes[i]].corr(merged[codes[j]])
                    corr_matrix[i][j] = corr
                    corr_matrix[j][i] = corr

    # 输出 CSV
    os.makedirs(os.path.join(BASE_DIR, "dist", "data"), exist_ok=True)
    output = os.path.join(BASE_DIR, "dist", "data", "correlation.csv")
    with open(output, "w", encoding="utf-8-sig") as f:
        # 表头
        f.write("代码,名称," + ",".join(codes) + "\n")
        # 每行数据
        for i, code in enumerate(codes):
            name = etf_names.get(code, code)
            row = [code, name] + [f"{corr_matrix[i][j]:.4f}" for j in range(n)]
            f.write(",".join(row) + "\n")
    print(f"相关性矩阵已生成，共 {n} 个 ETF")


def copy_close_csv():
    """将 .cache 下的 {code}_close.csv 拷贝到 data/dist/data 下"""
    cache_dir = os.path.join(BASE_DIR, ".cache")
    dist_data_dir = os.path.join(BASE_DIR, "dist", "data")
    os.makedirs(dist_data_dir, exist_ok=True)

    if not os.path.exists(cache_dir):
        return

    for filename in os.listdir(cache_dir):
        if filename.endswith("_close.csv"):
            src = os.path.join(cache_dir, filename)
            dst = os.path.join(dist_data_dir, filename)
            shutil.copy2(src, dst)
            print(f"已拷贝 {filename}")


if __name__ == "__main__":
    run_etf_atr()
    run_stock_atr()
    run_correlation()
    copy_close_csv()
