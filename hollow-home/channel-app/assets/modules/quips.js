// transmissão: frase viva do skippy-cards, digitada
const QUIP = SRV + '/api/quip?where=home';
let typing = null, lastQ = '';
async function quip() {
  try { const q = await (await fetch(QUIP, {cache: 'no-store'})).json(); if (q.text === lastQ) return; lastQ = q.text;
    const el = document.getElementById('tx'), t = document.getElementById('txt'); el.className = q.mood; let i = 0; t.textContent = '';
    clearInterval(typing); typing = setInterval(() => { t.textContent = q.text.slice(0, ++i); if (i >= q.text.length) clearInterval(typing); }, 30);
  } catch (e) {}
}
quip(); setInterval(quip, 30000);
