# Schema Compatibility Guide

## Canonical Experience Schema

The `canonical-experience-v1` schema is designed to work alongside the existing `resume-document-v1` schema, not replace it.

### Key Differences:
- **Purpose**: Canonical Experience represents a single confirmed experience, while Resume Document represents a complete resume
- **Scope**: Canonical Experience is role-agnostic, Resume Document is role-specific
- **Structure**: Canonical Experience uses flat fact lists, Resume Document uses structured sections

### Integration Points:
- Evidence IDs from Resume Document can be referenced in Canonical Experience
- Canonical Experience can be embedded in Resume Document's `capability_profile` field
- Both schemas share the same evidence reference system

## Role Pack Schema

The `role-pack-v1` schema extends the existing translation logic in `resume_translation.py`:

### Reuse Strategy:
- Existing translation mappings can be migrated to Role Pack format
- The same priority logic applies
- New fields provide more granular control over expression generation

### Migration Path:
- Existing `TARGET_PROFILES` dictionary → Role Pack JSON files
- Translation service can load both formats during transition
- New features only available in Role Pack format

## Bullet Claim Schema

The `bullet-claim-v1` schema introduces audit trail capabilities that extend the existing rewrite audit system:

### Audit Enhancement:
- Each claim has independent ID and status
- Full traceability from claim to canonical experience to evidence
- User disposition tracking (accepted/edited/rejected)
- Risk flagging for potential issues

### Backward Compatibility:
- Existing rewrite audit records can be mapped to Bullet Claims
- New claims include all fields needed for audit compliance
- Browser storage format remains compatible

## Implementation Strategy

1. **Phase 1**: Implement new schemas alongside existing code
2. **Phase 2**: Migrate existing translation logic to use Role Packs
3. **Phase 3**: Replace rewrite audit with Bullet Claim Ledger
4. **Phase 4**: Add new Experience Draft and Confirmation services

This approach ensures no breaking changes to existing functionality while enabling new capabilities.