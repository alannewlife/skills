import json
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.request import urlopen

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import video_master
import workflow

class FinalFileEndpointTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        story = root / 'story.md'
        story.write_text('一个完整故事。', encoding='utf-8')
        self.project = root / 'project'
        workflow.initialize(self.project, story)
        (self.project / 'output' / '成片.mp4').write_bytes(b'video')
        self.server = video_master.Server(('127.0.0.1', 0), video_master.Handler)
        self.server.project = self.project
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        self.tmp.cleanup()

    def result(self):
        with urlopen(f'http://127.0.0.1:{self.server.server_port}/api/final-file') as response:
            return json.load(response)

    def test_only_confirmed_existing_project_video_has_absolute_path(self):
        self.assertIsNone(self.result()['path'])
        state = workflow.read(self.project)
        state['active'] = 'done'
        state['stages']['final'] = {'status': 'confirmed', 'data': {'video': 'output/成片.mp4'}}
        workflow.write(self.project, state)
        self.assertEqual(self.result()['path'], str((self.project / 'output' / '成片.mp4').resolve()))
        state['stages']['final']['data']['video'] = '../story.md'
        workflow.write(self.project, state)
        self.assertIsNone(self.result()['path'])

if __name__ == '__main__':
    unittest.main()
