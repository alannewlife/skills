import React from 'react';
import {AdaptiveHeading} from './AdaptiveHeading';
import {AbsoluteFill,useCurrentFrame,useVideoConfig} from 'remotion';
import {SceneOneAdaptive} from './CompositionAdaptive';
import {DrawingPaper,editorialRed,ramp} from './EditorialFrame';
// A chapter-boundary study. The next scene is a typographic chapter opening,
// not a finished illustration scene or a replacement for the next narration.
export const TransitionAdaptive:React.FC=()=>{
 const f=useCurrentFrame(),{fps}=useVideoConfig(),t=f/fps;
 const wipe=ramp(t,3.35,.55),nextTime=t-3.72;
 return <AbsoluteFill>
  <DrawingPaper/>
  <AbsoluteFill style={{clipPath:`inset(0 0 0 ${wipe*100}%)`}}><SceneOneAdaptive audio={false} timeOffset={17} outroAt={20.15}/></AbsoluteFill>
  <AbsoluteFill style={{clipPath:`inset(0 ${(1-wipe)*100}% 0 0)`}}>
   <DrawingPaper/>
   <AdaptiveHeading adaptive={false} t={nextTime} chapter="02" section="改变" parts={['智能体连接流程，','提高效率']}/>
   <div style={{position:'absolute',left:130,top:350,fontFamily:'"PingFang SC", sans-serif',color:'#252c32'}}>
    {['重复操作，交给智能体。','关键判断，由人把关。'].map((text,i)=><div key={text} style={{height:124,overflow:'hidden',fontSize:76,fontWeight:650,letterSpacing:1}}><div style={{transform:`translateY(${(1-ramp(nextTime,.3+i*.17,.42))*130}px)`}}>{text}</div></div>)}
    <div style={{display:'flex',gap:30,marginTop:48,alignItems:'center',fontSize:25,color:'#677381',clipPath:`inset(0 ${(1-ramp(nextTime,.75,.45))*100}% 0 0)`}}><span style={{width:64,height:4,background:editorialRed}}/>信息、工具、业务系统，连接起来协同推进任务。</div>
   </div>
  </AbsoluteFill>
  {wipe>0&&wipe<1&&<div style={{position:'absolute',left:wipe*1920-3,top:0,width:6,height:1080,background:editorialRed}}/>}
 </AbsoluteFill>;
};
