import unittest
from smaa.benchmark import (
    ActiveSMAAAgent, AgentDecision, AgentObservation, BudgetLimits, BudgetMeter,
    EvaluationTarget, LogOnlyAgent, StateTrackerAgent, evaluate_decision,
    run_blinded_trial, summarize_trials,
)

class SMAA12BenchmarkTests(unittest.TestCase):
    def setUp(self):
        self.observation = AgentObservation(
            "trial-001", 0.4, ("navigation",), "identity-token-B",
            ("wait", "probe"), {"load": 0.7})
        self.target = EvaluationTarget(
            0.35, False, "identity-token-B", {"wait": 0.2, "probe": 0.8})

    def test_agent_api_receives_observation_not_target(self):
        decision = StateTrackerAgent().decide(self.observation, BudgetMeter(BudgetLimits()))
        self.assertIsInstance(decision, AgentDecision)

    def test_log_only_retains_events_without_adapting(self):
        agent = LogOnlyAgent()
        first = agent.decide(self.observation, BudgetMeter(BudgetLimits()))
        self.assertEqual(agent.event_log, ["trial-001"])
        self.assertEqual(first.predicted_performance, 0.5)

    def test_four_control_arms_are_distinct(self):
        from smaa.benchmark import FixedSelfReportAgent
        agents = [LogOnlyAgent(), FixedSelfReportAgent(), StateTrackerAgent(), ActiveSMAAAgent()]
        self.assertEqual(len({a.architecture.value for a in agents}), 4)

    def test_blinded_trial_returns_behavioral_metrics(self):
        _, metrics, budget = run_blinded_trial(StateTrackerAgent(), self.observation, self.target)
        self.assertAlmostEqual(metrics.performance_absolute_error, 0.05)
        self.assertTrue(metrics.identity_correct)
        self.assertEqual(budget["used"]["environment"], 5)
        self.assertEqual(budget["used"]["evaluator"], 6)

    def test_decision_changes_with_predicted_self_capability(self):
        low = StateTrackerAgent().decide(self.observation, BudgetMeter(BudgetLimits()))
        high_observation = AgentObservation(
            "trial-002", 0.9, ("navigation",), "identity-token-B",
            ("attempt", "abstain"), {})
        high = StateTrackerAgent().decide(high_observation, BudgetMeter(BudgetLimits()))
        self.assertEqual(low.chosen_action, "probe")
        self.assertEqual(high.chosen_action, "attempt")

    def test_target_not_added_to_observation(self):
        run_blinded_trial(LogOnlyAgent(), self.observation, self.target)
        self.assertFalse(hasattr(self.observation, "actual_identity"))

    def test_budget_enforced_per_component(self):
        meter = BudgetMeter(BudgetLimits(agent=2))
        meter.consume("agent", 2)
        with self.assertRaises(RuntimeError):
            meter.consume("agent", 1)

    def test_budget_rejects_unknown_component(self):
        with self.assertRaises(ValueError):
            BudgetMeter(BudgetLimits()).consume("gpu", 1)

    def test_active_smaa_updates_from_feedback(self):
        agent = ActiveSMAAAgent(learning_rate=0.5)
        agent.decide(self.observation, BudgetMeter(BudgetLimits()))
        old = agent.performance_bias
        agent.receive_feedback(0.8)
        self.assertNotEqual(agent.performance_bias, old)

    def test_feedback_requires_prediction(self):
        with self.assertRaises(RuntimeError):
            ActiveSMAAAgent().receive_feedback(0.5)

    def test_invalid_action_rejected(self):
        decision = AgentDecision(0.5, True, "x", "not-offered", 0.5)
        with self.assertRaises(ValueError):
            evaluate_decision(self.observation, decision, self.target, BudgetMeter(BudgetLimits()))

    def test_behavioral_summary_fields(self):
        _, metrics, _ = run_blinded_trial(StateTrackerAgent(), self.observation, self.target)
        self.assertEqual(set(summarize_trials([metrics])), {
            "mean_performance_absolute_error", "limitation_detection_accuracy",
            "identity_accuracy", "mean_decision_reward", "mean_decision_regret",
            "mean_confidence_brier"})

    def test_empty_summary_rejected(self):
        with self.assertRaises(ValueError):
            summarize_trials([])

    def test_nonfinite_feedback_rejected(self):
        agent = ActiveSMAAAgent()
        agent.decide(self.observation, BudgetMeter(BudgetLimits()))
        with self.assertRaises(ValueError):
            agent.receive_feedback(float("nan"))

if __name__ == "__main__":
    unittest.main()
