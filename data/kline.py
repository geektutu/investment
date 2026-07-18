import os
import time
import pandas as pd
from typing import Optional
from tickflow import TickFlow
from tickflow._exceptions import RateLimitError

from diskcache import Cache

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE = Cache(os.path.join(BASE_DIR, ".cache"))
# 使用免费服务（无需 API key）
TF = TickFlow.free()


def suffix_of(code: str) -> str:
    return ".SH" if (code.startswith("5") or code.startswith("6")) else ".SZ"


@CACHE.memoize(expire=3600 * 12)
def get_kline_data_of(code: str, count: int = 100) -> Optional[pd.DataFrame]:
    print(f"获取 {code} 的历史数据...")
    # 查询日K线数据
    while True:
        try:
            df = TF.klines.get(
                (code + suffix_of(code)),
                period="1d",
                count=count,
                adjust="forward_additive",
                as_dataframe=True,
            )
            time.sleep(1.2)
            break
        except RateLimitError as e:
            print(f"限流: {e}，等待 10s 后重试...")
            time.sleep(10)
    df.to_csv(
        os.path.join(BASE_DIR, ".cache", f"{code}_close.csv"),
        index=False,
        encoding="utf-8-sig",
    )
    if df.empty:
        print(f"获取 {code} 历史数据失败")
    return df


class KLine(object):
    def __init__(self, code: str, count=100) -> None:
        self.code = code
        self.count = count

    def date_range(self) -> tuple:
        df = get_kline_data_of(self.code, self.count)
        if df.empty:
            return None
        return (df["trade_date"].min(), df["trade_date"].max())

    def atr_ratio(self, window: int = 14) -> tuple[pd.DataFrame, float]:
        df = get_kline_data_of(self.code, self.count)
        if df.empty:
            return df, 0.0
        # 计算TR (True Range)
        df["last_close"] = df["close"].shift(1)
        df["TR"] = df.apply(
            lambda x: max(
                x["high"] - x["low"],
                abs(x["high"] - x["last_close"]),
                abs(x["low"] - x["last_close"]),
            ),
            axis=1,
        )
        # 滚动14天计算ATR
        df["ATR"] = df["TR"].rolling(window=window).mean()
        df["ATR_Ratio"] = df["ATR"] / df["close"]
        return df, df["ATR_Ratio"].iloc[-1]

    def drawdown(self, window: int = 60) -> tuple[pd.DataFrame, float, float]:
        """
        计算最大回撤和当前回撤
        """
        df = get_kline_data_of(self.code, self.count)
        if df.empty:
            return df, 0.0, 0.0

        df["滚动最高价"] = df["close"].rolling(window=window, min_periods=1).max()
        df["回撤"] = (df["close"] - df["滚动最高价"]) / df["滚动最高价"]
        # 获取最大回撤
        max_drawdown = df["回撤"].min()
        current_drawdown = df["回撤"].iloc[-1]
        return df, max_drawdown, current_drawdown

    def bias(self, window: int = 50) -> float:
        """
        计算乖离率 BIAS = (Close - MA) / MA * 100%
        返回最后一天的 BIAS 值
        """
        df = get_kline_data_of(self.code, self.count)
        if df.empty or len(df) < window:
            return 0.0
        df["MA"] = df["close"].rolling(window=window).mean()
        df["BIAS"] = (df["close"] - df["MA"]) / df["MA"] * 100
        return df["BIAS"].iloc[-1]

    def __pct_change(self, window: int = 20) -> pd.DataFrame:
        """
        计算涨跌幅
        """
        df = get_kline_data_of(self.code, self.count)
        if df.empty:
            return df
        df["涨幅"] = df["close"].pct_change(periods=window)
        return df

    def corr_of(self, other: "KLine", window: int = 20, key: str = "涨幅") -> float:
        df1 = self.__pct_change(window)
        df2 = other.__pct_change(window)
        if df1.empty or df2.empty:
            return 0.0
        merged = pd.merge(
            df1[["trade_date", key]],
            df2[["trade_date", key]],
            on="trade_date",
            how="inner",
            suffixes=("_1", "_2"),
        )

        if merged.empty:
            print("两个ETF的日期不匹配，无法计算相关性")
            return 0.0

        merged = merged.sort_values("trade_date")

        merged["corr"] = (
            merged[f"{key}_1"]
            .rolling(window=window, min_periods=1)
            .corr(merged[f"{key}_2"])
        )
        return merged["corr"].mean()
