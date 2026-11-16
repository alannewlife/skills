import React from 'react';
import {AdaptiveHeading} from './AdaptiveHeading';
import {DrawingPaper,editorialPaper,ramp} from './EditorialFrame';
import {closingSway} from './closingSway';
import {popMotion} from './popMotion';
import {cameraCrisp} from './cameraCrisp';
import {AbsoluteFill, Audio, Img, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {Documents,Messages,System,ink,paper,green,blue,amber} from './art/Illustrations';
const clamp=(n:number)=>Math.min(1,Math.max(0,n));
const ease=(n:number)=>{n=clamp(n);return n*n*(3-2*n)};
const enter=(t:number,start:number,duration=.32)=>ease((t-start)/duration);
const font='"PingFang SC", "Microsoft YaHei", sans-serif';
const label:React.CSSProperties={fontFamily:font,fontWeight:650,fontSize:30,letterSpacing:1};
export const SceneOneAdaptive:React.FC<{audio?:boolean;timeOffset?:number;outroAt?:number}>=({audio=true,timeOffset=0,outroAt=99})=>{
 const frame=useCurrentFrame(),{fps}=useVideoConfig(),t=frame/fps+timeOffset;
 const exit=ramp(t,outroAt,.4);
 const camera=cameraCrisp(t),sway=closingSway(t);
 const node=(id:string,x:number,y:number,w:number,h:number,start:number,depth:number,children:React.ReactNode)=>{
  const p=enter(t,start),age=t-start;
  const featured=['documents','messages','process-person','expert-person'].includes(id)||id.startsWith('system-');
  const direction=id==='documents'||id==='expert-person'?-1:1;
  const pose=featured?popMotion(age,direction):{opacity:p,scale:1,x:0,y:(1-p)*10,roll:(1-p)*-2.5,skew:0};
  const origin=id==='expert-person'?'50% 85%':'50% 70%';
  return <div key={id} data-asset={id} style={{position:'absolute',left:x,top:y,width:w,height:h,opacity:pose.opacity,transform:`translate(${pose.x+camera.yaw*depth*.018}px,${pose.y+camera.pitch*depth*.018}px) rotate(${pose.roll}deg) skewX(${pose.skew}deg) scale(${pose.scale})`,transformOrigin:origin}}>{children}</div>
 };
 const tag=(text:string,color:string,w=210,left=12,top=-20)=><div data-badge={text} style={{...label,position:'absolute',left,top,zIndex:2,color:paper,background:color,padding:'7px 15px',borderRadius:26,width:w,textAlign:'center',boxShadow:'3px 5px 0 rgba(58,68,57,.10)'}}>{text}</div>;
 const connection=(id:string,path:string,start:number,_color:string,caption?:string,cx=0,cy=0)=>{
  const p=enter(t,start,.36);
  return <g key={id} opacity={p} data-connection={id}><defs><mask id={`reveal-${id}`}><path d={path} pathLength={1} stroke="white" strokeWidth="20" strokeDasharray={`${p} 1`} fill="none"/></mask></defs><path d={path} pathLength={1} stroke="#8d9691" strokeWidth="3" strokeDasharray=".014 .012" fill="none" opacity=".72" mask={`url(#reveal-${id})`} markerEnd={p>.95?'url(#arrow)':undefined}/>{caption&&<g transform={`translate(${cx} ${cy})`}><rect x="-44" y="-19" width="88" height="38" rx="19" fill="#f0f2f5"/><text textAnchor="middle" y="7" fontFamily={font} fontWeight="600" fontSize="22" fill="#747f7c">{caption}</text></g>}</g>
 };
 return <AbsoluteFill style={{background:editorialPaper,fontFamily:font,color:ink}}>
  <DrawingPaper/>
  {audio&&<Audio src={staticFile('scene-audio.wav')}/>}

  <AdaptiveHeading t={t} exit={exit}/>
  <div data-viewport style={{transform:`translateY(${-exit*10}px) scale(${1-exit*.025})`,transformOrigin:'50% 50%',position:'absolute',left:0,top:0,width:1920,height:1080,overflow:'hidden'}}>
  <div data-stage style={{position:'absolute',left:0,top:0,width:1920,height:1080,transform:`translate(${(960-camera.x)*camera.zoom}px,${(600-camera.y)*camera.zoom}px) scale(${camera.zoom}) skewY(${camera.yaw*.3}deg) skewX(${-camera.pitch*.48}deg) scaleX(${Math.cos(camera.yaw*Math.PI/180)}) translate(${sway.x}px,${sway.y}px) rotate(${sway.roll}deg) skewX(${sway.skew}deg)`,transformOrigin:'960px 600px'}}>
   <svg width="1920" height="1080" style={{position:'absolute',inset:0,overflow:'visible'}}>
    <defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse"><path d="M1 1 L9 5 L1 9" fill="none" stroke="#7c8782" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/></marker></defs>
    {connection('search','M1188 464 C1220 464 1195 330 1350 330',6.05,green,'查找',1230,365)}
    {connection('copy','M1188 603 C1264 603 1240 545 1350 545',7.15,green,'复制',1260,570)}
    {connection('system-a','M1188 708 C1240 708 1252 702 1358 702',8.6,blue,'核对',1250,702)}
    {connection('system-b','M1217 706 C1303 706 1250 808 1358 808',9.05,blue)}
    {connection('system-c','M1217 706 C1306 706 1243 915 1358 915',9.5,blue)}
    {connection('ask-process','M447 473 C600 473 577 518 696 518',11.8,amber,'询问',580,449)}
    {connection('ask-expert','M447 770 C612 770 584 674 696 674',13.2,green,'沟通',581,737)}
    <g opacity={enter(t,16.25,.8)} stroke="#939d95" strokeWidth="2.4" fill="none"><path d="M940 823 V840 M858 865 V852 Q858 840 870 840 H1015 Q1027 840 1027 852 V865"/></g>
   </svg>
   {node('employee',651,320,600,450,.3,45,<div style={{position:'relative',width:'100%',height:'100%'}}>
    <Img src={staticFile('assets/line-art-v2/employee.png')} style={{width:'100%',height:'100%',objectFit:'contain'}}/>
    <div style={{position:'absolute',left:'12%',top:'46%',width:'24%',textAlign:'center',fontSize:24,fontWeight:650,transform:'rotate(-8deg)'}}>任务</div>
    <div style={{position:'absolute',left:'65%',top:'45%',width:'24%',textAlign:'center',fontSize:24,fontWeight:650,transform:'rotate(10deg)'}}>任务</div>
   </div>)}
   {node('manual-label',819,762,242,54,.9,52,<div style={{...label,textAlign:'center',fontSize:32,color:paper,background:'#697773',padding:'9px 20px',borderRadius:28,boxShadow:'4px 6px 0 #d9ddd3'}}>人工衔接</div>)}
   {node('process-person',135,318,340,275,11.0,30,<>{tag('流程与方法',amber,222,45,-18)}<div style={{position:'absolute',top:12,width:'100%',height:265}}><Img src={staticFile('assets/line-art-v2/consultant.png')} style={{width:'100%',height:'100%',objectFit:'contain'}}/></div></>)}
   {node('expert-person',135,653,340,280,12.4,38,<>{tag('外部专家',green,200,46,-18)}<div style={{position:'absolute',top:5,width:'100%',height:275}}><Img src={staticFile('assets/line-art-v2/expert.png')} style={{width:'100%',height:'100%',objectFit:'contain'}}/></div></>)}
   {node('documents',1351,249,390,188,5.28,12,<><div style={{position:'absolute',inset:0}}><Documents/></div>{tag('知识',green,132,8,-15)}</>)}
   {node('messages',1353,486,390,167,6.45,32,<><div style={{position:'absolute',inset:0}}><Messages/></div>{tag('动态信息',green,196,15,-20)}</>)}
   {['A','B','C'].map((letter,i)=>node(`system-${letter}`,1358,659+i*107,390,113,7.8+i*.48,18+i*4,<System name={`业务系统 ${letter}`} variant={i} taskLabel="任务"/>))}
   {node('task-state',689,855,520,112,16.25,65,<div style={{display:'flex',gap:18,justifyContent:'center'}}>{['待回复','待处理'].map((s,i)=><div key={s} style={{background:paper,border:'2.8px solid #727d76',borderRadius:15,padding:'14px 21px',fontSize:27,fontWeight:600,boxShadow:'4px 7px 0 #e2e5da',transform:`translateY(${(1-enter(t,16.25+i*.25))*12}px)`,opacity:enter(t,16.25+i*.25)}}><span style={{display:'inline-block',width:18,height:18,border:'2px solid #8d978e',borderRadius:3,marginRight:12}}/>{s}</div>)}</div>)}
   {node('question-marks',828,267,250,70,1.3,48,<div style={{display:'flex',gap:20,alignItems:'end',color:'#747b70',fontSize:42,fontWeight:500,transform:`rotate(-9deg) translateY(0px)`}}><span style={{fontSize:29}}>?</span><span>?</span><span style={{fontSize:31}}>?</span></div>)}
  </div></div>
 </AbsoluteFill>;
};
