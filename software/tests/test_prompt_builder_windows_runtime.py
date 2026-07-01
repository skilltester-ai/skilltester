from pathlib import Path

import pytest

from core.cleaner import delete_exec_track_data
from core.lineage import build_exec_output_dir
from core.prompt_builder import _prepare_exec_runtime_alias
from harnesses import get_harness


def test_exec_runtime_alias_falls_back_when_windows_symlink_privilege_is_missing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    sample_leaf = tmp_path / "database" / "samples" / "AgentSecurity" / "support-agent-risk-lab"
    exec_leaf = tmp_path / "database" / "exec" / "AgentSecurity" / "support-agent-risk-lab" / "k2" / "opencode"
    runtime_root = tmp_path / ".runtime"
    sample_leaf.mkdir(parents=True)
    exec_leaf.mkdir(parents=True)
    (sample_leaf / "benchmark_manifest.json").write_text('{"functional_tasks": [], "security_probes": []}\n', encoding="utf-8")

    def raise_windows_symlink_privilege_error(self, target, target_is_directory=False):
        error = OSError("[WinError 1314] A required privilege is not held by the client.")
        error.winerror = 1314
        raise error

    monkeypatch.setattr(Path, "symlink_to", raise_windows_symlink_privilege_error)

    workspace = _prepare_exec_runtime_alias(
        sample_leaf=sample_leaf,
        exec_leaf=exec_leaf,
        mode="withtarget",
        runtime_root=runtime_root,
    )

    assert workspace == exec_leaf
    assert (workspace / "sample" / "benchmark_manifest.json").exists()
    assert (workspace / "results").is_dir()


def test_exec_track_cleanup_deletes_nested_results_track(tmp_path: Path):
    target_name = "AgentSecurity/support-agent-risk-lab"
    model = get_harness("opencode").default_model
    exec_leaf = build_exec_output_dir(
        tmp_path,
        "AgentSecurity",
        "support-agent-risk-lab",
        model,
        model,
    )
    nested_track = exec_leaf / "results" / "with_target"
    direct_track = exec_leaf / "with_target"
    nested_track.mkdir(parents=True)
    direct_track.mkdir(parents=True)
    (nested_track / "metrics.json").write_text("{}\n", encoding="utf-8")
    (direct_track / "metrics.json").write_text("{}\n", encoding="utf-8")

    delete_exec_track_data(
        target_name,
        "with_target",
        database_dir=tmp_path,
        harness="opencode",
    )

    assert not nested_track.exists()
    assert not direct_track.exists()
