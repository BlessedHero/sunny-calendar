import {useI18n} from './i18n';
import React from 'react';

export function PageCorners({onTurn,busy}){
  const {t,language}=useI18n();
  return <>{['top-left','bottom-left','top-right','bottom-right'].map(corner=>{
    const forward=corner.startsWith('top');
    return <button key={corner} className={`page-corner ${corner}`} aria-label={t(`${forward?'Next':'Previous'} month from ${corner.replace('-',' ')} corner`)} title={t(`${forward?'Next':'Previous'} month — turn page`)} disabled={busy} onClick={()=>onTurn(forward?1:-1)}><span className="corner-arrow" aria-hidden="true">{forward?'↑':'↓'}</span><span className="corner-label" aria-hidden="true">{t(forward?'UP MONTH':'DOWN MONTH')}</span></button>;
  })}</>;
}

export function TurningPage({turn}){
  const {t,language}=useI18n();
  if(!turn)return null;
  return <div className={`month-turn ${turn.forward?'forward':'backward'} ${turn.reduced?'reduce-turn':''}`} aria-hidden="true" inert><div className="month-turn-front" dangerouslySetInnerHTML={{__html:turn.html}}/><div className="month-turn-back"><span>{t("Sunny Calendar")}</span></div></div>;
}
