import {useI18n} from './i18n';
import React,{useEffect,useRef} from 'react';

export function DeleteTaskDialog({request,onCancel,onConfirm}){
  const {t,language}=useI18n();
  const dialog=useRef(null);
  useEffect(()=>{dialog.current.showModal();},[]);
  return <dialog ref={dialog} className="delete-task-dialog" aria-labelledby="delete-task-title" onCancel={e=>{e.preventDefault();onCancel();}}>
    <h2 id="delete-task-title">{t("Delete this task?")}</h2>
    <p>{new Date(request.date+'T12:00:00').toLocaleDateString(language==='ko'?'ko-KR':'en-US',{weekday:'long',year:'numeric',month:'long',day:'numeric'})} {t("· Task")} {request.index+1}</p>
    <div className="delete-task-preview">{request.preview||t('Empty task')}</div>
    <p className="delete-task-courtesy">{t("You can use Undo after deleting, until you close or reload the app.")}</p>
    <div className="delete-task-actions"><button className="cancel-delete-button" autoFocus onClick={onCancel}>{t("Cancel")}</button><button className="confirm-delete-button" onClick={onConfirm}>{t("Delete task")}</button></div>
  </dialog>;
}
