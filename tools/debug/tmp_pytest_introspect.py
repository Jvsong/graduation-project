
import unittest

class T(unittest.TestCase):
    def tearDown(self):
        print('OUTCOME_TYPE', type(getattr(self, '_outcome', None)))
        outcome = getattr(self, '_outcome', None)
        if outcome is not None:
            print('OUTCOME_DIR_HAS_SUCCESS', hasattr(outcome, 'success'), getattr(outcome, 'success', None))
            print('OUTCOME_RESULT_TYPE', type(getattr(outcome, 'result', None)))
            result = getattr(outcome, 'result', None)
            if result is not None:
                print('RESULT_CLASS', result.__class__)
                for name in ['errors', 'failures', 'skipped', 'passed', 'outcome', 'nodeid']:
                    print('RESULT_ATTR', name, hasattr(result, name), getattr(result, name, None))
                print('RESULT_DIR_SAMPLE', [n for n in dir(result) if n in ['errors','failures','skipped','passed','when','outcome']])
    def test_fail(self):
        self.assertEqual(1,2)
