export type ClosingSway={roll:number;x:number;y:number;skew:number};
// Continue the pull-back's momentum on the whole content plane, then settle.
// No looping movement, opacity changes or additional 3D compositor layers.
export const closingSway=(t:number):ClosingSway=>{
 const age=t-18.02;
 if(t<=18.02||t>=19.2)return {roll:0,x:0,y:0,skew:0};
 const raw=Math.max(0,Math.min(1,(age-.75)/.43));
 const tail=1-raw*raw*(3-2*raw);
 const wave=Math.sin(age*Math.PI*2/.58)*Math.exp(-age*3.4)*tail;
 return {roll:wave*1.8,x:wave*8,y:-wave*2,skew:wave*.4};
};
