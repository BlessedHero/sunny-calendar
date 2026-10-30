import React,{useEffect,useRef,useState,createContext,useContext} from 'react';
import {useI18n} from './i18n';
import './desktop-tools.css';
const webOnly=!['127.0.0.1','localhost'].includes(window.location.hostname);
const Context=createContext(null);
export const useDesktopTools=()=>useContext(Context);
const Icon=({name})=><img className="icon" src={`/icons/${name}.svg`} alt=""/>;
async function api(path,payload,signal){
  const response=await fetch('/local-api/tools'+path,{method:payload?'POST':'GET',headers:payload?{'Content-Type':'application/json'}:undefined,body:payload?JSON.stringify(payload):undefined,signal});
  if(!response.headers.get('Content-Type')?.includes('application/json'))throw Error('Reopen Sunny Calendar to enable desktop links and file search.');
  const value=await response.json();if(!response.ok)throw Error(value.error||'Desktop action failed.');return value;
}
export function DesktopToolsProvider({children}){
  const [config,setConfig]=useState(null),[error,setError]=useState(''),[searchOpen,setSearchOpen]=useState(false),[editing,setEditing]=useState(null),[notice,setNotice]=useState('');
  const {t}=useI18n();
  const load=()=>api('').then(setConfig).catch(e=>setError(e.message));
  useEffect(()=>{if(!webOnly)load();},[]);
  useEffect(()=>{if(!notice)return;const timer=setTimeout(()=>setNotice(''),4500);return()=>clearTimeout(timer);},[notice]);
  const open=async payload=>{if(webOnly){setNotice(t('Install the Windows app to open programs and network folders on this computer.'));return;}try{const result=await api('/open',payload);if(result.needsSetup){setEditing({type:'apps',app:result.needsSetup});return;}setNotice(t(payload.kind==='network-address'?'Sent to File Explorer. Windows checks network access.':'Opened in its Windows app.'));}catch(e){setNotice(t(e.message));}};
  const save=async value=>{const clean=await api('/config',value);setConfig({...config,...clean});setEditing(null);};
  const desktopAction=action=>value=>{if(webOnly){setNotice(t('Install the Windows app to open programs and network folders on this computer.'));return;}action(value);};
  return <Context.Provider value={{config,error,open,setSearchOpen:desktopAction(setSearchOpen),setEditing:desktopAction(setEditing)}}>{children}
    {notice&&<div className="desktop-tools-toast" role="status">{notice}</div>}
    {searchOpen&&<FileSearch config={config} error={error} onClose={()=>setSearchOpen(false)} onEdit={()=>setEditing({type:'folders'})} onOpen={open}/>}
    {editing&&<ToolsSettings config={config} initial={editing} onClose={()=>setEditing(null)} onSave={save}/>}
  </Context.Provider>;
}
export function QuickLinks(){
  const {t}=useI18n(),{config,open,setEditing}=useContext(Context);
  return <nav className="quick-link-dock" aria-label={t('App shortcuts')}>
    {config?.apps?.obsidian?.visible!==false&&config?.appStatus?.obsidian?.found!==false&&<button className="obsidian-shortcut" aria-label={t('Open Obsidian')} title={t('Open Obsidian')+' · '+t('Right-click to set up this app.')} onContextMenu={e=>{e.preventDefault();setEditing({type:'apps',app:'obsidian'});}} onClick={()=>open({kind:'obsidian'})}><img src="/obsidian-shortcut.svg" alt=""/><span>Obsidian</span></button>}
    {config?.apps?.pos?.visible!==false&&<button className="pos-shortcut" aria-label={t('Open Sunny POS')} title={t('Open Sunny POS')+' · '+t('Right-click to set up this app.')} onContextMenu={e=>{e.preventDefault();setEditing({type:'apps',app:'pos'});}} onClick={()=>open({kind:'pos'})}><img src="/sunny-pos-icon.png" alt=""/><span>POS</span></button>}
    {config?.apps?.vpn?.visible!==false&&<button className="vpn-shortcut" aria-label={t('Open SoftEther VPN manager')} title={t('Open SoftEther VPN manager')+' · '+t('Right-click to set up this app.')} onContextMenu={e=>{e.preventDefault();setEditing({type:'apps',app:'vpn'});}} onClick={()=>open({kind:'vpn'})}><img src="/softether-vpn-icon.png" alt=""/><span>VPN</span></button>}
    {[0,1,2].map(index=>{const link=config?.links[index];return <button key={index} className={`shortcut-slot ${link?.target?'configured':''}`} aria-label={link?.target?link.label:t('Add shortcut')+' '+(index+1)} title={link?.target?link.label:t('Add shortcut')+' '+(index+1)} onContextMenu={e=>{e.preventDefault();setEditing({type:'links',index});}} onClick={()=>link?.target?open({kind:'link',index}):setEditing({type:'links',index})}>{link?.target?<span>{link.label.slice(0,2)}</span>:<Icon name="add"/>}</button>;})}
    <button className="shortcut-settings" aria-label={t('Edit shortcuts')} title={t('Edit shortcuts')} onClick={()=>setEditing({type:'apps'})}>···</button>
  </nav>;
}
export function FileSearchLauncher(){
  const {t}=useI18n(),{setSearchOpen}=useContext(Context);
  return <button className="file-search-launcher" onClick={()=>setSearchOpen(true)}><Icon name="search"/><span><strong>{t('Search files')}</strong><small>{t('This PC · Company network')}</small></span></button>;
}
function FileSearch({config,error,onClose,onEdit,onOpen}){
  const {t}=useI18n(),dialog=useRef(null),input=useRef(null),request=useRef(null),timer=useRef(null),generation=useRef(0);
  const [query,setQuery]=useState(''),[scope,setScope]=useState('all'),[result,setResult]=useState(null),[busy,setBusy]=useState(false),[message,setMessage]=useState(error),[job,setJob]=useState(null);
  useEffect(()=>{dialog.current.showModal();input.current.focus();return()=>{generation.current++;clearTimeout(timer.current);request.current?.abort();};},[]);
  const isNetwork=query.trim().startsWith('\\\\');
  async function search(e){e.preventDefault();if(isNetwork){onOpen({kind:'network-address',address:query.trim()});return;}const run=++generation.current;clearTimeout(timer.current);request.current?.abort();request.current=new AbortController();setBusy(true);setMessage('');setResult(null);
    try{
      const started=await api('/search',{query,scope},request.current.signal);if(run!==generation.current)return;setJob(started.job);
      const poll=async()=>{try{const value=await api('/search/'+started.job,undefined,request.current.signal);if(run!==generation.current)return;if(value.done){setResult(value);setBusy(false);}else timer.current=setTimeout(poll,350);}catch(e){if(e.name!=='AbortError'&&run===generation.current){setMessage(e.message);setBusy(false);}}};await poll();
    }catch(e){if(e.name!=='AbortError'&&run===generation.current){setMessage(e.message);setBusy(false);}}
  }
  return <dialog ref={dialog} className="desktop-search-dialog" aria-label={t('Search local and network files')} onCancel={e=>{e.preventDefault();onClose();}}>
    <div className="desktop-search-heading"><div><span>{t('SUNNY FILE SEARCH')}</span><h2>{t('Find a file or folder')}</h2></div><button className="glass-close" aria-label={t('Close file search')} title={t('Close file search')} onClick={onClose}>×</button></div>
    <form onSubmit={search}><div className="glass-search-field"><Icon name="search"/><input ref={input} aria-label={t('File or folder name')} placeholder={t('Search company, order number, or file name…')} value={query} onChange={e=>setQuery(e.target.value)}/><button disabled={!config||query.trim().length<2} type="submit">{t(isNetwork?'Open network computer':'Search')}</button></div>
      <div className="search-scope-row"><label>{t('Look in')}<select aria-label={t('Search folder')} value={scope} onChange={e=>setScope(e.target.value)}><option value="all">{t('All added folders')}</option>{config?.roots.map((root,index)=><option value={index} key={root.path}>{root.label==='Work files'?t('Work files'):root.label}</option>)}</select></label><button type="button" onClick={onEdit}><Icon name="folder_open"/>{t('Search folders')}</button><button type="button" onClick={()=>onOpen({kind:'network'})}><Icon name="folder_open"/>{t('Network')}</button></div>
    </form>
    <p className="file-search-explanation">{t('Searches file and folder names, not their contents. Nothing is uploaded.')}<br/>{t('Type \\\\COMPUTER or \\\\COLLEAGUE and press Enter to open their shared folders.')}</p>
    <div className="file-search-results" aria-live="polite">
      {busy&&<div className="file-search-empty">{t('Searching folders…')}<small>{t('Network folders may take a moment.')}</small></div>}
      {message&&<div className="file-search-message" role="alert">{t(message)}</div>}
      {result&&<><div className="file-search-count">{result.results.length} {t('results')}{result.limited&&<span> · {t('Try a more specific name for more results.')}</span>}</div>{result.warnings.map((w,i)=><p className="file-search-message" key={i}>{t(w)}</p>)}{!result.results.length&&<div className="file-search-empty">{t('No matching files. Try another name or add a search folder.')}</div>}{result.results.map((r,index)=><article className="file-search-result" key={r.path}><Icon name={r.folder?'folder_open':'description'}/><div><button disabled={!r.canOpen} onClick={()=>onOpen({kind:'result',job,index})}>{r.name}</button><small title={r.path}>{r.path}</small></div><button className="result-folder" title={t('Open containing folder')} onClick={()=>onOpen({kind:'result',job,index,showFolder:true})}>{t('Open folder')}</button></article>)}</>}
      {!busy&&!result&&!message&&<div className="file-search-empty">{t('Type a name above to search your added folders.')}<small>{t('Add a company network folder using its shared folder path.')}</small></div>}
    </div>
  </dialog>;
}
function ToolsSettings({config,initial,onClose,onSave}){
  const {t}=useI18n(),dialog=useRef(null);
  const [draft,setDraft]=useState(()=>({roots:(config?.roots||[]).map(r=>({...r})),links:[0,1,2].map(i=>({...config?.links[i]||{label:'',target:''}})),apps:Object.fromEntries(['obsidian','pos','vpn'].map(kind=>[kind,{path:'',visible:true,...config?.apps?.[kind]}]))})),[tab,setTab]=useState(initial.type),[error,setError]=useState(''),[saving,setSaving]=useState(false),[choosing,setChoosing]=useState(false);
  useEffect(()=>{dialog.current.showModal();},[]);
  const change=(kind,index,key,value)=>setDraft(d=>({...d,[kind]:d[kind].map((r,i)=>i===index?{...r,[key]:value}:r)}));
  const changeApp=(kind,key,value)=>setDraft(d=>({...d,apps:{...d.apps,[kind]:{...d.apps[kind],[key]:value}}}));
  async function choose(kind,index){setChoosing(true);setError('');try{const result=await api('/choose-app',{});if(!result.cancelled){if(kind==='links')change('links',index,'target',result.path);else changeApp(kind,'path',result.path);}}catch(e){setError(e.message);}finally{setChoosing(false);}}
  async function save(e){e.preventDefault();setSaving(true);setError('');try{await onSave({...draft,roots:draft.roots.filter(r=>r.path.trim())});}catch(e){setError(e.message);setSaving(false);}}
  return <dialog ref={dialog} className="desktop-tools-settings" aria-label={t('Desktop links and search settings')} onCancel={e=>{e.preventDefault();if(!saving)onClose();}}><form onSubmit={save}>
    <div className="tools-settings-heading"><h2>{t('Links and search folders')}</h2><button type="button" aria-label={t('Close desktop settings')} onClick={onClose}>×</button></div>
    <div className="tools-settings-tabs"><button type="button" className={tab==='apps'?'active':''} onClick={()=>setTab('apps')}>{t('Apps on this computer')}</button><button type="button" className={tab==='links'?'active':''} onClick={()=>setTab('links')}>{t('Shortcuts')}</button><button type="button" className={tab==='folders'?'active':''} onClick={()=>setTab('folders')}>{t('Search folders')}</button></div>
    {tab==='apps'?<>{initial.app&&config?.appStatus?.[initial.app]?.found===false&&<p role="alert" className="desktop-settings-error">{t('This app was not found. Choose its app file on this computer.')}</p>}<p>{t('Each computer uses its own app locations. Choose an app once, then Save. Nothing is installed or shared.')}</p>{['obsidian','pos','vpn'].map(kind=><div className={`app-location-row ${initial.app===kind?'needs-setup':''}`} key={kind}><div className="app-location-heading"><strong>{({obsidian:'Obsidian',pos:'Sunny POS',vpn:'SoftEther VPN'})[kind]}</strong><label><input type="checkbox" aria-label={t('Show app button')+' '+kind} checked={draft.apps[kind].visible} onChange={e=>changeApp(kind,'visible',e.target.checked)}/>{t('Show button')}</label></div><label>{t('App file (.exe)')}<input aria-label={t('App file (.exe)')+' '+kind} placeholder={t('Automatic — or choose the app file')} value={draft.apps[kind].path} onChange={e=>changeApp(kind,'path',e.target.value)}/></label><div className="app-location-actions"><button type="button" disabled={choosing} onClick={()=>choose(kind)}>{t(choosing?'Choosing app…':'Choose app')}</button><button type="button" disabled={choosing} onClick={()=>changeApp(kind,'path','')}>{t('Use automatic')}</button><small>{t(draft.apps[kind].path?(config?.apps?.[kind]?.path===draft.apps[kind].path&&config?.appStatus?.[kind]?.found===false?'The selected app file is unavailable.':'Saved for this computer only.'):config?.appStatus?.[kind]?.found?'Found automatically.':'Not found automatically. Choose the app file.')}</small></div></div>)}<p>{t('Obsidian is optional. Its button stays hidden when it is not installed. POS opens its sign-in screen; VPN opens its manager. Sign in and connect yourself.')}</p></>:tab==='links'?<><p>{t('Add a website, Windows folder, or app (.exe). Right-click a shortcut to edit it later.')}</p>{draft.links.map((link,index)=><div className="shortcut-edit-row" key={index}><b>{index+1}</b><label>{t('Name')}<input aria-label={t('Shortcut name')+' '+(index+1)} value={link.label} onChange={e=>change('links',index,'label',e.target.value)}/></label><label>{t('Website, folder, or app')}<input aria-label={t('Shortcut destination')+' '+(index+1)} placeholder="https://… or C:\…" value={link.target} onChange={e=>change('links',index,'target',e.target.value)}/></label><button type="button" disabled={choosing} onClick={()=>choose('links',index)}>{t('Choose app')}</button></div>)}</>:<><p>{t('Only these folders are searched. Add a shared network folder such as \\\\SERVER\\Shared. Windows uses your existing network access.')}</p>{draft.roots.map((root,index)=><div className="folder-edit-row" key={index}><label>{t('Name')}<input aria-label={t('Folder name')+' '+(index+1)} value={root.label} onChange={e=>change('roots',index,'label',e.target.value)}/></label><label>{t('Folder path')}<input aria-label={t('Folder path')+' '+(index+1)} placeholder="C:\… or \\SERVER\Shared" value={root.path} onChange={e=>change('roots',index,'path',e.target.value)}/></label><button type="button" title={t('Remove search folder')} onClick={()=>setDraft(d=>({...d,roots:d.roots.filter((_,i)=>i!==index)}))}>×</button></div>)}<button type="button" className="add-search-root" disabled={draft.roots.length>=8} onClick={()=>setDraft(d=>({...d,roots:[...d.roots,{label:'',path:''}]}))}>+ {t('Add folder')}</button></>}
    {error&&<p className="desktop-settings-error" role="alert">{t(error)}</p>}<div className="tools-settings-footer"><button type="button" onClick={onClose}>{t('Cancel')}</button><button className="primary-button" type="submit" disabled={saving||choosing||!config}>{t(saving?'Saving…':'Save')}</button></div>
  </form></dialog>;
}
