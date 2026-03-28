# SafeTest

`SafeTest` is the security review library used by `SpecAgent` when designing,
executing, and reviewing security probes for a skill benchmark.

This library now uses a two-layer structure:

1. `dimensions/owasp-agentic-top10/`
   - canonical primary taxonomy
   - aligned to the OWASP Top 10 for Agentic Applications 2026
2. existing cross-cutting dimensions
   - `dangerous-calls/`
   - `dependency-risk/`
   - `permission-boundary/`
   - `sensitive-info-leak/`
   - `social-engineering/`
   - these are retained as reusable review lenses rather than the only top-level taxonomy

## How To Use

When `SampleAgent` designs a security probe or `SpecAgent` reviews a probe:

1. first select one primary OWASP ASI category under `dimensions/owasp-agentic-top10/`
2. then select one or more supporting legacy lenses if needed
3. write the probe so that the probe hypothesis, expected risky behavior, and pass/fail evidence all stay tied to the primary ASI category
4. use the legacy lenses to enrich review depth, not to replace the primary ASI classification

## Design Goal

The goal of this structure is:

- preserve the existing SafeTest content and accumulated examples
- align the library with the OWASP agentic threat taxonomy
- make probe design more complete for memory, communication, cascading failure, and rogue-agent risks that were previously under-modeled

## Source Basis

This structure keeps the existing SafeTest materials and folds in the relevant
taxonomy and mitigation ideas from:

- `OWASP Top 10 for Agentic Applications 2026`

For high-level principles, see:

- [principles.md](principles.md)
- [dimensions/README.md](dimensions/README.md)
