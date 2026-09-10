import ast
import csv
import os
from concurrent.futures import ThreadPoolExecutor

import requests
import yaml
from diskcache import Cache
from tickflow import TickFlow

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
# 脚本不生成、需保留的手工配置
KEEP_SECTIONS = ["成分股分析"]


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


# python3 etf_growth.py
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

    # 手工维护的分区原样保留
    kept = {}
    if os.path.exists(CONFIG_YAML):
        with open(CONFIG_YAML, "r", encoding="utf-8-sig") as f:
            old = yaml.safe_load(f) or {}
        for key in KEEP_SECTIONS:
            if key in old:
                kept[key] = old[key]

    with open(CONFIG_YAML, "w", encoding="utf-8") as result:
        for name in SECTION_ORDER:
            if name not in sections:
                continue
            print(f"{name}:", file=result)
            for code in sorted(sections[name]):
                print(f'    "{code}": {sections[name][code]}', file=result)
        for key, value in kept.items():
            print(f"{key}:", file=result)
            for code in sorted(value):
                print(f'    "{code}": {value[code]}', file=result)

    stats = {}
    for (big, _, key), items in groups.items():
        n, g = stats.get(big, (0, 0))
        stats[big] = (n + len(items), g + 1)
    for big in BIG_ORDER:
        if big in stats:
            print(f"{big}: {stats[big][0]} 只 -> {stats[big][1]} 个指数组")
