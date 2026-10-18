const C=window.RN_CONTENT, $=s=>document.querySelector(s);
const safeURL=s=>{if(typeof s!=='string'||!s.trim())return '';try{const u=new URL(s,location.href);return ['https:','http:'].includes(u.protocol)?u.href:''}catch{return ''}};
function youtubeId(value){
  try{const u=new URL(value);if(u.protocol!=='https:')return '';let id='';
    if(u.hostname==='youtu.be')id=u.pathname.split('/')[1];
    else if(['youtube.com','www.youtube.com','m.youtube.com','youtube-nocookie.com','www.youtube-nocookie.com'].includes(u.hostname))id=u.searchParams.get('v')||u.pathname.match(/^\/(?:embed|shorts|live)\/([^/]+)/)?.[1]||'';
    return /^[A-Za-z0-9_-]{11}$/.test(id)?id:'';
  }catch{return ''}
}
function media(el,data,title){
  const id=youtubeId(data.src);
  if(id){
    const play=document.createElement('button');play.type='button';play.className='video-facade';play.setAttribute('aria-label','Play '+title);
    const poster=document.createElement('img');poster.src=safeURL(data.poster)||'https://i.ytimg.com/vi/'+id+'/hqdefault.jpg';poster.alt='';poster.loading='lazy';
    const icon=document.createElement('span');icon.className='play';icon.textContent='▶';
    const label=document.createElement('strong');label.textContent=title;
    play.append(poster,icon,label);el.append(play);
    play.onclick=()=>{const f=document.createElement('iframe');f.src='https://www.youtube-nocookie.com/embed/'+id+'?autoplay=1&playsinline=1';f.title=title;f.allow='autoplay; encrypted-media; picture-in-picture; fullscreen';f.allowFullscreen=true;f.referrerPolicy='strict-origin-when-cross-origin';el.replaceChildren(f);f.focus()};
  }else if(data.src&&safeURL(data.src)){
    const u=new URL(safeURL(data.src));
    if(u.hostname==='player.vimeo.com'){const f=document.createElement('iframe');f.src=u.href;f.title=title;f.allowFullscreen=true;f.loading='lazy';el.append(f)}
    else if(/\.(mp4|webm)(?:$|\?)/i.test(u.href)){const v=document.createElement('video');v.controls=true;v.preload='none';v.playsInline=true;v.src=u.href;if(data.poster)v.poster=safeURL(data.poster);el.append(v)}
    else placeholder();
  }else placeholder();
  function placeholder(){el.innerHTML='<div class="placeholder"><span class="play" aria-hidden="true">▶</span><strong></strong><small>FILM COMING SOON</small></div>';el.querySelector('strong').textContent=title}
}
media($('[data-video="hero"]'),C.hero,'Your brand. The next chapter.');media($('[data-video="story"]'),C.story,'A little about us.');
C.creators.forEach((c,i)=>{const el=document.createElement(c.url?'a':'div');el.className='creator';if(c.url){el.href=safeURL(c.url);el.target='_blank';el.rel='noopener noreferrer'}const a=document.createElement('span');a.className='avatar';if(c.image){const im=document.createElement('img');im.src=safeURL(c.image);im.alt=c.name;im.loading='lazy';a.append(im)}else{a.textContent=String(i+1).padStart(2,'0');a.setAttribute('aria-label','Creator profile coming soon')}el.append(a);if(c.name){const s=document.createElement('span');s.textContent=c.name;el.append(s)}$('#creators').append(el)});
C.results.forEach((r,i)=>{let e;if(r.src){e=document.createElement('div');e.className='result-card result-video media';media(e,r,r.caption||'Client work')}else if(r.image){e=document.createElement('button');e.className='result-card';const im=document.createElement('img');im.src=safeURL(r.image);im.alt=r.caption||'Client result';im.loading='lazy';e.append(im);e.type='button';e.onclick=()=>{const d=$('#lightbox');d.querySelector('img').src=im.src;d.querySelector('img').alt=im.alt;d.querySelector('p').textContent=r.caption;d.showModal()}}else{e=document.createElement('div');e.className='result-card empty';e.innerHTML='<span>↗</span><p></p><small>CLIENT HIGHLIGHTS · COMING SOON</small>';e.querySelector('p').textContent=['The views','The growth','The feedback'][i%3]}e.hidden=i>2;$('#results-grid').append(e)});
$('#more-results').hidden=C.results.length<=3;$('#more-results').onclick=()=>{const expanded=$('#more-results').getAttribute('aria-expanded')==='true';document.querySelectorAll('.result-card').forEach((e,i)=>e.hidden=i>2&&expanded);$('#more-results').setAttribute('aria-expanded',String(!expanded));$('#more-results').innerHTML=expanded?'View more <span>↓</span>':'View less <span>↑</span>'};$('#lightbox button').onclick=()=>$('#lightbox').close();
C.faq.forEach((q,i)=>{const d=document.createElement('details');const s=document.createElement('summary');s.textContent=q.question;const v=document.createElement('div');v.className='media';media(v,q,'Reyhane answers this one on camera');d.append(s,v);d.addEventListener('toggle',()=>{if(!d.open){d.querySelectorAll('video').forEach(v=>v.pause());if(d.querySelector('iframe')){v.replaceChildren();media(v,q,'Reyhane answers this one on camera')}}});$('#faq-list').append(d)});
if(C.handle){const h=document.createElement('span');h.className='social-handle';h.textContent='@'+String(C.handle).replace(/^@/,'');$('#socials').append(h)}Object.entries(C.socials).forEach(([name,url])=>{if(name==='tiktok'&&!url)return;const a=document.createElement(url?'a':'span');a.textContent=name==='linkedin'?'LinkedIn':name[0].toUpperCase()+name.slice(1);if(url){a.href=name==='email'?'mailto:'+url:safeURL(url);if(name!=='email'){a.target='_blank';a.rel='noopener noreferrer'}}else a.title='Profile coming soon';$('#socials').append(a)});$('#year').textContent=new Date().getFullYear();
const dubaiDate=d=>new Intl.DateTimeFormat('en-CA',{timeZone:'Asia/Dubai',year:'numeric',month:'2-digit',day:'2-digit'}).format(d);let month=new Date(dubaiDate(new Date())+'T12:00:00'),selectedDate='',selectedTime='',request=0,submitting=false;month.setDate(1);const now=new Date(dubaiDate(new Date())+'T12:00:00'),max=new Date(dubaiDate(new Date(Date.now()+90*86400000))+'T12:00:00');const dayKey=d=>`${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`;
function calendar(){const y=month.getFullYear(),m=month.getMonth();$('#month-title').textContent=month.toLocaleDateString('en-US',{month:'long',year:'numeric'});$('#calendar').replaceChildren();for(let i=0;i<(new Date(y,m,1).getDay()+6)%7;i++)$('#calendar').append(document.createElement('span'));for(let n=1;n<=new Date(y,m+1,0).getDate();n++){const d=new Date(y,m,n),key=dayKey(d),b=document.createElement('button');b.type='button';b.textContent=n;b.disabled=key<dayKey(now)||key>dayKey(max);b.className=(key===selectedDate?'selected ':'')+(key===dayKey(now)?'today':'');b.setAttribute('aria-label',d.toLocaleDateString('en-US',{dateStyle:'full'}));b.setAttribute('aria-pressed',String(key===selectedDate));b.onclick=()=>loadSlots(key);$('#calendar').append(b)}$('#prev-month').disabled=y===now.getFullYear()&&m===now.getMonth();$('#next-month').disabled=y===max.getFullYear()&&m===max.getMonth()}
$('#prev-month').onclick=()=>{month.setMonth(month.getMonth()-1);calendar()};$('#next-month').onclick=()=>{month.setMonth(month.getMonth()+1);calendar()};calendar();
async function loadSlots(date){if(submitting)return;selectedDate=date;selectedTime='';const seq=++request;calendar();$('#slots').replaceChildren();$('#booking-form').hidden=true;$('#confirmation').hidden=true;$('#slot-status').textContent='Checking available times…';try{const r=await fetch('/api/availability?date='+date),data=await r.json();if(seq!==request)return;if(!r.ok)throw Error(data.error||'Availability is temporarily unavailable.');$('#slot-status').textContent=data.available.length?'Choose a time · Dubai (UTC+04:00)':'No available times on this day. Please choose another date.';data.available.forEach(time=>{const b=document.createElement('button');b.type='button';b.textContent=time;b.onclick=()=>{if(submitting)return;selectedTime=time;$('#slots').querySelectorAll('button').forEach(x=>x.classList.toggle('selected',x===b));$('#booking-form').hidden=false;$('#selected-slot').textContent=new Date(date+'T12:00:00').toLocaleDateString('en-US',{dateStyle:'long'})+' · '+time+' Dubai time';$('#local-time').textContent='In your timezone: '+new Date(date+'T'+time+':00+04:00').toLocaleString(undefined,{dateStyle:'medium',timeStyle:'short'})+' ('+Intl.DateTimeFormat().resolvedOptions().timeZone+')';$('#booking-form .form-status').textContent=''};$('#slots').append(b)})}catch(e){if(seq===request)$('#slot-status').textContent=e instanceof SyntaxError?'Booking opens soon. Please check back shortly.':e.message}}
let retryKey='',retryPayload='';
$('#booking-form').onsubmit=async e=>{
  e.preventDefault();if(submitting)return;
  const form=e.currentTarget,b=form.querySelector('button[type=submit]'),status=form.querySelector('.form-status');
  const bookingDate=selectedDate,bookingTime=selectedTime;
  const body={...Object.fromEntries(new FormData(form)),consent:form.elements.consent.checked,date:bookingDate,time:bookingTime};
  const payload=JSON.stringify(body);if(payload!==retryPayload){retryKey=crypto.randomUUID();retryPayload=payload}body.request_id=retryKey;
  submitting=true;b.disabled=true;status.textContent='Reserving your call…';
  const controls=[...document.querySelectorAll('#calendar button,#slots button,#prev-month,#next-month')];const disabled=controls.map(x=>x.disabled);controls.forEach(x=>x.disabled=true);
  try{
    const r=await fetch('/api/book',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
    const data=await r.json();if(!r.ok){const err=Error(data.error||'Could not reserve your call.');err.conflict=r.status===409;throw err}
    form.hidden=true;$('#slots').replaceChildren();$('#slot-status').textContent='';const c=$('#confirmation');c.replaceChildren();
    const h=document.createElement('h3');h.textContent='Your time is reserved.';
    const p=document.createElement('p');p.textContent=`${bookingDate} at ${bookingTime} · Dubai time. Your answers have been sent to Reyhane. She’ll contact you by email or WhatsApp with the meeting details.`;
    const ref=document.createElement('small');ref.textContent='Booking reference: '+data.id;
    c.append(h,p,ref);c.hidden=false;c.tabIndex=-1;c.focus();form.reset();retryPayload='';
  }catch(err){
    if(err.conflict){submitting=false;await loadSlots(bookingDate);$('#slot-status').textContent=err.message;}
    else status.textContent=err instanceof SyntaxError?'Booking service is unavailable. Please try again.':err.message;
  }finally{submitting=false;b.disabled=false;controls.forEach((x,i)=>x.disabled=disabled[i]);calendar()}
};
