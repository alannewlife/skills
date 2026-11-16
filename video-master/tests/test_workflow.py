import json
import subprocess
import time
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import workflow


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.project = Path(self.tmp.name) / 'film'
        self.story = Path(self.tmp.name) / 'story.md'
        self.story.write_text('开头：团队收到任务。\n过程：大家一起解决问题。\n结尾：任务顺利完成。', encoding='utf-8')
        workflow.initialize(self.project, self.story)
        # Retain the original five-stage contract as a legacy project fixture.
        state = workflow.read(self.project)
        state['schema'] = 1
        state['stages'].pop('restoration', None)
        workflow.write(self.project, state)

    def tearDown(self):
        self.tmp.cleanup()

    def test_confirm_requires_current_revision_and_artifacts(self):
        state = workflow.read(self.project)
        with self.assertRaises(workflow.Conflict):
            workflow.submit(self.project, 'style', {}, state['revision'] - 1, True)
        with self.assertRaises(workflow.Invalid):
            workflow.submit(self.project, 'style', {}, state['revision'], True)
        state = workflow.submit(self.project, 'style', {'style_id': 'business-line-art'}, state['revision'], True)
        self.assertEqual(state['active'], 'styleframe')
        with self.assertRaises(workflow.Invalid):
            workflow.submit(self.project, 'styleframe', {}, state['revision'], True)

    def test_complete_and_invalidate(self):
        state = workflow.read(self.project)
        state = workflow.submit(self.project, 'style', {'style_id': 'business-line-art'}, state['revision'], True)
        for stage, payload in [
            ('styleframe', {'image': 'assets/frame.png'}),
            ('storyboard', {'scenes': [{'id': 's1', 'narration': '内容', 'image': 'assets/frame.png'}]}),
            ('sample', {'video': 'assets/sample.mp4'}),
            ('final', {'video': 'assets/sample.mp4'}),
        ]:
            for filename in ('frame.png', 'sample.mp4'):
                p = self.project / 'assets' / filename
                p.parent.mkdir(exist_ok=True)
                p.write_bytes(b'test')
            state = workflow.propose(self.project, stage, payload)
            state = workflow.submit(self.project, stage, {}, state['revision'], True)
        self.assertEqual(state['active'], 'done')
        old = state['revision']
        state = workflow.reopen(self.project, 'styleframe', old)
        self.assertEqual(state['active'], 'styleframe')
        self.assertEqual(state['stages']['style']['status'], 'confirmed')
        self.assertEqual(state['stages']['storyboard']['status'], 'stale')
        self.assertEqual(state['stages']['final']['status'], 'stale')
        self.assertTrue(state['history'])
        self.assertEqual(workflow.read(self.project)['revision'], state['revision'])

    def test_path_traversal_rejected_and_draft_saves(self):
        state = workflow.read(self.project)
        state = workflow.submit(self.project, 'style', {'style_id': 'paper-story', 'notes': '暖色'}, state['revision'], False)
        self.assertEqual(workflow.read(self.project)['stages']['style']['data']['notes'], '暖色')
        state = workflow.submit(self.project, 'style', {}, state['revision'], True)
        state = workflow.propose(self.project, 'styleframe', {'image': '../story.md'})
        with self.assertRaises(workflow.Invalid):
            workflow.submit(self.project, 'styleframe', {}, state['revision'], True)

    def test_changed_file_and_notes_block_confirmation(self):
        state = workflow.read(self.project)
        state = workflow.submit(self.project, 'style', {'style_id': 'business-line-art'}, state['revision'], True)
        image = self.project / 'assets/frame.png'
        image.write_bytes(b'frame-v1')
        state = workflow.propose(self.project, 'styleframe', {'image': 'assets/frame.png'})
        state = workflow.submit(self.project, 'styleframe', {}, state['revision'], True)
        image.write_bytes(b'frame-v2')
        state = workflow.propose(self.project, 'storyboard', {'scenes': [{'id': 's1', 'narration': '内容', 'image': 'assets/frame.png'}]})
        with self.assertRaises(workflow.Invalid):
            workflow.submit(self.project, 'storyboard', {}, state['revision'], True)
        state = workflow.reopen(self.project, 'styleframe', state['revision'])
        state = workflow.submit(self.project, 'styleframe', {}, state['revision'], True)
        with self.assertRaises(workflow.Invalid):
            workflow.submit(self.project, 'storyboard', {}, state['revision'], True)
        state = workflow.propose(self.project, 'storyboard', {'notes': '需要重画'})
        with self.assertRaises(workflow.Invalid):
            workflow.submit(self.project, 'storyboard', {}, state['revision'], True)

    def test_wait_reports_new_saved_review_without_confirmation(self):
        state = workflow.read(self.project)
        previous_revision = state['revision']
        state = workflow.submit(self.project, 'style', {'style_id': 'business-line-art', 'notes': '希望更简洁'}, previous_revision, False)
        cli = Path(__file__).resolve().parents[1] / 'scripts' / 'video_master.py'
        result = subprocess.run([sys.executable, str(cli), 'wait', str(self.project), 'style', '--after-revision', str(previous_revision), '--timeout', '0'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['revision'], state['revision'])
        self.assertEqual(json.loads(result.stdout)['stages']['style']['status'], 'draft')

    def test_live_wait_reports_connection_and_receives_confirmation(self):
        state = workflow.read(self.project)
        cli = Path(__file__).resolve().parents[1] / 'scripts' / 'video_master.py'
        child = subprocess.Popen([sys.executable, str(cli), 'wait', str(self.project), 'style', '--after-revision', str(state['revision']), '--timeout', '10'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        try:
            deadline = time.monotonic() + 5
            while time.monotonic() < deadline and not workflow.waiter_status(self.project)['connected']:
                time.sleep(.05)
            self.assertTrue(workflow.waiter_status(self.project)['connected'])
            self.assertEqual(workflow.waiter_status(self.project)['stage'], 'style')
            workflow.submit(self.project, 'style', {'style_id': 'business-line-art'}, state['revision'], True)
            stdout, stderr = child.communicate(timeout=5)
            self.assertEqual(child.returncode, 0, stderr)
            self.assertEqual(json.loads(stdout)['active'], 'styleframe')
            self.assertFalse(workflow.waiter_status(self.project)['connected'])
        finally:
            if child.poll() is None:
                child.terminate(); child.communicate(timeout=5)

    def test_proposal_rejects_a_stale_revision(self):
        state = workflow.read(self.project)
        earlier_revision = state['revision']
        state = workflow.submit(self.project, 'style', {'style_id': 'business-line-art', 'notes': '用户的新意见'}, earlier_revision, False)
        with self.assertRaises(workflow.Conflict):
            workflow.propose(self.project, 'style', {'notes': ''}, expected_revision=earlier_revision)
        self.assertEqual(workflow.read(self.project)['stages']['style']['data']['notes'], '用户的新意见')

    def test_scene_revision_request_identifies_one_scene(self):
        state = workflow.read(self.project)
        state = workflow.submit(self.project, 'style', {'style_id': 'business-line-art'}, state['revision'], True)
        (self.project / 'assets' / 'frame.png').write_bytes(b'frame')
        state = workflow.propose(self.project, 'styleframe', {'image': 'assets/frame.png'})
        state = workflow.submit(self.project, 'styleframe', {}, state['revision'], True)
        scenes = [{'id':'s1','narration':'一','image':'assets/frame.png'}, {'id':'s2','narration':'二','image':'assets/frame.png'}]
        state = workflow.propose(self.project, 'storyboard', {'scenes': scenes})
        edits = [{'id':'s1','notes':'增加人物'}, {'id':'s2','notes':'未提交的想法'}]
        state = workflow.submit(self.project, 'storyboard', {'scenes': edits, 'request_scene': 's1'}, state['revision'])
        data = state['stages']['storyboard']['data']
        self.assertEqual(data['requested_scene_ids'], ['s1'])
        self.assertEqual(data['scenes'][1]['notes'], '未提交的想法')
        with self.assertRaises(workflow.Invalid):
            workflow.submit(self.project, 'storyboard', {'request_scene': 'missing'}, state['revision'])

    def test_video_cannot_be_approved_during_rework(self):
        state = workflow.read(self.project)
        state = workflow.submit(self.project, 'style', {'style_id':'business-line-art'}, state['revision'], True)
        (self.project/'assets'/'frame.png').write_bytes(b'frame')
        (self.project/'assets'/'sample.mp4').write_bytes(b'video')
        state = workflow.propose(self.project, 'styleframe', {'image':'assets/frame.png'})
        state = workflow.submit(self.project, 'styleframe', {}, state['revision'], True)
        state = workflow.propose(self.project, 'storyboard', {'scenes':[{'id':'s1','narration':'旁白','image':'assets/frame.png'}]})
        state = workflow.submit(self.project, 'storyboard', {}, state['revision'], True)
        state = workflow.propose(self.project, 'sample', {'video':'assets/sample.mp4','processing':True})
        with self.assertRaises(workflow.Invalid):
            workflow.submit(self.project, 'sample', {}, state['revision'], True)
        state = workflow.propose(self.project, 'sample', {'processing':False}, expected_revision=state['revision'])
        state = workflow.submit(self.project, 'sample', {}, state['revision'], True)
        self.assertEqual(state['active'], 'final')


class RestorationWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.project = Path(self.tmp.name) / 'film'
        story = Path(self.tmp.name) / 'story.md'
        story.write_text('故事的开始、过程和结尾。', encoding='utf-8')
        self.state = workflow.initialize(self.project, story)
        for name in ('frame.png', 'other.png', 'restored.png', 'sample.mp4'):
            (self.project / 'assets' / name).write_bytes(b'original-' + name.encode())
        self.plan = [{'name':'人物','method':'drawn','source':'参考分镜中的人物'}, {'name':'关系线','method':'code','source':'按原图连接对象'}]

    def tearDown(self): self.tmp.cleanup()

    def advance_to_sample(self):
        s=workflow.submit(self.project,'style',{'style_id':'business-line-art'},self.state['revision'],True)
        s=workflow.propose(self.project,'styleframe',{'image':'assets/frame.png'})
        s=workflow.submit(self.project,'styleframe',{},s['revision'],True)
        s=workflow.propose(self.project,'storyboard',{'scenes':[{'id':'one','narration':'一','image':'assets/frame.png'}, {'id':'two','narration':'二','image':'assets/other.png'}]})
        return workflow.submit(self.project,'storyboard',{},s['revision'],True)

    def sample_data(self):
        return {'video':'assets/sample.mp4','comparison_scene_id':'one','comparison_frame':'assets/restored.png','comparison_time':3.0,'asset_plan':self.plan,'deviation':'人物表情略有变化'}

    def advance_to_restoration(self):
        s=self.advance_to_sample()
        s=workflow.propose(self.project,'sample',self.sample_data(),expected_revision=s['revision'])
        return workflow.submit(self.project,'sample',{'deviation_accepted':True},s['revision'],True)

    def comparisons(self):
        return [{'scene_id':sid,'frame':'assets/restored.png','video':'assets/sample.mp4','asset_plan':self.plan,'deviation':'','notes':''} for sid in ('one','two')]

    def test_sample_requires_original_scene_comparison_and_explicit_acceptance(self):
        s=self.advance_to_sample()
        s=workflow.propose(self.project,'sample',{'video':'assets/sample.mp4'})
        with self.assertRaises(workflow.Invalid): workflow.submit(self.project,'sample',{},s['revision'],True)
        s=workflow.propose(self.project,'sample',self.sample_data())
        with self.assertRaises(workflow.Invalid): workflow.submit(self.project,'sample',{},s['revision'],True)
        s=workflow.submit(self.project,'sample',{'deviation_accepted':True},s['revision'],True)
        self.assertEqual(s['active'],'restoration')

    def test_agent_cannot_preaccept_or_reaccept_reported_differences(self):
        s=self.advance_to_sample();proposal=self.sample_data();proposal['deviation_accepted']=True
        s=workflow.propose(self.project,'sample',proposal)
        self.assertFalse(s['stages']['sample']['data']['deviation_accepted'])
        s=workflow.submit(self.project,'sample',{'deviation_accepted':True},s['revision'],True)
        items=self.comparisons();items[0]['deviation']='线条变动';items[0]['deviation_accepted']=True
        s=workflow.propose(self.project,'restoration',{'comparisons':items})
        self.assertFalse(s['stages']['restoration']['data']['comparisons'][0]['deviation_accepted'])

    def test_restoration_requires_actual_scene_clips_and_binds_their_contents(self):
        s=self.advance_to_restoration()
        items=self.comparisons()
        for item in items: item.pop('video')
        s=workflow.propose(self.project,'restoration',{'review_video_required':True,'comparisons':items})
        with self.assertRaises(workflow.Invalid): workflow.submit(self.project,'restoration',{},s['revision'],True)
        for item in items: item['video']='assets/sample.mp4'
        s=workflow.propose(self.project,'restoration',{'comparisons':items},expected_revision=s['revision'])
        s=workflow.submit(self.project,'restoration',{},s['revision'],True)
        (self.project/'assets/sample.mp4').write_bytes(b'changed clip')
        s=workflow.propose(self.project,'final',{'video':'assets/sample.mp4'})
        with self.assertRaises(workflow.Invalid): workflow.submit(self.project,'final',{},s['revision'],True)

    def test_restoration_requires_every_scene_and_acceptance(self):
        s=self.advance_to_restoration()
        s=workflow.propose(self.project,'restoration',{'comparisons':self.comparisons()[:1]})
        with self.assertRaises(workflow.Invalid): workflow.submit(self.project,'restoration',{},s['revision'],True)
        comparisons=self.comparisons();comparisons[1]['deviation']='消息图标有变化'
        s=workflow.propose(self.project,'restoration',{'comparisons':comparisons})
        with self.assertRaises(workflow.Invalid): workflow.submit(self.project,'restoration',{},s['revision'],True)
        s=workflow.submit(self.project,'restoration',{'comparisons':[{'scene_id':'two','deviation_accepted':True}]},s['revision'],True)
        self.assertEqual(s['active'],'final')

    def test_revision_requests_preserve_other_drafts_and_invalidate_acceptance(self):
        s=self.advance_to_restoration();items=self.comparisons();items[0]['deviation']='位置变化'
        s=workflow.propose(self.project,'restoration',{'comparisons':items})
        s=workflow.submit(self.project,'restoration',{'comparisons':[{'scene_id':'one','deviation_accepted':True,'notes':'请调整'}, {'scene_id':'two','notes':'尚未提交'}],'request_scene':'one'},s['revision'])
        self.assertEqual(s['stages']['restoration']['data']['requested_scene_ids'],['one'])
        self.assertEqual(s['stages']['restoration']['data']['comparisons'][1]['notes'],'尚未提交')
        items=s['stages']['restoration']['data']['comparisons'];items[0]['frame']='assets/other.png';items[0]['notes']=''
        s=workflow.propose(self.project,'restoration',{'comparisons':items,'requested_scene_ids':[]},expected_revision=s['revision'])
        self.assertFalse(s['stages']['restoration']['data']['comparisons'][0].get('deviation_accepted',False))
        self.assertEqual(s['stages']['restoration']['data']['comparisons'][1]['notes'],'尚未提交')

    def test_reference_files_are_bound_to_confirmed_revision(self):
        s=self.advance_to_restoration();s=workflow.propose(self.project,'restoration',{'comparisons':self.comparisons()})
        s=workflow.submit(self.project,'restoration',{},s['revision'],True)
        (self.project/'assets/restored.png').write_bytes(b'changed')
        s=workflow.propose(self.project,'final',{'video':'assets/sample.mp4'})
        with self.assertRaises(workflow.Invalid): workflow.submit(self.project,'final',{},s['revision'],True)

    def test_changed_comparison_at_same_path_requires_new_review(self):
        s=self.advance_to_sample()
        s=workflow.propose(self.project,'sample',self.sample_data())
        s=workflow.submit(self.project,'sample',{'deviation_accepted':True},s['revision'])
        (self.project/'assets/restored.png').write_bytes(b'new version at the same path')
        with self.assertRaises(workflow.Invalid): workflow.submit(self.project,'sample',{},s['revision'],True)
        s=workflow.propose(self.project,'sample',{'comparison_frame':'assets/restored.png'},expected_revision=s['revision'])
        self.assertFalse(s['stages']['sample']['data']['deviation_accepted'])
        with self.assertRaises(workflow.Invalid): workflow.submit(self.project,'sample',{},s['revision'],True)

    def test_partial_scene_proposal_preserves_other_scene_and_drafts(self):
        s=self.advance_to_restoration();s=workflow.propose(self.project,'restoration',{'comparisons':self.comparisons()})
        s=workflow.submit(self.project,'restoration',{'comparisons':[{'scene_id':'two','notes':'还没提交的意见'}]},s['revision'])
        s=workflow.propose(self.project,'restoration',{'comparisons':[{'scene_id':'one','frame':'assets/other.png'}]},expected_revision=s['revision'])
        items=s['stages']['restoration']['data']['comparisons']
        self.assertEqual([c['scene_id'] for c in items],['one','two'])
        self.assertEqual(items[0]['frame'],'assets/other.png')
        self.assertEqual(items[1]['notes'],'还没提交的意见')
        updated=copy_items=[dict(c) for c in items]
        copy_items[1]['notes']=''
        s=workflow.propose(self.project,'restoration',{'comparisons':updated},expected_revision=s['revision'])
        self.assertEqual(s['stages']['restoration']['data']['comparisons'][1]['notes'],'还没提交的意见')

    def test_changed_scene_frame_cannot_keep_old_deviation_acceptance(self):
        s=self.advance_to_restoration();items=self.comparisons();items[0]['deviation']='显示有变化'
        s=workflow.propose(self.project,'restoration',{'comparisons':items})
        s=workflow.submit(self.project,'restoration',{'comparisons':[{'scene_id':'one','deviation_accepted':True}]},s['revision'])
        (self.project/'assets/restored.png').write_bytes(b'changed after acceptance')
        with self.assertRaises(workflow.Invalid): workflow.submit(self.project,'restoration',{},s['revision'],True)
        s=workflow.propose(self.project,'restoration',{'processing':True},expected_revision=s['revision'])
        self.assertFalse(s['stages']['restoration']['data']['comparisons'][0]['deviation_accepted'])

    def test_legacy_completed_project_is_not_mutated_on_read(self):
        self.assertEqual(self.state['schema'],2)
        s=workflow.read(self.project);s['schema']=1;s['stages'].pop('restoration');s['active']='done';workflow.write(self.project,s)
        before=(self.project/'project.json').read_bytes()
        self.assertEqual(workflow.read(self.project)['active'],'done')
        self.assertEqual((self.project/'project.json').read_bytes(),before)

    def test_legacy_upgrade_is_explicit_and_reopens_sample_without_touching_media(self):
        s=workflow.read(self.project);s['schema']=1;s['stages'].pop('restoration');s['active']='done'
        s['stages']['sample']={'status':'confirmed','data':{'video':'assets/sample.mp4'}}
        s['stages']['final']={'status':'confirmed','data':{'video':'assets/sample.mp4'}}
        workflow.write(self.project,s); before=(self.project/'assets/sample.mp4').read_bytes()
        with self.assertRaises(workflow.Conflict): workflow.upgrade(self.project,s['revision']-1)
        s=workflow.upgrade(self.project,s['revision'])
        self.assertEqual(s['schema'],2);self.assertEqual(s['active'],'sample')
        self.assertEqual(s['stages']['restoration']['status'],'pending')
        self.assertEqual(s['stages']['sample']['status'],'draft')
        self.assertTrue(s['stages']['sample']['needs_update'])
        self.assertEqual(s['stages']['final']['status'],'stale')
        self.assertEqual((self.project/'assets/sample.mp4').read_bytes(),before)

    def test_chat_acceptance_is_explicit_and_scene_specific(self):
        s=self.advance_to_sample();s=workflow.propose(self.project,'sample',self.sample_data())
        cli=Path(__file__).resolve().parents[1]/'scripts/chat_confirm.py'
        args=[sys.executable,str(cli),str(self.project),'sample',str(s['revision'])]
        failed=subprocess.run(args,capture_output=True,text=True)
        self.assertNotEqual(failed.returncode,0)
        ok=subprocess.run(args+['--accept-deviation'],capture_output=True,text=True)
        self.assertEqual(ok.returncode,0,ok.stderr)
        s=workflow.read(self.project);items=self.comparisons();items[1]['deviation']='位置变化'
        s=workflow.propose(self.project,'restoration',{'comparisons':items})
        args=[sys.executable,str(cli),str(self.project),'restoration',str(s['revision'])]
        wrong=subprocess.run(args+['--accept-scene','one'],capture_output=True,text=True)
        self.assertNotEqual(wrong.returncode,0)
        ok=subprocess.run(args+['--accept-scene','two'],capture_output=True,text=True)
        self.assertEqual(ok.returncode,0,ok.stderr)


if __name__ == '__main__':
    unittest.main()
