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
    req.add_header("User-Agent", "Advanced-Console-Profile-Generator")
    try:
        with urlopen(req) as response:
            return json.loads(response.read().decode())
    except HTTPError as e:
        raise RuntimeError(f"HTTP_{e.code}_{e.reason}")
    except Exception as e:
        raise RuntimeError(f"ConnError_{str(e)}")

# 数据科学级：精确计算包含中文、特殊符号的字符串在终端中的「视觉投影宽度」
def get_visual_width(s):
    width = 0
    for ch in s:
        # 检测是否属于 CJK 中文字符集范围
        if '\u4e00' <= ch <= '\u9fff':
            width += 2
        else:
            width += 1
    return width

# 自适应视觉对齐函数，替代原生 broken 的 ljust
def visual_ljust(s, width):
    w = get_visual_width(s)
    if w >= width:
        return s
    return s + " " * (width - w)

def draw_bar(value, max_value, length=30):
    if max_value == 0: return "░" * length
    filled = int((value / max_value) * length)
    return "█" * filled + "░" * (length - filled)

def analyze_profile():
    bt = "`" * 3
    
    try:
        user_data = fetch_github_data(f"users/{GITHUB_USERNAME}")
        repos = fetch_github_data(f"users/{GITHUB_USERNAME}/repos?per_page=100&sort=updated") or []
        events = fetch_github_data(f"users/{GITHUB_USERNAME}/events/public?per_page=100") or []
    except Exception as kernel_err:
        return f"{bt}text\n[FATAL] SYSTEM_CORE_PANIC: {str(kernel_err)}\n{bt}"

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

    # 开始构建纯净扁平化终端流输出
    output = []
    output.append("========================================================================")
    output.append(f"HYDRO-OS v3.0.0-UNBOXED // SYSTEM DIAGNOSTIC REPORT ENGINE")
    output.append("========================================================================\n")
    
    output.append("[System Identity]")
    output.append(f"  User:         {visual_ljust(GITHUB_USERNAME, 30)}")
    output.append(f"  Alias:        {visual_ljust(ALIAS_YURIKALE, 30)}")
    output.append(f"  Legacy:       {visual_ljust(ALIAS_MARKCHAI, 30)}")
    output.append(f"  Status:       Incoming CS Undergrad")
    output.append(f"  Clock:        {current_time}\n")
    
    output.append("[Core Kernel Metrics]")
    output.append(f"  Public Repos: {str(user_data.get('public_repos', 0)).ljust(10)}  Total Stars:  {str(total_stars).ljust(10)}")
    output.append(f"  Total Forks:  {str(total_forks).ljust(10)}  Tech Entropy: H={f'{lang_entropy:.2f}'}")
    output.append(f"  Architecture: {stack_type}\n")
    
    output.append("[Stack Distribution Vector]")
    for lang, count in top_langs:
        pct = (count / total_lang_repos) * 100 if total_lang_repos > 0 else 0
        # 对齐语言标签(长14)，确保进度条 [ 起点绝对一致，总长统一为 30
        lang_label = visual_ljust(lang, 14)
        output.append(f"  {lang_label} [{draw_bar(count, max_lang_count, 30)}] {pct:5.1f}%")
    output.append("")
        
    output.append("[Circadian Activity Rhythm]")
    output.append(f"  Schedule:     {chronotype}\n")
    
    # 对齐时间段标签
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
        
    output.append("[brain.service - Process Status]")
    output.append(f"  Status:       active (running) since 2013-09-01 (Minecraft Server Genesis)")
    output.append(f"  Intent:       {intent_str}")
    output.append(f"  Flags:        [C++] [Python] [Kotlin] [TypeScript] [Linux Kernel Tuning] [OI]")
    output.append("\n========================================================================")

    tui_body = "\n".join(output)
    return f"{bt}text\n" + tui_body + f"\n{bt}"

if __name__ == "__main__":
    content = analyze_profile()
    with open("README.md", "w", encoding="utf-8") as f:
        f.write(content)
    print("[SUCCESS] Flattened TUI Panel rendered.")
