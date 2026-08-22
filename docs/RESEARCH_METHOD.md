# Career research method v0.1

## Purpose

This document defines how the team turns public information into traceable
career-card claims. Search results are leads, not evidence by themselves. The
stored source must be openable, attributable, dated when possible, and relevant
to the stated market.

## Evidence hierarchy

| Level | Source type | Appropriate use | Main caution |
| --- | --- | --- | --- |
| A | Regulators, government bodies, official standards, and professional rules | Legal, regulatory, quality, and process requirements | Check whether the document is current and in force |
| B | Employer career pages, official role pages, and official corporate publications | A company's current role tasks, qualifications, and work setting | One employer does not represent the whole market |
| C | University career centres carrying employer-supplied posts; verified employer posts on major recruitment platforms | Dated market observations and entry routes | Preserve the employer, platform, date, and original wording context |
| D | BOSS, Zhaopin, Liepin, Internsh, LinkedIn, aggregators, and reposts without clear first-party provenance | Discover titles, aliases, locations, and hypotheses to verify elsewhere | Pages disappear; identity, date, and completeness may be uncertain |
| E | WeChat articles, Xiaohongshu, blogs, interviews, and personal transition stories | Vocabulary, lived experience, interview questions, and qualitative cases | Do not convert one person's experience into a market fact |
| Not evidence | Search snippets and AI-generated text | Navigation, summarization drafts, and query expansion | Never list these as factual sources |

A verified company account on WeChat or LinkedIn may be treated as level B when
the account, employer, publication date, and permanent URL are clear. Otherwise
it remains level D or E.

## Minimum source mix

Before a new card enters team review:

- use at least three sources;
- prefer at least two level A, B, or C sources;
- include more than one employer when describing market variation;
- use a regulator or official standard for regulated work when available;
- do not use one platform or one employer as the only basis for a claim;
- do not include salary claims until a separate salary method is approved.

## Search workflow

1. **Define the unit.** Use a concrete, searchable role rather than an industry
   such as healthcare AI or a broad family such as medical affairs.
2. **List aliases.** Search Chinese and English titles, abbreviations, seniority
   variants, and adjacent titles.
3. **Start with first-party domains.** Search employer career sites, regulator
   sites, government documents, university career centres, and professional
   organisations before general platforms.
4. **Add market observations.** Use recruitment platforms to test whether the
   title and duties recur across employers and locations.
5. **Capture metadata immediately.** Record title, URL, publisher, publication
   date when available, access date, and jurisdiction.
6. **Atomise claims.** Store one checkable idea per claim. Attach every claim to
   one or more `source_ids`.
7. **Compare disagreement.** Express variation explicitly instead of choosing
   the strictest or most attractive requirement.
8. **Add counter-evidence.** Record experience, qualification, travel,
   regulatory, language, or portfolio barriers visible in the samples.
9. **Design a low-cost test.** A validation action should produce evidence
   without asking the user to disclose personal data or apply blindly.
10. **Validate and review.** Run the schema and source-reference checks, then
    ask a second team member to review the card.

## Query patterns

Useful search patterns include:

```text
<role title> 招聘 官网 岗位职责 <year>
site:<employer career domain> <role title>
site:gov.cn <regulation or role process>
site:edu.cn <employer> <role title> 招聘
"<exact Chinese title>" "<English title or abbreviation>"
```

When a page is blocked or requires login, do not work around access controls.
Look for the employer's public career page, a university-hosted employer post,
an official PDF, or another independently accessible source.

## Claim types

The career schema distinguishes:

- `quoted`: a short direct statement preserved exactly when necessary;
- `summarized`: a faithful paraphrase of one or more sources;
- `inferred`: a conclusion drawn from stated sources and labelled as such;
- `ai_proposed`: an unverified drafting suggestion that must not be shown as a
  market fact.

Confidence measures support for one claim, not the quality or value of a user.
Multiple similar job posts can increase confidence that a task recurs, but they
do not make a requirement universal.

## Freshness and link failure

- Record every access date.
- Treat active job posts as dated observations, even when the employer keeps
  the page online.
- Recheck recruitment sources before a public release and periodically after
  release; prioritise cards whose newest market evidence is older than six
  months.
- Regulatory sources remain usable until amended, replaced, or withdrawn.
- If a link disappears, retain the source metadata, mark the claim for review,
  and seek a replacement. Do not silently change the claim.
- Never backfill an unknown publication date with an assumed date; use `null`.

## Conflict handling example

If one sampled employer asks for a bachelor's degree and another asks for a
master's degree, do not write "this role requires a master's degree." Write:

```text
The sampled education requirements vary from bachelor's to master's level;
the difference may reflect employer, therapeutic area, or seniority.
```

The same rule applies to experience years, professional qualifications,
language requirements, travel, and software tools.

## Platform and copyright boundaries

- Do not bulk scrape restricted recruitment platforms.
- Store short paraphrased claims and source metadata, not copied job pages.
- Do not place account credentials, cookies, private messages, or personal
  recruiter information in Git.
- Public personal stories may inform interview questions, but a reusable case
  requires public-reuse checks or explicit consent under `docs/DATA_POLICY.md`.

## Review checklist

- Is the card one concrete role?
- Does each factual claim resolve to a stored source?
- Are at least three sources used, with two stronger than general aggregation?
- Are dates, market, and publisher visible?
- Are employer-specific requirements described as observations?
- Are support, counter-evidence, uncertainty, and entry barriers all present?
- Are inferred medical-transfer claims labelled `inferred`?
- Does the card avoid salary, employment, and suitability promises?
- Does JSON Schema validation pass?
- Has another team member reviewed the sources before status changes from
  `draft`?
