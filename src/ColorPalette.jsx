import {useI18n} from './i18n';
import React from 'react';

const COLORS=[['Black','#111111'],['Red','#b3261e'],['Orange','#c45100'],['Gold','#9c7400'],['Green','#137333'],['Blue','#1967d2'],['Purple','#8430a3'],['Pink','#b32e78'],['Brown','#795548'],['Gray','#5f6368']];

export function ColorPalette({value,onChange,disabled=false,mode='note'}){
  const {t}=useI18n();
  const locked=disabled||mode==='personal'||mode==='completed-team';
  const hint=mode==='completed-team'?'Completed team tasks stay black. Uncheck to reopen before choosing a color.':mode==='personal'?'Personal tasks use red for unfinished and black for completed. Colors are available for team drafts and reference notes.':mode==='team'?'Choose a color for this whole team draft. It turns black when completed.':'Select text in a reference note, then choose a color.';
  return <div className="color-palette" role="group" aria-label={t("Text colors")} title={t(hint)}>{COLORS.map(([name,color])=><button type="button" key={color} className="color-swatch" style={{'--swatch-color':color}} aria-label={t(`${name} text`)} title={t(locked?hint:name)} disabled={locked} aria-pressed={value===color} onMouseDown={e=>e.preventDefault()} onClick={()=>onChange(color)}/>)}</div>;
}
