import type {Camera} from './camera';
type Move={start:number;end:number;target:Camera;tilt:number};
const overview:Camera={x:960,y:600,zoom:1,yaw:0,pitch:0};
const moves:Move[]=[
 {start:.25,end:.75,target:{...overview,x:950,y:550,zoom:1.36},tilt:-4},
 {start:4.95,end:5.55,target:{...overview,x:1410,y:445,zoom:1.3},tilt:-5},
 {start:7.55,end:8.05,target:{...overview,x:1410,y:640,zoom:1.3},tilt:-4},
 {start:10.55,end:11.2,target:{...overview,x:650,y:560,zoom:1.25},tilt:5},
 {start:16.2,end:16.75,target:{...overview,x:950,y:700,zoom:1.18},tilt:-4},
 {start:17.6,end:18.15,target:overview,tilt:3},
];
export const cameraCrisp=(t:number):Camera=>{
 let previous=overview;
 for(const m of moves){
  if(t<m.start)return previous;
  if(t<=m.end){
   const raw=(t-m.start)/(m.end-m.start),p=raw*raw*(3-2*raw);
   const mix=(key:keyof Camera)=>previous[key]+(m.target[key]-previous[key])*p;
   const lean=Math.sin(Math.PI*raw);
   return {x:mix('x'),y:mix('y'),zoom:mix('zoom'),yaw:m.tilt*lean,pitch:-m.tilt*.38*lean};
  }
  previous=m.target;
 }
 return previous;
};
