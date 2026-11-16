import test from 'node:test';
import assert from 'node:assert/strict';
import {cameraAt, headingAt, closingSwayAt, isolateContextAt} from '../styles/business-line-art/motion.ts';

const overview={x:960,y:600,zoom:1,yaw:0,pitch:0};
const cues=[{start:2,end:2.6,target:{...overview,x:400,y:450,zoom:1.5},tilt:5},{start:6,end:6.6,target:overview,tilt:-4}];
test('focus follows each configured story cue and remains steady',()=>{
 const middle=cameraAt(2.3,cues,overview), focus=cameraAt(4,cues,overview);
 assert.ok(middle.x<overview.x&&middle.x>focus.x);
 assert.ok(Math.abs(middle.yaw)>0);
 assert.equal(focus.x,400);assert.equal(focus.zoom,1.5);assert.equal(focus.yaw,0);
 assert.equal(cameraAt(7,cues,overview).zoom,1);
});
test('title compacts for explanation, returns for overview',()=>{
 assert.equal(headingAt(0,1,2,8,9).compact,0);
 assert.equal(headingAt(4,1,2,8,9).compact,1);
 assert.equal(headingAt(10,1,2,8,9).compact,0);
});
test('closing sway follows return and settles completely',()=>{
 assert.equal(closingSwayAt(7,8,9.2).roll,0);
 assert.notEqual(closingSwayAt(8.15,8,9.2).roll,0);
 assert.equal(closingSwayAt(10,8,9.2).roll,0);
});
test('unrelated context fades before the focus and returns in the overview',()=>{
 assert.equal(isolateContextAt(9,10.1,10.55,19.7,20.35),1);
 assert.equal(isolateContextAt(11.7,10.1,10.55,19.7,20.35),0);
 assert.ok(isolateContextAt(20,10.1,10.55,19.7,20.35)>0);
 assert.equal(isolateContextAt(21,10.1,10.55,19.7,20.35),1);
});
