#!/usr/bin/env python3
"""
ai-agent-toolkit — 一个轻量的AI情报扫描工具。
每天跑一次，看看技术圈发生了什么。
"""
import urllib.request
import json
from datetime import datetime
from pathlib import Path
import time
import sys
import re

# ────────── 配置区 ──────────
# 你可以在这里改数据源：想加就加，想删就删，改下面这个字典就行。
DATA_SOURCES = {
    "github": {
        "url": "https://api.github.com/search/repositories?q=AI+agent+created:>2025-01-01&sort=stars&per_page=8",
        "label": "GitHub AI 项目",
        "timeout": 10,
        "enabled": True,
    },
    "oschina": {
        "url": "https://www.oschina.net/news/widgets/_news_index_latest?p=1&type=ajax&catalog=1",
        "label": "OSCHINA 开源中国",
        "timeout": 8,
        "enabled": True,
    },
    "hackernews": {
        "url": "https://hacker-news.firebaseio.com/v0/topstories.json",
        "label": "Hacker News 热门",
        "timeout": 5,       # 国内限速严重，5s 能跑就跑，不行就跳过
        "item_count": 3,
        "enabled": True,
    },
}
CACHE_ENABLED = True        # 同一天缓存，不重复请求
# ────────── 配置结束 ──────────


def cache_path():
    """返回今天的缓存文件路径"""
    cache_dir = Path.home() / ".cache" / "ai-agent-toolkit"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir / f"{datetime.now().strftime('%Y-%m-%d')}.json"


def load_cache():
    """如果今天已缓存过，直接返回"""
    if not CACHE_ENABLED:
        return None
    cp = cache_path()
    if cp.exists():
        try:
            return json.loads(cp.read_text())
        except Exception:
            return None
    return None


def save_cache(data):
    """保存今天的结果到缓存"""
    if not CACHE_ENABLED:
        return
    try:
        cache_path().write_text(json.dumps(data, ensure_ascii=False, indent=2))
    except Exception:
        pass


def fetch_source(key, fetch_func):
    """通用数据源抓取模板——所有数据源共用这个外壳"""
    cfg = DATA_SOURCES.get(key)
    if not cfg or not cfg["enabled"]:
        return []
    sys.stdout.write(f"  🟡 正在扫描 {cfg['label']}...")
    sys.stdout.flush()
    t1 = time.time()
    try:
        items = fetch_func(cfg)
        elapsed = time.time() - t1
        bar = "🟢" if elapsed < 3 else "🟡" if elapsed < 8 else "🔴"
        sys.stdout.write(f"\r  {bar} {cfg['label']}：{len(items)} 条（{elapsed:.1f}s）\n")
        sys.stdout.flush()
        return items
    except Exception as e:
        elapsed = time.time() - t1
        sys.stdout.write(f"\r  ⚠️  {cfg['label']} 暂时不可达（{elapsed:.1f}s）：{type(e).__name__}\n")
        sys.stdout.flush()
        return []


def _fetch_github(cfg):
    """实际抓取 GitHub"""
    req = urllib.request.Request(cfg["url"], headers={"User-Agent": "ai-agent-toolkit/1.0"})
    data = json.loads(urllib.request.urlopen(req, timeout=cfg["timeout"]).read())
    return [
        (r["full_name"], r["stargazers_count"], (r.get("description") or "")[:80], r.get("language", "") or "")
        for r in data.get("items", [])
    ]


def _fetch_oschina(cfg):
    """实际抓取 OSCHINA（国内源，速度快）"""
    req = urllib.request.Request(cfg["url"], headers={"User-Agent": "Mozilla/5.0"})
    data = urllib.request.urlopen(req, timeout=cfg["timeout"]).read().decode("utf-8")
    titles = re.findall(r'title="([^"]+?)"', data)[:5]
    return [(t.strip()[:80],) for t in titles]


def _fetch_hackernews(cfg):
    """实际抓取 Hacker News（国内限速严重）"""
    ids = json.loads(urllib.request.urlopen(cfg["url"], timeout=cfg["timeout"]).read())[:cfg["item_count"]]
    items = []
    for sid in ids:
        item = json.loads(
            urllib.request.urlopen(f"https://hacker-news.firebaseio.com/v0/item/{sid}.json", timeout=cfg["timeout"]).read()
        )
        items.append((item.get("title", "")[:80], item.get("score", 0)))
    return items


def main():
    now = datetime.now()
    dt = now.strftime("%Y-%m-%d %H:%M")
    print(f"\n📡 {dt} 扫描报告")
    print("━" * 40)

    # 检查缓存
    cached = load_cache()
    if cached and cached.get("date") == now.strftime("%Y-%m-%d"):
        print(f"  📦 今日已扫描过（{cached['time']}），直接使用缓存。")
        print(f"  如果想重新扫描，删除 ~/.cache/ai-agent-toolkit/{now.strftime('%Y-%m-%d')}.json 即可。\n")
        data = cached
    else:
        print(f"  📦 正在逐一扫描数据源，请稍候...\n")

        data = {
            "date": now.strftime("%Y-%m-%d"),
            "time": now.strftime("%Y-%m-%d %H:%M"),
            "github": fetch_source("github", _fetch_github),
            "oschina": fetch_source("oschina", _fetch_oschina),
            "hackernews": fetch_source("hackernews", _fetch_hackernews),
        }
        save_cache(data)
        print()

    print("━" * 40)

    # GitHub 项目（最核心，放最前面）
    if data.get("github"):
        print(f"\n📌 GitHub AI 项目（{len(data['github'])} 条）")
        print("  " + "─" * 50)
        for name, stars, desc, lang in data["github"]:
            lang_tag = f"  [{lang}]" if lang else ""
            print(f"  {name:40s} ⭐{stars:>8d}{lang_tag}")
            if desc:
                print(f"  {'':>40s} {desc[:70]}")
    else:
        print(f"\n📌 GitHub AI 项目：暂时无数据")

    # OSCHINA（国内源，快且准，放第二位）
    if data.get("oschina"):
        print(f"\n🇨🇳 OSCHINA 开源中国热点（{len(data['oschina'])} 条）")
        print("  " + "─" * 50)
        for (title,) in data["oschina"]:
            print(f"  • {title[:70]}")
    else:
        print(f"\n🇨🇳 OSCHINA：暂时无数据")

    # Hacker News（最慢，放最后）
    if data.get("hackernews"):
        print(f"\n🔥 Hacker News 热门（{len(data['hackernews'])} 条）")
        print("  " + "─" * 50)
        for title, score in data["hackernews"]:
            print(f"  [{score:3d}pts] {title[:70]}")
    else:
        print(f"\n🔥 Hacker News：暂时无数据（国内网络偏慢，不影响其他数据源）")

    # 汇总
    print(f"\n{'━' * 40}")
    counts = [len(data.get(k, [])) for k in ("github", "oschina", "hackernews")]
    print(f"  扫描完成：{counts[0]} GitHub + {counts[1]} 国内 + {counts[2]} HN")
    if data.get("date") == now.strftime("%Y-%m-%d"):
        print(f"  缓存已保存至 ~/.cache/ai-agent-toolkit/（同一天不再重复请求）")
    print()


if __name__ == "__main__":
    main()