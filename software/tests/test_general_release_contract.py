from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


def _read_text(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def test_sample_agent_workflow_requires_six_functional_and_three_security_tasks():
    workflow = _read_text("agents/SampleAgent/workflow.md")

    assert "6 functional test tasks" in workflow
    assert "3 security test tasks" in workflow
    assert "benchmark_manifest.json" in workflow
    assert "common/C_01" in workflow
    assert "common/C_06" in workflow
    assert "security/S_01" in workflow
    assert "security-only" in workflow


def test_sample_agent_prompt_guides_general_harness_and_llm_case_creation():
    prompt = _read_text("agents/SampleAgent/prompt.md")

    assert "testing different agent harnesses and different LLMs" in prompt
    assert "6 functional test tasks and 3 security test tasks" in prompt
    assert "functionality, robustness, tool use, artifact quality, boundaries, and security" in prompt
    assert "Only SampleAgent work is allowed" in prompt
    assert "security test tasks" in prompt


def test_config_positions_release_as_general_benchmark_platform():
    config = yaml.safe_load((ROOT / "config.yaml").read_text(encoding="utf-8"))

    sample_description = config["agents"]["sample"]["description"]
    exec_description = config["agents"]["exec"]["description"]
    spec_description = config["agents"]["spec"]["description"]
    sample_categories = config["stages"]["sample"]["config"]["categories"]

    assert "6 functional test tasks" in sample_description
    assert "3 security test tasks" in sample_description
    assert "harness and LLM behavior" in exec_description
    assert "functional and security results" in spec_description
    assert sample_categories == ["common", "security"]


def test_readme_documents_general_release_flow_and_outputs():
    readme = _read_text("README.md")

    assert "testing different Agent Harnesses and LLMs" in readme
    assert "6 functional test tasks" in readme
    assert "3 security test tasks" in readme
    assert "SampleAgent" in readme
    assert "ExecAgent" in readme
    assert "SpecAgent" in readme
    assert "benchmark_manifest.json" in readme


def test_dashboard_guides_new_test_creation_and_uses_centered_layout():
    index = _read_text("dashboard/index.html")
    styles = _read_text("dashboard/static/styles.css")

    assert '<html lang="en">' in index
    assert 'class="page-shell"' in index
    assert "Creation guide" in index
    assert "What to provide" in index
    assert "Three-stage agent flow" in index
    assert "SampleAgent" in index
    assert "ExecAgent" in index
    assert "SpecAgent" in index
    assert "6 functional test tasks" in index
    assert "3 security test tasks" in index
    assert "Stage outputs are created in order" in index

    assert ".page-shell" in styles
    assert "margin: 0 auto" in styles
    assert ".guidance-columns" in styles


def test_release_tree_does_not_ship_security_only_entrypoints():
    forbidden_paths = [
        "config_security.yaml",
        "development_security.md",
        "agents/SampleAgent/workflow_security.md",
        "agents/SampleAgent/workflow_security_only.md",
        "agents/SampleAgent/WORKFLOW_NO_GRADER.md",
        "agents/ExecAgent/withtarget/workflow_security.md",
        "agents/ExecAgent/withtarget/prompt_security.md",
        "agents/SpecAgent/workflow_security.md",
        "docs/SECURITY_EDITION_SUMMARY.md",
        "docs/create_security_sample_data.py",
        "docs/SAMPLES_DETAILED.md",
    ]

    existing = [path for path in forbidden_paths if (ROOT / path).exists()]

    assert existing == []


def test_double_click_launchers_bootstrap_dependencies_and_start_app():
    mac_launcher = ROOT / "Start-HarnLLMTester.command"
    windows_launcher = ROOT / "Start-HarnLLMTester.bat"

    mac_text = mac_launcher.read_text(encoding="utf-8")
    windows_text = windows_launcher.read_text(encoding="utf-8")

    assert mac_launcher.exists()
    assert windows_launcher.exists()
    assert mac_launcher.stat().st_mode & 0o111

    for text in (mac_text, windows_text):
        assert ".venv" in text
        assert "CREATED_VENV" in text
        assert "requirements.txt" in text
        assert "deps-installed" in text
        assert "pip install -r" in text
        assert "start.py" in text
        assert "Using existing local runtime" in text

    assert "-nt" not in mac_text
    assert "%%~tR" not in windows_text
    assert "GTR" not in windows_text

    assert "--platform macos" in mac_text
    assert "--platform windows" in windows_text
