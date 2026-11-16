import React from 'react';
import {BrandMark,editorialPaper,editorialRed,ramp} from './EditorialFrame';
import {closingSway} from './closingSway';
const font='"PingFang SC", "Microsoft YaHei", sans-serif';
export const headingLayout=(t:number,adaptive=true)=>{
 const compact=adaptive?ramp(t,1.7,.55)*(1-ramp(t,17.6,.55)):0;
 return {compact,fontSize:53-25*compact,kickerY:48-18*compact,titleY:89-27*compact,lineY:171-61*compact};
};
export const AdaptiveHeading:React.FC<{t:number;chapter?:string;section?:string;parts?:string[];exit?:number;adaptive?:boolean}>=({t,chapter='01',section='现状',parts=['人在','碎片化环境','中推进工作'],exit=0,adaptive=true})=>{
 const l=headingLayout(t,adaptive),s=adaptive?closingSway(t):{roll:0,x:0,y:0,skew:0};
 const width=parts.join('').length*(l.fontSize+1),draw=ramp(t,.24,.52)*(1-exit);
 return <div style={{position:'absolute',inset:0,zIndex:5,pointerEvents:'none',fontFamily:font}}>
  <div data-heading-group style={{position:'absolute',inset:0,transform:`translate(${s.x}px,${s.y}px) rotate(${s.roll}deg) skewX(${s.skew}deg)`,transformOrigin:'960px 600px'}}>
   <div data-local-title-mask style={{position:'absolute',left:82,top:l.kickerY-14,width:width+38,height:l.lineY-l.kickerY+29,background:editorialPaper,borderRadius:10}}/>
   <div style={{position:'absolute',left:100,top:l.kickerY,overflow:'hidden',height:29,color:editorialRed,fontSize:20-5*l.compact,fontWeight:650,letterSpacing:2}}>
    <div style={{transform:`translateY(${(1-ramp(t,0,.25))*30-exit*30}px)`}}>{chapter}<span style={{margin:'0 13px',color:'#949da8'}}>/</span>{section}</div>
   </div>
   <div data-heading-text style={{position:'absolute',left:100,top:l.titleY,display:'flex',alignItems:'baseline',overflow:'hidden',height:l.fontSize*1.4,fontSize:l.fontSize,fontWeight:750,letterSpacing:1,color:'#252c32',transformOrigin:'0 100%',transform:`translateY(${-exit*8}px) scale(${1-exit*.045})`}}>
    {parts.map((text,i)=><span key={text} style={{display:'inline-block',transform:`translateY(${(1-ramp(t,.05+i*.09,.35))*l.fontSize*1.5-exit*l.fontSize*1.7}px)`}}>{text}</span>)}
   </div>
   <svg width="1920" height="200" style={{position:'absolute',inset:0}}>
    <path d={`M100 ${l.lineY} H${100+width*draw}`} fill="none" stroke={editorialRed} strokeWidth={4-1.5*l.compact} strokeLinecap="round" opacity={draw>.001?1:0}/>
    <circle cx={100+width*draw} cy={l.lineY} r="3.1" fill={editorialRed} opacity={draw>.001&&draw<.99?1:0}/>
   </svg>
  </div>
  <div data-local-logo-mask style={{position:'absolute',right:48,top:18,width:222,height:93,borderRadius:10,background:editorialPaper}}/>
  <BrandMark/>
 </div>;
};
