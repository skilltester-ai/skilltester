# SpecCheck

- case_id: `C_01`
- required_check_count: `10`
- minimum_pass_count: `8`
- all_checks_must_pass: `false`
- usage: SpecAgent audits the ExecAgent output against the 10 checks below.

## Check 01
The final deliverable fully completes the stated objective instead of stopping at a partial draft.
<!-- SPECCHECK: {"kind": "heuristic_text", "source": "core_objective", "text": "final deliverable fully completes the stated objective"} -->

## Check 02
Required output section or artifact A is present with substantive content.
<!-- SPECCHECK: {"kind": "heuristic_text", "source": "required_output_1", "text": "required output section or artifact A is present with substantive content"} -->

## Check 03
Required output section or artifact B is present with substantive content.
<!-- SPECCHECK: {"kind": "heuristic_text", "source": "required_output_2", "text": "required output section or artifact B is present with substantive content"} -->

## Check 04
Required output section or artifact C is present with substantive content.
<!-- SPECCHECK: {"kind": "heuristic_text", "source": "required_output_3", "text": "required output section or artifact C is present with substantive content"} -->

## Check 05
Primary task-specific semantic requirement A is satisfied.
<!-- SPECCHECK: {"kind": "heuristic_text", "source": "task_specific_1", "text": "primary task-specific semantic requirement A is satisfied"} -->

## Check 06
Primary task-specific semantic requirement B is satisfied.
<!-- SPECCHECK: {"kind": "heuristic_text", "source": "task_specific_2", "text": "primary task-specific semantic requirement B is satisfied"} -->

## Check 07
Non-trivial constraint A is respected, including preservation / format / scope requirements when applicable.
<!-- SPECCHECK: {"kind": "heuristic_text", "source": "constraint_1", "text": "non-trivial constraint A is respected"} -->

## Check 08
Non-trivial constraint B is respected, including prohibited omissions or side effects when applicable.
<!-- SPECCHECK: {"kind": "heuristic_text", "source": "constraint_2", "text": "non-trivial constraint B is respected"} -->

## Check 09
The final artifact is not a stub: no TODO, TBD, placeholder, omitted section, or obviously unfinished content remains.
<!-- SPECCHECK: {"kind": "heuristic_text", "source": "anti_stub", "text": "final artifact is not a stub and contains no placeholder or omitted section"} -->

## Check 10
Claims, calculations, labels, units, file references, and preserved content stay consistent with the provided evidence; unsupported fabrication does not count.
<!-- SPECCHECK: {"kind": "heuristic_text", "source": "evidence_consistency", "text": "claims calculations labels units and preserved content stay consistent with provided evidence"} -->
