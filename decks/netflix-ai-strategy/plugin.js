// Original explanatory motion graphics for the Netflix AI strategy deck.
// These scenes are deliberately drawn from the argument of the report, not from a slide template.
const DM = window.DeckMotion;

const makeCanvas = (el, W, H) => {
  const dpr = 2, c = document.createElement('canvas');
  c.width = W * dpr; c.height = H * dpr;
  c.style.cssText = `width:${W}px;height:${H}px;display:block;max-width:100%`;
  el.appendChild(c); const g = c.getContext('2d'); g.scale(dpr, dpr);
  const cs = getComputedStyle(el), C = n => cs.getPropertyValue(n).trim();
  const clamp = (v,a=0,b=1)=>Math.max(a,Math.min(b,v));
  const rr = (x,y,w,h,r=14) => { g.beginPath(); g.moveTo(x+r,y); g.arcTo(x+w,y,x+w,y+h,r); g.arcTo(x+w,y+h,x,y+h,r); g.arcTo(x,y+h,x,y,r); g.arcTo(x,y,x+w,y,r); g.closePath(); };
  const text = (s,x,y,z=14,w=500,col='#fff',align='left')=>{g.font=`${w} ${z}px Inter,Arial,sans-serif`;g.fillStyle=col;g.textAlign=align;g.fillText(s,x,y)};
  return {g,C,clamp,rr,text,W,H};
};

DM.custom('signalToDecision', (el, api) => {
  const o=makeCanvas(el,650,420), {g,C,clamp,rr,text,W,H}=o;
  const features=['Pacing','Arc tension','Sentiment','Genre fit'];
  const draw=(t,dt,st)=>{ const acc=C('--acc'),ink=C('--ink'),mute=C('--mute'),faint=C('--faint'),line=C('--line'),card=C('--card'); const p=api.STATIC?1:clamp(st/3);
    g.clearRect(0,0,W,H); rr(1,1,W-2,H-2,22);g.fillStyle='rgba(13,13,13,.78)';g.fill();g.strokeStyle='rgba(255,255,255,.13)';g.stroke();
    text('FROM SCRIPT SIGNALS TO A HUMAN DECISION',26,35,12,700,mute); text('What the model sees — and what it must not decide',26,59,17,600,ink);
    const ys=[112,166,220,274]; features.forEach((f,i)=>{ const y=ys[i], on=clamp((p-.08-i*.12)/.26); text(f,26,y+5,12,600,faint); g.strokeStyle=line;g.lineWidth=1;g.beginPath();g.moveTo(110,y);g.lineTo(252,y);g.stroke(); g.strokeStyle=i===1?acc:mute;g.lineWidth=2.4;g.beginPath(); for(let k=0;k<=42;k++){const x=110+k*3.38;const yy=y+Math.sin(k*.42+i*1.7)*9*Math.sin(k*.11+1)*on; k?g.lineTo(x,yy):g.moveTo(x,yy)}g.stroke(); });
    const cx=330,cy=193; rr(cx-56,cy-52,112,104,18);g.fillStyle='rgba(229,9,20,.16)';g.fill();g.strokeStyle=acc;g.lineWidth=1.4;g.stroke(); text('NLP',cx,cy-5,23,700,ink,'center');text('feature map',cx,cy+18,12,500,mute,'center');
    ys.forEach((y,i)=>{const q=clamp((p-.25-i*.08)/.26);g.strokeStyle=`rgba(229,9,20,${.22+.65*q})`;g.lineWidth=1.5;g.beginPath();g.moveTo(254,y);g.quadraticCurveTo(285,y,cx-58,cy);g.stroke(); const qx=254+(cx-312)*q,qy=y+(cy-y)*q;g.fillStyle=acc;g.beginPath();g.arc(qx,qy,3.5,0,7);g.fill();});
    const dx=510,dy=178; rr(dx-97,dy-79,190,156,18);g.fillStyle=card;g.fill();g.strokeStyle='rgba(255,255,255,.16)';g.stroke(); text('DEMAND RANGE',dx,dy-50,11,700,mute,'center');g.strokeStyle=acc;g.lineWidth=3;g.beginPath();for(let k=0;k<=62;k++){const x=dx-67+k*2.15, v=Math.exp(-Math.pow((k-35)/13,2))*50*clamp((p-.43)/.34); k?g.lineTo(x,dy+40-v):g.moveTo(x,dy+40-v)}g.stroke();g.fillStyle='rgba(229,9,20,.12)';g.lineTo(dx+66,dy+40);g.lineTo(dx-67,dy+40);g.fill(); text('low',dx-67,dy+61,11,500,faint);text('likely',dx,dy+61,11,600,ink,'center');text('high',dx+67,dy+61,11,500,faint,'right');
    g.strokeStyle=line;g.lineWidth=1.4;g.beginPath();g.moveTo(cx+58,cy);g.lineTo(dx-99,dy);g.stroke();const q=clamp((p-.48)/.24),qx=cx+58+(dx-cx-157)*q;g.fillStyle=acc;g.beginPath();g.arc(qx,cy+(dy-cy)*q,4,0,7);g.fill();
    rr(58,338,534,54,14);g.fillStyle='rgba(255,255,255,.055)';g.fill(); text('MODEL OUTPUT',78,360,11,700,mute);text('range + segments + uncertainty drivers',78,380,14,600,ink); text('HUMAN OWNER',418,360,11,700,mute);text('creative executive',418,380,14,600,acc);
  }; return draw;
});

DM.custom('readinessRadar', (el, api) => {
  const o=makeCanvas(el,600,410),{g,C,clamp,rr,text,W,H}=o;const labs=['Data','Technology','Leadership','Process','Talent','Governance'],vals=[5,5,4,3,3,2];
  return (t,dt,st)=>{const acc=C('--acc'),ink=C('--ink'),mute=C('--mute'),faint=C('--faint'),line=C('--line');const p=api.STATIC?1:clamp(st/2.6);g.clearRect(0,0,W,H);rr(1,1,W-2,H-2,22);g.fillStyle='rgba(13,13,13,.82)';g.fill();g.strokeStyle='rgba(255,255,255,.13)';g.stroke();text('READINESS DIAGNOSTIC',24,33,12,700,mute);text('Capability is uneven — governance is the scale-up gate',24,58,17,600,ink);
    const cx=280,cy=229,R=130,pts=[];for(let l=1;l<=5;l++){g.strokeStyle=line;g.lineWidth=1;g.beginPath();for(let i=0;i<6;i++){let a=-Math.PI/2+i*Math.PI/3,x=cx+Math.cos(a)*R*l/5,y=cy+Math.sin(a)*R*l/5;i?g.lineTo(x,y):g.moveTo(x,y)}g.closePath();g.stroke()}for(let i=0;i<6;i++){let a=-Math.PI/2+i*Math.PI/3;g.strokeStyle=line;g.beginPath();g.moveTo(cx,cy);g.lineTo(cx+Math.cos(a)*R,cy+Math.sin(a)*R);g.stroke();let tx=cx+Math.cos(a)*(R+30),ty=cy+Math.sin(a)*(R+30)+5;text(labs[i],tx,ty,13,600,i===5?acc:mute,'center');let r=R*(vals[i]/5)*p;pts.push([cx+Math.cos(a)*r,cy+Math.sin(a)*r]);}
    g.fillStyle='rgba(229,9,20,.20)';g.beginPath();pts.forEach(([x,y],i)=>i?g.lineTo(x,y):g.moveTo(x,y));g.closePath();g.fill();g.strokeStyle=acc;g.lineWidth=2.5;g.stroke();pts.forEach(([x,y],i)=>{g.fillStyle=i===5?acc:ink;g.beginPath();g.arc(x,y,5,0,7);g.fill()});
    rr(430,144,140,145,14);g.fillStyle='rgba(229,9,20,.1)';g.fill();g.strokeStyle='rgba(229,9,20,.45)';g.stroke();text('SCALE-UP GATE',446,171,11,700,mute);text('2 / 5',446,212,34,700,acc);text('Governance',446,236,14,600,ink);text('must rise before',446,259,12,500,faint);text('full integration',446,277,12,500,faint);
  };
});

DM.custom('dataFlywheel', (el, api) => {
  const o=makeCanvas(el,860,390),{g,C,clamp,rr,text,W,H}=o; const nodes=[['01','Better\ngreenlights',180,120],['02','Deeper\nengagement',620,120],['03','Richer\nbehaviour signals',620,280],['04','Stronger\nnext forecast',180,280]];
  const edge=(a,b,t,col)=>{g.strokeStyle='rgba(255,255,255,.18)';g.lineWidth=2;g.beginPath();g.moveTo(a[2],a[3]);g.lineTo(b[2],b[3]);g.stroke();for(let k=0;k<5;k++){let q=(t*.12+k/5)%1,x=a[2]+(b[2]-a[2])*q,y=a[3]+(b[3]-a[3])*q;g.fillStyle=col;g.beginPath();g.arc(x,y,3.6,0,7);g.fill()}};
  return (t,dt,st)=>{const acc=C('--acc'),ink=C('--ink'),mute=C('--mute'),faint=C('--faint'),card=C('--card');g.clearRect(0,0,W,H);rr(1,1,W-2,H-2,22);g.fillStyle='rgba(13,13,13,.82)';g.fill();g.strokeStyle='rgba(255,255,255,.13)';g.stroke();text('THE COMPOUNDING MECHANISM',28,34,12,700,mute);text('Each release makes the next greenlight more informed',28,58,17,600,ink);edge(nodes[0],nodes[1],t,acc);edge(nodes[1],nodes[2],t+2,'#22d3ee');edge(nodes[2],nodes[3],t+4,'#a855f7');edge(nodes[3],nodes[0],t+6,acc);
    nodes.forEach((n,i)=>{const x=n[2]-92,y=n[3]-42;rr(x,y,184,84,16);g.fillStyle=i===0?'rgba(229,9,20,.18)':card;g.fill();g.strokeStyle=i===0?acc:'rgba(255,255,255,.16)';g.lineWidth=i===0?1.8:1;g.stroke();text(n[0],x+15,y+22,11,700,i===0?acc:faint);let ls=n[1].split('\n');text(ls[0],x+15,y+49,16,700,ink);if(ls[1])text(ls[1],x+15,y+68,16,700,ink);});
    text('RETENTION-ADJUSTED ROI',420,210,12,700,acc,'center');text('not volume of titles',420,230,13,500,mute,'center');
  };
});

DM.custom('ecosystemMap', (el, api) => {
  const o=makeCanvas(el,700,420),{g,C,clamp,rr,text,W,H}=o;const n=[['Content\nsuppliers',110,110],['Subscribers',590,105],['Cloud &\ncomplementors',590,305],['Regulators',110,310],['Data\necosystem',350,365],['Competitors',350,80]];
  return (t,dt,st)=>{const acc=C('--acc'),ink=C('--ink'),mute=C('--mute'),faint=C('--faint'),line=C('--line'),card=C('--card');g.clearRect(0,0,W,H);rr(1,1,W-2,H-2,22);g.fillStyle='rgba(13,13,13,.82)';g.fill();g.strokeStyle='rgba(255,255,255,.13)';g.stroke();text('NETFLIX AI ECOSYSTEM',28,33,12,700,mute);text('Prediction sits inside a system of rights, trust and feedback',28,57,15,600,ink);const c=[350,220];n.forEach((v,i)=>{g.strokeStyle='rgba(255,255,255,.18)';g.lineWidth=1.4;g.beginPath();g.moveTo(c[0],c[1]);g.quadraticCurveTo((c[0]+v[1])/2,c[1]-(i%2?20:-20),v[1],v[2]);g.stroke();for(let k=0;k<2;k++){let q=(t*.11+i*.16+k*.49)%1,x=c[0]+(v[1]-c[0])*q,y=c[1]+(v[2]-c[1])*q;g.fillStyle=i===3?acc:(i===2?'#22d3ee':ink);g.beginPath();g.arc(x,y,3,0,7);g.fill();}});rr(235,166,230,106,20);g.fillStyle='rgba(229,9,20,.18)';g.fill();g.strokeStyle=acc;g.lineWidth=2;g.stroke();text('AI SCRIPT & DEMAND',350,207,16,700,ink,'center');text('PREDICTION ENGINE',350,229,16,700,ink,'center');text('decision-support layer',350,251,12,500,mute,'center');n.forEach((v,i)=>{rr(v[1]-62,v[2]-27,124,54,13);g.fillStyle=card;g.fill();g.strokeStyle='rgba(255,255,255,.15)';g.stroke();let a=v[0].split('\n');text(a[0],v[1],v[2]-2,12,600,i===3?acc:ink,'center');if(a[1])text(a[1],v[1],v[2]+15,12,600,i===3?acc:ink,'center');});
  };
});
