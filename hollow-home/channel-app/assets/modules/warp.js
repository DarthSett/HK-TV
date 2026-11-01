// easter egg: código Konami → salto hiperespacial (estrelas esticando) e volta
const KON = ['ArrowUp','ArrowUp','ArrowDown','ArrowDown','ArrowLeft','ArrowRight','ArrowLeft','ArrowRight'];
let kseq = [], warping = false;
const DEST = ['Destino: Plex. Tempo estimado: 0 s. Distância percorrida: nenhuma.', 'Destino: a geladeira. Rota calculada.',
  'Destino: Alfa Centauri. Cancelado: o Wi-Fi não pega lá.', 'Destino: o mesmo sofá. Viagem incrível, né?'];
function warp() {
  if (warping) return; warping = true;
  const w = document.getElementById('warp'), c = document.getElementById('wc'), g = c.getContext('2d');
  document.getElementById('ws').textContent = DEST[Math.floor(Math.random() * DEST.length)];
  w.classList.add('on');
  const S = Array.from({length: 400}, () => ({a: Math.random() * 6.283, r: Math.random() * 60, v: 2 + Math.random() * 6}));
  let f = 0;
  const step = () => {
    g.fillStyle = 'rgba(0,4,12,.35)'; g.fillRect(0, 0, 1920, 1080);
    const k = Math.min(1, f / 60);
    S.forEach(s => { const r0 = s.r; s.r += s.v * (1 + k * 18); const x0 = 960 + Math.cos(s.a) * r0, y0 = 540 + Math.sin(s.a) * r0,
      x1 = 960 + Math.cos(s.a) * s.r, y1 = 540 + Math.sin(s.a) * s.r;
      g.strokeStyle = `rgba(${170 + 80 * k},235,255,${.5 + .5 * k})`; g.lineWidth = 1 + k * 2; g.beginPath(); g.moveTo(x0, y0); g.lineTo(x1, y1); g.stroke();
      if (s.r > 1200) { s.r = Math.random() * 40; } });
    if (++f < 200) requestAnimationFrame(step); else { w.classList.remove('on'); g.clearRect(0, 0, 1920, 1080); warping = false; lastQ = '';
      document.getElementById('txt').textContent = 'Salto concluído. Chegamos exatamente onde estávamos. De nada.'; }
  };
  step();
}
document.addEventListener('keydown', ev => { if (warping) { ev.stopPropagation(); ev.preventDefault(); return; } kseq.push(ev.key); kseq = kseq.slice(-8); if (kseq.join() === KON.join()) { kseq = []; row = 1; idx[1] = 0; focus(); warp(); ev.stopPropagation(); ev.preventDefault(); } }, true);
