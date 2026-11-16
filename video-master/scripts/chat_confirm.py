#!/usr/bin/env python3
"""Only after explicit user chat confirmation of this exact stage and revision."""
import argparse
import json
import sys
import workflow

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('project'); p.add_argument('stage', choices=workflow.STAGES); p.add_argument('revision', type=int)
p.add_argument('--accept-deviation', action='store_true', help='仅在用户明确接受样片列出的差异时使用')
p.add_argument('--accept-scene', action='append', default=[], help='仅填写用户明确接受差异的场景 ID，可重复')
a = p.parse_args()
try:
    if a.accept_deviation and a.stage != 'sample': raise workflow.Invalid('样片差异确认仅适用于样片阶段')
    if a.accept_scene and a.stage != 'restoration': raise workflow.Invalid('逐幕差异确认仅适用于还原阶段')
    patch = {}
    if a.accept_deviation: patch['deviation_accepted'] = True
    if a.accept_scene: patch['comparisons'] = [{'scene_id': s, 'deviation_accepted': True} for s in a.accept_scene]
    print(json.dumps(workflow.submit(a.project, a.stage, patch, a.revision, True, origin='chat'), ensure_ascii=False, indent=2))
except (workflow.Invalid, workflow.Conflict, OSError) as e:
    print(f'错误：{e}', file=sys.stderr); sys.exit(1)
