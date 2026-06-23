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

# 核心改进 1：采用像素级绝对等宽的几何符号 ■ 和 □
def draw_bar(value, max_value, length=30):
    if max_value == 0: return "□" * length
    filled = int((value / max_value) * length)
    return "■" * filled + "□" * (length - filled)

def calculate_gini(languages_counter):
    counts = sorted(list(languages_counter.values()))
    n = len(counts)
    if n <= 1 or sum(counts) == 0: return 0.0
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

    gini_index = calculate_gini(languages)

    # 核心改进 2：多策略鲁棒语义解析器
    commit_hours = []
    intent_vectors = {"Features": 0, "Fixes": 0, "Refactor": 0, "Maintenance": 0}
    
    # 统计时间（不受 API 文本截断影响）
    for event in events:
        if event.get("type") == "PushEvent":
            created_at = event.get("created_at")
            if created_at:
                dt = datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%SZ")
                commit_hours.append(dt.hour)
            
            # 尝试从事件流中提取提交信息
            for c in event.get("payload", {}).get("commits", []):
                msg = c.get("message", "").strip().lower()
                if msg:
                    if any(w in msg for w in ["feat", "add", "create", "new", "implement"]):
                        intent_vectors["Features"] += 1
                    elif any(w in msg for w in ["fix", "bug", "patch", "issue", "prevent"]):
                        intent_vectors["Fixes"] += 1
                    elif any(w in msg for w in ["refactor", "clean", "perf", "opt", "optimize", "reformat"]):
                        intent_vectors["Refactor"] += 1
                    else:
                        intent_vectors["Maintenance"] += 1

    # 核心改进 3：回溯降级子系统（若事件流没有文本，直接闪击真实仓库的 Commit Logs）
    if sum(intent_vectors.values()) == 0 and repos:
        print("[WARN] Public events feed text truncated by GitHub. Activating Deep Fallback Engine...")
        for repo in repos[:3]: # 扫描最近活跃的前 3 个仓库
            repo_name = repo.get("name")
            try:
                commit_list = fetch_github_data(f"repos/{GITHUB_USERNAME}/{repo_name}/commits?author={GITHUB_USERNAME}&per_page=15")
                if isinstance(commit_list, list):
                    for commit_obj in commit_list:
                        msg = commit_obj.get("commit", {}).get("message", "").strip().lower()
                        if msg:
                            if any(w in msg for w in ["feat", "add", "create", "new", "implement"]):
                                intent_vectors["Features"] += 1
                            elif any(w in msg for w in ["fix", "bug", "patch", "issue", "prevent"]):
                                intent_vectors["Fixes"] += 1
                            elif any(w in msg for w in ["refactor", "clean", "perf", "opt", "optimize", "reformat"]):
                                intent_vectors["Refactor"] += 1
                            else:
                                intent_vectors["Maintenance"] += 1
            except Exception:
                continue # 某个仓库报错直接跳过，确保核心稳定性

    time_slots = {"00-06": 0, "06-12": 0, "12-18": 0, "18-24": 0}
    for h in commit_hours:
        if 0 <= h < 6: time_slots["00-06"] += 1
        elif 6 <= h < 12: time_slots["06-12"] += 1
        elif 12 <= h < 18: time_slots["12-18"] += 1
        else: time_slots["18-24"] += 1
        
    time_entropy = 0.0
    total_commits = sum(time_slots.values())
    if total_commits > 0:
        for count in time_slots.values():
            if count > 0:
                p = count / total_commits
                time_entropy -= p * math.log(p)

    if time_entropy > 1.1:    chaos_rating = "High Chaos (Erratic Hacker Schedule)"
    elif time_entropy > 0.6:  chaos_rating = "Semi-Structured Intermittent"
    else:                     chaos_rating = "Strict Monolithic Routine"

    max_slot_val = max(time_slots.values()) if commit_hours else 1
    top_langs = languages.most_common(6)
    max_lang_count = max(languages.values()) if languages else 1
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")

    if lang_entropy < 0.6:   stack_type = "Hyper-Focused Specialist"
    elif lang_entropy < 1.3: stack_type = "Balanced Polymath"
    else:                    stack_type = "High-Entropy FullStack Generalist"

    output = []
    output.append("========================================================================")
    output.append(f"HYDRO-OS v4.5.0-LTS // TELEMETRY & DATA SCIENCE DASHBOARD")
    output.append("========================================================================\n")
    
    output.append("[System Identity & Temporal State]")
    output.append(f"  User:          {visual_ljust(GITHUB_USERNAME, 30)}")
    output.append(f"  Alias:         {visual_ljust(ALIAS_YURIKALE, 30)}")
    output.append(f"  Legacy:        {visual_ljust(ALIAS_MARKCHAI, 30)}")
    output.append(f"  Clock Engine:  {current_time}\n")
    
    output.append("[Core Mathematical Vectors]")
    output.append(f"  Public Repos:  {str(user_data.get('public_repos', 0)).ljust(10)}  Total Stars:         {str(total_stars).ljust(10)}")
    output.append(f"  Total Forks:   {str(total_forks).ljust(10)}  Language Shannon H:  {f'{lang_entropy:.2f}'}")
    output.append(f"  Gini Index G:  {f'{gini_index:.2f}'.ljust(10)}  Circadian Entropy:   {f'{time_entropy:.2f}'}")
    output.append(f"  Schedule Mode: {chaos_rating}\n")
    
    output.append("[Advanced Stack Distribution Vector (Top 6)]")
    for lang, count in top_langs:
        pct = (count / total_lang_repos) * 100 if total_lang_repos > 0 else 0
        lang_label = visual_ljust(lang, 15)
        output.append(f"  {lang_label} [{draw_bar(count, max_lang_count, 30)}] {pct:5.1f}% ({count} repos)")
    output.append("")
        
    output.append("[Circadian Activity Rhythm]")
    slots_config = [
        ("00-06 Midnight", "00-06"),
        ("06-12 Morning", "06-12"),
        ("12-18 Afternoon", "12-18"),
        ("18-24 Evening", "18-24")
    ]
    for label, key in slots_config:
        slot_label = visual_ljust(label, 16)
        output.append(f"  {slot_label} [{draw_bar(time_slots[key], max_slot_val, 30)}] {str(time_slots[key]).rjust(3)} commits")
    output.append("")
        
    output.append("[Semantic Developer Intent Vector]")
    total_intents = sum(intent_vectors.values())
    max_intent = max(intent_vectors.values()) if total_intents > 0 else 1
    for category, count in intent_vectors.items():
        pct = (count / total_intents) * 100 if total_intents > 0 else 0
        cat_label = visual_ljust(category, 16)
        output.append(f"  {cat_label} [{draw_bar(count, max_intent, 30)}] {pct:5.1f}%")
        
    output.append("\n[brain.service - Runtime Subsystems]")
    output.append(f"  Status:        active (running) since 2013-09-01 (Minecraft Server Genesis)")
    output.append(f"  Sub-Layers:    [Paper Plugin Architecture] [Koishi Bot Framework] [Vue Ecosystem]")
    output.append(f"  SysAdmin Caps: [Linux Kernel Tuning] [Network Routing Optimization] [OI Background]")
    output.append("========================================================================")

    tui_body = "\n".join(output)
    return f"{bt}text\n" + tui_body + f"\n{bt}"

if __name__ == "__main__":
    content = analyze_profile()
    with open("README.md", "w", encoding="utf-8") as f:
        f.write(content)
    print("[SUCCESS] Telemetry alignment complete.")
