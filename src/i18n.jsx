import React,{createContext,useContext,useEffect,useState} from 'react';
import {translate} from './translations';
const Context=createContext(null);
export function LanguageProvider({children}){
  const [language,setLanguage]=useState(()=>{try{return localStorage.getItem('sunny-calendar-clean-language')==='ko'?'ko':'en';}catch{return 'en';}});
  useEffect(()=>{try{localStorage.setItem('sunny-calendar-clean-language',language);}catch{}document.documentElement.lang=language;document.title=language==='ko'?'써니전자 캘린더 · 데모':'Sunny Calendar · Demo';},[language]);
  return <Context.Provider value={{language,setLanguage,t:text=>translate(text,language)}}>{children}</Context.Provider>;
}
export const useI18n=()=>useContext(Context);
export function LanguageSwitch(){
  const {language,setLanguage}=useI18n();
  return <button type="button" role="switch" className={`language-switch ${language==='ko'?'is-korean':''}`} aria-checked={language==='ko'} aria-label="Eng / Kor" title={language==='ko'?'한국어 사용 중 · 클릭하면 영어로 변경':'English selected · Click for Korean'} onMouseDown={e=>e.preventDefault()} onClick={()=>setLanguage(language==='ko'?'en':'ko')}><span className="language-thumb" aria-hidden="true"/><span lang="en">Eng</span><span lang="en">Kor</span></button>;
}
