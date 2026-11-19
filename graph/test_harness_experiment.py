from pathlib import Path

from experiments.harness_ablation.run_experiment import run

ROOT = Path(__file__).resolve().parents[1]


def test_three_run_performance_shape():
    rows = {name: run(name) for name in ("bare", "harnessed", "ablated")}
    assert rows["bare"]["passed"] == 4
    assert rows["harnessed"]["passed"] == 8
    assert rows["ablated"]["passed"] == 5
    assert rows["harnessed"]["pass_rate"] > rows["ablated"]["pass_rate"] > rows["bare"]["pass_rate"]


def test_agents_file_meets_requested_length_and_sections():
    text = (ROOT / "AGENTS.md").read_text()
    assert 80 <= len(text.splitlines()) <= 100
    for heading in ("Project overview", "Stack", "Setup", "Focused verification", "Full verification"):
        assert heading in text
