import os
import json
import math
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
    req.add_header("User-Agent", "Minimal-Terminal-Generator")
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
    if max_value == 0: return "." * length
    filled = int((value / max_value) * length)
    return "#" * filled + "." * (length - filled)

def calculate_gini(languages_counter):
    counts = sorted(list(languages_counter.values()))
    n = len(counts)
    if n <= 1 or sum(counts) == 0: return 0.0
    num = sum((2 * (i + 1) - n - 1) * val for i, val in enumerate(counts))
    return num / (n * sum(counts))

# 核心改进 1：基于开发者行为学修正的精细化多源分类器
def classify_commit(msg):
    msg = msg.lower()
    
    # 优先提取确切的线上/线下缺陷修复
    if any(w in msg for w in ["fix", "bug", "patch", "issue", "prevent", "修复", "解决", "修正", "报错", "排查"]):
        return "Fixes"
        
    # 架构演进与深度代码性能优化
    if any(w in msg for w in ["refactor", "clean", "perf", "opt", "optimize", "reformat", "重构", "优化", "性能", "重写", "rewrite"]):
        return "Refactor"
        
    # 显式新特性开发
    if any(w in msg for w in ["feat", "add", "create", "new", "implement", "新增", "添加", "创建", "引入", "功能", "支持", "support", "init", "初始化", "实现"]):
        return "Features"
        
    # 显式的基础设施维护（文档、依赖、流水线、测试用例）
    if any(w in msg for w in ["chore", "docs", "style", "test", "build", "ci", "deps", "bump", "wip", "release", "文档", "测试", "依赖", "workflow", "readme"]):
        return "Maintenance"
        
    # 行为补偿机制：对于“update main.js”或“修改文件”等日常非规范性提交，本质属于特性演进或日常开发，归入 Features 矩阵
    if any(w in msg for w in ["update", "change", "modify", "adjust", "更新", "修改", "调整", "改动"]):
        return "Features"
        
    # 绝对兜底：拒绝默认维护化，未识别的敏捷开发提交默认视为业务演进
    return "Features"

def analyze_profile():
    bt = "`" * 3
    
    try:
        user_data = fetch_github_data(f"users/{GITHUB_USERNAME}")
        
        # 核心改进 2：多渠道全量仓库交叉检索系统（解决组织内贡献无法统计 Star 的问题）
        repo_map = {}
        
        # 渠道 A：用户个人名下的直接仓库
        owned_repos = fetch_github_data(f"users/{GITHUB_USERNAME}/repos?per_page=100") or []
        for r in owned_repos:
            repo_map[r["full_name"]] = r
            
        # 渠道 B：全网检索包含用户显式贡献（Contributor）的组织及外部仓库
        try:
            search_url = f"search/repositories?q=contributor:{GITHUB_USERNAME}&per_page=100"
            search_res = fetch_github_data(search_url)
            if search_res and "items" in search_res:
                for r in search_res["items"]:
                    repo_map[r["full_name"]] = r
        except Exception as e:
            print(f"[WARN] Cross-org scanning encountered a limit rate or issue: {e}")
            
        all_repos = list(repo_map.values())
        # 按照活跃时间降序排序，保证高权重回溯
        all_repos.sort(key=lambda x: x.get("pushed_at") or x.get("updated_at") or "", reverse=True)
        
        events = fetch_github_data(f"users/{GITHUB_USERNAME}/events/public?per_page=100") or []
    except Exception as kernel_err:
        return f"{bt}text\n[FATAL] SYSTEM_PANIC: {str(kernel_err)}\n{bt}"

    # 汇总计算包含组织在内的全量全局数据
    total_stars = sum(repo.get("stargazers_count", 0) for repo in all_repos)
    total_forks = sum(repo.get("forks_count", 0) for repo in all_repos)
    
    languages = Counter()
    for repo in all_repos:
        if repo.get("language"):
            languages[repo["language"]] += 1
            
    total_lang_repos = sum(languages.values())
    
    lang_entropy = 0.0
    if total_lang_repos > 0:
        for count in languages.values():
            p = count / total_lang_repos
            lang_entropy -= p * math.log(p)

    gini_index = calculate_gini(languages)

    commit_hours = []
    intent_vectors = {"Features": 0, "Fixes": 0, "Refactor": 0, "Maintenance": 0}
    
    # 统计公共活动流（提取时间轴分布）
    for event in events:
        if event.get("type") == "PushEvent":
            created_at = event.get("created_at")
            if created_at:
                dt = datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%SZ")
                commit_hours.append(dt.hour)
            
            for c in event.get("payload", {}).get("commits", []):
                msg = c.get("message", "")
                if msg:
                    intent_vectors[classify_commit(msg)] += 1

    # 核心改进 3：修复组织仓库 Commit 日志回溯时因 Owner 缺失导致的 404 盲区
    if all_repos:
        print("[INFO] Harvesting deeper semantic logs from merged repos stack...")
        for repo in all_repos[:5]:
            full_name = repo.get("full_name") # 直接获取标准的 "org/repo" 或 "user/repo" 完整命名空间
            try:
                commit_list = fetch_github_data(f"repos/{full_name}/commits?author={GITHUB_USERNAME}&per_page=30")
                if isinstance(commit_list, list):
                    for commit_obj in commit_list:
                        msg = commit_obj.get("commit", {}).get("message", "")
                        if msg:
                            intent_vectors[classify_commit(msg)] += 1
            except Exception:
                continue

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

    if time_entropy > 1.1:    chaos_rating = "Erratic Hacker Schedule"
    elif time_entropy > 0.6:  chaos_rating = "Semi-Structured Routine"
    else:                     chaos_rating = "Strict Monolithic Routine"

    max_slot_val = max(time_slots.values()) if commit_hours else 1
    top_langs = languages.most_common(6)
    max_lang_count = max(languages.values()) if languages else 1
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")

    output = []
    output.append("========================================================================")
    output.append(f"HYDROGEST // PROFILE TERMINAL MONITOR")
    output.append("========================================================================\n")
    
    output.append("[System Identity]")
    output.append(f"  User:          {visual_ljust(GITHUB_USERNAME, 30)}")
    output.append(f"  Alias:         {visual_ljust(ALIAS_YURIKALE, 30)}")
    output.append(f"  Legacy:        {visual_ljust(ALIAS_MARKCHAI, 30)}")
    output.append(f"  Clock:         {current_time}\n")
    
    output.append("[Kernel Metrics]")
    output.append(f"  Public Repos:  {str(len(all_repos)).ljust(10)}  Total Stars:    {str(total_stars).ljust(10)}")
    output.append(f"  Total Forks:   {str(total_forks).ljust(10)}  Language H:     {f'{lang_entropy:.2f}'}")
    output.append(f"  Gini Index:    {f'{gini_index:.2f}'.ljust(10)}  Time Entropy:   {f'{time_entropy:.2f}'}")
    output.append(f"  Schedule:      {chaos_rating}\n")
    
    output.append("[Language Stack (Top 6)]")
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
        
    output.append("[Developer Intent Mapping]")
    total_intents = sum(intent_vectors.values())
    max_intent = max(intent_vectors.values()) if total_intents > 0 else 1
    for category, count in intent_vectors.items():
        pct = (count / total_intents) * 100 if total_intents > 0 else 0
        cat_label = visual_ljust(category, 16)
        output.append(f"  {cat_label} [{draw_bar(count, max_intent, 30)}] {pct:5.1f}%")
        
    output.append("\n[Subsystems]")
    output.append(f"  Status:        active (running) since 2020-09-01 (Minecraft Server Genesis)")
    output.append(f"  Stack:         [Paper Plugin] [Koishi Bot Framework] [Vue Ecosystem]")
    output.append(f"  Capabilities:  [Linux Kernel Tuning] [Network Routing] [OI Background]")
    output.append("========================================================================")

    tui_body = "\n".join(output)
    return f"{bt}text\n" + tui_body + f"\n{bt}"

if __name__ == "__main__":
    content = analyze_profile()
    with open("README.md", "w", encoding="utf-8") as f:
        f.write(content)
    print("[SUCCESS] Monospace profile synced successfully.")
