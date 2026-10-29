import test from 'node:test';
import assert from 'node:assert/strict';
import {taskTextColor,savedTaskColor} from '../src/task-colors.js';

test('legacy and personal tasks keep the red/black completion rule',()=>{
  assert.equal(taskTextColor({},0),'#b3261e');
  assert.equal(taskTextColor({taskColors:['#1967d2']},0),'#b3261e');
  assert.equal(taskTextColor({completedLayers:[true]},0),'#111111');
});
test('team tasks start green and completion temporarily overrides the chosen color',()=>{
  const doc={teamLayers:[true,true],taskColors:[null,'#1967d2'],completedLayers:[false,false]};
  assert.equal(taskTextColor(doc,0),'#137333');
  assert.equal(taskTextColor(doc,1),'#1967d2');
  doc.completedLayers[1]=true;
  assert.equal(taskTextColor(doc,1),'#111111');
  doc.completedLayers[1]=false;
  assert.equal(taskTextColor(doc,1),'#1967d2');
  assert.equal(taskTextColor(doc,0),'#137333');
});
test('untrusted backup colors cannot inject arbitrary CSS',()=>{
  for(const value of ['url(https://example.invalid)', 'var(--other)', '#fff;display:none',{},null]){
    const doc={teamLayers:[true],taskColors:[value]};
    assert.equal(savedTaskColor(doc,0),null);
    assert.equal(taskTextColor(doc,0),'#137333');
  }
});
