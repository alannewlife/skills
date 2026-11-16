import tempfile, sys, shutil, subprocess, time, json
from pathlib import Path
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'scripts'))
import workflow
with tempfile.TemporaryDirectory() as tmp:
    tmp=Path(tmp); story=tmp/'story.md'; story.write_text('开头：同事收到一个任务。\n过程：大家寻找信息并合作。\n结尾：任务完成。',encoding='utf8')
    project=tmp/'project';workflow.initialize(project,story)
    shutil.copy(root/'styles/business-line-art/poster.png',project/'assets/frame.png')
    shutil.copy(root/'styles/business-line-art/preview.mp4',project/'video/sample.mp4')
    proc=subprocess.Popen([sys.executable,str(root/'scripts/video_master.py'),'serve',str(project),'--port','0','--no-browser'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    try:
      url=proc.stdout.readline().strip().split('Video Master: ', 1)[1]
      with sync_playwright() as p:
        browser=p.chromium.launch(headless=True);page=browser.new_page(viewport={'width':1440,'height':1000});errors=[]
        page.on('pageerror',lambda e:errors.append(str(e)))
        page.goto(url,wait_until='networkidle')
        assert page.locator('.bottombar #save').count()==0
        assert page.locator('#style-notes').locator('..').locator('#save').inner_text()=='修改实施'
        page.locator('[data-style="paper-story"]').click();page.locator('#style-notes').fill('使用浅绿色');page.locator('#remove-logo').click()
        page.wait_for_timeout(400);assert workflow.read(project)['brand']['logo'] is None
        assert page.locator('#style-notes').input_value()=='使用浅绿色'
        revision=workflow.read(project)['revision']
        waiter=subprocess.Popen([sys.executable,str(root/'scripts/video_master.py'),'wait',str(project),'style','--after-revision',str(revision),'--timeout','20'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        page.get_by_text('自动等待已连接',exact=False).wait_for(timeout=10000)
        page.locator('#confirm').click();page.wait_for_selector('text=等待 Codex 制作风格试图')
        out,err=waiter.communicate(timeout=5)
        assert waiter.returncode==0,err
        assert json.loads(out)['active']=='styleframe'
        assert workflow.read(project)['active']=='styleframe'
        workflow.propose(project,'styleframe',{'processing':True})
        page.locator('.media-frame .work-loading').wait_for(state='visible',timeout=10000)
        assert page.locator('.media-frame .work-loading .work-dot').count()==9
        workflow.propose(project,'styleframe',{'image':'assets/frame.png','processing':False})
        page.wait_for_selector('img[alt="当前故事风格试图"]',timeout=10000)
        assert page.locator('#review-notes').locator('..').locator('#save').inner_text()=='修改实施'
        page.locator('#review-notes').fill('调整构图');page.locator('#save').click();page.wait_for_timeout(300)
        page.reload(wait_until='networkidle');assert page.locator('#review-notes').input_value()=='调整构图'
        page.locator('#confirm').click();page.wait_for_timeout(300);assert workflow.read(project)['active']=='styleframe'
        workflow.propose(project,'styleframe',{'notes':'','image':'assets/frame.png'})
        page.wait_for_timeout(4500);page.locator('#confirm').click();page.wait_for_selector('text=等待 Codex 制作图文分镜')
        scenes=[{'id':'one','title':'开场','narration':'故事开始','description':'出现人物','image':'assets/frame.png'}, {'id':'two','title':'结尾','narration':'故事结束','description':'任务完成','image':'assets/frame.png'}]
        workflow.propose(project,'storyboard',{'scenes':scenes,'notes':''});page.wait_for_selector('[data-down="0"]',timeout=10000)
        workflow.propose(project,'storyboard',{'processing':True,'processing_scene_ids':['one']})
        page.locator('[data-scene-id="one"] .work-loading').wait_for(state='visible',timeout=10000)
        assert page.locator('[data-scene-id="two"] .work-loading').is_hidden()
        workflow.propose(project,'storyboard',{'processing':False,'processing_scene_ids':[]})
        page.locator('[data-scene-id="one"] .work-loading').wait_for(state='hidden',timeout=10000)
        revision=workflow.read(project)['revision']
        waiter=subprocess.Popen([sys.executable,str(root/'scripts/video_master.py'),'wait',str(project),'storyboard','--after-revision',str(revision),'--timeout','20'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        page.get_by_text('自动等待已连接',exact=False).wait_for(timeout=10000)
        assert page.locator('[data-request="0"]').inner_text()=='修改实施'
        assert page.locator('#request-overall').inner_text()=='修改实施'
        page.locator('[data-field="notes"]').first.fill('请增加人物')
        page.locator('[data-request="0"]').click()
        out,err=waiter.communicate(timeout=5);assert waiter.returncode==0,err
        received=json.loads(out);data=received['stages']['storyboard']['data']
        assert data['requested_scene_ids']==['one'] and data['scenes'][0]['notes']=='请增加人物'
        data['scenes'][0]['notes']='';workflow.propose(project,'storyboard',{'scenes':data['scenes'],'requested_scene_ids':[]},expected_revision=received['revision'])
        page.wait_for_timeout(4500)
        page.locator('[data-down="0"]').click();page.locator('[data-field="narration"]').first.fill('修改后的旁白');page.locator('#confirm').click();page.wait_for_selector('text=等待 Codex 制作动态样片')
        d=workflow.read(project)['stages']['storyboard']['data']['scenes'];assert d[0]['id']=='two' and d[0]['narration']=='修改后的旁白'
        plan=[{'name':'人物','method':'drawn','source':'分镜人物'}, {'name':'连线','method':'code','source':'分镜关系'}]
        workflow.propose(project,'sample',{'video':'video/sample.mp4','notes':'','processing':True,'comparison_scene_id':'two','comparison_frame':'assets/frame.png','comparison_time':3,'asset_plan':plan,'deviation':'人物姿态略有变化'});page.wait_for_selector('video[src^="/project/"]',timeout=10000)
        page.locator('.media-frame:has(video) .work-loading').wait_for(state='visible',timeout=10000)
        assert page.locator('.media-frame:has(video)').evaluate('(el)=>parseFloat(getComputedStyle(el).borderTopWidth)')>=1
        assert page.locator('#confirm').is_disabled()
        workflow.propose(project,'sample',{'processing':False})
        page.locator('.media-frame:has(video) .work-loading').wait_for(state='hidden',timeout=10000)
        assert page.locator('[data-comparison="sample"] img').count()==2
        page.locator('#confirm').click();page.wait_for_timeout(300);assert workflow.read(project)['active']=='sample'
        page.locator('#sample-accept').check();page.locator('#confirm').click();page.wait_for_selector('text=逐幕还原对照')
        items=[{'scene_id':'two','frame':'assets/frame.png','asset_plan':plan,'deviation':'','notes':''}, {'scene_id':'one','frame':'assets/frame.png','asset_plan':plan,'deviation':'线条有变化','notes':''}]
        workflow.propose(project,'restoration',{'comparisons':items})
        page.wait_for_selector('[data-restore-card="one"] img[alt="还原画面"]',timeout=10000)
        assert page.locator('[data-restore-card="one"] img').count()==2
        page.locator('#confirm').click();page.wait_for_timeout(300);assert workflow.read(project)['active']=='restoration'
        revision=workflow.read(project)['revision']
        waiter=subprocess.Popen([sys.executable,str(root/'scripts/video_master.py'),'wait',str(project),'restoration','--after-revision',str(revision),'--timeout','20'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        page.get_by_text('自动等待已连接',exact=False).wait_for(timeout=10000)
        page.locator('[data-restore-accept="one"]').check()
        page.locator('[data-restore-notes="two"]').fill('调整连线')
        page.locator('[data-restore-request="two"]').click()
        page.locator('[data-restore-card="two"]').get_by_text('已提交，等待处理').wait_for(timeout=5000)
        out,err=waiter.communicate(timeout=5);assert waiter.returncode==0,err
        assert json.loads(out)['stages']['restoration']['data']['requested_scene_ids']==['two']
        data=workflow.read(project)['stages']['restoration']['data'];assert data['requested_scene_ids']==['two'] and data['comparisons'][1]['deviation_accepted']
        data['comparisons'][0]['notes']='';workflow.propose(project,'restoration',{'comparisons':data['comparisons'],'requested_scene_ids':[]},expected_revision=workflow.read(project)['revision'])
        page.wait_for_timeout(4500);page.locator('#confirm').click();page.wait_for_selector('text=等待 Codex 制作完整视频')
        workflow.propose(project,'final',{'video':'video/sample.mp4','notes':''});page.wait_for_selector('video[src^="/project/"]',timeout=10000);page.locator('#confirm').click();page.wait_for_selector('text=故事，已经成片。')
        assert workflow.read(project)['active']=='done';assert not errors,errors
        print('Browser flow PASS: style, brand, review notes, reload, stage gates, reordered narration, sample, final')
        mobile=browser.new_page(viewport={'width':390,'height':844});mobile.goto(url,wait_until='networkidle');assert mobile.locator('body').evaluate('(e)=>e.scrollWidth')<=390;mobile.close()
        print('Mobile layout PASS')
        browser.close()
    finally:
      proc.terminate();proc.wait(timeout=5)
