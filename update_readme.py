import os
import json
import math
import re
from datetime import datetime
from collections import Counter
from urllib.request import Request, urlopen
from urllib.error import HTTPError

GITHUB_USERNAME = "HydroGest"
ALIAS_YURIKALE = "YuriKale / 羽衣甘蓝"
ALIAS_MARKCHAI = "Markchai"

def fetch_github_data(endpoint):
    url = f"https://api.github.com/{endpoint}"
    req = Request(url)
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    req.add_header("User-Agent", "Data-Science-TUI-Generator")
    try:
        with urlopen(req) as response:
            return json.loads(response.read().decode())
    except HTTPError as e:
        raise RuntimeError(f"HTTP_{e.code}_{e.reason}")
    except Exception as e:
        raise RuntimeError(f"ConnError_{str(e)}")

def get_visual_width(s):
    width = 0
    for ch in s:
        if '\u4e00' <= ch <= '\u9fff': width += 2
        else: width += 1
    return width

def visual_ljust(s, width):
    w = get_visual_width(s)
    if w >= width: return s
    return s + " " * (width - w)

def draw_bar(value, max_value, length=30):
    if max_value == 0: return "░" * length
    filled = int((value / max_value) * length)
    return "█" * filled + "░" * (length - filled)

# 数据科学算法：计算语言集中度的基尼系数
def calculate_gini(languages_counter):
    counts = sorted(list(languages_counter.values()))
    n = len(counts)
    if n <= 1 or sum(counts) == 0: return 0.0
    # Gini Coefficient 标准计算公式
    num = sum((2 * (i + 1) - n - 1) * val for i, val in enumerate(counts))
    return num / (n * sum(counts))

def analyze_profile():
    bt = "`" * 3
    
    try:
        user_data = fetch_github_data(f"users/{GITHUB_USERNAME}")
        repos = fetch_github_data(f"users/{GITHUB_USERNAME}/repos?per_page=100&sort=updated") or []
        events = fetch_github_data(f"users/{GITHUB_USERNAME}/events/public?per_page=100") or []
    except Exception as kernel_err:
        return f"{bt}text\n[FATAL] CRITICAL_METRICS_PANIC: {str(kernel_err)}\n{bt}"

    total_stars = sum(repo.get("stargazers_count", 0) for repo in repos)
    total_forks = sum(repo.get("forks_count", 0) for repo in repos)
    
    # 1. 扩充多语言维度统计
    languages = Counter()
    for repo in repos:
        if repo.get("language"):
            languages[repo["language"]] += 1
            
    total_lang_repos = sum(languages.values())
    
    # 计算香农语言熵
    lang_entropy = 0.0
    if total_lang_repos > 0:
        for count in languages.values():
            p = count / total_lang_repos
            lang_entropy -= p * math.log(p)

    # 计算技术栈基尼系数
    gini_index = calculate_gini(languages)

    # 2. 深度时序作息与时间熵计算
    commit_hours = []
    intent_vectors = {"Features": 0, "Fixes": 0, "Refactor": 0, "Maintenance": 0}
    
    # 语义解析分类器字典映射
    semantic_map = {
        r'^(feat|add|create|new|implement)\b': "Features",
        r'^(fix|bug|patch|issue|prevent)\b': "Fixes",
        r'^(refactor|clean|perf|opt|optimize|reformat)\b': "Refactor",
        r'^(chore|docs|style|test|build|ci|deps|update|merge|release)\b': "Maintenance"
    }

    for event in events:
        if event.get("type") == "PushEvent":
            created_at = event.get("created_at")
            if created_at:
                dt = datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%SZ")
                commit_hours.append(dt.hour)
            
            for c in event.get("payload", {}).get("commits", []):
                msg = c.get("message", "").strip().lower()
                matched = False
                for pattern, category in semantic_map.items():
                    if re.match(pattern, msg):
                        intent_vectors[category] += 1
                        matched = True
                        break
                if not matched and msg:
                    # 默认归入通用行为
                    intent_vectors["Features" if "add" in msg or "make" in msg else "Maintenance"] += 1

    time_slots = {"00-06": 0, "06-12": 0, "12-18": 0, "18-24": 0}
    for h in commit_hours:
        if 0 <= h < 6: time_slots["00-06"] += 1
        elif 6 <= h < 12: time_slots["06-12"] += 1
        elif 12 <= h < 18: time_slots["12-18"] += 1
        else: time_slots["18-24"] += 1
        
    # 计算时间空间分布熵 (Circadian Time Entropy)
    time_entropy = 0.0
    total_commits = sum(time_slots.values())
    if total_commits > 0:
        for count in time_slots.values():
            if count > 0:
                p = count / total_commits
                time_entropy -= p * math.log(p)

    # 作息定性评价
    if time_entropy > 1.1:    chaos_rating = "High Chaos (Erratic Hacker Schedule)"
    elif time_entropy > 0.6:  chaos_rating = "Semi-Structured Intermittent"
    else:                     chaos_rating = "Strict Monolithic Routine"

    max_slot_val = max(time_slots.values()) if commit_hours else 1
    top_langs = languages.most_common(6) # 扩展到前 6 种语言显示
    max_lang_count = max(languages.values()) if languages else 1
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
