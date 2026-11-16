#!/usr/bin/env python3
"""Synthesize one approved narration file with Xiaomi MiMo using the OS credential store."""
import argparse
import base64
import json
import os
import tempfile
import urllib.error
import urllib.request
from pathlib import Path
import credentials

ENDPOINT='https://api.xiaomimimo.com/v1/chat/completions'
class SpeechError(Exception): pass

def synthesize(text, output, voice='mimo_default', direction=''):
    if not text.strip(): raise SpeechError('旁白文本为空')
    if len(text)>6000: raise SpeechError('旁白过长，请按段落拆分后分别合成')
    key=credentials.load_key()
    if not key: raise SpeechError('未设置 MiMo Key，请先在 Video Master 配音设置中填写。')
    messages=[]
    if direction.strip(): messages.append({'role':'user','content':direction.strip()})
    messages.append({'role':'assistant','content':text.strip()})
    payload={'model':'mimo-v2.5-tts','messages':messages,'audio':{'format':'wav','voice':voice},'stream':False}
    request=urllib.request.Request(ENDPOINT,data=json.dumps(payload,ensure_ascii=False).encode(),headers={'api-key':key,'Content-Type':'application/json'},method='POST')
    try:
        with urllib.request.urlopen(request,timeout=120) as resp:
            raw=resp.read(40*1024*1024+1)
        if len(raw)>40*1024*1024: raise SpeechError('配音响应过大，请缩短旁白段落')
        response=json.loads(raw)
        audio=base64.b64decode(response['choices'][0]['message']['audio']['data'],validate=True)
        if not audio.startswith(b'RIFF') or audio[8:12]!=b'WAVE': raise SpeechError('服务未返回有效的 WAV 音频')
    except urllib.error.HTTPError as e:
        raise SpeechError(f'MiMo 请求失败（HTTP {e.code}），请检查 Key、模型权限和服务额度。') from None
    except (urllib.error.URLError,TimeoutError): raise SpeechError('无法连接 MiMo，请检查网络后重试。') from None
    except (ValueError,KeyError,IndexError,TypeError): raise SpeechError('MiMo 返回的数据不完整，请检查服务状态。') from None
    output=Path(output)
    if output.suffix.lower()!='.wav': raise SpeechError('输出文件应为 .wav')
    output.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix='.mimo-',suffix='.wav',dir=output.parent)
    try:
        with os.fdopen(fd,'wb') as f:f.write(audio)
        os.replace(tmp,output)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--text-file',required=True);p.add_argument('--out',required=True);p.add_argument('--voice',default='mimo_default');p.add_argument('--direction',default='')
    args=p.parse_args()
    try:
        synthesize(Path(args.text_file).read_text(encoding='utf-8'),args.out,args.voice,args.direction)
        print(f'已生成配音：{args.out}')
    except (OSError,credentials.CredentialError,SpeechError) as e:
        print(f'配音失败：{e}',file=__import__('sys').stderr);return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
