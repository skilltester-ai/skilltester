from core.scanner import check_database


def test_included_examples_have_expected_stage_statuses():
    expected = {
        "ExampleSuite/new-ticket-router": "new",
        "ExampleSuite/sample-research-summarizer": "sample_completed",
        "ExampleSuite/exec-config-auditor": "exec_completed",
        "ExampleSuite/exec-log-triage": "exec_completed",
        "ExampleSuite/completed-doc-quality": "completed",
        "ExampleSuite/completed-data-normalizer": "completed",
    }

    actual = {name: check_database(name)["status"] for name in expected}

    assert actual == expected
