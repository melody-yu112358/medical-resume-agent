#!/usr/bin/env python3
"""Generate the single current catalog status document from repository sources."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = Path("docs/CAREER_CATALOG_STATUS.md")


def render(root=ROOT):
    paths = sorted([*root.glob("data/role-packs/*.json"), *root.glob("data/career_cards/*.json"),
                    *root.glob("data/careers/*.json"), root / "data/career-map/directions-v1.json",
                    root / "data/career-map/career-card-match-rules-v1.json",
                    root / "skill-lite/medical-resume-skill/references/workflow-contract.json"])
    data = {p.relative_to(root).as_posix(): json.loads(p.read_text(encoding="utf-8")) for p in paths}
    digest = hashlib.sha256(json.dumps(data, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    packs = {d["role_pack"]: (p, d) for p, d in data.items() if p.startswith("data/role-packs/")}
    cards = {d["role_pack"]: (p, d) for p, d in data.items() if p.startswith("data/career_cards/")}
    drafts = [(p, d) for p, d in data.items() if p.startswith("data/careers/")]
    registry = data["data/career-map/directions-v1.json"]
    rules = data["data/career-map/career-card-match-rules-v1.json"]["rules"]
    targets = {x["role_pack"] for x in data["skill-lite/medical-resume-skill/references/workflow-contract.json"]["targets"]}
    assignments = {x["role_pack"] for x in registry["canonical_role_pack_taxonomy"]}
    if assignments != packs.keys() or not targets <= packs.keys():
        raise ValueError("taxonomy/runtime Pack reference mismatch")
    if not cards.keys() <= packs.keys():
        raise ValueError("Card Pack reference mismatch")
    if len({x["rule_key"] for x in rules}) != len(rules):
        raise ValueError("duplicate rule key")
    for rule in rules:
        if rule["role_pack"] not in cards or cards[rule["role_pack"]][1]["career_card_id"] != rule["career_card_id"]:
            raise ValueError("rule Card reference mismatch")
    link = lambda p, label: f"[{label}](../{p})"
    lines = ["# 职业目录当前资产状态", "", "<!-- GENERATED: python scripts/generate_career_catalog_status.py --write -->", "",
             "本页是职业目录当前数量与 Pack/Card/规则/入口关联的唯一生成状态页，不是可编辑真值。最终真值仍是下列机器文件；若不一致，重新生成，不手改状态。未读取晋升评分或模型运行记录，不能据此宣称通过验证、全国覆盖率或个人适配。", "",
             f"源内容摘要：`{digest}`（排除文件路径所在机器与时间；不是 knowledge_snapshot_id）。", "",
             "| 资产维度 | 数量 |", "| --- | --- |",
             f"| Canonical Pack 源 | {len(packs)} |", f"| JD-driven 目录方向 | {len(registry['jd_driven_directions'])} |",
             f"| Beta 目录方向 | {len(registry['beta_directions'])} |", f"| 已导入路径的 Career Card 源 | {len(cards)} |",
             f"| 有解释规则的方向 / 规则条数 | {len({r['role_pack'] for r in rules})} / {len(rules)} |",
             f"| workflow 显式 target | {len(targets)} |", f"| 旧探索卡（单独计数） | {len(drafts)} |",
             f"| Card 人工逐 claim 支持注释 | {sum(len(c['jd_evidence'].get('claim_support', [])) for _, c in cards.values())} |", "",
             "这些轴不能相加，也不是递进成熟度；目录含申请目标和宽方向，不等于同数量的具体职业。Card 来源中的 JD snapshot 数量不是独立雇主数量或逐 claim 支持数量。", "",
             "| Pack 源 | Card 源 | Card JD 引用 | 解释规则 | workflow target |", "| --- | --- | --- | --- | --- |"]
    for key, (path, pack) in sorted(packs.items()):
        card = cards.get(key)
        lines.append(f"| {link(path, pack['label'])} `{key}` | {link(card[0], card[1]['career_card_id']) if card else '—'} | {len(card[1]['jd_evidence']['snapshot_ids']) if card else '—'} | {sum(r['role_pack']==key for r in rules)} | {'是' if key in targets else '否'} |")
    lines += ["", "## 无独立 Pack 的目录方向", "", "| key | 名称 | 目录模式 |", "| --- | --- | --- |"]
    for mode, field in (("JD-driven", "jd_driven_directions"), ("Beta", "beta_directions")):
        for d in registry[field]:
            lines.append(f"| `{d['external_key']}` | {d['label']} | {mode} |")
    lines += ["", "## 旧探索卡", "", "名称接近不等于与 Pack 等价，也不继承其状态。", "", "| 文件 | 原名称 | review_status |", "| --- | --- | --- |"]
    lines += [f"| {link(p,d['career_id'])} | {d['name']} | {d['review_status']} |" for p,d in sorted(drafts)]
    lines += ["", "## 生成与来源", "", "```powershell", "python scripts/generate_career_catalog_status.py --write", "python scripts/generate_career_catalog_status.py --check", "```", "",
              "源集合包括 Canonical Pack、Career Card、旧探索卡、taxonomy registry、match-rule registry 与 workflow-contract。本文不消费候选采集表，不向 SQL 导入任何职业。", "",
              "职责分工见 [文档导航](README.md)；结构建议见 [目录结构](CAREER_CATALOG_STRUCTURE.md)；扩展方法见 [广度采集方法](research/career-catalog-breadth-plan-v1.md)。", ""]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    content = render()
    if args.write:
        (ROOT / OUTPUT).write_text(content, encoding="utf-8")
    if args.check and (not (ROOT / OUTPUT).exists() or (ROOT / OUTPUT).read_text(encoding="utf-8") != content):
        parser.exit(1, "career catalog status drift; run --write\n")
    print("career catalog status verified" if args.check else str(OUTPUT))


if __name__ == "__main__":
    main()
