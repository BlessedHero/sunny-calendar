import {useI18n} from './i18n';
import React from 'react';
import {rowWeek} from './week-numbers';

export function WeekNumber({start,current}){
  const {t,language}=useI18n();
  const info=rowWeek(start),active=info.year===current.year&&info.week===current.week;
  const beginning=info.monday.toLocaleDateString(language==='ko'?'ko-KR':'en-US',{month:'short',day:'numeric',year:'numeric'});
  return <div className={`week-number ${active?'current-week-number':''}`} role="rowheader" aria-label={language==='ko'?`${info.year}년 ${info.week}주차, 월요일 ${beginning}`:`ISO week ${info.week} of ${info.year}, Monday ${beginning}`} aria-current={active?'true':undefined} title={language==='ko'?`${info.year}년 ${info.week}주차 · 월요일 ${beginning}`:`ISO week ${info.week} of ${info.year} · Monday ${beginning}`}><span>{t("W")}{String(info.week).padStart(2,'0')}</span></div>;
}
