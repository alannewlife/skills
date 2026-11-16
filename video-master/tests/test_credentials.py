import sys
import unittest
from unittest import mock
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import credentials

class CredentialTests(unittest.TestCase):
    def test_rejects_invalid_key_without_storing(self):
        with mock.patch.object(credentials, '_store') as store:
            for value in ('', '  ', 'hello\nworld', 'a' * 4097):
                with self.assertRaises(credentials.CredentialError): credentials.save_key(value)
            store.assert_not_called()

    def test_status_does_not_return_secret(self):
        with mock.patch.object(credentials, '_lookup', return_value='fake-secret-for-test'):
            value = credentials.status()
            self.assertTrue(value['configured'])
            self.assertNotIn('fake-secret-for-test', str(value))

    def test_environment_fallback(self):
        with mock.patch.object(credentials, '_lookup', return_value=None), mock.patch.dict('os.environ', {'MIMO_API_KEY': 'fake-env-secret'}):
            self.assertEqual(credentials.load_key(), 'fake-env-secret')
            self.assertEqual(credentials.status()['source'], 'environment')

    def test_recognizes_mimo_environment_alias(self):
        with mock.patch.object(credentials, '_lookup', return_value=None), mock.patch.dict('os.environ', {'XIAOMI_MIMO_API_KEY': 'fake-env-secret'}, clear=True):
            self.assertEqual(credentials.load_key(), 'fake-env-secret')
            status = credentials.status()
            self.assertTrue(status['configured'])
            self.assertEqual(status['source'], 'environment')
            self.assertNotIn('fake-env-secret', str(status))

if __name__ == '__main__': unittest.main()
