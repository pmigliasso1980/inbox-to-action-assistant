import unittest
from pydantic import ValidationError
from agents.plan_validator import Plan, Step, topological_order, validate_plan


def valid_plan():
    return Plan(objective="review",completion_criterion="review synthesized",steps=[
        Step(id="read",description="read source",tool="read_code",depends_on=[],produces="source",success_criterion="code is non-empty"),
        Step(id="lint",description="analyze source",tool="run_linter",depends_on=["read"],produces="findings",success_criterion="findings is a list"),
        Step(id="synth",description="synthesize evidence",tool=None,depends_on=["read","lint"],produces="review",success_criterion="valid review JSON"),
    ])


class PlanValidatorTests(unittest.TestCase):
    def test_valid_dag(self):
        plan=valid_plan();self.assertEqual(validate_plan(plan),[]);self.assertEqual(topological_order(plan),["read","lint","synth"])
    def test_missing_and_later_dependencies(self):
        plan=valid_plan();plan.steps[0].depends_on=["lint","absent"]
        text="\n".join(validate_plan(plan));self.assertIn("later_dependency",text);self.assertIn("missing_dependency",text)
    def test_cycle(self):
        plan=valid_plan();plan.steps[0].depends_on=["synth"]
        self.assertTrue(any(x.startswith("cycle:") for x in validate_plan(plan)))
    def test_unknown_tool_and_bound(self):
        plan=valid_plan();plan.steps[0].tool="write_everything";plan.steps*=3
        text="\n".join(validate_plan(plan));self.assertIn("unknown_tool",text);self.assertIn("step_bound",text)
    def test_reasoning_step_requires_prior_artifact(self):
        plan=valid_plan();plan.steps[2].depends_on=[]
        self.assertTrue(any("missing_required_input" in x for x in validate_plan(plan)))
    def test_schema_rejects_empty_completion(self):
        with self.assertRaises(ValidationError): Plan(objective="x",steps=[],completion_criterion="")


if __name__=="__main__":unittest.main()
