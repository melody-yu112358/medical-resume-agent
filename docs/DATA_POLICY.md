# Data policy

## Allowed in Git

- public occupational classifications with attribution;
- source metadata and links;
- manually verified career cards derived from permitted sources;
- synthetic profiles and synthetic evaluation cases;
- anonymized aggregate findings that cannot identify a participant.

## Forbidden in Git

- names, phone numbers, email addresses, account identifiers, or addresses;
- unredacted resumes, interview recordings, or raw transcripts;
- API keys, access tokens, cookies, or credentials;
- scraped data whose terms do not permit collection or reuse;
- health or psychological information connected to an identifiable person.

## Source requirements

Every career claim must record:

- source title and URL;
- publisher;
- publication date when available;
- access date;
- jurisdiction or market;
- whether the claim is quoted, summarized, inferred, or AI-proposed;
- reviewer and review status.

AI-generated text is not a factual source. User cases enter a review queue and
must not automatically change recommendation rules or career records.

## Transient local intake

- The intake page requires explicit acknowledgement before sending text to the
  locally configured model provider.
- Users are instructed to remove patient names, record numbers, contact details
  and other third-party identifiers before submission.
- The current backend holds no participant database and does not write intake
  text or confirmed profiles to `data/` or Git.
- Model-proposed capability labels remain unverified until the user confirms
  each quoted evidence item.
- A quote-presence check reduces invention but does not make the model's
  capability interpretation automatically correct.
- Production deployment still requires authentication, retention and deletion
  rules, provider review, consent records and access logging.
