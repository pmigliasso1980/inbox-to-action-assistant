import tempfile
import unittest
from pathlib import Path

from agents.gates_multiagent import CriticArtifact,GeneratorArtifact,gate_critic,gate_generator
from agents.panel import deterministic_merge,jaccard,normalize_issue
from agents.reflection import Issue
from evals.run_baseline import Defect,Review


class MultiAgentTests(unittest.TestCase):
    def setUp(self):
        self.item={"input":"x = 1\nprint(x)","file":"x.py"}

    def test_generator_gate_checks_trace_and_lines(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/"trace.jsonl").touch()
            artifact=GeneratorArtifact(output=Review(defects=[Defect(category="off_by_one",line=9,severity="high",rationale="bad")]),assumptions=["No hidden caller contract."],unresolved=[],trace_id="trace.jsonl")
            errors=gate_generator(artifact,item=self.item,root=root)
            self.assertTrue(any("nonexistent line" in e for e in errors))

    def test_critic_gate_enforces_blocking_invariant(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/"trace").touch()
            artifact=CriticArtifact(defects=[Issue(location="line 1",observation="wrong",rubric_criterion="precision",severity="blocking")],decision="accept",rationale="looks fine",rejected_assumptions=[],trace_id="trace")
            self.assertTrue(any("decision must" in e for e in gate_critic(artifact,item=self.item,root=root)))

    def test_normalization_and_jaccard(self):
        a=normalize_issue({"location":"Line 2","rubric_criterion":"Security!","observation":"SQL-injection."})
        b=normalize_issue({"location":"2","rubric_criterion":"security","observation":"SQL injection"})
        self.assertEqual(a,b);self.assertEqual(jaccard({a},{b}),1.0)

    def test_merge_records_roles_and_rejects(self):
        issue=Issue(location="line 1",observation="same",rubric_criterion="precision",severity="major")
        from agents.gates_multiagent import PanelCriticArtifact
        artifacts={role:PanelCriticArtifact(defects=[issue],decision="reject" if role=="security" else "accept",rationale="r",rejected_assumptions=[],trace_id="t",reviewer_role=role) for role in ["correctness","security","robustness"]}
        merged=deterministic_merge(artifacts)
        self.assertEqual(merged["decision"],"reject");self.assertEqual(set(merged["defects"][0]["roles"]),set(artifacts))


if __name__=="__main__":unittest.main()
