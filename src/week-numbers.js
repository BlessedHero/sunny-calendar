// ISO weeks start on Monday; week 1 contains January 4.
// Work with calendar dates in UTC to avoid daylight-saving offsets.
export function isoWeek(date){
  const thursday=new Date(Date.UTC(date.getFullYear(),date.getMonth(),date.getDate()));
  thursday.setUTCDate(thursday.getUTCDate()+4-(thursday.getUTCDay()||7));
  const year=thursday.getUTCFullYear(),first=new Date(Date.UTC(year,0,1));
  return {year,week:Math.ceil(((thursday-first)/86400000+1)/7)};
}

// The month keeps its Sunday-first layout. Label each row by its Monday,
// which gives the ISO week shared by the Monday-through-Saturday dates.
export function rowWeek(sunday){
  const monday=new Date(sunday.getFullYear(),sunday.getMonth(),sunday.getDate()+1);
  return {...isoWeek(monday),monday};
}
