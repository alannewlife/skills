export type PopPose={opacity:number;scale:number;x:number;y:number;roll:number;skew:number};
const points=[
 {at:0,scale:.16,x:0,y:24,roll:-9,skew:-2},
 {at:.23,scale:1.18,x:9,y:-5,roll:5.5,skew:2.8},
 {at:.42,scale:.965,x:-7,y:2,roll:-4,skew:-2},
 {at:.64,scale:1.025,x:4,y:0,roll:2.4,skew:1.2},
 {at:.86,scale:1,x:-1.5,y:0,roll:-.9,skew:-.45},
 {at:1.12,scale:1,x:0,y:0,roll:0,skew:0},
];
// A single entrance: quick scale overshoot, two diminishing sways, then exact rest.
// All transforms stay on a flat compositing plane to preserve the V4 flicker fix.
export const popMotion=(age:number,direction=1):PopPose=>{
 if(age<=0)return {opacity:0,scale:.16,x:0,y:24,roll:-9*direction,skew:-2*direction};
 let a=points[0],b=a;
 for(let i=1;i<points.length;i++){b=points[i];if(age<=b.at)break;a=b;}
 const raw=a===b?0:Math.max(0,Math.min(1,(age-a.at)/(b.at-a.at))),p=raw*raw*(3-2*raw);
 const mix=(key:'scale'|'x'|'y'|'roll'|'skew')=>a[key]+(b[key]-a[key])*p;
 return {opacity:Math.min(1,age/.11),scale:mix('scale'),x:mix('x')*direction,y:mix('y'),roll:mix('roll')*direction,skew:mix('skew')*direction};
};
