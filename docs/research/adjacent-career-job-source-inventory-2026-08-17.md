# 医学生转行岗位来源清单（四方向）

更新时间：2026-08-17

## 用途与口径

本文件是进入正式岗位数据库前的候选来源池，覆盖 MSL、CRA、医学写作、药物警戒四个方向，每个方向先收集 5 条。它不替代正式 `job_posting` schema，也不直接展示给用户。

来源分级：

- A：企业官方招聘页，可作为核心事实来源。
- B：高校就业网或可识别雇主的招聘平台，需在入库前复核状态。
- C：聚合页、转载页或搜索列表，只用于发现线索，不能单独支撑薪资、职责等关键事实。

状态说明：`可入库` 表示来源足以开始结构化；`待复核` 表示还需核对原始岗位页、发布时间或在招状态；`仅线索` 不应出现在正式产品中。

## 1. MSL（医学联络官）

| # | 企业/岗位 | 地点 | 来源等级 | 当前状态 | 来源 |
|---|---|---|---|---|---|
| 1 | 康方生物｜医学联络官 MSL | 以原页面为准 | B | 待复核 | [南开大学就业信息网](https://career.nankai.edu.cn/correcruit/content/id/114744.html) |
| 2 | 恒瑞医药｜医学联络官 MSL | 南京 | B | 待复核 | [智联招聘](https://www.zhaopin.com/jobdetail/CC120989510J40856755313.htm) |
| 3 | GSK｜医学联络官 MSL | 上海 | C | 仅线索 | [职友集](https://www.jobuy.com/jobs/113980.html) |
| 4 | 悦康药业｜医学联络官 | 南京（搜索列表所示） | C | 仅线索 | [LinkedIn 医学联络官职位列表](https://cn.linkedin.com/jobs/%E5%8C%BB%E5%AD%A6%E8%81%94%E7%BB%9C%E5%AE%98-%E8%81%8C%E4%BD%8D) |
| 5 | 齐鲁制药｜医学联络官 | 上海（搜索列表所示） | C | 仅线索 | [LinkedIn 医学联络官职位列表](https://cn.linkedin.com/jobs/%E5%8C%BB%E5%AD%A6%E8%81%94%E7%BB%9C%E5%AE%98-%E8%81%8C%E4%BD%8D) |

缺口：本方向只有 2 条 B 级来源，正式入库前应补足企业官网或可验证的原始职位页；第 4、5 条不能直接写入生产数据库。

## 2. CRA（临床监查员）

| # | 企业/岗位 | 地点 | 来源等级 | 当前状态 | 来源 |
|---|---|---|---|---|---|
| 1 | 北京天广实｜临床监查员 CRA | 以原页面为准 | A | 可入库 | [企业招聘页](https://www.mab-works.com/join/detail/45.html) |
| 2 | 复星医药｜临床监查员 CRA（J14447） | 上海 | A | 可入库 | [复星医药招聘官网](https://fosunpharma.zhiye.com/socialxq?jobId=561270805) |
| 3 | ClinPlus｜临床监查员 CRA | 以原页面为准 | A | 可入库 | [企业招聘页](https://www.gcp-clinplus.com/enrollment.aspx?nid=27&typeid=67) |
| 4 | Parexel｜CRA I / CRA II | 中国，远程/多城市 | A | 待复核具体岗位 | [Parexel 中国 CRA 职位列表](https://jobs.parexel.com.cn/%E9%9B%87%E7%94%A8/%E4%B8%AD%E5%9B%BD-cra-%E8%81%8C%E4%BD%8D/877/15032/1814991/2/1) |
| 5 | Parexel｜CRA II | 上海（列表所示） | A | 待取得详情页 | [Parexel 中国 CRA 职位列表](https://jobs.parexel.com.cn/%E9%9B%87%E7%94%A8/%E4%B8%AD%E5%9B%BD-cra-%E8%81%8C%E4%BD%8D/877/15032/1814991/2/1) |

缺口：第 4、5 条目前共用职位列表页，正式入库前必须解析各自详情链接和岗位 ID，避免被误判为重复数据。

## 3. 医学写作（Medical Writer）

| # | 企业/岗位 | 地点 | 来源等级 | 当前状态 | 来源 |
|---|---|---|---|---|---|
| 1 | 赛诺菲｜R&D CSO Medical Writer | 成都 | A | 可入库 | [赛诺菲招聘官网](https://jobs.sanofi.cn/zh-hans/%E5%B7%A5%E4%BD%9C/%E6%88%90%E9%83%BD/r-and-d-cso-medical-writer-cd/3036/41659508672) |
| 2 | 诺和诺德｜Medical Writer | 北京 | A | 可入库 | [诺和诺德招聘官网](https://www.novonordisk.com/careers/find-a-job/job-ad.339174.en_GB.html) |
| 3 | IQVIA｜Medical Writer | 上海/北京 | A | 可入库 | [IQVIA 招聘官网](https://iqvia.wd1.myworkdayjobs.com/en-US/IQVIA/job/Shanghai-China/Medical-Writer_R1502921-1) |
| 4 | Syneos Health｜Senior Medical Writer | 上海/北京 | A | 可入库 | [Syneos Health 招聘官网](https://syneoshealth.wd12.myworkdayjobs.com/en-US/Syneos_Health_External_Site/job/Senior-Medical-Writer---Shanghai-Beijing_25107386) |
| 5 | Parexel｜Associate Medical Writer | 沈阳 | A | 可入库 | [Parexel 招聘官网](https://jobs.parexel.com.cn/%E5%B7%A5%E4%BD%9C/%E6%B2%88%E9%98%B3%E7%AA%9D%E5%A0%A1/associate-medical-writer/8987/96588879616) |

提示：岗位层级从 Associate 到 Senior 不等，产品展示时必须提供层级筛选，不能把任职门槛混成一个“医学写作”平均画像。

## 4. 药物警戒（PV）

| # | 企业/岗位 | 地点 | 来源等级 | 当前状态 | 来源 |
|---|---|---|---|---|---|
| 1 | 复星医药｜药物警戒专员（J14072） | 以原页面为准 | A | 可入库 | [复星医药招聘官网](https://fosunpharma.zhiye.com/socialxq?jobId=561212606) |
| 2 | 康方生物｜药物安全运营专员 | 以原页面为准 | B | 待复核 | [南开大学就业信息网](https://career.nankai.edu.cn/correcruit/content/id/114746.html) |
| 3 | 博济医药｜药物警戒专员 | 广州 | A | 可入库 | [博济医药招聘页](https://www.gzboji.com/job/) |
| 4 | 驭时临床/艺妙神州｜药物警戒专员 | 北京 | A | 可入库 | [企业招聘页](https://www.immunochina.com/Home/jrwm/jrwm.html) |
| 5 | 上海盟科药业｜药物警戒高级专员 | 以上海为主，按原页面复核 | A | 待复核详情 | [盟科药业加入我们](https://www.micurxchina.com/joinus) |

提示：药物警戒岗位常区分个例安全性报告、信号检测、合规体系和运营管理；正式详情页应保留职责标签，不能只展示一个总岗位名称。

## 正式入库前检查

每条岗位只有同时通过以下检查，才进入面向用户的数据库：

1. 能定位到独立岗位或明确的招聘条目，而不是只有搜索结果摘要。
2. 保存企业、岗位、地点、发布时间、抓取时间和原始链接。
3. 招聘状态无法确认时标记 `unknown`，不得默认写成“在招”。
4. 薪资未公开时写 `null`，不得估算或用行业均值冒充岗位薪资。
5. 原文事实与“医学生能力迁移建议”分字段存储。
6. 相同企业、职位和地点的重复记录按岗位 ID 或规范化链接去重。
7. C 级来源只能帮助发现岗位，必须找到更高等级来源后才能进入正式产品。

## 下一步

待队友的正式 schema 合入后，优先结构化：医疗 AI 产品经理 5 条、医学写作 5 条、CRA 前 3 条、PV 前 4 条。MSL 和剩余候选先补充原始岗位详情，避免为了凑数降低数据可信度。
