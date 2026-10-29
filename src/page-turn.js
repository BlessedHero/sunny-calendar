let paperAudio;

export function playPaperTurn(){
  try{
    const Audio=window.AudioContext||window.webkitAudioContext;if(!Audio)return;
    paperAudio=paperAudio||new Audio();
    paperAudio.resume().then(()=>{
      const length=1.35,buffer=paperAudio.createBuffer(1,paperAudio.sampleRate*length,paperAudio.sampleRate),data=buffer.getChannelData(0);
      for(let i=0;i<data.length;i++)data[i]=(Math.random()*2-1)*(.65+.35*Math.sin(i/170));
      const noise=paperAudio.createBufferSource(),filter=paperAudio.createBiquadFilter(),gain=paperAudio.createGain(),now=paperAudio.currentTime;
      noise.buffer=buffer;filter.type='bandpass';filter.frequency.value=1700;filter.Q.value=.65;
      gain.gain.setValueAtTime(.0001,now);gain.gain.exponentialRampToValueAtTime(.045,now+.15);gain.gain.exponentialRampToValueAtTime(.012,now+.6);gain.gain.exponentialRampToValueAtTime(.035,now+.95);gain.gain.exponentialRampToValueAtTime(.0001,now+length);
      noise.connect(filter);filter.connect(gain);gain.connect(paperAudio.destination);noise.start(now);noise.stop(now+length);
    }).catch(()=>{});
  }catch{}
}

export function pageSnapshot(grid){
  if(!grid)return '';
  const copy=grid.cloneNode(true),original=grid.querySelectorAll('input[type="checkbox"]');
  copy.querySelectorAll('input[type="checkbox"]').forEach((n,i)=>{if(original[i].checked)n.setAttribute('checked','');else n.removeAttribute('checked');});
  copy.querySelectorAll('[id]').forEach(n=>n.removeAttribute('id'));
  copy.querySelectorAll('[contenteditable]').forEach(n=>n.setAttribute('contenteditable','false'));
  return copy.outerHTML;
}
