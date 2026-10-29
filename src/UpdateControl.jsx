import React,{useEffect,useState} from 'react';
import {createPortal} from 'react-dom';
import {useI18n} from './i18n';
import release from '../app-release.json';
import './updates.css';

async function api(action,body){
  const response=await fetch('/local-api/updates/'+action,body===undefined?{cache:'no-store'}:{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
  if(!response.ok)throw Error('update-service');
  return response.json();
}
let startupCheck;
const checkOnOpen=()=>startupCheck||(startupCheck=api('check',{automatic:true}));

export function UpdateControl({ready,beforeDownload}){
  const {t,language}=useI18n();
  const [state,setState]=useState({phase:'checking',currentVersion:release.version});
  const [busy,setBusy]=useState(false),[message,setMessage]=useState(''),[details,setDetails]=useState(false),[prepared,setPrepared]=useState(false);
  useEffect(()=>{const native=window.chrome?.webview;if(!native)return;const receive=e=>{if(e.data==='sunny-update-failed'){setBusy(false);setMessage('Could not start the installer. Your calendar stays open. Try again after saving.');}};native.addEventListener('message',receive);return()=>native.removeEventListener('message',receive);},[]);
  useEffect(()=>{let alive=true;checkOnOpen().then(value=>{if(alive)setState(value);}).catch(()=>{if(alive)setState({phase:'unavailable',currentVersion:release.version});});return()=>{alive=false;};},[]);
  // A second window may have started the same check. Poll only that local result.
  useEffect(()=>{if(state.phase!=='checking')return;let alive=true;const timer=setTimeout(()=>api('status').then(value=>{if(alive)setState(value);}).catch(()=>{if(alive)setState(s=>({...s,phase:'unavailable'}));}),1500);return()=>{alive=false;clearTimeout(timer);};},[state]);
  const available=state.phase==='available';
  const label=busy?t('Preparing update…'):state.phase==='checking'?t('Checking updates…'):available?
    (language==='ko'?`새 버전 v${state.latestVersion} 업데이트 가능`:`Update available · v${state.latestVersion}`):state.phase==='current'?
    (language==='ko'?`최신 버전 · v${state.currentVersion}`:`Up to date · v${state.currentVersion}`):t('Check updates');
  async function click(){
    if(busy||!ready)return;
    if(available&&!state.canOpenInstaller){setMessage('This working test copy stays separate. Updates through this button are for the installed coworker edition.');setDetails(true);return;}
    setBusy(true);setMessage('');
    try{
      if(available){
        await beforeDownload();const value=await api('prepare',{});setState(value);setPrepared(true);
        setMessage('A backup was saved on this computer. Click Update below. Sunny Calendar will close and reopen. Windows may still ask you to click Install.');setDetails(true);
      }else{setState(s=>({...s,phase:'checking'}));const value=await api('check',{});setState(value);if(value.phase==='unavailable'){setMessage('Could not check online. Your calendar still works. Try again later.');setDetails(true);}}
    }catch{setMessage('Could not prepare the update. Your calendar is unchanged. Try again later.');setDetails(true);}
    finally{setBusy(false);}
  }
  async function updateNow(){
    setBusy(true);
    try{
      await beforeDownload();
      if(window.chrome?.webview){window.chrome.webview.postMessage('sunny-update-now');return;}
      await api('open',{});setPrepared(false);setMessage('The installer download is open. Use the installed Windows app for the close-and-reopen Update button.');
    }catch{setMessage('Could not start the installer. Your calendar stays open. Try again after saving.');}
    setBusy(false);
  }
  const title=state.phase==='unavailable'?t('Could not check online. Your calendar still works. Try again later.'):
    t('Checks for a new version when this app opens. Your notes and pictures are not uploaded.');
  return <div className="app-update-control"><button type="button" className={`app-update-button ${available?'update-available':''}`} title={title} aria-label={label} disabled={!ready||busy||state.phase==='checking'} onClick={click}>
    <img src={available?'/icons/download.svg':'/icons/check_circle.svg'} alt=""/><span>{label}</span></button>
    {details&&createPortal(<div className="modal-backdrop update-backdrop"><section className="update-info" role="dialog" aria-modal="true" aria-label={t(prepared?'Sunny Calendar — Update now':'Sunny Calendar updates')}><h2>{t(prepared?'Sunny Calendar — Update now':'Sunny Calendar updates')}</h2><p>{t(message)}</p>{prepared?<div className="update-dialog-actions"><button disabled={busy} onClick={()=>setDetails(false)}>{t('Cancel')}</button><button className="primary-button" disabled={busy} onClick={updateNow}>{t(busy?'Opening installer…':'Update')}</button></div>:<button className="primary-button" onClick={()=>setDetails(false)}>{t('Got it')}</button>}</section></div>,document.body)}
  </div>;
}
