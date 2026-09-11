from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import HTMLResponse


router = APIRouter(tags=["X Manual Replies"])


@router.get("/x/opportunities", response_class=HTMLResponse)
def x_manual_reply_queue() -> HTMLResponse:
    return HTMLResponse(
        content=r"""
<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Holomancy · X Opportunities</title>
  <style>
    :root { color-scheme: dark; }
    body { font-family: Inter, system-ui, sans-serif; margin: 0; background: #0b0b0f; color: #f5f5f7; }
    main { width: min(980px, calc(100% - 32px)); margin: 40px auto; }
    h1 { margin-bottom: 8px; }
    .muted { color: #a7a7b3; }
    .toolbar { display: grid; grid-template-columns: 1fr auto auto; gap: 10px; margin: 24px 0; }
    input, select, textarea, button, a.button { font: inherit; }
    input, select, textarea { background: #17171d; color: #fff; border: 1px solid #30303a; border-radius: 10px; padding: 11px 12px; }
    button, a.button { border: 0; border-radius: 10px; padding: 10px 14px; cursor: pointer; text-decoration: none; background: #fff; color: #111; font-weight: 650; }
    .secondary { background: #24242c !important; color: #fff !important; }
    .card { background: #141419; border: 1px solid #2a2a33; border-radius: 16px; padding: 18px; margin: 14px 0; }
    .meta { display: flex; gap: 10px; flex-wrap: wrap; color: #aaaab6; font-size: 13px; }
    .tweet { margin: 14px 0; line-height: 1.5; white-space: pre-wrap; }
    textarea { width: 100%; min-height: 88px; box-sizing: border-box; resize: vertical; }
    .actions { display: flex; gap: 10px; margin-top: 12px; flex-wrap: wrap; }
    .error { color: #ff8f8f; margin: 12px 0; white-space: pre-wrap; }
    @media (max-width: 700px) { .toolbar { grid-template-columns: 1fr; } }
  </style>
</head>
<body>
<main>
  <h1>Oportunidades no X</h1>
  <div class="muted">Carrega as oportunidades geradas pela IA. Copie a resposta e abra o tweet para publicar manualmente.</div>

  <div class="toolbar">
    <input id="token" type="password" placeholder="X_SCHEDULER_ADMIN_TOKEN" autocomplete="off" />
    <select id="status">
      <option value="GENERATED">GENERATED</option>
      <option value="FAILED">FAILED</option>
      <option value="REJECTED">REJECTED</option>
      <option value="POSTED">POSTED</option>
    </select>
    <button id="load">Carregar</button>
  </div>

  <div id="error" class="error"></div>
  <div id="list"></div>
</main>
<script>
const tokenEl = document.getElementById('token');
const statusEl = document.getElementById('status');
const listEl = document.getElementById('list');
const errorEl = document.getElementById('error');

document.getElementById('load').addEventListener('click', loadOpportunities);

async function loadOpportunities() {
  errorEl.textContent = '';
  listEl.innerHTML = '';
  const token = tokenEl.value.trim();
  if (!token) {
    errorEl.textContent = 'Informe o X_SCHEDULER_ADMIN_TOKEN.';
    return;
  }

  const status = encodeURIComponent(statusEl.value);
  const response = await fetch(`/api/social/x/opportunities?status=${status}&limit=100`, {
    headers: { Authorization: `Bearer ${token}` }
  });

  if (!response.ok) {
    errorEl.textContent = `${response.status} ${await response.text()}`;
    return;
  }

  const rows = await response.json();
  if (!rows.length) {
    listEl.innerHTML = '<div class="muted">Nenhuma oportunidade encontrada.</div>';
    return;
  }

  for (const row of rows) {
    const card = document.createElement('section');
    card.className = 'card';

    const username = row.author_username ? `@${row.author_username}` : 'autor desconhecido';
    const tweetUrl = row.author_username
      ? `https://x.com/${encodeURIComponent(row.author_username)}/status/${encodeURIComponent(row.tweet_id)}`
      : `https://x.com/i/web/status/${encodeURIComponent(row.tweet_id)}`;

    card.innerHTML = `
      <div class="meta">
        <span>#${escapeHtml(String(row.id))}</span>
        <span>${escapeHtml(username)}</span>
        <span>score ${escapeHtml(String(row.score))}</span>
        <span>${escapeHtml(row.language || '')}</span>
      </div>
      <div class="tweet">${escapeHtml(row.tweet_text || '')}</div>
      <textarea>${escapeHtml(row.suggested_reply || '')}</textarea>
      <div class="actions">
        <button class="copy">Copiar resposta</button>
        <a class="button secondary" href="${tweetUrl}" target="_blank" rel="noopener noreferrer">Abrir tweet no X</a>
      </div>
    `;

    card.querySelector('.copy').addEventListener('click', async (event) => {
      const text = card.querySelector('textarea').value;
      await navigator.clipboard.writeText(text);
      const button = event.currentTarget;
      const original = button.textContent;
      button.textContent = 'Copiado';
      setTimeout(() => button.textContent = original, 1200);
    });

    listEl.appendChild(card);
  }
}

function escapeHtml(value) {
  return value
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;');
}
</script>
</body>
</html>
"""
    )
