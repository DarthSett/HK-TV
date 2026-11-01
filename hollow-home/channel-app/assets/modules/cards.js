// OPTIONAL feature "cards": the HUD card row fed by the cards server (cards/app.py). Enabled with features.cards in house.json.
const FEED = SRV + '/feed.json?home=1';
let feedSig = '';
async function loadFeed() {
  const net = document.getElementById('net');
  try {
    const r = await fetch(FEED, {cache: 'no-store'}); const j = await r.json();
    const sigNew = JSON.stringify(j.cards || []);
    if (sigNew === feedSig) { net.className = 'ok'; net.textContent = 'ONLINE'; loaded = true; return; }   // nothing changed: do not redraw (avoids flicker)
    feedSig = sigNew;
    const keep = row === 0 && CARDS[idx[0]] ? CARDS[idx[0]].id : null;
    CARDS = j.cards || [];
    if (keep) { const n = CARDS.findIndex(c => c.id === keep); if (n >= 0) idx[0] = n; }
    net.className = 'ok'; net.textContent = 'ONLINE';
  } catch (e) { net.className = 'off'; net.textContent = 'OFFLINE'; }
  loaded = true; render();
}
loadFeed(); setInterval(loadFeed, 30 * 1000);   // the feed is cached on the server (~30 ms)
