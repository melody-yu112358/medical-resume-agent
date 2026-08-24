#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
V3.2生成质量验证脚本

验证正式生成链是否真正生成接近人工黄金V3.2的完整简历。

所有检查均以 JSON（v3.2-resume-document.json）与 HTML
（v3.2-professional-generated.html）为输入，任一硬性失败都以退出码 1 返回。
"""
import json
import re
import sys
from pathlib import Path


# 禁止出现的中英内部枚举 / 硬编码动词 / 通用占位句
FORBIDDEN_PATTERNS = [
    "ensured",
    "maintained",
    "guaranteed",
    "perform_analysis",
    "collect_patient_history",
    "clinical_assessment",
    "提升工作质量和效果",
]

# 允许在正文中出现的英文医学术语（用于中英粘连白名单判断）
ALLOWED_LATIN_TERMS = [
    "Meta", "PICO", "PRISMA", "PubMed", "Embase", "Cochrane", "RoB",
    "R", "SPSS", "Excel", "EndNote", "NoteExpress", "ACS", "Logistic",
    "CET", "GPA",
]


def load_json(path: Path):
    """读取并解析JSON文件，失败时抛异常。"""
    return json.loads(path.read_text(encoding="utf-8"))


def collect_bullets(json_content):
    """从Resume Document JSON收集所有经历Bullet。

    返回:
        (meta_bullets, dachuang_bullets, clinical_bullets, all_bullets)
        all_bullets 为 (experience_key, bullet_dict) 列表，便于唯一定位。
    """
    meta_bullets = []
    dachuang_bullets = []
    clinical_bullets = []

    for exp in json_content.get("research_experience", []):
        meta_bullets.extend(exp.get("bullets", []))
    for exp in json_content.get("projects", []):
        dachuang_bullets.extend(exp.get("bullets", []))
    for exp in json_content.get("clinical_experience", []):
        clinical_bullets.extend(exp.get("bullets", []))

    all_bullets = (
        [("meta", b) for b in meta_bullets]
        + [("dachuang", b) for b in dachuang_bullets]
        + [("clinical", b) for b in clinical_bullets]
    )
    return meta_bullets, dachuang_bullets, clinical_bullets, all_bullets


def contains_internal_enums(text):
    """检测下划线形式的内部 action/method 枚举（如 collect_patient_history）。"""
    return bool(re.search(r"[a-z_]+_[a-z_]+", text))


def contains_mixed_cn_latin(text):
    """检测中英变量粘连（中文字符与拉丁字母无空格直接相邻）。

    白名单中的完整术语（Meta分析、PICO框架、RoB工具等）允许，但
    像 '使用spss、r' 这类小写裸枚举会被判定为粘连。
    """
    # 先将白名单术语替换为空格占位符，避免误报（空格会断开相邻关系）
    sanitized = text
    for term in ALLOWED_LATIN_TERMS:
        sanitized = sanitized.replace(term, " ")

    # 剩余情况：中文紧跟拉丁字母，或拉丁字母紧跟中文
    pattern = re.compile(r"[A-Za-z][一-鿿]|[一-鿿][A-Za-z]")
    return bool(pattern.search(sanitized))


def contains_placeholder_bullet(text):
    """检测通用占位句（无具体信息的空洞表达）。"""
    # 明确标记的空洞占位句；"提升工作质量和效果" 已在 FORBIDDEN_PATTERNS，
    # 这里补充检测同样空洞、不含任何事实要素的泛化句式。
    placeholder_phrases = [
        "提升工作质量和效果",
        "提升相关工作的专业能力",
        "支持相关研究工作",
    ]
    return any(p in text for p in placeholder_phrases)


def normalize_for_similarity(text):
    """归一化文本用于相似度比较：去标点、去空白、小写。"""
    text = re.sub(r"[^\w一-鿿]", "", text)
    return text.lower().strip()


def find_duplicate_or_similar_bullets(all_bullets):
    """查找完全重复或高度相似的Bullet。

    高度相似定义为：归一化后完全相同（仅剩动词差异时视为凑数），
    或编辑距离极低（长度接近且仅一字之差）。
    """
    problems = []

    for i in range(len(all_bullets)):
        key_i, bullet_i = all_bullets[i]
        text_i = normalize_for_similarity(bullet_i.get("text", ""))
        if not text_i:
            continue

        for j in range(i + 1, len(all_bullets)):
            key_j, bullet_j = all_bullets[j]
            text_j = normalize_for_similarity(bullet_j.get("text", ""))
            if not text_j:
                continue

            if text_i == text_j:
                problems.append((bullet_i.get("text"), bullet_j.get("text"), "完全重复"))
                continue

            # 编辑距离检查：仅当长度接近时计算
            if abs(len(text_i) - len(text_j)) <= 3:
                dist = _edit_distance(text_i, text_j)
                max_len = max(len(text_i), len(text_j))
                if max_len > 0 and dist / max_len < 0.15 and len(text_i) > 8:
                    problems.append((bullet_i.get("text"), bullet_j.get("text"), "高度相似"))

    return problems


def _edit_distance(a, b):
    """Levenshtein编辑距离（动态规划）。"""
    if not a:
        return len(b)
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(
                prev[j] + 1,
                cur[j - 1] + 1,
                prev[j - 1] + (ca != cb)
            ))
        prev = cur
    return prev[-1]


def strip_visible_text(html_content):
    """提取HTML可见正文，排除style、script、注释与标签。"""
    text = re.sub(r"<style[^>]*>.*?</style>", "", html_content, flags=re.DOTALL)
    text = re.sub(r"<script[^>]*>.*?</script>", "", text, flags=re.DOTALL)
    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
    text = re.sub(r"<[^>]+>", "", text)
    text = text.replace("&nbsp;", " ").replace("&amp;", "&")
    text = re.sub(r"\s+", "", text)
    return text


def check_v32_generated_quality():
    """检查V3.2生成质量，返回 (results, errors)。"""
    repo_root = Path(__file__).parent.parent
    html_path = repo_root / "golden-sample" / "generated" / "v3.2-professional-generated.html"
    json_path = repo_root / "golden-sample" / "generated" / "v3.2-resume-document.json"
    golden_html_path = repo_root / "golden-sample" / "v3.2-professional.html"

    results = {"checks": [], "errors": []}

    def add_check(name, passed, detail=""):
        results["checks"].append((name, passed))
        if not passed:
            results["errors"].append(f"{name}: {detail}" if detail else name)

    # ---------- JSON 基础存在性 ----------
    if not json_path.exists():
        add_check("生成JSON存在", False, "文件不存在")
        return results
    add_check("生成JSON存在", True)

    try:
        json_content = load_json(json_path)
    except (json.JSONDecodeError, OSError) as e:
        add_check("生成JSON可解析", False, str(e))
        return results
    add_check("生成JSON可解析", True)

    if not html_path.exists():
        add_check("生成HTML存在", False, "文件不存在")
        return results
    add_check("生成HTML存在", True)
    html_content = html_path.read_text(encoding="utf-8")

    # ---------- Bullet数量（从JSON统计） ----------
    meta_bullets, dachuang_bullets, clinical_bullets, all_bullets = collect_bullets(json_content)

    if not json_content.get("research_experience"):
        add_check("Meta经历非空", False, "research_experience为空")
    else:
        add_check("Meta经历非空", True)

    if not json_content.get("projects"):
        add_check("大创经历非空", False, "projects为空")
    else:
        add_check("大创经历非空", True)

    if not json_content.get("clinical_experience"):
        add_check("临床经历非空", False, "clinical_experience为空")
    else:
        add_check("临床经历非空", True)

    add_check("Meta Bullet为7-9条", 7 <= len(meta_bullets) <= 9,
              f"当前{len(meta_bullets)}条")
    add_check("大创Bullet为4-6条", 4 <= len(dachuang_bullets) <= 6,
              f"当前{len(dachuang_bullets)}条")
    add_check("临床Bullet为4-6条", 4 <= len(clinical_bullets) <= 6,
              f"当前{len(clinical_bullets)}条")

    # ---------- dimension_id 唯一性（同一经历内唯一） ----------
    dim_problems = []
    # 按经历分桶检查
    buckets = {"meta": meta_bullets, "dachuang": dachuang_bullets, "clinical": clinical_bullets}
    for key, bucket in buckets.items():
        seen = set()
        for bullet in bucket:
            dim_id = bullet.get("dimension_id")
            if not dim_id or not str(dim_id).strip():
                dim_problems.append(f"{key}缺少dimension_id")
            elif dim_id in seen:
                dim_problems.append(f"{key}的dimension_id重复: '{dim_id}'")
            else:
                seen.add(dim_id)
    add_check("每条Bullet有非空且同一经历内唯一的dimension_id",
              not dim_problems, "; ".join(dim_problems[:5]))

    # ---------- 文本质量检测（遍历JSON中所有Bullet文本与HTML全文） ----------
    all_text = html_content
    all_bullet_texts = [b.get("text", "") for _, b in all_bullets]

    # 1. 禁止模式
    found_forbidden = []
    for pattern in FORBIDDEN_PATTERNS:
        if pattern in all_text or any(pattern in t for t in all_bullet_texts):
            found_forbidden.append(pattern)
    add_check("HTML与Bullet不含禁止模式",
              not found_forbidden,
              f"发现: {', '.join(found_forbidden)}")

    # 2. 下划线内部枚举
    enum_hits = []
    for t in all_bullet_texts:
        if contains_internal_enums(t):
            enum_hits.append(t[:40])
    add_check("无下划线内部枚举", not enum_hits, f"发现: {enum_hits[:3]}")

    # 3. 中英变量粘连
    mixed_hits = []
    for t in all_bullet_texts:
        if contains_mixed_cn_latin(t):
            mixed_hits.append(t[:40])
    add_check("无中英变量粘连", not mixed_hits, f"发现: {mixed_hits[:3]}")

    # 4. 通用占位句
    placeholder_hits = []
    for t in all_bullet_texts:
        if contains_placeholder_bullet(t):
            placeholder_hits.append(t[:40])
    add_check("无通用占位句", not placeholder_hits, f"发现: {placeholder_hits[:3]}")

    # 5. 完全重复 / 高度相似
    similar = find_duplicate_or_similar_bullets(all_bullets)
    add_check("无完全重复或高度相似Bullet", not similar,
              "; ".join(f"「{a}」≈「{b}」({kind})" for a, b, kind in similar[:3]))

    # ---------- HTML结构完整性 ----------
    add_check("HTML包含教育背景", "教育背景" in html_content)
    add_check("HTML包含科研经历", "科研经历" in html_content)
    add_check("HTML包含大创经历", "大创" in html_content or "流行病学调查" in html_content)
    add_check("HTML包含临床实习", "临床实习" in html_content)
    add_check("HTML包含专业技能", "专业技能" in html_content)
    add_check("HTML包含研究兴趣", "研究兴趣" in html_content)
    add_check("HTML不包含未替换模板变量", "{{" not in html_content and "}}" not in html_content)

    # ---------- 个人信息数据驱动（不得依赖硬编码） ----------
    # 硬编码占位符仅当值确实是占位（如“电话·邮箱·所在城市”）时才算失败；
    # 真实候选人姓名本身不是硬编码。
    if "医学研究候选人" in html_content and "电话 · 邮箱 · 所在城市" in html_content:
        add_check("个人信息不依赖Renderer硬编码", False,
                  "HTML包含占位个人信息（电话 · 邮箱 · 所在城市）")
    else:
        add_check("个人信息不依赖Renderer硬编码", True)

    # ---------- 头像相对路径对应真实文件 ----------
    html_dir = html_path.parent
    avatar_problems = []
    for src in re.findall(r'<img[^>]+src="([^"]+)"', html_content):
        if src.startswith("http://") or src.startswith("https://") or src.startswith("data:"):
            continue
        resolved = (html_dir / src).resolve()
        if not resolved.exists():
            avatar_problems.append(f"src='{src}' -> {resolved} 不存在")
    add_check("头像相对路径对应真实文件", not avatar_problems, "; ".join(avatar_problems[:3]))

    # ---------- 信息量对比 ----------
    if golden_html_path.exists():
        golden_text = strip_visible_text(golden_html_path.read_text(encoding="utf-8"))
        generated_text = strip_visible_text(html_content)
        golden_chars = len(golden_text)
        generated_chars = len(generated_text)
        ratio = generated_chars / golden_chars if golden_chars > 0 else 0.0
        add_check("正文信息量不低于黄金样本90%",
                  generated_chars >= golden_chars * 0.9,
                  f"生成{generated_chars}字符 / 黄金{golden_chars}字符 ({ratio:.1%})")
    else:
        add_check("黄金样本存在", False, "golden-sample/v3.2-professional.html不存在")

    return results


def main():
    # Windows 控制台默认 GBK，强制 UTF-8 输出避免乱码
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

    results = check_v32_generated_quality()

    print("V3.2生成质量验证结果:")
    print("=" * 50)

    passed = sum(1 for _, ok in results["checks"] if ok)
    total = len(results["checks"])
    print(f"通过检查: {passed}/{total}")

    if results["errors"]:
        print("\nErrors:")
        for error in results["errors"]:
            print(f"  - {error}")

    print("\n详细检查结果:")
    for name, ok in results["checks"]:
        print(f"  {'PASS' if ok else 'FAIL'} {name}")

    print("\n退出码:", 1 if results["errors"] else 0)
    return 1 if results["errors"] else 0


if __name__ == "__main__":
    sys.exit(main())
