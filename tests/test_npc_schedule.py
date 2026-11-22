import unittest
from companion.npc_schedule import classify, analyze


def discovery(state, decision=1, result='FOUND_ONE', session='a-1'):
    return dict(result=result, session=session, entity=42, ai_state=state, decision=decision)


class ScheduleEvidenceTests(unittest.TestCase):
    def test_sleep_and_sleep_intent_are_independent_blockers(self):
        self.assertEqual(classify(discovery(8, 5))['blockers'], ['Sleep', 'WantsToSleep'])
        self.assertIn('WantsToSleep', classify(discovery(7, 5))['blockers'])
        self.assertIn('Sleep', classify(discovery(8, 1))['blockers'])

    def test_awake_does_not_prove_day_or_readiness(self):
        r = classify(discovery(7))
        self.assertEqual(r['status'], 'NO_SCHEDULE_BLOCK_OBSERVED')
        self.assertFalse(r['movement_ready'])
        self.assertEqual(r['daytime'], 'NOT_INFERRED_FROM_AI_STATE')

    def test_transition_to_sleep_and_back_does_not_claim_wake_control(self):
        rows = [dict(kind='SAMPLE', value=dict(discovery=discovery(s, d), orders=0))
                for s, d in [(7, 1), (2, 5), (8, 5), (8, 5), (13, 1), (7, 1)]]
        r = analyze(rows)
        self.assertEqual(len(r['transitions']), 5)
        self.assertFalse(r['runtime_ready'])
        self.assertTrue(all(not t['classification']['wake_supported'] for t in r['transitions']))

    def test_ambiguity_and_session_changes_not_conflated(self):
        self.assertEqual(classify(discovery(8, result='AMBIGUOUS'))['status'], 'IDENTITY_UNCONFIRMED')
        r = analyze([dict(kind='SAMPLE', value=dict(discovery=discovery(8, session=s)))
                     for s in ['a-1', 'b-1']])
        self.assertEqual(len(r['transitions']), 2)

    def test_empty_evidence_never_ready(self):
        self.assertFalse(analyze([])['installation_ready'])
