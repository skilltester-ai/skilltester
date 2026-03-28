# SafeTest Dimensions

`dimensions/` now has two layers.

## 1. Primary Taxonomy

Primary classification lives in:

- [owasp-agentic-top10](owasp-agentic-top10/README.md)

This is the canonical top-level structure for new security probe design and
review.

## 2. Supporting Cross-Cutting Lenses

The existing directories are retained and should still be reused:

- `dangerous-calls`: [Audit Manual](dangerous-calls/Audit-Manual.md), [Case Library](dangerous-calls/Case-Library.md)
- `dependency-risk`: [Audit Manual](dependency-risk/Audit-Manual.md), [Case Library](dependency-risk/Case-Library.md)
- `permission-boundary`: [Audit Manual](permission-boundary/Audit-Manual.md), [Case Library](permission-boundary/Case-Library.md)
- `sensitive-info-leak`: [Audit Manual](sensitive-info-leak/Audit-Manual.md), [Case Library](sensitive-info-leak/Case-Library.md)
- `social-engineering`: [Audit Manual](social-engineering/Audit-Manual.md), [Case Library](social-engineering/Case-Library.md)

These are no longer the only top-level taxonomy. They are supporting review
lenses used to deepen an ASI-classified probe.

## Working Rule

For every new security probe:

1. assign exactly one primary ASI category
2. optionally assign one or more supporting legacy lenses
3. write the probe hypothesis, evidence standard, and pass/fail conclusion
   against the primary ASI category

See:

- [Mapping-Matrix.md](Mapping-Matrix.md)
