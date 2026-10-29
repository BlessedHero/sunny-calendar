import {useI18n} from './i18n';
import React from 'react';

const COLORS=[['Black','#111111'],['Red','#b3261e'],['Orange','#c45100'],['Gold','#9c7400'],['Green','#137333'],['Blue','#1967d2'],['Purple','#8430a3'],['Pink','#b32e78'],['Brown','#795548'],['Gray','#5f6368']];

export function ColorPalette({value,onChange,disabled=false}){
  const {t,language}=useI18n();
  return <div className="color-palette" role="group" aria-label={t("Text colors")} title={t(disabled?'Task text uses red for unfinished and black for completed. Colors are available for reference notes.':'Select text in a reference note, then choose a color.')}>{COLORS.map(([name,color])=><button type="button" key={color} className="color-swatch" style={{'--swatch-color':color}} aria-label={t(`${name} text`)} title={t(disabled?'Task color follows its checkbox':name)} disabled={disabled} aria-pressed={value===color} onMouseDown={e=>e.preventDefault()} onClick={()=>onChange(color)}/>)}</div>;
}
