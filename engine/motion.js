/* ───────────────────────────────────────────────────────────────────────────
   deckforge motion engine v2
   A small, programmable motion-graphics runtime. Everything is a plugin:

     DeckMotion.register(name, {selector, setup(el, api) -> update(t, dt)|void, global?})
     DeckMotion.scene(name, (ctx, t, w, h, opts) => void)          // ambient canvas scenes
     DeckMotion.easings[name] = fn                                 // custom easings
     DeckMotion.on(fn, {slide})                                    // per-frame callback
     DeckMotion.config                                             // merged deck "motion" config

   Declarative use (no code):
     data-motion="float:amp=8,per=6 pulse:scale=1.05 spin:per=40"   composable transform behaviors
     data-kf='[{"t":0,"x":0},{"t":.5,"x":40,"ease":"inOut"}]'       keyframe timeline (x y s r o), data-dur, data-pingpong
     <canvas class="amb" data-amb="aurora" data-opts='{"hue":"#ff4b1f"}'>
   Per-deck code: decks/<slug>/plugin.js (an ES module; use window.DeckMotion).
   Config (deck.json "motion"): {speed, intensity, seed, reduce:"respect"|"ignore", scenes:{aurora:{...}}}
   URL flags: ?pdf (static frame, no loops)  ?thumb (no chrome; driven by postMessage)
   ─────────────────────────────────────────────────────────────────────────── */
import {defineMorphIcon} from '../vendor/element.js';
import * as I from '../vendor/icons.js';
defineMorphIcon();

const Q=new URLSearchParams(location.search);
const PDF=Q.has('pdf'),THUMB=Q.has('thumb');
const cfgEl=document.getElementById('deck-config');
const config=Object.assign({speed:1,intensity:1,seed:null,reduce:'respect',scenes:{}},cfgEl?JSON.parse(cfgEl.textContent):{});
const REDUCE=config.reduce!=='ignore'&&matchMedia('(prefers-reduced-motion: reduce)').matches;
const STATIC=PDF||REDUCE;
const NS='http://www.w3.org/2000/svg';
const css=getComputedStyle(document.documentElement);
const ACC=(css.getPropertyValue('--acc')||'#ff4b1f').trim(),INK=(css.getPropertyValue('--ink')||'#141412').trim();

/* ── utilities ─────────────────────────────────────────────────────────── */
const $=(s,r=document)=>[...r.querySelectorAll(s)];
let _seed=config.seed==null?null:(config.seed>>>0);
const rand=()=>{if(_seed==null)return Math.random();_seed|=0;_seed=_seed+0x6D2B79F5|0;let t=Math.imul(_seed^_seed>>>15,1|_seed);t=t+Math.imul(t^t>>>7,61|t)^t;return((t^t>>>14)>>>0)/4294967296};
const rnd=(a,b)=>a+rand()*(b-a);
const clamp=(v,a=0,b=1)=>Math.min(b,Math.max(a,v));
const lerp=(a,b,k)=>a+(b-a)*k;
const easings={
  linear:p=>p,in:p=>p*p,out:p=>1-(1-p)*(1-p),inOut:p=>.5-.5*Math.cos(Math.PI*p),
  inCubic:p=>p*p*p,outCubic:p=>1-Math.pow(1-p,3),inOutCubic:p=>p<.5?4*p*p*p:1-Math.pow(-2*p+2,3)/2,
  outBack:p=>{const c=1.70158;return 1+(c+1)*Math.pow(p-1,3)+c*Math.pow(p-1,2)},
  outElastic:p=>p===0||p===1?p:Math.pow(2,-10*p)*Math.sin((p*10-.75)*(2*Math.PI/3))+1,
  outBounce:p=>{const n=7.5625,d=2.75;if(p<1/d)return n*p*p;if(p<2/d)return n*(p-=1.5/d)*p+.75;if(p<2.5/d)return n*(p-=2.25/d)*p+.9375;return n*(p-=2.625/d)*p+.984375}
};
const ease=(p,name='inOut')=>(easings[name]||easings.inOut)(clamp(p));
/* attribute helpers: data-x="12" or data-opts='{"x":12}' */
const opts=el=>{try{return el.dataset.opts?JSON.parse(el.dataset.opts):{}}catch(_){return{}}};
const num=(el,k,d)=>{const o=opts(el);if(o[k]!=null)return +o[k];const v=el.dataset[k];return v!=null&&v!==''&&!isNaN(+v)?+v:d};
const str=(el,k,d)=>opts(el)[k]??el.dataset[k]??d;
const mk=(svg,r,fill,stroke)=>{const c=document.createElementNS(NS,'circle');c.setAttribute('r',r);c.setAttribute('fill',fill||'none');if(stroke)c.setAttribute('stroke',stroke);svg.appendChild(c);return c};
function hexA(hex,a){const h=hex.replace('#','');const n=parseInt(h.length===3?h.replace(/./g,'$&$&'):h,16);return `rgba(${n>>16&255},${n>>8&255},${n&255},${a})`}

$('morph-icon[data-i]').forEach(el=>{el.icon=I[el.dataset.i]});

/* ── navigation ────────────────────────────────────────────────────────── */
const deck=document.getElementById('deck'),slides=$('.slide'),dots=document.getElementById('dots');
const prev=document.getElementById('prev'),next=document.getElementById('next');
let cur=0;
if(dots)slides.forEach((_,k)=>{const b=document.createElement('button');b.onclick=()=>go(k,true);b.setAttribute('aria-label','Slide '+(k+1));dots.appendChild(b)});
function go(n,manual){
  cur=clamp(n,0,slides.length-1);
  slides.forEach((s,k)=>s.classList.toggle('active',k===cur));
  if(dots)[...dots.children].forEach((d,k)=>d.classList.toggle('on',k===cur));
  if(prev)prev.disabled=cur===0;if(next)next.disabled=cur===slides.length-1;
  if(!THUMB&&!PDF)history.replaceState(null,'','#'+(cur+1));
  document.dispatchEvent(new CustomEvent('deck:slide',{detail:{index:cur,manual:!!manual}}));
}
window.__deckGo=(n,manual)=>go(n,manual);window.__deckIndex=()=>cur;window.__deckCount=()=>slides.length;
function fit(){
  const w=innerWidth,h=innerHeight;
  if(THUMB){deck.style.transform='translate(-50%,-50%) scale('+Math.min(w/1280,h/720)+')';return}
  const portrait=h>w*1.15,ui=h<500?34:56;
  const s=portrait?Math.min(w/720,(h-112)/1280):Math.min(w/1280,(h-ui)/720);
  deck.style.transform='translate(-50%,-50%) scale('+s+')'+(portrait?' rotate(90deg)':'');
}
addEventListener('resize',fit);fit();
if(!THUMB){
  addEventListener('keydown',e=>{
    if(e.target.closest&&e.target.closest('input,textarea'))return;
    if(['ArrowRight','PageDown',' ','Enter'].includes(e.key)){e.preventDefault();go(cur+1,true)}
    if(['ArrowLeft','PageUp','Backspace'].includes(e.key)){e.preventDefault();go(cur-1,true)}
    if(e.key==='Home')go(0,true);if(e.key==='End')go(slides.length-1,true);
  });
  if(prev)prev.onclick=()=>go(cur-1,true);if(next)next.onclick=()=>go(cur+1,true);
  let x0;addEventListener('touchstart',e=>x0=e.touches[0].clientX,{passive:true});
  addEventListener('touchend',e=>{const d=e.changedTouches[0].clientX-x0;if(Math.abs(d)>50)go(cur+(d<0?1:-1),true)});
}else addEventListener('message',e=>{const d=e.data;if(d&&d.deckforge==='go')go(d.slide)});
const exp=document.getElementById('exp'),expIcon=document.querySelector('#exp morph-icon');
if(exp&&expIcon)exp.addEventListener('click',()=>{expIcon.morphTo(I.check);setTimeout(()=>expIcon.morphTo(I.download),2200)});

/* ── runtime core ──────────────────────────────────────────────────────── */
const behaviors={},scenes={},frame=[];          // frame: {slide, fn}
const slideOf=el=>slides.indexOf(el.closest('.slide'));
const INT=()=>config.intensity;
/* api handed to every behavior */
const api={
  get cur(){return cur},slides,ACC,INK,config,PDF,STATIC,I,
  rand,rnd,clamp,lerp,ease,easings,num,str,opts,mk,hexA,NS,
  amp:v=>v*INT(),
  /* run fn(t,dt) every frame while `el`'s slide is on screen (or every slide if slide<0) */
  every(el,fn){frame.push({slide:typeof el==='number'?el:slideOf(el),fn})},
  /* run fn at random intervals [a,b] seconds while the slide is on screen */
  later(el,a,b,fn){const s=slideOf(el);(function nx(){setTimeout(()=>{if(cur===s)fn();nx()},rnd(a,b)*1000/config.speed)})()},
  phase:(el,per)=>{const o=num(el,'ph',null);return o==null?rand():o}
};
function register(name,def){behaviors[name]=def;if(window.__deckBooted)boot([def])}
function scene(name,fn){scenes[name]=fn}
function boot(defs){
  for(const def of defs){
    if(!def.selector)continue;
    for(const el of $(def.selector)){
      if(el.__dm&&el.__dm.has(def))continue;(el.__dm=el.__dm||new Set()).add(def);
      if(STATIC&&!def.always){def.still&&def.still(el,api);continue}
      const upd=def.setup&&def.setup(el,api);
      if(typeof upd==='function')frame.push({slide:def.global?-1:slideOf(el),fn:upd});
    }
  }
}
window.DeckMotion=Object.assign(window.DeckMotion||{},{version:'2.0',config,api,register,scene,easings,rand,rnd,ease,
  on:(fn,o={})=>frame.push({slide:o.slide==null?-1:o.slide,fn}),behaviors,scenes,go,get index(){return cur}});

/* ── scenes: ambient canvas motion graphics ────────────────────────────── */
scene('aurora',(c,t,w,h,o)=>{
  c.clearRect(0,0,w,h);const a=o.alpha??1,col=o.color||ACC;
  [[.15,.2,520,.13,.21,.17,0],[.85,.3,460,.10,.17,.23,2],[.5,.95,560,.09,.13,.19,4],[.7,.7,360,.07,.27,.11,1]].forEach(([x0,y0,r,al,f1,f2,p],k)=>{
    const x=w*(x0+.16*Math.sin(t*f1+p)),y=h*(y0+.18*Math.cos(t*f2+p*1.3)),g=c.createRadialGradient(x,y,0,x,y,r);
    g.addColorStop(0,k%2?`rgba(20,20,18,${al*.55*a})`:hexA(col,al*a));g.addColorStop(1,'rgba(255,255,255,0)');c.fillStyle=g;c.fillRect(0,0,w,h);
  });
});
scene('grid',(c,t,w,h,o)=>{
  c.clearRect(0,0,w,h);const cols=o.cols||48,rows=o.rows||27,col=o.color||ACC,a=o.alpha??1;
  for(let i=0;i<cols;i++)for(let j=0;j<rows;j++){
    const x=(i+.5)*w/cols,y=(j+.5)*h/rows,v=Math.max(0,Math.sin(x*.011+t*1.05)*Math.sin(y*.016-t*.8)+.15*Math.sin((x+y)*.007+t*.5));
    c.beginPath();c.arc(x,y,1+2.4*v,0,7);c.fillStyle=v>.55?hexA(col,.5*v*a):`rgba(20,20,18,${(.07+.1*v)*a})`;c.fill();
  }
});
scene('waves',(c,t,w,h,o)=>{
  c.clearRect(0,0,w,h);const base=o.y??.82,col=o.color||ACC,a=o.alpha??1;
  for(let k=0;k<6;k++){c.beginPath();for(let x=0;x<=w;x+=8){const y=h*base+Math.sin(x*.005+t*(.5+k*.13)+k)*(16+k*7)+Math.sin(x*.013-t*.7+k*2)*6;x?c.lineTo(x,y):c.moveTo(x,y)}
    c.strokeStyle=k===2?hexA(col,.45*a):`rgba(20,20,18,${(.05+k*.012)*a})`;c.lineWidth=k===2?1.6:1;c.stroke()}
});
scene('orbits',(c,t,w,h,o)=>{
  c.clearRect(0,0,w,h);const cx=w*(o.x??.8),cy=h*(o.y??.5),col=o.color||ACC,sp=o.speed||1;
  [[150,.31],[230,-.22],[310,.15],[400,-.1]].forEach(([r,s],k)=>{
    c.beginPath();c.arc(cx,cy,r,0,7);c.strokeStyle='rgba(20,20,18,.07)';c.setLineDash(k%2?[2,7]:[]);c.stroke();c.setLineDash([]);
    for(let n=0;n<k+2;n++){const a=t*s*sp+n*6.283/(k+2)+k,hot=k===1&&!n;c.beginPath();c.arc(cx+r*Math.cos(a),cy+r*Math.sin(a),hot?5:2.6,0,7);c.fillStyle=hot?col:'rgba(20,20,18,.28)';c.fill()}
  });
});
scene('particles',(c,t,w,h,o)=>{
  const n=o.count||46,col=o.color||ACC;c.clearRect(0,0,w,h);const P=scene._p||(scene._p=Array.from({length:n},(_,i)=>({x:(i*97.3)%w,y:(i*61.7)%h,s:.4+((i*13)%7)/10,p:i})));
  P.forEach(p=>{p.px=(p.x+Math.sin(t*.12*p.s+p.p)*60+t*8*p.s)%w;p.py=p.y+Math.cos(t*.1*p.s+p.p)*40});
  for(let i=0;i<P.length;i++)for(let j=i+1;j<P.length;j++){const dx=P[i].px-P[j].px,dy=P[i].py-P[j].py,d=Math.hypot(dx,dy);if(d<150){c.beginPath();c.moveTo(P[i].px,P[i].py);c.lineTo(P[j].px,P[j].py);c.strokeStyle=`rgba(20,20,18,${.09*(1-d/150)})`;c.stroke()}}
  P.forEach((p,i)=>{c.beginPath();c.arc(p.px,p.py,i%9?2:3.6,0,7);c.fillStyle=i%9?'rgba(20,20,18,.3)':col;c.fill()});
});

/* ── behaviors ─────────────────────────────────────────────────────────── */
register('ambient',{selector:'canvas.amb',always:true,
  setup(cv,A){const ctx=cv.getContext('2d'),name=str(cv,'amb','aurora'),o=Object.assign({},config.scenes[name],opts(cv)),w=1280,h=720;ctx.setTransform(2,0,0,2,0,0);
    const fn=()=>(scenes[name]||scenes.aurora);
    if(A.STATIC){fn()(ctx,4.2,w,h,o);return}
    fn()(ctx,0,w,h,o);return t=>fn()(ctx,t,w,h,o)}});

register('flow',{selector:'svg',
  setup(svg,A){const i=slideOf(svg);if(i<0)return;
    $('path.flow',svg).forEach(p=>{const len=p.getTotalLength(),per=num(p,'per',A.rnd(2.4,4.6)),ph=A.rand(),c=A.mk(svg,3,ACC);
      A.every(i,t=>{const q=((t/per)+ph)%1,pt=p.getPointAtLength(len*A.ease(q));c.setAttribute('cx',pt.x);c.setAttribute('cy',pt.y);c.setAttribute('opacity',Math.sin(Math.PI*q))})});
    $('path.mk',svg).forEach(p=>{const len=p.getTotalLength(),per=num(p,'p',9),ph=num(p,'ph',0),col=str(p,'c',ACC),r=num(p,'r',5),c=A.mk(svg,r,col),h=A.mk(svg,r,'none',col);
      A.every(i,t=>{const q=((t/per)+ph)%1,k=A.ease(Math.min(q/.82,1)),pt=p.getPointAtLength(len*k),f=(t*.9)%1;
        for(const e of [c,h]){e.setAttribute('cx',pt.x);e.setAttribute('cy',pt.y)}
        h.setAttribute('r',r+9*f);h.setAttribute('stroke-opacity',.5*(1-f));c.setAttribute('opacity',q<.93?1:1-(q-.93)*14);h.setAttribute('opacity',q<.93?1:0)})});
    if(svg.dataset.packets){const src=JSON.parse(svg.dataset.packets),pk=[];let nx=0;
      A.every(i,t=>{if(t>nx){pk.push({k:Math.floor(A.rand()*src.from.length),t0:t,c:A.mk(svg,3,ACC)});nx=t+A.rnd(.5,1.8)}
        for(let j=pk.length-1;j>=0;j--){const o=pk[j],e=t-o.t0,a=src.from[o.k];
          if(e<1.1){const k=A.ease(e/1.1);o.c.setAttribute('cx',a[0]+(src.mid[0]-a[0])*k);o.c.setAttribute('cy',a[1]+(src.mid[1]-a[1])*k);o.c.setAttribute('fill',ACC)}
          else if(e<1.9){const k=(e-1.1)/.8;o.c.setAttribute('cx',src.mid[0]+(src.out[0]-src.mid[0])*k);o.c.setAttribute('cy',src.mid[1]+(src.out[1]-src.mid[1])*k);o.c.setAttribute('fill',INK)}
          else{o.c.remove();pk.splice(j,1)}}})}}});

register('cycle',{selector:'[data-cycle]',
  setup(box,A){const kids=[...box.children];let h=-1;A.later(box,1.1,2.4,()=>{let n;do{n=Math.floor(A.rand()*kids.length)}while(n===h&&kids.length>1);kids.forEach((k,j)=>k.classList.toggle('hi',j===n));h=n})}});

register('morph',{selector:'morph-icon[data-morph]',
  setup(el,A){const list=el.dataset.morph.split(','),caps=el.dataset.caps?el.dataset.caps.split('|'):null,capEl=el.dataset.capEl?document.querySelector(el.dataset.capEl):null;let h=0;
    A.later(el,2.2,4.2,()=>{let n;do{n=Math.floor(A.rand()*list.length)}while(n===h&&list.length>1);h=n;el.morphTo(A.I[list[n]],str(el,'spring','smooth'));
      if(capEl&&caps){capEl.style.opacity=0;setTimeout(()=>{capEl.textContent=caps[n];capEl.style.opacity=1},180)}})}});

register('rand',{selector:'[data-rand]',
  setup(box,A){const kids=[...box.children],stars=box.dataset.rand==='stars';
    A.later(box,2,3.8,()=>{const n=stars?3+Math.floor(A.rand()*3):Math.floor(A.rand()*kids.length);kids.forEach((k,j)=>k.classList.toggle('on',stars?j<n:j===n))})},
  still(box){const kids=[...box.children];kids.forEach((k,j)=>k.classList.toggle('on',box.dataset.rand==='stars'?j<4:j===2))}});

register('timeline',{selector:'.dotm[data-loop]',setup(d,A){const per=num(d,'loop',11);return t=>{d.style.left=(((t/per)%1)*100)+'%'}}});
register('gauge',{selector:'.ks b[data-base]',setup(b,A){const base=num(b,'base',50);return t=>{b.style.left=(base+A.amp(3)*Math.sin(t*.6)+A.amp(1.6)*Math.sin(t*1.7))+'%'}}});
register('whisker',{selector:'.sc[data-m]',
  setup(r,A){const m=num(r,'m',0),lo=num(r,'lo',0),hi=num(r,'hi',0),mn=num(r,'min',1),mx=num(r,'max',7),f=v=>(v-mn)/(mx-mn)*100,ph=A.rnd(0,6),w=A.rnd(.35,.75),dt=r.querySelector('.dt'),wh=r.querySelector('.wh'),em=r.querySelector('em');
    return t=>{const d=A.amp(.03)*(mx-mn)*Math.sin(t*w+ph),s=.007*(mx-mn)*Math.sin(t*w*1.7+ph);dt.style.left=f(m+d)+'%';wh.style.left=f(lo+d-s)+'%';wh.style.width=(f(hi+d+s)-f(lo+d-s))+'%';em.textContent=(m+d).toFixed(1)}}});
register('meters',{selector:'.firm',
  setup(f,A){const ms=$('.meter i[data-v]',f).map(el=>({el,b:+el.dataset.v,a:A.amp(A.rnd(.035,.065)),w1:A.rnd(.35,.75),w2:A.rnd(.9,1.6),p1:A.rnd(0,6),p2:A.rnd(0,6)})),big=f.querySelector('.big[data-auto]');
    return t=>{let s=0;ms.forEach(o=>{const v=A.clamp(o.b+o.a*Math.sin(t*o.w1+o.p1)+o.a*.5*Math.sin(t*o.w2+o.p2),.04,.98);o.el.style.setProperty('--v',v.toFixed(3));s+=v});if(big)big.textContent=Math.round(s/ms.length*100)+'%'}}});
register('counter',{selector:'.stat .val[data-to]',
  setup(v,A){const to=num(v,'to',0),dec=num(v,'dec',0),amp=A.amp(num(v,'amp',0)),num_=v.querySelector('.num'),ph=A.rnd(0,6),w=A.rnd(.4,.8),bar=v.closest('.stat').querySelector('.bar i');let t0=null,was=-1;
    return t=>{if(was!==cur||t0===null){t0=t;was=cur}const k=A.ease((t-t0)/1.6);num_.textContent=(to*k+amp*Math.sin(t*w+ph)*k).toFixed(dec);if(bar)bar.style.setProperty('--v',A.clamp(num(bar,'v',.5)*k+.03*Math.sin(t*w+ph)))}},
  still(v){v.querySelector('.num').textContent=(+v.dataset.to).toFixed(+v.dataset.dec||0)}});

/* composable transform motion: data-motion="float:amp=8,per=6 pulse spin:per=40" + data-kf keyframes */
const FX={
  float:(s,t,p)=>{const a=(p.amp??8)*INT(),per=p.per??6,ph=p.ph??0;s.y+=a*Math.sin(t/per*6.283+ph);s.x+=a*.5*Math.sin(t/(per*1.37)*6.283+ph*2)},
  drift:(s,t,p)=>{const a=(p.amp??30)*INT(),per=p.per??14;s.x+=a*Math.sin(t/per*6.283);s.y+=a*.6*Math.cos(t/(per*1.3)*6.283)},
  pulse:(s,t,p)=>{s.s*=1+((p.scale??1.06)-1)*INT()*(.5+.5*Math.sin(t/(p.per??3)*6.283+(p.ph??0)))},
  spin:(s,t,p)=>{s.r+=(t/(p.per??30)*360)*(p.dir??1)},
  sway:(s,t,p)=>{s.r+=(p.deg??4)*INT()*Math.sin(t/(p.per??5)*6.283+(p.ph??0))},
  breathe:(s,t,p)=>{s.o*=1-(p.depth??.25)*INT()*(.5-.5*Math.sin(t/(p.per??4)*6.283+(p.ph??0)))},
  wobble:(s,t,p)=>{const a=(p.amp??3)*INT();s.x+=a*Math.sin(t*1.9+(p.ph??0));s.y+=a*Math.cos(t*2.3+(p.ph??0))}
};
const parseMotion=str_=>(str_||'').trim().split(/\s+/).filter(Boolean).map(tok=>{const [n,a]=tok.split(':'),p={};(a||'').split(',').filter(Boolean).forEach(kv=>{const [k,v]=kv.split('=');p[k]=isNaN(+v)?v:+v});return {n,p}});
register('fx',{selector:'[data-motion],[data-kf]',
  setup(el,A){
    const list=parseMotion(el.dataset.motion).filter(m=>FX[m.n]),ph0=A.rnd(0,6.283);list.forEach(m=>{if(m.p.ph==null)m.p.ph=ph0});
    let kf=null;if(el.dataset.kf){try{kf=JSON.parse(el.dataset.kf).sort((a,b)=>a.t-b.t)}catch(_){}}
    const dur=num(el,'dur',6),ping=el.dataset.pingpong!=null,eName=str(el,'ease','inOut'),base=getComputedStyle(el).transform;const pre=base&&base!=='none'?base+' ':'';
    return t=>{
      const s={x:0,y:0,s:1,r:0,o:1};
      for(const m of list)FX[m.n](s,t,m.p);
      if(kf){let q=(t/dur)%(ping?2:1);if(ping&&q>1)q=2-q;let a=kf[0],b=kf[kf.length-1];for(let i=0;i<kf.length-1;i++)if(q>=kf[i].t&&q<=kf[i+1].t){a=kf[i];b=kf[i+1];break}
        const k=b.t===a.t?1:A.ease((q-a.t)/(b.t-a.t),b.ease||a.ease||eName);
        for(const key of ['x','y','r']){if(a[key]!=null||b[key]!=null)s[key]+=A.lerp(a[key]??0,b[key]??a[key]??0,k)}
        if(a.s!=null||b.s!=null)s.s*=A.lerp(a.s??1,b.s??a.s??1,k);if(a.o!=null||b.o!=null)s.o*=A.lerp(a.o??1,b.o??a.o??1,k)}
      el.style.transform=`${pre}translate(${s.x.toFixed(2)}px,${s.y.toFixed(2)}px) rotate(${s.r.toFixed(2)}deg) scale(${s.s.toFixed(4)})`;
      if(s.o!==1||el.__fxo)el.style.opacity=s.o.toFixed(3),el.__fxo=1;
    }}});

/* typewriter: data-motion-type="line one|line two" types, holds, erases, moves on */
register('type',{selector:'[data-type]',
  setup(el,A){const lines=el.dataset.type.split('|');let li=0,st='type',t0=null;const speed=num(el,'cps',22);
    return t=>{if(t0===null)t0=t;const e=t-t0,L=lines[li];
      if(st==='type'){const n=Math.min(L.length,Math.floor(e*speed));el.textContent=L.slice(0,n);if(n>=L.length){st='hold';t0=t}}
      else if(st==='hold'){if(e>2.2){st='erase';t0=t}}
      else{const n=Math.max(0,L.length-Math.floor(e*speed*2));el.textContent=L.slice(0,n);if(n<=0){li=(li+1)%lines.length;st='type';t0=t}}}},
  still(el){el.textContent=el.dataset.type.split('|')[0]}});

/* ── frame loop ────────────────────────────────────────────────────────── */
boot(Object.values(behaviors));
window.__deckBooted=true;
let last=0;
(function loop(ms){const t=ms/1000*config.speed,dt=t-last;last=t;for(const f of frame)if(f.slide<0||f.slide===cur)f.fn(t,dt);requestAnimationFrame(loop)})(0);

/* per-deck plugin hook: decks/<slug>/plugin.js runs after this module */
document.dispatchEvent(new CustomEvent('deckmotion:ready',{detail:window.DeckMotion}));
go((parseInt(location.hash.slice(1))||1)-1);
window.__ready=true;
