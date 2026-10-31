import unittest
from smaa.benchmark import AgentObservation, BudgetLimits, EvaluationTarget, LogOnlyAgent, StateTrackerAgent
from smaa.harness import Preregistration, TrialSpec, balanced_random_assignment, preregistration_digest, run_isolated_decision, run_study

class HarnessTests(unittest.TestCase):
    def setUp(self):
        self.obs=AgentObservation("t1",0.7,("cap",),"id-A",("attempt","abstain"),{})
        self.target=EvaluationTarget(0.65,True,"id-A",{"attempt":1.0,"abstain":0.0})
        self.pr=Preregistration("pilot","mean_decision_regret","minimize",17,10.0,("log","state"),"plan-v1")
    def test_assignment_reproducible_and_balanced(self):
        strata={"a":[f"a{i}" for i in range(8)],"b":[f"b{i}" for i in range(7)]}
        x=balanced_random_assignment(strata,("A","B","C"),42)
        self.assertEqual(x,balanced_random_assignment(strata,("A","B","C"),42))
        for ids in strata.values():
            counts=[sum(x[i]==arm for i in ids) for arm in ("A","B","C")]
            self.assertLessEqual(max(counts)-min(counts),1)
    def test_duplicate_ids_rejected(self):
        with self.assertRaises(ValueError): balanced_random_assignment({"s":["x","x"]},("a","b"),1)
    def test_digest_stable(self):
        self.assertEqual(preregistration_digest(self.pr),preregistration_digest(self.pr))
    def test_spawned_agent_decision(self):
        decision,budget,elapsed=run_isolated_decision(LogOnlyAgent(),self.obs,BudgetLimits(),10)
        self.assertEqual(decision.predicted_identity,"unknown")
        self.assertEqual(budget["used"]["agent"],1)
        self.assertGreaterEqual(elapsed,0)
    def test_study_records_no_target_fields_in_decision(self):
        trials=[TrialSpec("t1","f",self.obs,self.target,11),
          TrialSpec("t2","f",AgentObservation("t2",.3,("cap",),"id-A",("attempt","abstain"),{}),
          EvaluationTarget(.25,True,"id-A",{"attempt":1.0,"abstain":0.0}),12)]
        records=run_study(self.pr,trials,{"log":LogOnlyAgent(),"state":StateTrackerAgent()})
        self.assertEqual(len(records),2)
        self.assertEqual({r.arm for r in records},{"log","state"})
        self.assertTrue(all(r.preregistration_sha256==preregistration_digest(self.pr) for r in records))
        self.assertTrue(all("actual_identity" not in r.decision for r in records))
    def test_arm_mismatch_rejected(self):
        with self.assertRaises(ValueError): run_study(self.pr,[],{"log":LogOnlyAgent()})
    def test_invalid_timeout_rejected(self):
        with self.assertRaises(ValueError):
            Preregistration("x","y","minimize",1,0,("a","b"),"v")
if __name__=="__main__": unittest.main()
