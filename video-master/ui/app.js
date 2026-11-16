const labels={style:'选择风格',styleframe:'风格试图',storyboard:'图文分镜',sample:'动态样片',restoration:'逐幕还原',final:'完整视频'};
let stages=[]; const app=document.querySelector('#app'), steps=document.querySelector('#steps');
let state, draft={}, dirty=false, seenRemote=false, agentStatus={connected:false,stage:null};
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const media=p=>'/project/'+String(p||'').split('/').map(encodeURIComponent).join('/')+'?v='+state.revision;
function toast(t){let el=document.querySelector('#toast');el.textContent=t;el.classList.add('show');setTimeout(()=>el.classList.remove('show'),3200)}
async function api(path,body){let r=await fetch(path,body?{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}:{});let result=await r.json();if(!r.ok)throw Error(result.error||'请求失败');return result}
function header(en,title,desc,n){return `<div class="heading-row"><div><span class="eyebrow">${en}</span><h1>${title}</h1><p>${desc}</p></div><div class="phase">${String(n).padStart(2,'0')} <small>/ ${String(stages.length).padStart(2,'0')}</small></div></div>`}
function showState(s){state=s;stages=Object.keys(labels).filter(k=>state.stages[k]);draft=structuredClone(state.stages[state.active]?.data||{});dirty=false;seenRemote=false;render()}
function mediaFrame(content,sceneId='',kind=''){
 const dots=Array.from({length:9},()=>'<span class="work-dot"></span>').join('');
 return `<div class="media-frame ${kind==='video'?'media-video':''}"${sceneId?` data-scene-id="${esc(sceneId)}"`:''}>${content}<div class="work-loading" role="status" aria-live="polite" hidden><div class="work-loading-content"><div class="work-grid" aria-hidden="true">${dots}</div><strong>正在制作</strong><span>完成后会自动更新</span></div></div></div>`;
}
function syncProcessing(latest){
 if(!latest || latest.active!==state?.active)return;
 const d=latest.stages[latest.active]?.data||{}, targets=d.processing_scene_ids;
 app.querySelectorAll('.media-frame').forEach(frame=>{
  const busy=!!d.processing && (!['storyboard','restoration'].includes(latest.active) || !Array.isArray(targets) || targets.length===0 || !frame.dataset.sceneId || targets.includes(frame.dataset.sceneId));
  frame.querySelector('.work-loading').hidden=!busy;
  frame.setAttribute('aria-busy',String(busy));
 });
 document.querySelector('#confirm').disabled=!!d.processing;
}
function render(){document.querySelector('#project-title').textContent=state.title;let stage=state.active;document.querySelector('#crumb').textContent=labels[stage]||'已完成';
 steps.innerHTML=stages.map((key,i)=>{let status=state.stages[key].status;return `<button class="step ${key===stage?'active':''} ${status==='confirmed'?'done':''}" data-step="${key}" ${status!=='confirmed'&&status!=='stale'?'disabled':''}><span class="num">${status==='confirmed'?'✓':String(i+1).padStart(2,'0')}</span><span>${labels[key]}</span></button>`}).join('');
 steps.querySelectorAll('[data-step]').forEach(b=>b.onclick=async()=>{if(b.dataset.step===stage)return;if(!confirm('返回此阶段会使后续确认失效。继续吗？'))return;try{showState(await api('/api/reopen',{stage:b.dataset.step,revision:state.revision}));toast('已返回，后续阶段需要重新确认')}catch(e){toast(e.message)}});
 let confirmBtn=document.querySelector('#confirm');confirmBtn.style.display=stage==='done'?'none':'';confirmBtn.disabled=false;
 if(stage==='style')renderStyle();else if(stage==='styleframe')renderSingle('styleframe');else if(stage==='storyboard')renderStoryboard();else if(stage==='restoration')renderRestoration();else if(stage==='sample'||stage==='final')renderSingle(stage);else renderDone();
 if(stage!=='done')syncProcessing(state);
 if(stage!=='done'&&state.stages[stage].needs_update) app.insertAdjacentHTML('afterbegin','<div class="notice">上游内容已有变化。本阶段保留旧内容供参考，请让 Codex 更新后再确认。</div>');
 app.querySelector('#save')?.addEventListener('click',submitChanges);
 app.querySelectorAll('textarea, input[type=checkbox]').forEach(el=>el.addEventListener('input',()=>{dirty=true;collect()}));
}
function renderDone(){
 const video=state.stages.final?.data?.video;
 const player=video?`<video class="done-video" controls playsinline preload="metadata" src="${media(video)}" aria-label="已确认的最终视频"></video>`:'<div class="empty"><div><strong>未找到成片</strong>请返回完整视频阶段检查项目文件。</div></div>';
 const actions=video?`<div class="done-actions"><a class="button primary done-download" href="${media(video)}" download>下载视频 <span aria-hidden="true">↓</span></a><button class="button done-copy" id="copy-final-path" disabled>复制本机路径</button><div class="done-file"><span>本机文件</span><code id="final-file-path">正在读取路径…</code></div></div>`:'';
 app.innerHTML=`<section class="done-screen"><div class="done-intro"><h1>成片已确认</h1><p>观看、下载或复制本机路径</p></div><div class="done-result"><div class="done-player">${player}</div>${actions}</div></section>`;
 if(video){
  const button=app.querySelector('#copy-final-path'), pathEl=app.querySelector('#final-file-path');
  api('/api/final-file').then(({path})=>{
   if(!button.isConnected)return;
   pathEl.textContent=path||'文件不可用';
   if(!path)return;
   button.disabled=false;
   button.onclick=async()=>{try{await navigator.clipboard.writeText(path);toast('本机路径已复制')}catch(e){toast('复制失败，请手动选择下方路径')}};
  }).catch(()=>{if(button.isConnected)pathEl.textContent='无法读取本机路径'});
 }
}
function renderStyle(){let logo=state.brand.logo?`<img src="${media(state.brand.logo)}" alt="当前品牌 Logo">`:'<span class="helper">未使用 Logo</span>';
 app.innerHTML=header('01 / CREATIVE DIRECTION','先选一种视觉语言','从风格范例出发，再为你的故事生成专属试图。',1)+`<div class="section-head"><h2>选择一个风格</h2><span>可在后续试图中继续调整</span></div><div class="style-grid">
 <article class="style-card ${draft.style_id==='business-line-art'?'selected':''}"><img class="preview" src="/styles/business-line-art/poster.png" alt="商务线稿风格参考"><div class="card-content"><div class="card-line"><h3>商务线稿讲解</h3><span class="badge">已有项目验证</span></div><p>手绘线条、清晰关系与轻盈动效，适合业务、方案和流程讲解。</p><div class="card-actions"><button class="text-link" data-preview>▶ 查看动态范例</button><button class="select-style" data-style="business-line-art">${draft.style_id==='business-line-art'?'✓ 已选择':'选择此风格'}</button></div></div></article>
 <article class="style-card ${draft.style_id==='paper-story'?'selected':''}"><img class="preview" src="/styles/paper-story/poster.svg" alt="纸片拼贴概念示意"><div class="card-content"><div class="card-line"><h3>纸片拼贴故事</h3><span class="badge concept">概念示例 · 未验证</span></div><p>暖纸、柔和色块与叠放感，适合有温度的人物与品牌故事。</p><div class="card-actions"><span class="helper">示意图，无已验证动画</span><button class="select-style" data-style="paper-story">${draft.style_id==='paper-story'?'✓ 已选择':'选择此风格'}</button></div></div></article></div>
 <div class="section-head"><h2>让风格属于你的项目</h2><span>这些设置会随项目保存</span></div><div class="settings"><section class="panel"><label class="label" for="style-notes">风格补充说明</label><textarea id="style-notes" rows="3" placeholder="例如：人物穿公司工服，画面更简洁……">${esc(draft.notes)}</textarea><div class="scene-request"><button class="button scene-submit" id="save">修改实施</button><span class="helper">保留基础风格，也可以用自己的语言描述调整。</span></div></section><section class="panel"><span class="label">项目品牌素材</span><div class="brand-row"><div class="logo-box">${logo}</div><div><div class="helper">${state.brand.default?'已带入公司默认 Logo':'当前项目素材'}</div><div class="inline-actions"><label class="text-link" for="logo-upload">替换 Logo</label><button class="text-link" id="remove-logo">移除</button><input id="logo-upload" type="file" accept="image/png,image/jpeg,image/webp" hidden></div></div></div><div class="helper" style="margin-top:12px">支持 PNG、JPG、WEBP；也可不使用 Logo。</div></section></div>`;
 app.querySelectorAll('[data-style]').forEach(b=>b.onclick=()=>{collect();draft.style_id=b.dataset.style;dirty=true;render()});
 app.querySelector('[data-preview]').onclick=()=>{let d=document.querySelector('#story-dialog');d.innerHTML='<div class="dialog-head"><div><span class="eyebrow">STYLE IN MOTION</span><h2>商务线稿 · 动态范例</h2></div><button class="close" aria-label="关闭">×</button></div><video controls playsinline style="width:100%" src="/styles/business-line-art/preview.mp4"></video><p class="helper">现有项目的无声片段，用于观察画风和动效。</p>';d.querySelector('.close').onclick=()=>d.close();d.showModal()};
 app.querySelector('#remove-logo').onclick=()=>brand(null,null);
 app.querySelector('#logo-upload').onchange=async e=>{let f=e.target.files[0];if(!f)return;let buf=await f.arrayBuffer(), arr=new Uint8Array(buf), binary='';for(let i=0;i<arr.length;i+=32768)binary+=String.fromCharCode(...arr.subarray(i,i+32768));await brand(f.name,btoa(binary))};
}
async function brand(filename,content){try{if(dirty){let saved=await api('/api/save',{stage:state.active,revision:state.revision,data:collect()});showState(saved)}showState(await api('/api/brand',{revision:state.revision,filename,content}));toast(filename?'Logo 已替换':'已移除 Logo')}catch(e){toast(e.message)}}
function renderSingle(stage){let map={styleframe:['02 / STYLE FRAME','看看故事的样子','先用当前故事做一张试图，确定视觉方向。','image','风格试图'],sample:['04 / MOTION SAMPLE','让画面动起来','确认一幕的画风、动作、旁白和节奏，再扩展全片。','video','动态样片'],final:[`${String(stages.indexOf('final')+1).padStart(2,'0')} / FINAL REVIEW`,'观看完整视频','检查故事、声音与场景衔接，记录最后的修改。','video','完整视频']};let [en,title,desc,type,label]=map[stage];let url=draft[type];let visual=url?(type==='image'?`<img src="${media(url)}" alt="当前故事风格试图">`:`<video controls playsinline src="${media(url)}"></video>`):`<div class="empty"><div><strong>等待 Codex 制作${label}</strong>Codex 会根据已确认的内容和意见准备。<br>如果 Codex 对话已经结束，请回到聊天发送“继续”。</div></div>`;
 app.innerHTML=header(en,title,desc,stages.indexOf(stage)+1)+`<div class="media-panel"><section class="panel">${mediaFrame(visual,'',type)}${stage==='sample'&&state.schema>=2?sampleComparison():''}</section><section class="panel"><span class="eyebrow">REVIEW NOTES</span><h2 style="font-size:17px">你的想法</h2><p class="helper">把需要修改的地方写在这里，点击“修改实施”后由 Codex 继续处理。</p><label class="label" for="review-notes">修改意见</label><textarea id="review-notes" rows="7" placeholder="例如：背景再留白一些，人物表情更自然……">${esc(draft.notes)}</textarea><div class="scene-request"><button class="button scene-submit" id="save">修改实施</button></div><p class="helper">只有点击“确认并继续”才会进入下一阶段。</p></section></div>`;
}
function planDetails(plan){
 if(!Array.isArray(plan)||!plan.length)return '';
 const methods={drawn:'绘画素材',code:'代码元素',existing:'已有素材',group:'整体保留'};
 return `<details class="plan-details"><summary>查看素材与代码分工</summary><ul>${plan.map(e=>`<li><strong>${esc(e.name)}</strong> · ${esc(methods[e.method]||e.method)}<span>${esc(e.source)}</span></li>`).join('')}</ul></details>`;
}
function comparisonImages(reference,frame,sceneId='',video=''){
 const before=reference?`<img src="${media(reference)}" alt="已确认分镜图">`:'<div class="empty compare-empty">等待分镜图</div>';
 const after=video?`<video controls playsinline preload="metadata" ${frame?`poster="${media(frame)}"`:''} src="${media(video)}" aria-label="本幕视频片段"></video>`:frame?`<img src="${media(frame)}" alt="还原画面">`:'<div class="empty compare-empty">等待还原画面</div>';
 return `<div class="comparison-grid"><div><span class="comparison-label">已确认分镜</span><div class="comparison-image">${before}</div></div><div><span class="comparison-label">${video?'实际视频片段（含声音）':'制作后的画面'}</span>${mediaFrame(after,sceneId,video?'video':'')}</div></div>`;
}
function deviationReview(deviation,accepted,checkbox){
 if(typeof deviation!=='string')return '<p class="helper">还原差异待说明。</p>';
 if(!deviation.trim())return '<p class="helper">制作记录：未列出差异，请结合画面核对。</p>';
 return `<div class="deviation"><strong>需要你留意的差异</strong><p>${esc(deviation)}</p><label><input type="checkbox" ${checkbox} ${accepted?'checked':''}> 我了解并接受这处差异</label></div>`;
}
function sampleComparison(){
 const scene=(state.stages.storyboard.data.scenes||[]).find(s=>s.id===draft.comparison_scene_id);
 if(!scene && !draft.comparison_frame)return '<div class="sample-comparison"><p class="helper">样片完成后，这里会并排展示已确认分镜和视频中的对应全景。</p></div>';
 return `<section class="sample-comparison" data-comparison="sample"><div class="comparison-heading"><h3>分镜还原对照</h3><span>${esc(scene?.title||draft.comparison_scene_id||'')} · ${Number.isFinite(draft.comparison_time)?esc(draft.comparison_time)+' 秒':''}</span></div>${comparisonImages(scene?.image,draft.comparison_frame)}${deviationReview(draft.deviation,draft.deviation_accepted,'id="sample-accept"')}${planDetails(draft.asset_plan)}</section>`;
}
function renderRestoration(){
 const scenes=state.stages.storyboard.data.scenes||[], byId=new Map((draft.comparisons||[]).map(c=>[c.scene_id,c]));
 app.innerHTML=header('05 / SCENE REVIEW','逐幕还原对照','逐幕播放视频，对照分镜检查入场、连线、运镜、声音和画面关系。',stages.indexOf('restoration')+1)+`<div class="section-head"><h2>逐幕检查</h2><span>${scenes.length} 幕 · 可在对应卡片提出修改</span></div>`+
 (scenes.length?scenes.map((scene,i)=>{const c=byId.get(scene.id);return `<article class="panel restore-card" data-restore-card="${esc(scene.id)}"><div class="comparison-heading"><div><span class="mono">SCENE ${String(i+1).padStart(2,'0')} / ${esc(scene.id)}</span><h3>${esc(scene.title||'场景 '+(i+1))}</h3></div></div>${comparisonImages(scene.image,c?.frame,scene.id,c?.video)}${c?`${deviationReview(c.deviation,c.deviation_accepted,`data-restore-accept="${esc(scene.id)}"`)}${planDetails(c.asset_plan)}<label class="label" for="restore-notes-${i}">本幕修改意见</label><textarea id="restore-notes-${i}" data-restore-notes="${esc(scene.id)}" rows="2" placeholder="例如：保留分镜里员工旁的消息框">${esc(c.notes)}</textarea><div class="scene-request"><button class="button scene-submit" data-restore-request="${esc(scene.id)}">修改实施</button><span class="helper">${(draft.requested_scene_ids||[]).includes(scene.id)?'已提交，等待处理':''}</span></div>`:'<p class="helper">等待 Codex 制作逐幕还原画面。</p>'}</article>`}).join(''):'<div class="empty">等待 Codex 制作逐幕还原画面</div>')+`<section class="panel overall-review"><label class="label" for="review-notes">整体修改意见</label><p class="overall-review-hint">适用于全部画面的修改；单幕调整请在对应画面中填写。</p><textarea id="review-notes" rows="2" placeholder="对所有场景的还原提出修改意见">${esc(draft.notes)}</textarea><div class="scene-request"><button class="button scene-submit" id="restore-overall">修改实施</button><span class="helper">${draft.overall_requested?'已提交，等待处理':''}</span></div></section>`;
 app.querySelectorAll('[data-restore-request]').forEach(b=>b.onclick=async()=>{let payload=collect(),id=b.dataset.restoreRequest,c=draft.comparisons?.find(x=>x.scene_id===id);if(!c?.notes?.trim()){toast('请先填写本幕修改意见');return}try{payload.request_scene=id;showState(await api('/api/save',{stage:state.active,revision:state.revision,data:payload}));toast('本幕意见已提交')}catch(e){toast(e.message)}});
 app.querySelector('#restore-overall').onclick=async()=>{let payload=collect();if(!payload.notes.trim()){toast('请先填写整体修改意见');return}try{payload.request_overall=true;showState(await api('/api/save',{stage:state.active,revision:state.revision,data:payload}));toast('整体意见已提交')}catch(e){toast(e.message)}};
}
function renderStoryboard(){let scenes=draft.scenes||[];app.innerHTML=header('03 / STORYBOARD','逐幕确认故事','查看画面、调整旁白与顺序，留下需要修改的意见。',3)+`<div class="section-head"><h2>故事分镜</h2><span>${scenes.length} 幕 · 可调整顺序</span></div>`+(scenes.length?scenes.map((s,i)=>`<article class="panel scene-card"><div><div class="scene-controls"><span class="mono">SCENE ${String(i+1).padStart(2,'0')} / ${esc(s.id)}</span><button data-up="${i}" aria-label="上移第${i+1}幕">↑</button><button data-down="${i}" aria-label="下移第${i+1}幕">↓</button><button data-delete="${i}">删除</button></div>${mediaFrame(s.image?`<img src="${media(s.image)}" alt="第${i+1}幕场景图">`:'<div class="empty">等待场景图</div>',s.id)}</div><div><h3>${esc(s.title||'场景 '+(i+1))}</h3><label class="label">旁白稿</label><textarea data-field="narration" data-index="${i}" rows="3">${esc(s.narration)}</textarea><label class="label">画面说明</label><textarea data-field="description" data-index="${i}" rows="2">${esc(s.description)}</textarea><label class="label">本幕修改意见</label><textarea data-field="notes" data-index="${i}" rows="2" placeholder="告诉 Codex 哪些地方需要调整">${esc(s.notes)}</textarea><div class="scene-request"><button class="button scene-submit" data-request="${i}">修改实施</button><span class="helper">${(draft.requested_scene_ids||[]).includes(s.id)?'已提交，等待处理':''}</span></div></div></article>`).join(''):mediaFrame('<div class="empty"><div><strong>等待 Codex 制作图文分镜</strong>完成风格试图确认后，Codex 会准备每幕画面和旁白。</div></div>'))+`<section class="panel overall-review"><label class="label" for="review-notes">整体修改意见</label><p class="overall-review-hint">适用于全部画面的修改；单幕调整请在对应画面中填写。</p><textarea id="review-notes" rows="2" placeholder="例如：整体节奏更紧凑，第三幕和第四幕衔接更自然……">${esc(draft.notes)}</textarea><div class="scene-request"><button class="button scene-submit" id="request-overall">修改实施</button><span class="helper">${draft.overall_requested?'已提交，等待处理':''}</span></div></section>`;
 app.querySelectorAll('[data-request]').forEach(b=>b.onclick=async()=>{let payload=collect(),i=Number(b.dataset.request),s=draft.scenes[i];if(!s?.notes?.trim()){toast('请先填写本幕修改意见');return}try{payload.request_scene=s.id;let linked=agentStatus.connected&&agentStatus.stage===state.active;showState(await api('/api/save',{stage:state.active,revision:state.revision,data:payload}));toast(linked?'本幕意见已提交，Codex 将处理':'本幕意见已保存，等待 Codex 连接')}catch(e){toast(e.message)}});
 app.querySelector('#request-overall').onclick=async()=>{let payload=collect();if(!payload.notes.trim()){toast('请先填写整体修改意见');return}try{payload.request_overall=true;showState(await api('/api/save',{stage:state.active,revision:state.revision,data:payload}));toast('整体意见已提交')}catch(e){toast(e.message)}};
 app.querySelectorAll('[data-up],[data-down],[data-delete]').forEach(b=>b.onclick=()=>{collect();let a=draft.scenes, key=b.hasAttribute('data-up')?'up':b.hasAttribute('data-down')?'down':'delete',i=Number(b.dataset[key]);if(key==='delete'){if(!confirm('删除此幕？保存后如需恢复，请让 Codex 从故事重新准备。'))return;a.splice(i,1)}else{let j=i+(key==='up'?-1:1);if(j<0||j>=a.length)return;[a[i],a[j]]=[a[j],a[i]]}dirty=true;render()});
}
function collect(){
 let notes=document.querySelector('#style-notes')||document.querySelector('#review-notes');if(notes)draft.notes=notes.value;
 app.querySelectorAll('[data-field]').forEach(el=>{let s=draft.scenes?.[Number(el.dataset.index)];if(s)s[el.dataset.field]=el.value});
 app.querySelectorAll('[data-restore-notes]').forEach(el=>{let c=draft.comparisons?.find(x=>x.scene_id===el.dataset.restoreNotes);if(c)c.notes=el.value});
 app.querySelectorAll('[data-restore-accept]').forEach(el=>{let c=draft.comparisons?.find(x=>x.scene_id===el.dataset.restoreAccept);if(c)c.deviation_accepted=el.checked});
 if(state.active==='storyboard')return {scenes:(draft.scenes||[]).map(({id,narration,description,notes})=>({id,narration,description,notes})),notes:draft.notes||''};
 if(state.active==='restoration')return {comparisons:(draft.comparisons||[]).map(({scene_id,notes,deviation_accepted})=>({scene_id,notes:notes||'',deviation_accepted:!!deviation_accepted})),notes:draft.notes||''};
 if(state.active==='style')return {style_id:draft.style_id||'',notes:draft.notes||''};
 const accepted=app.querySelector('#sample-accept');if(state.active==='sample'&&accepted)return {notes:draft.notes||'',deviation_accepted:accepted.checked};
 return {notes:draft.notes||''};
}
async function submitChanges(){try{let payload=collect();if(state.active!=='style'&&!payload.notes.trim()){toast('请先填写修改意见');return}let linked=agentStatus.connected&&agentStatus.stage===state.active;showState(await api('/api/save',{stage:state.active,revision:state.revision,data:payload}));toast(linked?'修改已提交，Codex 将继续处理':'修改已提交；如 Codex 对话已结束，请在聊天中继续')}catch(e){toast(e.message)}}
document.querySelector('#confirm').onclick=async()=>{try{let linked=agentStatus.connected&&agentStatus.stage===state.active;showState(await api('/api/confirm',{stage:state.active,revision:state.revision,data:collect()}));toast(linked?'已确认，Codex 将自动继续':'已确认；如 Codex 对话已结束，请在聊天中继续')}catch(e){toast(e.message)}};
document.querySelector('#story-toggle').onclick=async()=>{try{let {story}=await api('/api/story');let d=document.querySelector('#story-dialog');d.innerHTML='<div class="dialog-head"><div><span class="eyebrow">ORIGINAL STORY</span><h2>原始故事</h2></div><button class="close" aria-label="关闭">×</button></div><pre></pre>';d.querySelector('pre').textContent=story;d.querySelector('.close').onclick=()=>d.close();d.showModal()}catch(e){toast(e.message)}};
api('/api/state').then(showState).catch(e=>{app.textContent='无法打开项目：'+e.message});
async function pollAgent(){try{agentStatus=await api('/api/agent')}catch(e){agentStatus={connected:false,stage:null}}let el=document.querySelector('#save-state');if(state?.active==='done'){el.innerHTML='<span class="live-dot"></span> 视频已确认 · 保存在本机';return}let linked=agentStatus.connected&&agentStatus.stage===state?.active;el.innerHTML=linked?'<span class="live-dot"></span> 自动等待已连接 · 页面确认后继续':'<span class="live-dot muted-dot"></span> Codex 可能正在制作；确认等待尚未连接'}
pollAgent();setInterval(pollAgent,2000);
setInterval(async()=>{try{let latest=await api('/api/state');if(latest.revision!==state?.revision){if(dirty){syncProcessing(latest);if(!seenRemote){toast('项目有更新，请先复制未保存的内容，再刷新页面');seenRemote=true}}else showState(latest)}}catch(e){}},4000);
document.querySelector('#voice-settings').onclick=async()=>{
 const d=document.querySelector('#story-dialog');
 d.innerHTML=`<div class="dialog-head"><div><span class="eyebrow">VOICE SETTINGS</span><h2>MiMo 配音设置</h2></div><button class="close" aria-label="关闭">×</button></div><p class="helper">默认推荐小米 MiMo 语音合成。制作样片时使用；你也可以选择其他可用的配音方式。</p><div class="credential-box"><div id="credential-status" class="credential-status">正在读取本机设置…</div><p class="helper">首次使用：登录 <a href="https://platform.xiaomimimo.com/" target="_blank" rel="noopener noreferrer">小米 MiMo 开放平台 ↗</a>，在控制台的 API Keys 中创建按量调用的 Key。</p><label class="label" for="mimo-key">API Key</label><input class="key-input" id="mimo-key" type="password" autocomplete="off" spellcheck="false" placeholder="在此粘贴 Key，不会显示已保存的内容"><div class="credential-actions"><button class="button primary" id="key-save">保存到本机</button><button class="button secondary" id="key-delete">删除已保存的 Key</button></div><div id="credential-error" class="credential-error" role="status"></div></div><p class="helper">仅检测 Video Master 自己保存的凭证及当前进程的 MiMo 环境变量；其他应用中可能已有配置。Key 不放进项目或交付包。已保存不代表已联网验证；合成语音时才调用 MiMo。</p>`;
 d.querySelector('.close').onclick=()=>{d.querySelector('#mimo-key').value='';d.close()};
 const statusEl=d.querySelector('#credential-status'),errorEl=d.querySelector('#credential-error'),input=d.querySelector('#mimo-key');
 const update=x=>{statusEl.textContent=x.configured?(x.source==='system'?`已保存到 ${x.storage}（尚未验证有效性）`:'检测到进程环境变量（尚未验证有效性）'):`Video Master 尚未发现可读取的 Key · 可保存到 ${x.storage}`};
 try{update(await api('/api/credentials'))}catch(e){statusEl.textContent='无法读取凭证状态';errorEl.textContent=e.message}
 d.querySelector('#key-save').onclick=async()=>{errorEl.textContent='';try{let x=await api('/api/credentials',{action:'save',key:input.value});input.value='';update(x);toast('MiMo Key 已保存到本机')}catch(e){errorEl.textContent=e.message}};
 d.querySelector('#key-delete').onclick=async()=>{errorEl.textContent='';try{let x=await api('/api/credentials',{action:'delete'});input.value='';update(x);toast('已删除本机保存的 MiMo Key')}catch(e){errorEl.textContent=e.message}};
 d.showModal();
};
