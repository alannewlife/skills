import React from 'react';
import {AbsoluteFill,Img,staticFile} from 'remotion';
export const editorialRed='#cc1831';
export const editorialPaper='#fcfcfd';
export const ramp=(t:number,start:number,duration:number)=>{
 const v=Math.max(0,Math.min(1,(t-start)/duration));return v*v*(3-2*v);
};
export const DrawingPaper:React.FC=()=> <AbsoluteFill style={{background:editorialPaper}}>
 <svg width="1920" height="1080" style={{position:'absolute',inset:0}} aria-hidden="true">
  <defs><pattern id="drawing-dot-grid" width="32" height="32" patternUnits="userSpaceOnUse"><circle cx="16" cy="16" r="1.35" fill="#9eabb9" opacity=".74"/></pattern></defs>
  <rect width="1920" height="1080" fill="url(#drawing-dot-grid)"/>
 </svg>
</AbsoluteFill>;
export const BrandMark:React.FC=()=> <Img src={staticFile('assets/company-logo.png')} alt="transcosmos" style={{position:'absolute',right:64,top:32,width:190,height:65,objectFit:'contain'}}/>;
