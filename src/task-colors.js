// A task's display color is separate from its saved rich text.
export const PERSONAL_PENDING_COLOR = '#b3261e';
export const TEAM_PENDING_COLOR = '#137333';
export const COMPLETED_COLOR = '#111111';
export const TASK_COLORS = ['#111111','#b3261e','#c45100','#9c7400','#137333','#1967d2','#8430a3','#b32e78','#795548','#5f6368'];
export const savedTaskColor = (doc,index) => TASK_COLORS.includes(doc.taskColors?.[index]) ? doc.taskColors[index] : null;
export function taskTextColor(doc,index){
  if(doc.completedLayers?.[index]===true)return COMPLETED_COLOR;
  return doc.teamLayers?.[index]===true ? savedTaskColor(doc,index)||TEAM_PENDING_COLOR : PERSONAL_PENDING_COLOR;
}
