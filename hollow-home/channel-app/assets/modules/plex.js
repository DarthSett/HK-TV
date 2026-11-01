// órbita do Plex: slides do /api/plex (agora, continuar, próximo, chegou, semana), troca a cada 9 s
let OS = [], oi = 0;
function slides(v) {
  const s = [], ago = t => { const d = Math.floor((Date.now() / 1000 - (t || 0)) / 86400); return d < 1 ? 'hoje' : d < 2 ? 'ontem' : 'há ' + d + ' dias'; };
  if (v.now) s.push({lab: v.now.state === 'paused' ? 'PLEX // PAUSADO' : 'PLEX // TOCANDO AGORA', live: true, tt: v.now.show, st: v.now.sub + (v.now.left != null ? ' · faltam ' + v.now.left + ' min' : ''), img: v.now.poster, prog: v.now.prog});
  if (v.next) s.push({lab: 'PLEX // PRÓXIMO EPISÓDIO', tt: v.next.show, st: v.next.sub, img: v.next.poster, prog: 0});
  (v.cont || []).slice(0, 2).forEach(c => s.push({lab: 'PLEX // CONTINUAR', tt: c.show, st: c.sub + (c.left != null ? ' · faltam ' + c.left + ' min' : ''), img: c.poster, prog: c.prog}));
  (v.new || []).slice(0, 3).forEach(n => s.push({lab: 'PLEX // CHEGOU ' + ago(n.added).toUpperCase(), tt: n.show, st: n.sub, img: n.poster, prog: 0}));
  const w = v.week;
  if (w && (w.eps || w.movies)) s.push({lab: 'PLEX // TUA SEMANA', stat: String(w.eps + w.movies), tt: w.eps + ' episódio' + (w.eps !== 1 ? 's' : '') + ' · ' + w.movies + ' filme' + (w.movies !== 1 ? 's' : ''),
    st: w.top && w.top_n >= 2 ? 'Maratona: ' + w.top + ', ' + w.top_n + ' ep. Eu vi. Eu julguei.' : 'Ritmo moderado. Eu esperava mais de ti.', prog: 0});
  return s;
}
function show(i) {
  const o = document.getElementById('orb'), t = document.getElementById('orbTxt'), x = OS[i]; if (!x) return;
  t.classList.add('out');
  setTimeout(() => {
    o.className = (x.live ? 'live' : '') + (x.stat ? ' stat' : '');
    document.getElementById('orbLab').innerHTML = '<i></i>' + x.lab;
    document.getElementById('orbTt').textContent = x.tt || '';
    document.getElementById('orbSt').textContent = x.st || '';
    if (x.img) document.getElementById('orbImg').src = SRV + x.img;
    document.getElementById('orbBig').textContent = x.stat || '';
    document.getElementById('orbRing').setAttribute('stroke-dasharray', (320.4 * (x.prog || 0)).toFixed(1) + ' 320.4');
    document.getElementById('orbDots').innerHTML = OS.map((_, k) => '<b' + (k === i ? ' class="on"' : '') + '></b>').join('');
    t.classList.remove('out');
  }, 450);
}
async function loadPlex() {
  try { const v = await (await fetch(SRV + '/api/plex', {cache: 'no-store'})).json(); const n = slides(v);
    if (JSON.stringify(n) !== JSON.stringify(OS)) { OS = n; oi = oi % Math.max(1, OS.length); show(oi); }
  } catch (e) {}
}
loadPlex(); setInterval(loadPlex, 60000);
setInterval(() => { if (OS.length > 1) { oi = (oi + 1) % OS.length; show(oi); } }, 9000);
