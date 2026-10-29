import React,{useEffect,useRef} from 'react';
import {useI18n} from './i18n';
import {isTeamTask} from './task-layers';

export function TeamTaskToggle({doc,index,onChange,enabled=true,connected=false}){
  const {t}=useI18n(),team=isTeamTask(doc,index);
  const action=t(team?'Make this task personal':'Prepare this task as a team draft');
  return <button type="button" className={`team-task-toggle ${team?(connected?'is-team team-connected':'is-team team-offline'):''}`} aria-pressed={team} aria-label={`${action} · ${doc.date} · ${index+1}`} title={action} disabled={!enabled} onClick={()=>onChange(doc,index,!team)}><b aria-hidden="true">{team?'++':'+'}</b>{t(team?(connected?'Team connected':'Team not connected'):'Personal')}</button>;
}
export function TeamDraftNotice(){
  const {t}=useI18n();
  return <p className="team-draft-notice" role="status">{t('Team draft — saved only on this computer. Coworker sync is not connected yet.')}</p>;
}

export function TeamModeDialog({enabled,onEnable,onClose}){
  const {t}=useI18n(),dialog=useRef(null);
  useEffect(()=>{dialog.current.showModal();},[]);
  return <dialog ref={dialog} className="team-mode-dialog" aria-label={t('Sunny team sharing setup')} onCancel={e=>{e.preventDefault();onClose();}}><h2>{t('One Sunny sharing group')}</h2><p className="team-connection-status">{t('Coworker sync: Not connected')}</p><p>{t('Enable team draft mode once. It stays enabled after closing the app until you turn it off in Settings.')}</p><p>{t('The green ++ creates outlined team drafts. Drafts currently save only on this computer; enabling this setting does not connect coworkers yet.')}</p><p>{t('Turning the mode off keeps existing drafts and personal tasks. The next ++ click will ask to enable it again.')}</p><div><button onClick={onClose}>{t('Cancel')}</button><button className="primary-button" onClick={onEnable}>{t(enabled?'Keep mode enabled':'Enable team draft mode')}</button></div></dialog>;
}
