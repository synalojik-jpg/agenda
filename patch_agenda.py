#!/usr/bin/env python3
# Usage : python3 patch_agenda.py index.html   ->  crée index_new.html
import re, sys

src = sys.argv[1] if len(sys.argv) > 1 else 'index.html'
html = open(src, encoding='utf-8', newline='').read()
assert 'btn-resa' not in html, "Déjà patché : utilise ton index.html d'origine."

CSS = r"""
#btn-resa{display:none;position:fixed;right:16px;bottom:calc(16px + env(safe-area-inset-bottom,0px));width:68px;height:68px;border-radius:50%;font-size:30px;border:none;background:linear-gradient(135deg,var(--rouge),var(--rouge-clair));color:#fff;box-shadow:0 4px 14px rgba(0,0,0,.35);z-index:150;cursor:pointer;}
@media (pointer:coarse) and (max-width:900px){#btn-resa{display:block;}}
#resa-mic{width:100%;font-size:1.3rem;padding:16px;border:none;border-radius:10px;background:linear-gradient(135deg,var(--bleu-fonce),var(--bleu));color:#fff;font-weight:700;margin-bottom:10px;}
"""

HTML = r"""
<button id="btn-resa" onclick="ouvrirResa()">⚡</button>
<div class="overlay" id="overlayResa">
  <div class="modal">
    <div class="modal-header"><h2>Réserver le créneau</h2><button class="modal-close" onclick="fermerResa()">✕</button></div>
    <div class="modal-body">
      <button id="resa-mic" onclick="dicter()">🎤 Dicter</button>
      <div class="form-field"><label>Ex : 10/10 de 9h à 10h Lemon Group Brive</label>
        <input type="text" id="resa-txt" placeholder="Date, heures, donneur, lieu" autocomplete="off"></div>
      <div id="resa-recap" style="font-size:.95rem;font-weight:600;min-height:44px;margin:8px 0;"></div>
      <button class="btn-ajouter" style="width:100%;font-size:1.2rem;padding:18px" onclick="validerResa()">OK, réserver</button>
    </div>
  </div>
</div>
"""

JS = r"""
// ---- RÉSERVER LE CRÉNEAU (téléphone) ----
function normResa(s){return s.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/groupe/g,'group');}
function parseResa(txt){
  let t=' '+normResa(txt)+' ';
  const out={debut:null,fin:null,dates:[],donneur:'',reste:''};
  const auj=new Date(); auj.setHours(12,0,0,0);
  const plus=n=>{const d=new Date(auj);d.setDate(d.getDate()+n);return d;};
  const add=d=>out.dates.push(fmtISO(d));
  const mkDate=(j,mo,a)=>{
    const an=a?(+a<100?2000+ +a:+a):auj.getFullYear();
    let d=new Date(an,mo,j,12);
    if(!a&&d<auj)d=new Date(an+1,mo,j,12);
    return d;
  };
  // donneur d'ordre connu (le plus long d'abord)
  const noms=[...DONNEURS_CONNUS].sort((a,b)=>b.length-a.length);
  for(const nom of noms){
    const k=normResa(nom).replace(/\s+/g,'').split('').map(c=>c.replace(/[^a-z0-9]/g,'\\$&')).join('\\s*');
    const re=new RegExp('(^|\\s)'+k+'(?=\\s|$)');
    if(re.test(t)){out.donneur=nom;t=t.replace(re,' ');break;}
  }
  // heures
  const hs=[];
  t=t.replace(/(\d{1,2})\s*(?:h|heures?|:)\s*(\d{2})?(?![a-z0-9])/g,(m,h,mn)=>{hs.push(h.padStart(2,'0')+':'+(mn||'00'));return ' ';});
  out.debut=hs[0]||null; out.fin=hs[1]||null;
  // mots-clés de date
  t=t.replace(/apres.?demain/g,()=>{add(plus(2));return ' ';});
  t=t.replace(/demain/g,()=>{add(plus(1));return ' ';});
  t=t.replace(/aujourd.?hui/g,()=>{add(plus(0));return ' ';});
  t=t.replace(/dans\s+(\d+|un|une|deux|trois)\s*(jour|semaine|mois)s?/g,(m,n,u)=>{
    n=({un:1,une:1,deux:2,trois:3})[n]||+n;
    const d=new Date(auj);
    if(u==='mois')d.setMonth(d.getMonth()+n); else d.setDate(d.getDate()+n*(u==='semaine'?7:1));
    add(d);return ' ';
  });
  const J=['dimanche','lundi','mardi','mercredi','jeudi','vendredi','samedi'];
  t=t.replace(/\b(dimanche|lundi|mardi|mercredi|jeudi|vendredi|samedi)\b/g,(m,j)=>{
    let n=(J.indexOf(j)-auj.getDay()+7)%7; if(n===0)n=7;
    add(plus(n));return ' ';
  });
  const MO=['janvier','fevrier','mars','avril','mai','juin','juillet','aout','septembre','octobre','novembre','decembre'];
  t=t.replace(new RegExp('(\\d{1,2})\\s*(?:er)?\\s*('+MO.join('|')+')(?:\\s+(\\d{4}))?','g'),(m,j,mo,a)=>{add(mkDate(+j,MO.indexOf(mo),a));return ' ';});
  t=t.replace(/(\d{1,2})\s*[\/.\-]\s*(\d{1,2})(?:\s*[\/.\-]\s*(\d{2,4}))?/g,(m,j,mo,a)=>{add(mkDate(+j,+mo-1,a));return ' ';});
  out.reste=t.replace(/\b(de|du|au|a|le|la|les|pour|ce|cette|prochain|prochaine|reserve|reserver|creneau)\b/g,' ').replace(/\s+/g,' ').trim().toUpperCase();
  out.dates.sort();
  return out;
}
function recapResa(r){
  if(!r.dates.length)return 'Date non comprise';
  const f=s=>s.split('-').reverse().join('/');
  const d=r.dates.length>1?f(r.dates[0])+' → '+f(r.dates[r.dates.length-1]):f(r.dates[0]);
  const h=r.debut?(' · '+r.debut+(r.fin?'–'+r.fin:'')):' · journée';
  return d+h+(r.donneur?' · '+r.donneur:'')+(r.reste?' · '+r.reste:'');
}
function ouvrirResa(){
  document.getElementById('resa-txt').value='';
  document.getElementById('resa-recap').textContent='';
  document.getElementById('resa-mic').style.display=(window.SpeechRecognition||window.webkitSpeechRecognition)?'block':'none';
  document.getElementById('overlayResa').classList.add('visible');
}
function fermerResa(){document.getElementById('overlayResa').classList.remove('visible');}
document.getElementById('overlayResa').addEventListener('click',function(e){if(e.target===this)fermerResa();});
document.getElementById('resa-txt').addEventListener('input',function(){
  document.getElementById('resa-recap').textContent=recapResa(parseResa(this.value));
});
function dicter(){
  const SR=window.SpeechRecognition||window.webkitSpeechRecognition;
  if(!SR)return;
  const r=new SR(); r.lang='fr-FR'; r.interimResults=true; r.continuous=false;
  const inp=document.getElementById('resa-txt'), btn=document.getElementById('resa-mic');
  btn.textContent='🔴 Je t\'écoute...';
  r.onresult=e=>{inp.value=[...e.results].map(x=>x[0].transcript).join(' ');inp.dispatchEvent(new Event('input'));};
  r.onend=r.onerror=()=>{btn.textContent='🎤 Dicter';};
  r.start();
}
async function validerResa(){
  const r=parseResa(document.getElementById('resa-txt').value);
  if(!r.dates.length){alert('Date non comprise');return;}
  const d1=new Date(r.dates[0]+'T12:00:00'), d2=new Date(r.dates[r.dates.length-1]+'T12:00:00');
  if((d2-d1)/86400000>60){alert('Plage trop longue (60 jours max)');return;}
  const sansHeure=!r.debut;
  for(let d=new Date(d1);d<=d2;d.setDate(d.getDate()+1)){
    interventions.push({id:Date.now().toString()+Math.random().toString(36).slice(2,6),
      date:fmtISO(d),debut:r.debut||'09:00',fin:r.fin||(sansHeure?'18:00':''),
      client:r.reste||'RÉSERVÉ',adresse:'',descriptif:'À COMPLÉTER',donneur:r.donneur,numero:'',tarif:'',
      valide:false,colis:false,journee:sansHeure,demiJournee:false});
  }
  await sauvegarder();render();fermerResa();
}
"""

# 1) CSS avant </style>
assert '</style>' in html
html = html.replace('</style>', CSS + '</style>', 1)

# 2) HTML (bouton + modal) avant le script principal
m = re.search(r'<script>\s*const CLIENT_ID', html)
assert m, "Ancre HTML introuvable"
html = html[:m.start()] + HTML + html[m.start():]

# 3) JS avant le render(); final du script principal
m = re.search(r"render\(\);\s*</script>\s*<script>\s*if\('serviceWorker'", html)
assert m, "Ancre JS introuvable"
html = html[:m.start()] + JS + '\n' + html[m.start():]

open('index_new.html', 'w', encoding='utf-8', newline='').write(html)
print('OK -> index_new.html')
