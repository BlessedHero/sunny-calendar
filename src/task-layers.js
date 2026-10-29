import {sanitizeHTML,plainText} from './local-store';
const cache=new Map();
export const MAX_TASKS=20;
export const PREVIEW_TASKS=4;
export function taskLayers(doc){
  if(Array.isArray(doc.layers)){
    const v=doc.layers.map(x=>sanitizeHTML(typeof x==='string'?x:''));
    return v;
  }
  const html=sanitizeHTML(doc.html||'');
  if(!plainText(html).trim()&&!html.includes('<img'))return [];
  if(cache.has(html))return cache.get(html);
  const t=document.createElement('template');t.innerHTML=html;
  const groups=[];let group=document.createElement('div'),breaks=0;
  const push=()=>{while(group.lastChild?.nodeName==='BR')group.lastChild.remove();if(group.textContent.trim()||group.querySelector('img'))groups.push(group.innerHTML);group=document.createElement('div');};
  for(const node of [...t.content.childNodes]){
    if(node.nodeName==='BR'){
      if(++breaks===2)push();
      else if(breaks===1)group.append(node.cloneNode(true));
    }else if(node.nodeType===Node.TEXT_NODE&&!node.textContent.trim()&&breaks){continue;}
    else if(node.nodeType===Node.ELEMENT_NODE&&/^(P|DIV)$/.test(node.nodeName)&&!node.textContent.trim()&&!node.querySelector('img,table')){push();breaks=2;}
    else{breaks=0;group.append(node.cloneNode(true));}
  }
  push();
  const result=groups.length>4?[...groups.slice(0,3),groups.slice(3).join('<br><br>')]:groups;
  cache.set(html,result.length?result:[html]);return result.length?result:[html];
}
export function layerDocument(owner,index){
  return {...owner,id:owner.id+'::task:'+index,ownerId:owner.id,layerIndex:index,completed:isTaskComplete(owner,index),teamDraft:isTeamTask(owner,index),html:taskLayers(owner)[index]||''};
}
export const isTaskComplete=(owner,index)=>owner.completedLayers?.[index]===true;

export const isTeamTask=(owner,index)=>owner.teamLayers?.[index]===true;
