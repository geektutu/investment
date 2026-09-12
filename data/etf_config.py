import ast
import csv
import os
from concurrent.futures import ThreadPoolExecutor

import requests
from diskcache import Cache
from tickflow import TickFlow

from etf_stock import EmETF

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE = Cache(os.path.join(BASE_DIR, ".cache"))

# 类别 -> 匹配关键词（简称或指数名命中任一即可）
CATEGORIES = {
    "成长": ["成长"],
    "价值": ["价值", "质量", "现金流"],
    "红利": ["红利", "股息", "股东", "央企", "国企"],
}
# 仅显示份额达标的 ETF
MIN_SHARES = 1_000_000_000
# 风格类阈值单独放宽
MIN_SHARES_STYLE = 500_000_000
# 行业关键词（匹配简称或指数名，命中归为行业大类）
INDUSTRY = [
    "银行",
    "证券",
    "保险",
    "医药",
    "医疗",
    "创新药",
    "中药",
    "生物",
    "白酒",
    "食品",
    "饮料",
    "乳业",
    "家电",
    "消费",
    "汽车",
    "军工",
    "国防",
    "半导体",
    "芯片",
    "存储",
    "电子",
    "计算机",
    "软件",
    "信创",
    "云计算",
    "算力",
    "人工智能",
    "机器人",
    "通信",
    "5G",
    "传媒",
    "游戏",
    "影视",
    "出版",
    "光伏",
    "新能源",
    "电池",
    "电力",
    "电网",
    "核电",
    "煤炭",
    "石油",
    "石化",
    "天然气",
    "油气",
    "钢铁",
    "有色",
    "稀土",
    "黄金",
    "化工",
    "地产",
    "房地产",
    "建筑",
    "建材",
    "水泥",
    "机械",
    "基建",
    "交通",
    "运输",
    "物流",
    "港口",
    "航空",
    "机场",
    "农业",
    "养殖",
    "畜牧",
    "种业",
    "粮食",
    "纺织",
    "造纸",
    "环保",
    "水务",
    "旅游",
    "酒店",
    "零售",
    "科技",
    "酒",
    "互联网",
    "金融",
    "能源",
    "资源",
    "金属",
    "集成电路",
    "信息技术",
    "新材料",
    "卫星",
    "船舶",
    "机床",
    "工业母机",
    "大数据",
    "农牧渔",
    "教育",
]
# 宽基指数代码 -> 简称
BROAD_CODES = {
    "000300": "沪深300",
    "000905": "中证500",
    "000016": "上证50",
    "000010": "上证180",
    "000906": "中证800",
    "000852": "中证1000",
    "932000": "中证2000",
    "000510": "中证A500",
    "930050": "中证A50",
    "399006": "创业板",
    "399330": "深证100",
    "399303": "国证2000",
    "399001": "深证成指",
    "399293": "创业板大盘",
    "399673": "创业板50",
    "000698": "科创100",
    "000699": "科创200",
    "000688": "科创50",
    "000680": "科创综指",
    "931643": "双创50",
    "000903": "中证A100",
    "000001": "上证指数",
    "746059": "MSCI中国A50",
    "HSI": "恒生指数",
    "HSTECH": "恒生科技",
    "HSFML25": "恒生香港30",
    "HSCEI": "恒生国企",
    "NDX100": "纳斯达克100",
    "SPX": "标普500",
    "N225": "日经225",
    "DJIA": "道琼斯",
    "930931": "港股通50",
    "HSSC50": "港股通50",
    "931395": "沪港深300",
    "750108": "美国50",
    "GPCSP006": "亚太精选",
    "TPX": "日本东证",
    "BVSP": "巴西",
    "GDAXI": "德国DAX",
    "FCHI": "法国CAC40",
    "FISAULMU": "沙特",
    "716567": "MSCI中国A股",
}
# 债券类关键词
BOND_KEYWORDS = ["债", "短融"]
# 商品指数代码 -> 简称（黄金股类是股票指数，不在此列，仍归行业）
COMMODITY_CODES = {
    "AU9999": "黄金",
    "SHAU": "黄金",
    "DCESMFI": "豆粕",
    "000066": "大宗商品",
    "ESZCE_ECIA": "能源化工",
    "IMCI": "有色金属",
}
# 指数与ETF的对应关系基本不变，落地 CSV 一次性查询，缺的增量追加
INDEX_MAP_CSV = os.path.join(BASE_DIR, "etf_index_map.csv")
# 生成的目标配置，分区名 = 大类 + ETF
CONFIG_YAML = os.path.join(BASE_DIR, "config.yaml")
# 个股分析来源按类别归并，每类指定分区及关键词规则（组内为「或」，组间为「且」），并排除指定关键词
STOCK_GROUPS = {
    "央企红利类ETF": {
        "sections": ["红利ETF", "价值ETF"],
        "rule": [["红利"], ["国企", "央企"]],
        # 净利同比 > 20% 免检，否则需 0 < PE(TTM) < 30 且 ROE(TTM) > 8
        "filter": [
            {"净利同比": (20, None)},
            {"PE(TTM)": (0, 30), "ROE(TTM)": (8, None)},
        ],
    },
    "价值类ETF": {
        "sections": ["价值ETF"],
        "rule": [["现金流", "价值", "质量"]],
        # 净利同比 > 20% 免检，否则需 0 < PE(TTM) < 30 且 ROE(TTM) > 8
        "filter": [
            {"净利同比": (20, None)},
            {"PE(TTM)": (0, 30), "ROE(TTM)": (8, None)},
        ],
    },
    "资源类ETF": {
        "sections": ["行业ETF"],
        "rule": [["煤炭", "石油", "电力", "黄金", "有色", "稀土", "稀有金属", "化工"]],
        # 净利同比 > 20% 免检，否则需 0 < PE(TTM) < 30 且 ROE(TTM) > 8
        "filter": [
            {"净利同比": (20, None)},
            {"PE(TTM)": (0, 30), "ROE(TTM)": (8, None)},
        ],
    },
}
STOCK_EXCLUDE = ["港股", "恒生", "创业板", "红利质量ETF华夏"]
STOCK_TOP = 30
# 手动补充的个股：类别 -> {代码: 名称}，用于当前 ETF 池覆盖不到的标的
STOCK_EXTRA = {
    "资源类ETF": {
        "002379": "宏桥控股",
    },
}
# 全 A 股估值/财务快照，来自东方财富行情列表接口
STOCK_FUNDAMENTAL_CSV = os.path.join(BASE_DIR, "stock_fundamental.csv")
STOCK_FUNDAMENTAL_HOSTS = [
    "https://push2delay.eastmoney.com",
    "https://push2.eastmoney.com",
]
# 沪深主板、创业板、科创板、北交所
STOCK_MARKETS = "m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23,m:0+t:81+s:2048"
# 财务指标：可读名称 -> 东财字段
STOCK_METRICS = {
    "代码": "f12",
    "名称": "f14",
    "最新价": "f2",
    "PE(TTM)": "f115",
    "PB": "f23",
    "营收同比": "f41",
    "净利同比": "f46",
    "毛利率": "f49",
    "总市值": "f20",
    "上市日期": "f26",
}
STOCK_FIELDS = ",".join(STOCK_METRICS.values())
# 派生指标：名称 -> (分子, 分母, 系数)，值 = 分子 / 分母 * 系数
# ROE(TTM) = PB / PE(TTM)，即 base 口径的 TTM 净资产收益率
STOCK_DERIVED = {
    "ROE(TTM)": ("PB", "PE(TTM)", 100),
}
# CSV 列顺序，可混用普通指标与派生指标
STOCK_COLUMNS = [
    "代码",
    "名称",
    "最新价",
    "PE(TTM)",
    "PB",
    "ROE(TTM)",
    "营收同比",
    "净利同比",
    "毛利率",
    "总市值",
    "上市日期",
]
# 接口单页最多返回 100 条，pz 传更大也只给 100
STOCK_PAGE_SIZE = 100
STOCK_HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://quote.eastmoney.com/",
}


@CACHE.memoize(expire=3600 * 12)
def fetch_etfs():
    # 交易所全量 ETF，比 CN_ETF 池更全（池会漏新上市的）
    print("fetch remote SH/SZ etf")
    tf = TickFlow.free()
    insts = tf.exchanges.get_instruments("SH", "etf") + tf.exchanges.get_instruments(
        "SZ", "etf"
    )
    return {i["code"]: i for i in insts}


def fetch_indexes(codes):
    # 天天基金移动端接口，返回跟踪指数代码与指数名（基金全称的核心词）
    print(f"fetch index names {len(codes)} 只")

    def fetch(code):
        res = requests.get(
            "https://fundmobapi.eastmoney.com/FundMNewApi/FundMNBasicInformation",
            params={
                "FCODE": code,
                "deviceid": "Wap",
                "plat": "Wap",
                "product": "EFund",
                "version": "6.2.8",
            },
            headers={
                "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X)"
            },
            timeout=10,
        )
        datas = res.json().get("Datas")
        if isinstance(datas, dict):
            info = datas
        else:
            info = ast.literal_eval(datas) if datas else {}
        try:
            shares = int(float(info.get("FEGM") or 0))
        except ValueError:
            shares = 0
        return code, (
            clean(info.get("INDEXCODE")),
            clean(info.get("INDEXNAME")),
            shares,
        )

    with ThreadPoolExecutor(10) as pool:
        return dict(pool.map(fetch, codes))


def clean(value):
    # 接口里用 -- 表示空值
    return "" if value in (None, "--") else value


def load_index_map():
    if not os.path.exists(INDEX_MAP_CSV):
        return {}
    with open(INDEX_MAP_CSV, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if "份额" not in (reader.fieldnames or []):
            return None
        return {
            row["代码"]: (
                clean(row["指数代码"]),
                clean(row["指数名"]),
                int(row["份额"] or 0),
            )
            for row in reader
        }


def append_index_map(rows):
    new_file = not os.path.exists(INDEX_MAP_CSV)
    encoding = "utf-8-sig" if new_file else "utf-8"
    with open(INDEX_MAP_CSV, "a", encoding=encoding, newline="") as f:
        writer = csv.writer(f)
        if new_file:
            writer.writerow(["代码", "指数代码", "指数名", "份额"])
        writer.writerows(rows)


def index_key(name):
    # 简称格式为「指数词ETF+公司」，取 ETF 前缀作为指数词；XD 为除息临时标记
    if name.startswith("XD"):
        name = name[2:]
    if "ETF" in name:
        return name[: name.index("ETF") + 3]
    return name


def pick(items):
    # 同一行业保留：优先科创，次创业，其余按份额最大
    def rank(item):
        name = item[1]
        if "科创" in name:
            board = 0
        elif "创业" in name:
            board = 1
        else:
            board = 2
        return (board, -item[2], item[0])

    return sorted(items, key=rank)[0]


def classify(name, index_code, index_name):
    # 大类优先级：宽基 > 风格 > 债券 > 行业 > 其他，每只 ETF 只归一个大类
    if index_code in BROAD_CODES:
        return [("宽基", BROAD_CODES[index_code])]
    for category, keywords in CATEGORIES.items():
        if any(k in name or k in index_name for k in keywords):
            return [("风格", category)]
    if any(k in name or k in index_name for k in BOND_KEYWORDS):
        return []
    if index_code in COMMODITY_CODES:
        return [("商品", COMMODITY_CODES[index_code])]
    # 简称比指数名更直接，优先在简称中匹配，再退回指数名
    hit = next((k for k in INDUSTRY if k in name), None) or next(
        (k for k in INDUSTRY if k in index_name.replace("非银行", "")), None
    )
    if hit:
        return [("行业", hit)]
    return [("其他", index_key(name))]


BIG_ORDER = {"风格": 0, "行业": 1, "宽基": 2, "商品": 3, "其他": 4}
# 风格拆分为红利/价值/成长独立分区，分区名 -> 生成顺序
SECTION_ORDER = [
    "红利ETF",
    "价值ETF",
    "成长ETF",
    "行业ETF",
    "宽基ETF",
    "商品ETF",
    "其他ETF",
]


def section_name(big, cat):
    # 风格大类按细分类别拆分分区，其余大类合并为一个分区
    return f"{cat}ETF" if big == "风格" else f"{big}ETF"


@CACHE.memoize(expire=3600 * 12)
def fetch_stock_page(page):
    # 全 A 股行情列表，单页分页拉取，diskcache 避免重复请求
    params = {
        "pn": page,
        "pz": STOCK_PAGE_SIZE,
        "po": 1,
        "np": 1,
        "fltt": 2,
        "invt": 2,
        "fid": "f12",
        "fs": STOCK_MARKETS,
        "fields": STOCK_FIELDS,
    }
    for host in STOCK_FUNDAMENTAL_HOSTS:
        try:
            res = requests.get(
                f"{host}/api/qt/clist/get",
                params=params,
                headers=STOCK_HEADERS,
                timeout=15,
            )
            res.raise_for_status()
            return res.json()["data"]
        except Exception as e:
            print(f"fetch stock page {page} failed {host}: {e}")
    raise RuntimeError("all hosts failed")


def save_stock_fundamentals():
    print("收集全 A 股估值/财务快照")
    rows = []
    page = 1
    total = 0
    while True:
        data = fetch_stock_page(page)
        if not data or not data.get("diff"):
            break
        total = data["total"]
        rows.extend(data["diff"])
        if len(rows) >= total:
            break
        page += 1

    header = list(STOCK_COLUMNS)
    with open(STOCK_FUNDAMENTAL_CSV, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        for item in rows:
            values = [column_value(item, name) for name in STOCK_COLUMNS]
            writer.writerow(["" if v in (None, "-") else v for v in values])
    print(f"{len(rows)} 只股票估值/财务快照已保存到 {STOCK_FUNDAMENTAL_CSV}")
    return {item["f12"]: item for item in rows}


def to_number(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def derived_value(item, name):
    # 按 (分子, 分母, 系数) 计算派生指标，缺数据返回 None
    numerator, denominator, factor = STOCK_DERIVED[name]
    a = to_number(item.get(STOCK_METRICS[numerator]))
    b = to_number(item.get(STOCK_METRICS[denominator]))
    if a is None or b in (None, 0):
        return None
    return a / b * factor


def column_value(item, name):
    # CSV 取值：普通指标取接口字段，派生指标现场计算
    if name in STOCK_METRICS:
        return item.get(STOCK_METRICS[name])
    return derived_value(item, name)


def metric_value(item, name):
    # 支持普通字段与派生指标
    if name in STOCK_METRICS:
        return to_number(item.get(STOCK_METRICS[name]))
    return to_number(derived_value(item, name))


def pass_filter(item, spec):
    # spec：子条件列表，子条件内为「且」，子条件间为「或」，全部不满足才拒绝
    if not spec:
        return True
    clauses = spec if isinstance(spec, list) else [spec]
    return any(pass_clause(item, clause) for clause in clauses)


def pass_clause(item, clause):
    # clause：可读指标名 -> (下限, 上限)，开区间；缺数据视为不通过
    for name, (low, high) in clause.items():
        value = metric_value(item, name)
        if value is None:
            return False
        if low is not None and value <= low:
            return False
        if high is not None and value >= high:
            return False
    return True


# python3 etf_config.py
if __name__ == "__main__":
    etfs = fetch_etfs()

    index_map = load_index_map()
    if index_map is None:
        # 旧格式（无份额列），全量重建
        print("map 含旧格式，全量重建")
        if os.path.exists(INDEX_MAP_CSV):
            os.remove(INDEX_MAP_CSV)
        index_map = {}
    missing = [code for code in sorted(etfs) if code not in index_map]
    if missing:
        rows = fetch_indexes(missing)
        append_index_map([(code, *idx) for code, idx in rows.items()])
        index_map.update(rows)

    groups = {}
    for code, inst in etfs.items():
        index_code, index_name, shares = index_map.get(code, ("", "", 0))
        name = inst["name"]
        key = index_code or index_key(name)
        for big, cat in classify(name, index_code, index_name):
            # 同一行业关键词只保留份额最大的一个，不再按指数细分
            if big == "行业":
                key = cat
            threshold = MIN_SHARES_STYLE if big == "风格" else MIN_SHARES
            if shares < threshold:
                continue
            groups.setdefault((big, cat, key), []).append((code, name, shares))

    # 分区 -> {代码: 名称}，每个指数组保留一只代表 ETF
    sections = {}
    for (big, cat, key), items in groups.items():
        code, name, _ = pick(items)
        sections.setdefault(section_name(big, cat), {})[code] = name

    # 个股分析目标：命中类别规则的 A 股 ETF 成分股，按代码去重保留首次出现的类别
    # 先取全 A 股估值/财务快照，供类别过滤使用
    fundamentals = save_stock_fundamentals()
    stocks = {}
    seen = set()
    for category, conf in STOCK_GROUPS.items():
        for section in conf["sections"]:
            for code in sorted(sections.get(section, {})):
                source = sections[section][code]
                if not all(any(k in source for k in group) for group in conf["rule"]):
                    continue
                if any(keyword in source for keyword in STOCK_EXCLUDE):
                    continue
                for stock_code, stock_name, _ in EmETF(code).fetch_stocks(
                    top=conf.get("top", STOCK_TOP)
                ):
                    # A 股代码为 6 位数字，港股为 5 位，排除港股
                    if not (stock_code.isdigit() and len(stock_code) == 6):
                        continue
                    # 估值/财务约束
                    if not pass_filter(
                        fundamentals.get(stock_code, {}), conf.get("filter", {})
                    ):
                        continue
                    if stock_code in seen:
                        continue
                    seen.add(stock_code)
                    stocks.setdefault(category, {})[stock_code] = stock_name

    # 合并手动补充的个股
    for category, items in STOCK_EXTRA.items():
        for stock_code, stock_name in items.items():
            stocks.setdefault(category, {})[stock_code] = stock_name

    with open(CONFIG_YAML, "w", encoding="utf-8") as result:
        for name in SECTION_ORDER:
            if name not in sections:
                continue
            print(f"{name}:", file=result)
            for code in sorted(sections[name]):
                print(f'    "{code}": {sections[name][code]}', file=result)
        if stocks:
            print("stock:", file=result)
            for source, items in stocks.items():
                print(f"    {source}:", file=result)
                for code in sorted(items):
                    print(f'        "{code}": {items[code]}', file=result)

    stats = {}
    for (big, _, key), items in groups.items():
        n, g = stats.get(big, (0, 0))
        stats[big] = (n + len(items), g + 1)
    for big in BIG_ORDER:
        if big in stats:
            print(f"{big}: {stats[big][0]} 只 -> {stats[big][1]} 个指数组")
