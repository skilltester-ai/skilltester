# SafeTest Dimensions

`dimensions/` now has two layers.

## 1. Primary Taxonomy

Primary classification lives in:

- [owasp-agentic-top10](./agents/SpecAgent/SpecLibrary/SafeTest/dimensions/owasp-agentic-top10)

This is the canonical top-level structure for new security probe design and
review.

## 2. Supporting Cross-Cutting Lenses

The existing directories are retained and should still be reused:

- [dangerous-calls](./agents/SpecAgent/SpecLibrary/SafeTest/dimensions/dangerous-calls)
- [dependency-risk](./agents/SpecAgent/SpecLibrary/SafeTest/dimensions/dependency-risk)
- [permission-boundary](./agents/SpecAgent/SpecLibrary/SafeTest/dimensions/permission-boundary)
- [sensitive-info-leak](./agents/SpecAgent/SpecLibrary/SafeTest/dimensions/sensitive-info-leak)
- [social-engineering](./agents/SpecAgent/SpecLibrary/SafeTest/dimensions/social-engineering)

These are no longer the only top-level taxonomy. They are supporting review
lenses used to deepen an ASI-classified probe.

## Working Rule

For every new security probe:

1. assign exactly one primary ASI category
2. optionally assign one or more supporting legacy lenses
3. write the probe hypothesis, evidence standard, and pass/fail conclusion
   against the primary ASI category

See:

- [Mapping-Matrix.md](./agents/SpecAgent/SpecLibrary/SafeTest/dimensions/Mapping-Matrix.md)
