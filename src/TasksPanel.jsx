import {taskTextColor} from './task-colors';
import {useI18n} from './i18n';
import React from 'react';
import {taskLayers,isTaskComplete,isTeamTask,MAX_TASKS,PREVIEW_TASKS} from './task-layers';
import {plainText} from './local-store';

export function TasksPanel({doc,ready,today,tomorrow,onDate,onClose,onOpen,onAdd,onComplete,onDelete,TaskCheck}){
  const {t,language}=useI18n();
  const layers=taskLayers(doc);
  const completed=layers.filter((_,index)=>isTaskComplete(doc,index)).length;
  return <aside className="right-sidebar tasks-sidebar" aria-label={t("Tasks")}>
    <div className="notes-heading"><div><span>{t("TASKS")}</span><h2>{t("My Tasks")}</h2></div><button className="icon-button" aria-label={t("Close tasks panel")} title={t("Close tasks panel")} onClick={onClose}><img className="icon" src="/icons/close.svg" alt=""/></button></div>
    <label className="task-date-label">{t("Tasks for")}<input aria-label={t("Task date")} type="date" value={doc.date} onChange={e=>e.target.value&&onDate(e.target.value)}/></label>
    <div className="task-date-shortcuts"><button onClick={()=>onDate(today)}>{t("Today")}</button><button onClick={()=>onDate(tomorrow)}>{t("Tomorrow")}</button></div>
    <button className="take-note add-sidebar-task" title={t("Add a task")} disabled={!ready||layers.length>=MAX_TASKS} onClick={()=>onAdd(doc)}><img className="icon" src="/icons/add.svg" alt=""/>{t("Add a task")}</button>
    <div className="sidebar-task-list">{layers.map((html,index)=>{
      const lines=plainText(html).trim().split('\n').filter(Boolean);
      const done=isTaskComplete(doc,index);
      return <article className={`sidebar-task task-${index%PREVIEW_TASKS+1} ${done?'is-completed':'is-pending'} ${!done&&taskTextColor(doc,index)==='#b3261e'?'task-red-pending':''} ${isTeamTask(doc,index)?'team-task-card':''}`} style={{'--task-text-color':taskTextColor(doc,index)}} key={index}>
        <TaskCheck doc={doc} index={index} onChange={onComplete} enabled={ready}/>
        <button className="sidebar-task-open" aria-label={t(`Open task ${index+1} for ${doc.date}`)} title={t(`Open task ${index+1} for ${doc.date}`)} onClick={()=>onOpen(doc,index)}>{isTeamTask(doc,index)&&<span className="sidebar-team-label">{t('Team draft — local only')}</span>}<strong>{lines[0]||t('Task')+' '+(index+1)}</strong>{lines.length>1&&<span>{lines.slice(1).join('\n')}</span>}<small>{t("More · Edit")}</small></button>
        <button className="sidebar-task-delete" title={t("Delete this task")} aria-label={t(`Delete task ${index+1} for ${doc.date}`)} disabled={!ready} onClick={()=>onDelete(doc,index)}><img className="icon" src="/icons/delete.svg" alt=""/></button>
      </article>;
    })}{!layers.length&&<div className="empty-notes"><p>{t("No tasks for this date.")}<br/>{t("Choose Add a task to start.")}</p></div>}</div>
    <p className="notes-hint">{layers.length?t(`${completed} of ${layers.length} completed. `):''}{t("These are the same tasks shown in the date box.")}</p>
  </aside>;
}
