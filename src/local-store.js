const DB_NAME = 'sunny-calendar-clean-v1';
let opened;
let backend;
const revisions=new Map();
async function fileBackend(){
  if(!backend)backend=(async()=>{try{const r=await fetch('/local-api/status',{cache:'no-store'});const v=await r.json();return v.storage==='local-file';}catch{return false;}})();
  return backend;
}
function openDB() {
  if (!opened) opened = new Promise((resolve, reject) => {
    const r = indexedDB.open(DB_NAME, 1);
    r.onupgradeneeded = () => r.result.createObjectStore('documents', { keyPath: 'id' });
    r.onsuccess = () => resolve(r.result);
    r.onerror = () => reject(r.error);
  });
  return opened;
}
async function loadBrowserDocuments() {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const r = db.transaction('documents').objectStore('documents').getAll();
    r.onsuccess = () => resolve(r.result);
    r.onerror = () => reject(r.error);
  });
}
async function saveBrowserDocument(doc) {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction('documents', 'readwrite');
    tx.objectStore('documents').put(doc);
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error);
    tx.onabort = () => reject(tx.error || new Error('Save interrupted'));
  });
}
export async function loadDocuments(){
  if(!await fileBackend())return loadBrowserDocuments();
  const r=await fetch('/local-api/documents',{cache:'no-store'});
  if(!r.ok)throw new Error('Could not open local data file');
  let records=await r.json();
  for(const d of records)revisions.set(d.id,d._revision);
  if(!records.length){
    const legacy=await loadBrowserDocuments();
    for(const d of legacy)await saveDocument(d);
    if(legacy.length){const refresh=await fetch('/local-api/documents',{cache:'no-store'});records=await refresh.json();for(const d of records)revisions.set(d.id,d._revision);}
  }
  return records;
}
export async function saveDocument(doc){
  if(!await fileBackend())return saveBrowserDocument(doc);
  const r=await fetch('/local-api/documents',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({doc,expectedRevision:revisions.get(doc.id)||0})});
  if(!r.ok)throw new Error(r.status===409?'This note was changed in another window. Export a backup before reopening.':'Could not save local data file');
  const v=await r.json();revisions.set(doc.id,v.revision);
}
export const escapeHTML = s => String(s).replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;').replaceAll('"', '&quot;');
export function sanitizeHTML(value) {
  const t = document.createElement('template');
  t.innerHTML = String(value || '');
  t.content.querySelectorAll('script,style,iframe,object,embed,link,meta,svg,math,form,input,button,textarea,select').forEach(n => n.remove());
  const allowed = new Set('DIV SPAN P BR B STRONG I EM U S OL UL LI TABLE TBODY THEAD TR TD TH FONT IMG HR H2 H3'.split(' '));
  for (const el of [...t.content.querySelectorAll('*')].reverse()) {
    if (!allowed.has(el.tagName)) { el.replaceWith(...el.childNodes); continue; }
    const src = el.getAttribute('src');
    if (el.tagName === 'IMG' && (!src || !/^data:image\/(png|jpeg|webp);base64,[A-Za-z0-9+/=]+$/.test(src) || src.length > 24_000_000)) { el.remove(); continue; }
    const styles = {};
    for (const k of ['color','background-color','font-size','font-family','font-weight','font-style','text-decoration','text-align','width']) {
      const v = el.style.getPropertyValue(k);
      if (v && !/url|expression|var\(/i.test(v) && v.length < 120) styles[k] = v;
    }
    const photo = el.classList.contains('photo') && el.querySelector('img');
    const cols = el.getAttribute('colspan'), rows = el.getAttribute('rowspan');
    const color = el.getAttribute('color'), face = el.getAttribute('face'), size = el.getAttribute('size');
    for (const a of [...el.attributes]) el.removeAttribute(a.name);
    for (const [k,v] of Object.entries(styles)) el.style.setProperty(k,v);
    if (el.tagName === 'IMG') { el.src=src; el.alt='Pasted screenshot'; el.draggable=false; }
    if (photo) { el.className='photo'; el.contentEditable='false'; const w=parseFloat(styles.width)||240; el.style.width=Math.max(40,Math.min(1600,w))+'px'; }
    if (/^(TD|TH)$/.test(el.tagName)) {
      if (+cols>0 && +cols<=30) el.setAttribute('colspan',cols);
      if (+rows>0 && +rows<=100) el.setAttribute('rowspan',rows);
    }
    if (el.tagName==='FONT') {
      if (color && CSS.supports('color',color)) el.setAttribute('color',color);
      if (face && /^[a-zA-Z가-힣 ,'-]{1,80}$/.test(face)) el.setAttribute('face',face);
      if (/^[1-7]$/.test(size||'')) el.setAttribute('size',size);
    }
  }
  for (const img of t.content.querySelectorAll('img')) {
    if (!img.closest('.photo')) { const p=document.createElement('span');p.className='photo';p.contentEditable='false';p.style.width='240px';img.replaceWith(p);p.append(img); }
  }
  return t.innerHTML;
}
export function plainText(html) {
  const t=document.createElement('template');t.innerHTML=sanitizeHTML(html);
  t.content.querySelectorAll('br').forEach(n=>n.replaceWith('\n'));
  t.content.querySelectorAll('div,p,li,tr,h2,h3').forEach(n=>n.append('\n'));
  return t.content.textContent || '';
}
export function imageCount(html) { return (html.match(/<img\b/gi)||[]).length; }
export async function imageHTML(file) {
  if (!/^image\/(png|jpeg|webp)$/.test(file.type)) throw new Error('Choose a PNG, JPG, or WebP picture.');
  if (file.size>20*1024*1024) throw new Error('This picture is too large. Use a smaller screen capture.');
  const bitmap=await createImageBitmap(file);
  const ratio=Math.min(1,1800/Math.max(bitmap.width,bitmap.height));
  const canvas=document.createElement('canvas');canvas.width=Math.round(bitmap.width*ratio);canvas.height=Math.round(bitmap.height*ratio);
  canvas.getContext('2d').drawImage(bitmap,0,0,canvas.width,canvas.height);bitmap.close();
  const url=canvas.toDataURL('image/webp',.92);
  return `<span class="photo" contenteditable="false" style="width:${Math.min(300,canvas.width)}px"><img src="${url}" alt="Pasted screenshot" draggable="false"></span><div><br></div>`;
}
