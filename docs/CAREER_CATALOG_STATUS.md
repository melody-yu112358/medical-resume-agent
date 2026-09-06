# 职业目录当前资产状态

<!-- GENERATED: python scripts/generate_career_catalog_status.py --write -->

本页是职业目录当前数量与 Pack/Card/规则/入口关联的唯一生成状态页，不是可编辑真值。最终真值仍是下列机器文件；若不一致，重新生成，不手改状态。未读取晋升评分或模型运行记录，不能据此宣称通过验证、全国覆盖率或个人适配。

源内容摘要：`a6f4a832ec03a731101c40b4c09c8d97c6d6757bceeaa222b2db1dc829b6715f`（排除文件路径所在机器与时间；不是 knowledge_snapshot_id）。

| 资产维度 | 数量 |
| --- | --- |
| Canonical Pack 源 | 10 |
| JD-driven 目录方向 | 6 |
| Beta 目录方向 | 0 |
| 已导入路径的 Career Card 源 | 5 |
| 有解释规则的方向 / 规则条数 | 2 / 11 |
| workflow 显式 target | 5 |
| 旧探索卡（单独计数） | 5 |
| Card 人工逐 claim 支持注释 | 0 |

这些轴不能相加，也不是递进成熟度；目录含申请目标和宽方向，不等于同数量的具体职业。Card 来源中的 JD snapshot 数量不是独立雇主数量或逐 claim 支持数量。

| Pack 源 | Card 源 | Card JD 引用 | 解释规则 | workflow target |
| --- | --- | --- | --- | --- |
| [临床数据管理 / CDM 支持](../data/role-packs/clinical_data_management_v1.json) `clinical_data_management_v1` | [clinical_data_management](../data/career_cards/clinical_data_management.v1.json) | 8 | 6 | 否 |
| [临床运营协调](../data/role-packs/clinical_operations_v1.json) `clinical_operations_v1` | — | — | 0 | 是 |
| [临床研究协调 / CRA 支持](../data/role-packs/clinical_research_associate_v1.json) `clinical_research_associate_v1` | [clinical_research_associate](../data/career_cards/clinical_research_associate.v1.json) | 8 | 0 | 否 |
| [临床科研](../data/role-packs/clinical_research_v1.json) `clinical_research_v1` | — | — | 0 | 是 |
| [考博 / 保研](../data/role-packs/doctoral_v1.json) `doctoral_v1` | — | — | 0 | 是 |
| [医疗数据 / 健康科技](../data/role-packs/health_ai_data_v1.json) `health_ai_data_v1` | — | — | 0 | 是 |
| [MSL / 医学事务](../data/role-packs/medical_affairs_v1.json) `medical_affairs_v1` | — | — | 0 | 是 |
| [医疗器械临床 / 应用支持](../data/role-packs/medical_device_clinical_application_specialist_v1.json) `medical_device_clinical_application_specialist_v1` | [medical_device_clinical_application_specialist](../data/career_cards/medical_device_clinical_application_specialist.v1.json) | 8 | 5 | 否 |
| [药物警戒 / 药物安全支持](../data/role-packs/pharmacovigilance_drug_safety_v1.json) `pharmacovigilance_drug_safety_v1` | [pharmacovigilance_drug_safety](../data/career_cards/pharmacovigilance_drug_safety.v1.json) | 10 | 0 | 否 |
| [法规医学写作 / Regulatory Medical Writing 支持](../data/role-packs/regulatory_medical_writing_v1.json) `regulatory_medical_writing_v1` | [regulatory_medical_writing](../data/career_cards/regulatory_medical_writing.v1.json) | 10 | 0 | 否 |

## 无独立 Pack 的目录方向

| key | 名称 | 目录模式 |
| --- | --- | --- |
| `market_access_jd_driven` | 市场准入（JD-driven） | JD-driven |
| `healthcare_product_jd_driven` | 医疗产品（JD-driven） | JD-driven |
| `healthcare_consulting_jd_driven` | 医疗咨询（JD-driven） | JD-driven |
| `commercial_business_analytics_jd_driven` | 商业 / 业务分析（JD-driven） | JD-driven |
| `healthcare_project_operations_jd_driven` | 医疗 / 项目运营（JD-driven） | JD-driven |
| `medical_sales_commercial_jd_driven` | 医学销售 / 商业（JD-driven） | JD-driven |

## 旧探索卡

名称接近不等于与 Pack 等价，也不继承其状态。

| 文件 | 原名称 | review_status |
| --- | --- | --- |
| [clinical-research-associate](../data/careers/clinical-research-associate.cn.json) | 临床监查员（CRA） | draft |
| [healthcare-ai-product-manager](../data/careers/healthcare-ai-product-manager.cn.json) | 医疗 AI 产品经理 | draft |
| [medical-science-liaison](../data/careers/medical-science-liaison.cn.json) | 医学科学联络官（MSL） | draft |
| [medical-writer](../data/careers/medical-writer.cn.json) | 医学写作 | draft |
| [pharmacovigilance-specialist](../data/careers/pharmacovigilance-specialist.cn.json) | 药物警戒专员 | draft |

## 生成与来源

```powershell
python scripts/generate_career_catalog_status.py --write
python scripts/generate_career_catalog_status.py --check
```

源集合包括 Canonical Pack、Career Card、旧探索卡、taxonomy registry、match-rule registry 与 workflow-contract。本文不消费候选采集表，不向 SQL 导入任何职业。

职责分工见 [文档导航](README.md)；结构建议见 [目录结构](CAREER_CATALOG_STRUCTURE.md)；扩展方法见 [广度采集方法](research/career-catalog-breadth-plan-v1.md)。
