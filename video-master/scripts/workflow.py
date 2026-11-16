#!/usr/bin/env python3
"""Persistent Video Master project state and version-bound review gates."""
import copy
import hashlib
import json
import os
import shutil
import tempfile
import time
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
LEGACY_STAGES = ('style', 'styleframe', 'storyboard', 'sample', 'final')
STAGES = ('style', 'styleframe', 'storyboard', 'sample', 'restoration', 'final')
LABELS = {'style': '选择风格', 'styleframe': '风格试图', 'storyboard': '图文分镜', 'sample': '动态样片', 'restoration': '逐幕还原', 'final': '完整视频'}

def stage_order(state):
    # Existing projects retain their original gates and recorded confirmations.
    return STAGES if state.get('schema', 1) >= 2 else LEGACY_STAGES

class Invalid(Exception): pass
class Conflict(Exception): pass

def now(): return datetime.now(timezone.utc).isoformat()
def digest(data): return hashlib.sha256(json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()

def write(project, state):
    project = Path(project)
    fd, temp = tempfile.mkstemp(prefix='.project-', dir=project)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
            f.write('\n'); f.flush(); os.fsync(f.fileno())
        os.replace(temp, project / 'project.json')
    finally:
        if os.path.exists(temp): os.unlink(temp)

def read(project):
    return json.loads((Path(project) / 'project.json').read_text(encoding='utf-8'))

def waiter_status(project):
    """Report only live polling processes, not whether the chat can be awakened."""
    review = Path(project) / 'review'
    for path in review.glob('.wait-*.json'):
        try:
            item = json.loads(path.read_text(encoding='utf-8'))
            if time.time() - item['at'] < 8:
                return {'connected': True, 'stage': item['stage']}
        except (OSError, ValueError, KeyError, TypeError):
            continue
    return {'connected': False, 'stage': None}

@contextmanager
def waiter(project, stage):
    review = Path(project) / 'review'
    token = uuid.uuid4().hex
    path = review / ('.wait-' + token + '.json')
    tmp = review / ('.wait-tmp-' + token)
    def pulse():
        tmp.write_text(json.dumps({'stage': stage, 'at': time.time()}), encoding='utf-8')
        os.replace(tmp, path)
    try:
        pulse()
        yield pulse
    finally:
        path.unlink(missing_ok=True)
        tmp.unlink(missing_ok=True)

@contextmanager
def locked(project):
    with (Path(project) / '.lock').open('a+b') as f:
        if os.name == 'nt':
            import msvcrt
            f.seek(0, os.SEEK_END)
            if f.tell() == 0: f.write(b'0'); f.flush()
            f.seek(0); msvcrt.locking(f.fileno(), msvcrt.LK_LOCK, 1)
            try: yield
            finally: f.seek(0); msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl
            fcntl.flock(f, fcntl.LOCK_EX)
            try: yield
            finally: fcntl.flock(f, fcntl.LOCK_UN)

def initialize(project, story, logo=None):
    project, story = Path(project).resolve(), Path(story).resolve()
    if not story.is_file() or not story.read_text(encoding='utf-8').strip(): raise Invalid('请提供非空的 UTF-8 故事文字文件')
    if project.exists() and any(project.iterdir()): raise Invalid('目标目录非空，请选择新目录')
    default_logo = SKILL / 'assets/brand/company-logo.png'
    source_logo = Path(logo).resolve() if logo else default_logo
    if not source_logo.is_file(): raise Invalid('Logo 文件不存在')
    if source_logo.suffix.lower() not in ('.png', '.jpg', '.jpeg', '.webp'): raise Invalid('Logo 需为 PNG、JPG 或 WEBP')
    project.mkdir(parents=True, exist_ok=True)
    for folder in ('source', 'assets', 'audio', 'video', 'review', 'output'): (project / folder).mkdir(exist_ok=True)
    shutil.copyfile(story, project / 'source' / 'story.md')
    logo_path = 'assets/company-logo' + source_logo.suffix.lower()
    shutil.copyfile(source_logo, project / logo_path)
    state = {'schema': 2, 'revision': 1, 'title': project.name, 'created': now(), 'source': 'source/story.md',
             'brand': {'logo': logo_path, 'default': not bool(logo)}, 'active': 'style',
             'stages': {s: {'status': 'pending', 'data': {}} for s in STAGES}, 'history': []}
    state['stages']['style']['data'] = {'style_id': '', 'notes': ''}
    state['stages']['restoration']['data'] = {'review_video_required': True}
    write(project, state)
    return state

def safe_file(project, relative):
    if not isinstance(relative, str) or not relative or relative.startswith('/') or '\\' in relative: return False
    root = Path(project).resolve(); candidate = (root / relative).resolve()
    return candidate.is_relative_to(root) and candidate.is_file()

def validate_plan(project, plan):
    if not isinstance(plan, list) or not plan: raise Invalid('请先准备本幕素材与代码元素分工')
    for element in plan:
        if not isinstance(element, dict) or not str(element.get('name', '')).strip() or element.get('method') not in ('drawn', 'code', 'existing', 'group') or not str(element.get('source', '')).strip():
            raise Invalid('每项画面元素需要名称、制作方式和参考来源')
        if element.get('asset') and not safe_file(project, element['asset']): raise Invalid('分工中引用的素材文件不存在')

def review_paths(stage, data):
    paths = []
    plans = []
    if stage == 'sample':
        paths.extend([data.get('video'), data.get('comparison_frame')]); plans.append(data.get('asset_plan', []))
    elif stage == 'restoration':
        for c in data.get('comparisons', []):
            paths.extend([c.get('frame'), c.get('video')]); plans.append(c.get('asset_plan', []))
    for plan in plans:
        if isinstance(plan, list): paths.extend(e.get('asset') for e in plan if isinstance(e, dict))
    return [p for p in paths if isinstance(p, str) and p]

def review_hashes(project, stage, data):
    return {p: hashlib.sha256((Path(project) / p).read_bytes()).hexdigest() for p in review_paths(stage, data) if safe_file(project, p)}

def validate(project, stage, data, state):
    if data.get('processing'): raise Invalid('Codex 正在重新制作本阶段，请等待新版完成后再确认')
    if stage == 'style' and data.get('style_id') not in ('business-line-art', 'paper-story', 'typographic-motion'): raise Invalid('请选择一种风格')
    if stage != 'style' and str(data.get('notes', '')).strip(): raise Invalid('当前有待处理的修改意见，请先保存并让 Codex 处理')
    if stage == 'styleframe' and not safe_file(project, data.get('image')): raise Invalid('当前项目缺少风格试图，请等待 Codex 制作')
    if stage == 'storyboard':
        scenes = data.get('scenes')
        if not isinstance(scenes, list) or not scenes: raise Invalid('尚无分镜，请等待 Codex 制作')
        ids = [s.get('id') for s in scenes if isinstance(s, dict)]
        if len(ids) != len(scenes) or not all(ids) or len(set(ids)) != len(ids): raise Invalid('每幕需要唯一的场景编号')
        if any(not str(s.get('narration', '')).strip() or not safe_file(project, s.get('image')) for s in scenes): raise Invalid('每幕都需要旁白和项目内的场景图')
        if any(str(s.get('notes', '')).strip() for s in scenes): raise Invalid('有场景修改意见尚未处理，请先保存并让 Codex 处理')
    if stage in ('sample', 'final') and not safe_file(project, data.get('video')): raise Invalid('当前项目缺少视频，请等待 Codex 制作')
    if state.get('schema', 1) >= 2 and stage == 'sample':
        ids = {s['id'] for s in state['stages']['storyboard']['data']['scenes']}
        if data.get('comparison_scene_id') not in ids or not safe_file(project, data.get('comparison_frame')): raise Invalid('样片需提供对应分镜与视频全景对照')
        t = data.get('comparison_time')
        if isinstance(t, bool) or not isinstance(t, (int, float)) or not 0 <= t < float('inf'): raise Invalid('请提供视频全景截图对应的时间')
        validate_plan(project, data.get('asset_plan'))
        if not isinstance(data.get('deviation'), str): raise Invalid('请说明样片与分镜的差异；无差异时填写空字符串')
        if data['deviation'].strip() and data.get('deviation_accepted') is not True: raise Invalid('样片存在待确认差异，请先处理或明确接受')
    if stage == 'restoration':
        scenes = state['stages']['storyboard']['data']['scenes']
        ids = [s['id'] for s in scenes]
        comparisons = data.get('comparisons')
        if not isinstance(comparisons, list) or any(not isinstance(c, dict) for c in comparisons): raise Invalid('请先准备逐幕还原对照')
        actual = [c.get('scene_id') for c in comparisons]
        if len(actual) != len(ids) or any(not isinstance(x, str) for x in actual) or set(actual) != set(ids): raise Invalid('每幕均需一份还原对照')
        for c in comparisons:
            if not safe_file(project, c.get('frame')): raise Invalid('每幕均需项目内的真实还原画面')
            if data.get('review_video_required') and not safe_file(project, c.get('video')): raise Invalid('每幕均需项目内的实际视频片段')
            validate_plan(project, c.get('asset_plan'))
            if not isinstance(c.get('deviation'), str): raise Invalid('请说明每幕与分镜的差异；无差异时填写空字符串')
            if str(c.get('notes', '')).strip(): raise Invalid('有场景修改意见尚未处理')
            if c['deviation'].strip() and c.get('deviation_accepted') is not True: raise Invalid('有画面差异尚未处理或明确接受')
    if state.get('schema', 1) >= 2 and stage in ('sample', 'restoration') and data.get('_review_files') != review_hashes(project, stage, data):
        raise Invalid('对照画面或素材已变化，请等待 Codex 更新并重新确认')

def material_digest(project, stage, data, brand):
    paths = ['source/story.md']
    if stage == 'style' and brand.get('logo'): paths.append(brand['logo'])
    if stage == 'styleframe' and data.get('image'): paths.append(data['image'])
    if stage == 'storyboard': paths += [s.get('image', '') for s in data.get('scenes', [])]
    if stage in ('sample', 'final') and data.get('video'): paths.append(data['video'])
    plans = []
    if stage == 'sample' and data.get('comparison_frame'):
        paths.append(data['comparison_frame']); plans.append(data.get('asset_plan', []))
    if stage == 'restoration':
        for c in data.get('comparisons', []):
            paths.append(c.get('frame', ''));
            if c.get('video'): paths.append(c['video'])
            plans.append(c.get('asset_plan', []))
    for plan in plans:
        if isinstance(plan, list):
            paths.extend(e['asset'] for e in plan if isinstance(e, dict) and e.get('asset'))
    files = {}
    for path in paths:
        if not safe_file(project, path): return None
        files[path] = hashlib.sha256((Path(project) / path).read_bytes()).hexdigest()
    return digest({'data': data, 'files': files, 'brand': brand if stage == 'style' else None})

def history_event(state, stage, kind, data=None):
    state['history'].append({'at': now(), 'stage': stage, 'event': kind, 'revision': state['revision'], 'digest': digest(data) if data is not None else None, 'snapshot': copy.deepcopy(data) if data is not None else None})

def upgrade(project, revision):
    """Opt in a legacy project without changing or fabricating media/approvals."""
    with locked(project):
        state = read(project)
        if revision != state['revision']: raise Conflict('项目版本已变化，请重新读取后再升级')
        if state.get('schema', 1) != 1: raise Invalid('该项目已使用新的还原流程')
        active = state['active']
        state['schema'] = 2
        state['stages']['restoration'] = {'status': 'pending', 'data': {}}
        sample = state['stages']['sample']
        if active in ('sample', 'final', 'done'):
            state['active'] = 'sample'
            sample['status'] = 'draft'
            sample['needs_update'] = True
        elif sample['status'] != 'pending':
            sample['status'] = 'stale'
            sample['needs_update'] = True
        final = state['stages']['final']
        if final['status'] != 'pending':
            final['status'] = 'stale'
            final['needs_update'] = True
        state['revision'] += 1
        history_event(state, state['active'], 'restoration_workflow_enabled', {'previous_schema': 1})
        write(project, state)
        return state

def invalidate(state, stage):
    order = stage_order(state)
    index = order.index(stage)
    for later in order[index + 1:]:
        item = state['stages'][later]
        if item['status'] != 'pending':
            item['status'] = 'stale'
            item['needs_update'] = True
    state['active'] = stage

def submit(project, stage, patch, revision, confirm=False, origin='page'):
    with locked(project):
        state = read(project)
        if revision != state['revision']: raise Conflict('页面版本已变化，请刷新后重新操作')
        order = stage_order(state)
        if stage != state['active'] or stage not in order: raise Conflict('当前阶段已变化，请刷新')
        if not isinstance(patch, dict): raise Invalid('数据格式不正确')
        allowed = {'style': ('style_id', 'notes'), 'styleframe': ('notes',), 'storyboard': ('scenes', 'notes', 'request_scene', 'request_overall'), 'sample': ('notes', 'deviation_accepted'), 'restoration': ('comparisons', 'notes', 'request_scene', 'request_overall'), 'final': ('notes',)}[stage]
        if set(patch) - set(allowed): raise Invalid('页面不能修改制作资源路径')
        patch = dict(patch)
        request_scene = patch.pop('request_scene', None)
        request_overall = patch.pop('request_overall', False)
        if confirm and (request_scene or request_overall): raise Invalid('请先提交修改意见并等待处理')
        data = copy.deepcopy(state['stages'][stage]['data'])
        if stage == 'storyboard' and 'scenes' in patch:
            old = {s['id']: s for s in data.get('scenes', [])}
            incoming = patch['scenes']
            if not isinstance(incoming, list) or any(not isinstance(s, dict) for s in incoming): raise Invalid('场景格式不正确')
            ids = [s.get('id') for s in incoming]
            if len(set(ids)) != len(ids) or not set(ids).issubset(old): raise Invalid('场景编号不匹配')
            scenes = []
            for s in incoming:
                clean = copy.deepcopy(old[s['id']])
                for key in ('narration', 'description', 'notes'):
                    if key in s and isinstance(s[key], str): clean[key] = s[key]
                scenes.append(clean)
            patch = dict(patch, scenes=scenes)
        if stage == 'sample' and 'deviation_accepted' in patch and not isinstance(patch['deviation_accepted'], bool): raise Invalid('差异确认必须为布尔值')
        if stage == 'restoration' and 'comparisons' in patch:
            old = {c['scene_id']: c for c in data.get('comparisons', [])}
            incoming = patch['comparisons']
            if not isinstance(incoming, list) or any(not isinstance(c, dict) for c in incoming): raise Invalid('对照格式不正确')
            ids = [c.get('scene_id') for c in incoming]
            if any(not isinstance(i, str) for i in ids) or len(set(ids)) != len(ids) or not set(ids).issubset(old): raise Invalid('场景编号不匹配')
            merged = copy.deepcopy(data.get('comparisons', []))
            by_id = {c['scene_id']: c for c in merged}
            for c in incoming:
                if set(c) - {'scene_id', 'notes', 'deviation_accepted'}: raise Invalid('页面不能修改制作资源路径')
                if 'notes' in c:
                    if not isinstance(c['notes'], str): raise Invalid('意见格式不正确')
                    by_id[c['scene_id']]['notes'] = c['notes']
                if 'deviation_accepted' in c:
                    if not isinstance(c['deviation_accepted'], bool): raise Invalid('差异确认必须为布尔值')
                    by_id[c['scene_id']]['deviation_accepted'] = c['deviation_accepted']
            patch = dict(patch, comparisons=merged)
        data.update(patch)
        if stage in ('storyboard', 'restoration'):
            by_id = ({s['id']: s for s in data.get('scenes', [])} if stage == 'storyboard' else {c['scene_id']: c for c in data.get('comparisons', [])})
            requested = [sid for sid in data.get('requested_scene_ids', []) if sid in by_id and str(by_id[sid].get('notes', '')).strip()]
            if request_scene is not None:
                if not isinstance(request_scene, str) or request_scene not in by_id or not str(by_id[request_scene].get('notes', '')).strip(): raise Invalid('请先在本幕填写修改意见')
                if request_scene not in requested: requested.append(request_scene)
            if request_overall and not str(data.get('notes', '')).strip(): raise Invalid('请先填写整体修改意见')
            if requested or 'requested_scene_ids' in data: data['requested_scene_ids'] = requested
            if request_overall: data['overall_requested'] = True
            elif not str(data.get('notes', '')).strip() and 'overall_requested' in data: data['overall_requested'] = False
        if confirm:
            if state['stages'][stage].get('needs_update'): raise Invalid('上游内容已修改，请等待 Codex 更新本阶段后再确认')
            for previous in order[:order.index(stage)]:
                item = state['stages'][previous]
                if item.get('status') != 'confirmed' or item.get('material_digest') != material_digest(project, previous, item['data'], state['brand']):
                    raise Invalid(f'{LABELS[previous]}的已确认内容或文件发生变化，请返回该阶段重新确认')
            validate(project, stage, data, state)
        changed = data != state['stages'][stage]['data']
        if changed: invalidate(state, stage)
        state['stages'][stage]['data'] = data
        state['revision'] += 1
        if confirm:
            state['stages'][stage]['status'] = 'confirmed'
            state['stages'][stage]['material_digest'] = material_digest(project, stage, data, state['brand'])
            history_event(state, stage, 'confirmed_chat' if origin == 'chat' else 'confirmed', data)
            i = order.index(stage)
            state['active'] = order[i + 1] if i + 1 < len(order) else 'done'
        else:
            state['stages'][stage]['status'] = 'draft'
            history_event(state, stage, 'scene_revision_requested' if request_scene else ('overall_revision_requested' if request_overall else 'draft_saved'), data)
        write(project, state)
        return state

def propose(project, stage, data, expected_revision=None):
    with locked(project):
        state = read(project)
        if expected_revision is not None and state['revision'] != expected_revision: raise Conflict('用户在制作期间更新了项目，请读取最新内容后再发布')
        if stage != state['active']: raise Conflict('只能更新当前阶段，请先处理确认或返回')
        if not isinstance(data, dict): raise Invalid('提案必须是 JSON 对象')
        current = state['stages'][stage]['data']
        data = copy.deepcopy(data)
        stale = state['stages'][stage].get('needs_update', False)
        if stage == 'sample' and state.get('schema', 1) >= 2:
            fields = ('video', 'comparison_scene_id', 'comparison_frame', 'comparison_time', 'asset_plan', 'deviation')
            candidate = {**current, **data}
            hashes = review_hashes(project, stage, candidate)
            changed = stale or any(k in data and data[k] != current.get(k) for k in fields) or hashes != current.get('_review_files', {})
            data['deviation_accepted'] = False if changed else current.get('deviation_accepted', False)
            data['_review_files'] = hashes
        if stage == 'restoration':
            items = data.get('comparisons', current.get('comparisons', []))
            if not isinstance(items, list) or any(not isinstance(c, dict) or not isinstance(c.get('scene_id'), str) for c in items): raise Invalid('对照格式不正确')
            valid_ids = {s['id'] for s in state['stages']['storyboard']['data'].get('scenes', [])}
            ids = [c['scene_id'] for c in items]
            if len(ids) != len(set(ids)) or not set(ids).issubset(valid_ids): raise Invalid('对照场景编号不匹配')
            old = {c['scene_id']: c for c in current.get('comparisons', []) if c.get('scene_id') in valid_ids}
            updates = {c['scene_id']: c for c in items}
            merged = []
            for sid in dict.fromkeys([*old, *ids]):
                item = updates.get(sid, {'scene_id': sid})
                previous = old.get(item['scene_id'], {})
                new = {**previous, **item}
                if previous.get('notes') and new.get('notes') != previous['notes']:
                    if sid not in current.get('requested_scene_ids', []):
                        new['notes'] = previous['notes']
                    elif expected_revision is None:
                        raise Conflict('处理场景意见时请提供读取时的版本')
                new_hashes = review_hashes(project, 'restoration', {'comparisons': [new]})
                previous_hashes = current.get('_review_files', {})
                changed = stale or any(new.get(k) != previous.get(k) for k in ('frame', 'video', 'asset_plan', 'deviation')) or any(previous_hashes.get(p) != h for p, h in new_hashes.items())
                new['deviation_accepted'] = False if changed else previous.get('deviation_accepted', False)
                merged.append(new)
            data['comparisons'] = merged
            if 'requested_scene_ids' in data:
                remaining = [c['scene_id'] for c in merged if c.get('notes') and c['scene_id'] in current.get('requested_scene_ids', [])]
                data['requested_scene_ids'] = list(dict.fromkeys([*data['requested_scene_ids'], *remaining]))
        if stage == 'restoration':
            data['_review_files'] = review_hashes(project, stage, {**current, **data})
        invalidate(state, stage)
        state['stages'][stage]['data'] = {**current, **data}
        state['stages'][stage]['status'] = 'draft'
        state['stages'][stage]['needs_update'] = False
        state['revision'] += 1
        history_event(state, stage, 'agent_proposal', state['stages'][stage]['data'])
        write(project, state)
        return state

def reopen(project, stage, revision):
    with locked(project):
        state = read(project)
        if revision != state['revision']: raise Conflict('页面版本已变化，请刷新后重新操作')
        if stage not in stage_order(state) or state['stages'][stage]['status'] not in ('confirmed', 'stale'): raise Invalid('该阶段尚未确认')
        invalidate(state, stage)
        state['stages'][stage]['status'] = 'draft'
        state['revision'] += 1
        history_event(state, stage, 'reopened')
        write(project, state)
        return state

def replace_brand(project, revision, filename=None, content=None):
    with locked(project):
        state = read(project)
        if state['revision'] != revision: raise Conflict('页面版本已变化，请刷新')
        if state['active'] != 'style': raise Invalid('请先返回风格阶段，再更换品牌素材')
        if filename is None:
            state['brand'] = {'logo': None, 'default': False}
        else:
            suffix = Path(filename).suffix.lower()
            magic = ((suffix == '.png' and content.startswith(b'\x89PNG\r\n\x1a\n')) or
                     (suffix in ('.jpg', '.jpeg') and content.startswith(b'\xff\xd8\xff')) or
                     (suffix == '.webp' and content.startswith(b'RIFF') and content[8:12] == b'WEBP'))
            if not magic or len(content) > 5 * 1024 * 1024: raise Invalid('Logo 请使用小于 5 MB 的 PNG、JPG 或 WEBP 图片')
            path = 'assets/company-logo' + suffix
            (Path(project) / path).write_bytes(content)
            state['brand'] = {'logo': path, 'default': False}
        invalidate(state, 'style')
        state['stages']['style']['status'] = 'draft'
        state['revision'] += 1
        history_event(state, 'style', 'brand_changed', state['brand'])
        write(project, state)
        return state
