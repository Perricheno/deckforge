/* deckforge viewer-side remote: one small button, follows the presenter over SSE.
   Works on every deck (generated or legacy). Does nothing in ?pdf and only listens in ?thumb. */
(function(){
  var Q=new URLSearchParams(location.search),PDF=Q.has('pdf'),THUMB=Q.has('thumb');
  var slug=location.pathname.split('/').filter(Boolean)[0]||'';
  var slides=function(){return [].slice.call(document.querySelectorAll('.slide'))};
  function index(){return window.__deckIndex?window.__deckIndex():slides().findIndex(function(s){return s.classList.contains('active')})}
  var moving=false;
  function goto(n){
    n=Math.max(0,Math.min(slides().length-1,n));moving=true;
    if(window.__deckGo)window.__deckGo(n);
    else{var d=n-index(),k=d>0?'ArrowRight':'ArrowLeft';for(var i=0;i<Math.abs(d);i++)document.dispatchEvent(new KeyboardEvent('keydown',{key:k,bubbles:true}))}
    setTimeout(function(){moving=false},80);
  }
  if(THUMB){addEventListener('message',function(e){var d=e.data;if(d&&d.deckforge==='go')goto(d.slide)});return}
  if(PDF||!slug||!window.EventSource)return;

  /* ---- ui ---- */
  var css=document.createElement('style');
  css.textContent='.rbtn{position:fixed;left:12px;bottom:12px;z-index:30;width:36px;height:36px;border-radius:50%;border:1px solid var(--line,#e5e5df);background:var(--card,#fff);color:var(--ink,#141412);display:flex;align-items:center;justify-content:center;cursor:pointer;padding:0;transition:.2s;font:inherit}'
  +'.rbtn:hover{border-color:var(--ink,#141412)}.rbtn svg{width:16px;height:16px;stroke:currentColor;fill:none;stroke-width:2;stroke-linecap:round;stroke-linejoin:round}'
  +'.rbtn i{position:absolute;top:4px;right:4px;width:8px;height:8px;border-radius:50%;background:#c9c9c3;border:2px solid var(--card,#fff);transition:.3s}.rbtn.live i{background:#2fb344;box-shadow:0 0 0 0 rgba(47,179,68,.5);animation:rping 2s infinite}'
  +'@keyframes rping{70%{box-shadow:0 0 0 7px rgba(47,179,68,0)}100%{box-shadow:0 0 0 0 rgba(47,179,68,0)}}'
  +'.rpop{position:fixed;left:12px;bottom:56px;z-index:31;width:244px;padding:14px;border-radius:14px;background:var(--card,#fff);border:1px solid var(--line,#e5e5df);box-shadow:0 18px 40px -18px rgba(0,0,0,.35);font:500 13px/1.4 Inter,system-ui,sans-serif;color:var(--ink,#141412);display:none}'
  +'.rpop.open{display:block}.rpop .st{display:flex;gap:8px;align-items:center;color:var(--mute,#6f6f69);font-weight:500;margin-bottom:10px}.rpop .st b{color:var(--ink,#141412);font-weight:600}'
  +'.rpop label{display:flex;justify-content:space-between;align-items:center;padding:8px 0;border-top:1px solid var(--line,#e5e5df);cursor:pointer}'
  +'.rpop .sw{width:34px;height:20px;border-radius:99px;background:#d6d6d0;position:relative;transition:.2s}.rpop .sw::after{content:"";position:absolute;left:2px;top:2px;width:16px;height:16px;border-radius:50%;background:#fff;transition:.2s}'
  +'.rpop input:checked+.sw{background:var(--ink,#141412)}.rpop input:checked+.sw::after{left:16px}.rpop input{display:none}'
  +'.rpop a,.rpop button{display:flex;align-items:center;justify-content:space-between;width:100%;padding:8px 0;border:0;border-top:1px solid var(--line,#e5e5df);background:none;color:inherit;font:inherit;text-decoration:none;cursor:pointer;text-align:left}'
  +'.rpop a:hover,.rpop button:hover{color:var(--acc,#ff4b1f)}'
  +'.rpill{position:fixed;left:50%;bottom:58px;transform:translate(-50%,12px);z-index:32;padding:9px 16px;border-radius:99px;background:var(--ink,#141412);color:#fff;font:500 12.5px Inter,system-ui,sans-serif;border:0;cursor:pointer;opacity:0;pointer-events:none;transition:.3s;box-shadow:0 12px 28px -12px rgba(0,0,0,.5)}'
  +'.rpill.show{opacity:1;transform:translate(-50%,0);pointer-events:auto}.rpill b{color:#ffb8a4;font-weight:600}';
  document.head.appendChild(css);

  var btn=document.createElement('button');btn.className='rbtn';btn.setAttribute('aria-label','Presenter and viewing options');
  btn.innerHTML='<svg viewBox="0 0 24 24"><path d="M4.9 19.1a10 10 0 0 1 0-14.2M7.8 16.2a6 6 0 0 1 0-8.4M16.2 7.8a6 6 0 0 1 0 8.4M19.1 4.9a10 10 0 0 1 0 14.2"/><circle cx="12" cy="12" r="2"/></svg><i></i>';
  var pop=document.createElement('div');pop.className='rpop';
  pop.innerHTML='<div class="st"><span id="rst">Connecting…</span></div>'
   +'<label>Follow presenter<input type="checkbox" id="rfol" checked><span class="sw"></span></label>'
   +'<button id="rfs">Fullscreen <span>F</span></button>'
   +'<a href="/admin/#'+slug+'">Presenter remote <span>PIN</span></a>'
   +'<a href="/">All presentations <span>↗</span></a>';
  var pill=document.createElement('button');pill.className='rpill';
  document.body.appendChild(btn);document.body.appendChild(pop);document.body.appendChild(pill);
  btn.onclick=function(e){e.stopPropagation();pop.classList.toggle('open')};
  document.addEventListener('click',function(e){if(!pop.contains(e.target)&&e.target!==btn)pop.classList.remove('open')});
  function fs(){if(document.fullscreenElement)document.exitFullscreen();else document.documentElement.requestFullscreen&&document.documentElement.requestFullscreen()}
  pop.querySelector('#rfs').onclick=fs;
  addEventListener('keydown',function(e){if((e.key==='f'||e.key==='F')&&!e.metaKey&&!e.ctrlKey&&!/input|textarea/i.test((e.target||{}).tagName||''))fs()});

  /* ---- state ---- */
  var follow=true,rem={slide:0,live:false,viewers:0},fol=pop.querySelector('#rfol');
  function ui(){
    btn.classList.toggle('live',rem.live);
    pop.querySelector('#rst').innerHTML=rem.live?'<b>Presenter is live</b> · slide '+(rem.slide+1):'No presenter connected';
    fol.checked=follow;
    var off=rem.live&&!follow&&index()!==rem.slide;
    pill.innerHTML='Presenter is on slide <b>'+(rem.slide+1)+'</b> · tap to follow';pill.classList.toggle('show',off);
  }
  fol.onchange=function(){follow=fol.checked;if(follow&&rem.live)goto(rem.slide);ui()};
  pill.onclick=function(){follow=true;goto(rem.slide);ui()};
  /* manual navigation pauses following instead of fighting the viewer */
  new MutationObserver(function(){if(!moving&&rem.live&&follow&&index()!==rem.slide){follow=false}ui()}).observe(document.body,{subtree:true,attributes:true,attributeFilter:['class']});

  var es;
  function connect(){
    es=new EventSource('/api/events/'+encodeURIComponent(slug)+'?role=viewer');
    es.addEventListener('state',function(e){
      try{rem=JSON.parse(e.data)}catch(_){return}
      if(rem.live&&follow&&index()!==rem.slide)goto(rem.slide);
      ui();
    });
    es.onerror=function(){rem.live=false;ui()};
  }
  connect();ui();
})();
