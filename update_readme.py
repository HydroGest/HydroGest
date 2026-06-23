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
    
    # 升级为现代 Bearer 鉴权协议，防止 401/403 限制
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    req.add_header("User-Agent", "Advanced-TUI-Profile-Generator")
    
    try:
        with urlopen(req) as response:
            return json.loads(response.read().decode())
    except HTTPError as e:
        raise RuntimeError(f"HTTP_{e.code}_{e.reason}")
    except Exception as e:
        raise RuntimeError(f"ConnError_{str(e)}")

def draw_bar(value, max_value, length=18):
    if max_value == 0: return "░" * length
    filled = int((value / max_value) * length)
    return "█" * filled + "░" * (length - filled)

def analyze_profile():
    bt = "`" * 3
    
    # 2. 深度数据抓取与高级异常解析
    try:
        user_data = fetch_github_data(f"users/{GITHUB_USERNAME}")
        repos = fetch_github_data(f"users/{GITHUB_USERNAME}/repos?per_page=100&sort=updated") or []
        events = fetch_github_data(f"users/{GITHUB_USERNAME}/events/public?per_page=100") or []
    except Exception as kernel_err:
        # 核心改进：发生 Panic 时直接将具体错误代码打印到 README，杜绝盲盒 Debug
        return f"{bt}text\n┌────────────────────────────────────────────────────────────────────────────┐\n│ [FATAL] Kernel Panic: Core Sync Engine Demise                              │\n│ Cause : {str(kernel_err).ljust(66)} │\n└────────────────────────────────────────────────────────────────────────────┘\n{bt}"

    # 后续高精度 TUI 渲染矩阵保持不变...
    total_stars = sum(repo.get("stargazers_count", 0) for repo in repos)
    total_forks = sum(repo.get("forks_count", 0) for repo in repos)
    
    languages = Counter()
    for repo in repos:
        if repo.get("language"):
            languages[repo["language"]] += 1
            
    total_lang_repos = sum(languages.values())
    lang_entropy = 0.0
    if total_lang_repos > 0:
        for count in languages.values():
            p = count / total_lang_repos
            lang_entropy -= p * math.log(p)
            
    if lang_entropy < 0.6:   stack_type = "Hyper-Focused Specialist"
    elif lang_entropy < 1.3: stack_type = "Balanced Polymath"
    else:                    stack_type = "High-Entropy FullStack Generalist"

    commit_verbs = []
    commit_hours = []
    for event in events:
        if event.get("type") == "PushEvent":
            created_at = event.get("created_at")
            if created_at:
                dt = datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%SZ")
                commit_hours.append(dt.hour)
            
            for c in event.get("payload", {}).get("commits", []):
                msg = c.get("message", "").strip()
                match = re.match(r'^([a-zA-Z]+)(?:\([^)]+\))?!?:?', msg)
                if match:
                    verb = match.group(1).lower()
                    if len(verb) > 1 and verb not in ['the', 'and', 'for', 'version']:
                        commit_verbs.append(verb)

    time_slots = {"00-06": 0, "06-12": 0, "12-18": 0, "18-24": 0}
    for h in commit_hours:
        if 0 <= h < 6: time_slots["00-06"] += 1
        elif 6 <= h < 12: time_slots["06-12"] += 1
        elif 12 <= h < 18: time_slots["12-18"] += 1
        else: time_slots["18-24"] += 1
        
    max_slot_val = max(time_slots.values()) if commit_hours else 1
    peak_slot = max(time_slots, key=time_slots.get) if commit_hours else "00-06"
    
    chronotype = "Unknown"
    if peak_slot == "00-06":   chronotype = "Extreme Night Owl (Circadian Shift)"
    elif peak_slot == "06-12": chronotype = "Early Bird"
    elif peak_slot == "12-18": chronotype = "Standard Diurnal"
    elif peak_slot == "18-24": chronotype = "Late-Night Hacker"

    top_verbs = Counter(commit_verbs).most_common(3)
    intent_str = ", ".join([f"{k}({v})" for k, v in top_verbs]) if top_verbs else "coding(active)"

    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
    top_langs = languages.most_common(3)
    max_lang_count = max(languages.values()) if languages else 1

    tui_body = f"""┌────────────────────────────────────────────────────────────────────────────┐
│  HYDRO-OS v2.6.0-LTS  [SYS: ONLINE]                 METRICS CORE MONITOR   │
└────────────────────────────────────────────────────────────────────────────┘
┌─ [ System Identity ] ──────────────────┐┌─ [ Core Kernel Metrics ] ────────┐
│ User   : {GITHUB_USERNAME.ljust(29)} ││ Public Repos : {str(user_data.get('public_repos', 0)).ljust(18)} │
│ Alias  : {ALIAS_YURIKALE.ljust(29)} ││ Total Stars  : {str(total_stars).ljust(18)} │
│ Legacy : {ALIAS_MARKCHAI.ljust(29)} ││ Total Forks  : {str(total_forks).ljust(18)} │
│ Status : Incoming CS Undergrad         ││ Tech Entropy : H={f"{lang_entropy:.2f}".ljust(16)} │
└────────────────────────────────────────┘└──────────────────────────────────┘
┌─ [ Stack Distribution Vector & Complexity Analysis ] ──────────────────────┐
│ Architecture Profile: {stack_type.ljust(52)} │
│                                                                            │"""
    for lang, count in top_langs:
        pct = (count / total_lang_repos) * 100 if total_lang_repos > 0 else 0
        bar = draw_bar(count, max_lang_count, length=24)
        tui_body += f"\n│  - {lang.ljust(12)} [{bar}] {pct:4.1f}%   │"
        
    tui_body += f"""
└────────────────────────────────────────────────────────────────────────────┘
┌─ [ Chronotype & Circadian Activity Rhythm ] ───────────────────────────────┐
│ Schedule Engine: {chronotype.ljust(57)} │
│                                                                            │
│  Midnight (00-06)  [{draw_bar(time_slots["00-06"], max_slot_val, 28)}] {time_slots["00-06"]:3d} commits  │
│  Morning  (06-12)  [{draw_bar(time_slots["06-12"], max_slot_val, 28)}] {time_slots["06-12"]:3d} commits  │
│  Afternoon(12-18)  [{draw_bar(time_slots["12-18"], max_slot_val, 28)}] {time_slots["12-18"]:3d} commits  │
│  Evening  (18-24)  [{draw_bar(time_slots["18-24"], max_slot_val, 28)}] {time_slots["18-24"]:3d} commits  │
└────────────────────────────────────────────────────────────────────────────┘
┌─ [ Process Manager & Runtime Flags ] ──────────────────────────────────────┐
│ ● brain.service - Dev Core Mentality Runtime Daemon                        │
│   Loaded: active (running) since 2013-09-01 (Minecraft Server Genesis)     │
│   Intent: [ {intent_str.ljust(64)} ] │
│   Flags : [C++] [Python] [Kotlin] [TypeScript] [Linux Kernel Tuning] [OI]   │
│   Clock : {current_time.ljust(66)} │
└────────────────────────────────────────────────────────────────────────────┘"""

    return f"{bt}text\n" + tui_body + f"\n{bt}"

if __name__ == "__main__":
    content = analyze_profile()
    with open("README.md", "w", encoding="utf-8") as f:
        f.write(content)
    print("[SUCCESS] TUI Panel rendered.")
