# TaskLibrary Principles

These principles govern how `SampleAgent` should design functional tasks using
this library.

## 1. Start From The Skill's User-Facing Job

Pick the task pattern that matches what the target promises users, not just the
underlying tools it happens to call.

## 2. Reuse Task Shape Before Topic

What matters most is the workflow shape: search and fact collection, data
extraction, multimodal layout, content packaging, browser workflow automation,
or code implementation. Domain flavor comes second.

## 3. Normalize To The Benchmark Surface

Reference cases should be read through `task_description.md` and `workspace/`
first, then converted into the current generated surface:
`TaskDescription.md`, `WorkSpace/`, and `Grader/`.

## 4. Keep Baseline And With-Skill Comparable

Functional tasks should remain meaningful in both modes so the benchmark shows
real skill lift rather than unfair routing bias.

## 5. Difficulty Must Come From Structure

Increase difficulty through count growth, branching workflows, artifact
richness, preservation constraints, validation depth, or multi-step execution,
not by vague wording alone.

## 6. Match Output To Skill Type

Design skills need render-visible outputs. Search skills need synthesized
fact artifacts. Data-processing skills need structured outputs. Browser
automation skills need visible execution evidence. Code skills need runnable or
reviewable code-centric artifacts.

## 7. Preserve Observable Evidence

A good task makes success and failure visible in the final artifact rather than
in process notes or intentions.

## 8. Use Cases As Analogies, Not Templates

Reference families exist to provide credible shapes and difficulty ladders. They
must not be copied verbatim unless the target skill genuinely solves the same
kind of user problem.

## 9. Prefer Broadly Reusable Task Types

Patterns should stay broad enough to cover many skills: multimodal design and
layout, information search and fact collection, data extraction and structured
processing, content writing and packaging, browser operations and workflow
automation, and code implementation and tool development are all more reusable
than a narrow domain taxonomy.

## 10. Keep The Library Curated

TaskLibrary is a design aid, not a dump of every task ever seen. Preserve cases
that illuminate a useful skill-task type, and discard the rest.
