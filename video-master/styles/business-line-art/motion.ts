/** Reusable camera grammar for the business-line-art style, not a global Video Master default. */
export type LineArtCamera = {x:number; y:number; zoom:number; yaw:number; pitch:number};
export type LineArtCue = {start:number; end:number; target:LineArtCamera; tilt:number};
export type LineArtSway = {roll:number; x:number; y:number; skew:number};

const clamp=(v:number)=>Math.max(0,Math.min(1,v));
const smooth=(v:number)=>{const p=clamp(v);return p*p*(3-2*p)};
export const progress=(t:number,start:number,end:number)=>smooth((t-start)/Math.max(.0001,end-start));

/** Hide unrelated context during a focused explanation and restore it for the overview. */
export function isolateContextAt(t:number,hideStart:number,hideEnd:number,showStart:number,showEnd:number){
 return clamp(1-progress(t,hideStart,hideEnd)+progress(t,showStart,showEnd));
}

/** Use one cue per narration beat, with focus/scale derived from actual object bounds. */
export function cameraAt(t:number,cues:LineArtCue[],overview:LineArtCamera):LineArtCamera {
 let previous=overview;
 for (const cue of cues) {
  if(t<cue.start)return previous;
  if(t<=cue.end){
   const raw=clamp((t-cue.start)/Math.max(.0001,cue.end-cue.start));
   const p=smooth(raw), lean=Math.sin(Math.PI*raw);
   const mix=(k:keyof LineArtCamera)=>previous[k]+(cue.target[k]-previous[k])*p;
   return {x:mix('x'),y:mix('y'),zoom:mix('zoom'),yaw:mix('yaw')+cue.tilt*lean,pitch:mix('pitch')-cue.tilt*.38*lean};
  }
  previous=cue.target;
 }
 return previous;
}

/** Values are per-project seconds; the title moves between large intro and compact narration. */
export function headingAt(t:number,compactStart:number,compactEnd:number,restoreStart:number,restoreEnd:number){
 const compact=progress(t,compactStart,compactEnd)*(1-progress(t,restoreStart,restoreEnd));
 return {compact,fontSize:59-28*compact,kickerY:58-27*compact,titleY:103-38*compact,lineY:202-76*compact};
}

/** A short damped overshoot, completely still after settle. */
export function closingSwayAt(t:number,start:number,settle:number):LineArtSway {
 if(t<=start||t>=settle)return {roll:0,x:0,y:0,skew:0};
 const age=t-start,duration=Math.max(.001,settle-start);
 const tail=1-progress(age,duration*.64,duration);
 const wave=Math.sin(age*Math.PI*2/.58)*Math.exp(-age*3.4)*tail;
 return {roll:wave*1.8,x:wave*8,y:-wave*2,skew:wave*.4};
}
