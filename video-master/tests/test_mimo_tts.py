import base64
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import mimo_tts

class SpeechTests(unittest.TestCase):
    def test_synthesis_uses_local_key_and_writes_audio(self):
        wave = b'RIFF\x04\x00\x00\x00WAVEtest'
        response = json.dumps({'choices':[{'message':{'audio':{'data':base64.b64encode(wave).decode()}}}]}).encode()
        fake = mock.MagicMock(); fake.__enter__.return_value.read.return_value = response
        with tempfile.TemporaryDirectory() as d, mock.patch.object(mimo_tts.credentials, 'load_key', return_value='fake-secret'), mock.patch.object(mimo_tts.urllib.request, 'urlopen', return_value=fake) as call:
            output = Path(d) / 'voice.wav'
            mimo_tts.synthesize('这是确认过的旁白。', output, '茉莉', '自然专业')
            self.assertEqual(output.read_bytes(), wave)
            request = call.call_args.args[0]
            payload = json.loads(request.data)
            self.assertEqual(payload['model'], 'mimo-v2.5-tts')
            self.assertEqual(payload['messages'][-1]['content'], '这是确认过的旁白。')
            self.assertEqual(payload['audio']['voice'], '茉莉')

    def test_missing_key_never_writes_audio(self):
        with tempfile.TemporaryDirectory() as d, mock.patch.object(mimo_tts.credentials, 'load_key', return_value=None):
            output = Path(d) / 'voice.wav'
            with self.assertRaises(mimo_tts.SpeechError): mimo_tts.synthesize('旁白', output)
            self.assertFalse(output.exists())

if __name__ == '__main__': unittest.main()
