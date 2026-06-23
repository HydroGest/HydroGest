import os
import json
from datetime import datetime
from collections import Counter
from urllib.request import Request, urlopen

# 配置信息
GITHUB_USERNAME = "HydroGest"
ALIAS_YURIKALE = "YuriKale / 羽衣甘蓝"
ALIAS_MARKCHAI = "Markchai"

def fetch_github_data(endpoint):
    url = f"https://api.github.com/{endpoint}"
    req = Request(url)
    # GitHub Action 会自动提供 GITHUB_TOKEN 免受 Rate Limit 限制
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", f"token {token}")
    req.add_header("User-Agent", "Terminal-Profile-Generator")
    
    try:
        with urlopen(req) as response:
            return json.loads(response.read().decode())
    except Exception as e:
        print(f"[ERROR] Failed to fetch {endpoint}: {e}")
        return None

def analyze_profile():
    # 1. 获取基本信息与仓库
    user_data = fetch_github_data(f"users/{GITHUB_USERNAME}")
    repos = fetch_github_data(f"users/{GITHUB_USERNAME}/repos?per_page=100") or []
    events = fetch_github_data(f"users/{GITHUB_USERNAME}/events/public?per_page=100") or []
    
    if not user_data:
        return "Error loading GitHub Profile."

    # 2. 深度分析：代码作息与提交偏好
    commit_hours = []
    commit_verbs = []
    total_stars = 0
    languages = Counter()

    for repo in repos:
        total_stars += repo.get("stargazers_count", 0)
        if repo.get("language"):
            languages[repo["language"]] += 1

    for event in events:
        if event.get("type") == "PushEvent":
            # 转换 ISO 时间到小时
            created_at = event.get("created_at")
            if created_at:
                dt = datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%SZ")
                commit_hours.append(dt.hour)
            
            # 提取 Commit 关键词
            commits = event.get("payload", {}).get("commits", [])
            for c in commits:
                msg = c.get("message", "").lower().split()
                if msg:
                    commit_verbs.append(msg[0]) # 提取第一个动词如 feat, fix, update

    # 3. 统计作息习惯
    time_slots = {"Midnight (0-6)": 0, "Morning (6-12)": 0, "Afternoon (12-18)": 0, "Evening (18-24)": 0}
    for h in commit_hours:
        if 0 <= h < 6: time_slots["Midnight (0-6)"] += 1
        elif 6 <= h < 12: time_slots["Morning (6-12)"] += 1
        elif 12 <= h < 18: time_slots["Afternoon (12-18)"] += 1
        else: time_slots["Evening (18-24)"] += 1
    
    favorite_time = max(time_slots, key=time_slots.get) if commit_hours else "Unknown"
    top_verbs = [f"{k}({v})" for k, v in Counter(commit_verbs).most_common(3)]
    top_langs = [k for k, _ in languages.most_common(4)]

    # 4. 格式化输出终端字符流
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
    
    readme_content = f"""```bash
guest@github:~$ neofetch --user {GITHUB_USERNAME}
       .---.         👤 Identity: {ALIAS_YURIKALE} (a.k.a {ALIAS_MARKCHAI})
      /     \\        🏫 Role: Incoming CS Undergrad
      \\_.-./         📦 Public Repos: {user_data.get('public_repos', 0)}
       `---'         ⭐ Total Stars: {total_stars}
                     🐧 Environment: Linux SysAdmin / Paper Plugin / OI
                     ⏰ Generated: {current_time}

guest@github:~$ ./analyze_activity.sh --deep

[SYS] Indexing latest 100 public events...
[INFO] Primary Code Environment: {', '.join(top_langs) if top_langs else "Heterogeneous Stack"}
[INFO] Peak Productivity Window: {favorite_time}
[INFO] Top Git Commits Intent:   {', '.join(top_verbs) if top_verbs else "N/A"}

guest@github:~$ systemctl status brain.service
● brain.service - Core Developer Mentality
   Loaded: loaded
   Active: active (running)
   Main Status Metrics:
   ├─ Core Stack:  [C++] [Python] [Kotlin] [TypeScript] [Linux Bash]
   ├─ Frameworks:  [Paper] [Flask] [Vue] [Koishi] (and dynamic scaling...)
   └─ SysAdmin:   [Kernel Tuning] [Minecraft Server Ops] [OI Background]

guest@github:~$ _
```"""
    return readme_content

if __name__ == "__main__":
    content = analyze_profile()
    with open("README.md", "w", encoding="utf-8") as f:
        f.write(content)
    print("README.md updated successfully.")
