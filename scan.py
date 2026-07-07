#!/usr/bin/env python3
"""
ai-agent-toolkit — 一个轻量的AI情报扫描工具。
每天跑一次，看看技术圈发生了什么。
"""
import urllib.request
import json
from datetime import datetime

def fetch_github():
    """获取GitHub热门AI项目"""
    url = "https://api.github.com/search/repositories?q=AI+agent&sort=stars&per_page=5"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "ai-agent-toolkit/1.0"})
        data = json.loads(urllib.request.urlopen(req, timeout=10).read())
        return [(r["full_name"], r["stargazers_count"], (r.get("description") or "")[:80]) for r in data.get("items", [])]
    except:
        return [("(当前网络不可达)", 0, "可尝试使用镜像源或稍后重试")]

def fetch_hn():
    """获取Hacker News热门"""
    try:
        ids = json.loads(urllib.request.urlopen("https://hacker-news.firebaseio.com/v0/topstories.json", timeout=10).read())[:3]
        return [(
            json.loads(urllib.request.urlopen(f"https://hacker-news.firebaseio.com/v0/item/{sid}.json", timeout=10).read())
        ) for sid in ids]
    except:
        return []

def main():
    dt = datetime.now().strftime("%Y-%m-%d %H:%M")
    print(f"\n📡 {dt} 扫描报告")
    print("━" * 35)
    
    repos = fetch_github()
    if repos and repos[0][1] > 0:
        for name, stars, desc in repos:
            print(f"\n  📌 {name}")
            print(f"     ⭐{stars}  |  {desc}")
    
    hn = fetch_hn()
    if hn:
        print(f"\n  🔥 Hacker News 热门")
        for item in hn[:3]:
            title = item.get("title", "")
            score = item.get("score", 0)
            print(f"     [{score}pts] {title[:80]}")

    print(f"\n{'━' * 35}")
    print(f"  扫描完成")
    print()

if __name__ == "__main__":
    main()
