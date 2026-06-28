/* ═══════════════════════════════════════════════════════════════════════════
   Sentinel — Frontend Logic v2
   Premium dashboard controller for the Sentiment & Urgency Detector
   ═══════════════════════════════════════════════════════════════════════════ */

const API = '';  // same origin

// ── State ───────────────────────────────────────────────────────────────────

let expandedTicketId = null;
let currentFilter = 'all';  // 'all' | 'flagged'

// ── DOM refs ────────────────────────────────────────────────────────────────

const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => document.querySelectorAll(sel);

// ── Helpers ─────────────────────────────────────────────────────────────────

function generateTicketId() {
  const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
  const prefix = chars[Math.floor(Math.random() * chars.length)] + chars[Math.floor(Math.random() * chars.length)];
  const num = Math.floor(Math.random() * 90000) + 10000;
  return `${prefix}-${num}`;
}

function clearForm() {
  document.getElementById('ticket-text').value = '';
  document.getElementById('ticket-id').value = generateTicketId();
  document.getElementById('results-panel').classList.remove('visible');
}

function scoreColor(score) {
  if (score <= 2) return 'var(--score-green)';
  if (score <= 4) return 'var(--score-lime)';
  if (score <= 6) return 'var(--score-yellow)';
  if (score <= 8) return 'var(--score-orange)';
  return 'var(--score-red)';
}

function scoreColorHex(score) {
  if (score <= 2) return '#10b981';
  if (score <= 4) return '#84cc16';
  if (score <= 6) return '#eab308';
  if (score <= 8) return '#f97316';
  return '#ef4444';
}

function scoreClass(score) {
  return `score-${Math.min(Math.max(Math.round(score), 0), 10)}`;
}

function fillClass(score) {
  return `fill-${Math.min(Math.max(Math.round(score), 0), 10)}`;
}

function badgeClass(score, highThreshold = 7) {
  if (score >= highThreshold) return 'table-badge--high';
  if (score >= 4) return 'table-badge--mid';
  return 'table-badge--low';
}

function formatDate(iso) {
  if (!iso) return '—';
  const d = new Date(iso);
  return d.toLocaleDateString('en-US', {
    month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
  });
}

function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

// ── Animated Particles Background ───────────────────────────────────────────

function initParticles() {
  const canvas = document.getElementById('particles-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');

  function resize() {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
  }
  resize();
  window.addEventListener('resize', resize);

  const particles = [];
  const count = 75;

  for (let i = 0; i < count; i++) {
    particles.push({
      x: Math.random() * canvas.width,
      y: Math.random() * canvas.height,
      vx: (Math.random() - 0.5) * 0.5,
      vy: Math.random() * 0.5 + 0.2, // drifting downwards like snow
      radius: Math.random() * 2 + 0.5,
      opacity: Math.random() * 0.5 + 0.2,
    });
  }

  function draw() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    particles.forEach(p => {
      p.x += p.vx;
      p.y += p.vy;

      if (p.x < 0) p.x = canvas.width;
      if (p.x > canvas.width) p.x = 0;
      if (p.y < 0) p.y = canvas.height;
      if (p.y > canvas.height) p.y = 0;

      ctx.beginPath();
      ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(255, 255, 255, ${p.opacity})`;
      ctx.shadowBlur = 4;
      ctx.shadowColor = 'rgba(255, 255, 255, 0.5)';
      ctx.fill();
      ctx.shadowBlur = 0; // reset for lines
    });

    // Draw connections
    for (let i = 0; i < particles.length; i++) {
      for (let j = i + 1; j < particles.length; j++) {
        const dx = particles[i].x - particles[j].x;
        const dy = particles[i].y - particles[j].y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < 120) {
          ctx.beginPath();
          ctx.moveTo(particles[i].x, particles[i].y);
          ctx.lineTo(particles[j].x, particles[j].y);
          ctx.strokeStyle = `rgba(255, 255, 255, ${0.1 * (1 - dist / 120)})`;
          ctx.lineWidth = 0.5;
          ctx.stroke();
        }
      }
    }

    requestAnimationFrame(draw);
  }
  draw();
}

// ── Score Ring Animation ────────────────────────────────────────────────────

function setScoreRing(ringId, score) {
  const ring = document.getElementById(ringId);
  if (!ring) return;
  const circumference = 2 * Math.PI * 52; // r=52
  const offset = circumference - (score / 10) * circumference;
  ring.style.strokeDasharray = circumference;
  ring.style.strokeDashoffset = offset;
  ring.style.stroke = scoreColorHex(score);
}

// ── Toast notifications ─────────────────────────────────────────────────────

function showToast(message, type = 'success') {
  const container = document.getElementById('toast-container');
  const toast = document.createElement('div');
  toast.className = `toast toast--${type}`;
  toast.innerHTML = `
    <span>${type === 'error' ? '❌' : '✅'}</span>
    <span>${escapeHtml(message)}</span>
  `;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.animation = 'toastOut 0.3s ease-in forwards';
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

// ── API calls ───────────────────────────────────────────────────────────────

async function apiGet(path) {
  const res = await fetch(`${API}${path}`);
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

async function apiPost(path, body) {
  const res = await fetch(`${API}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

async function apiDelete(path) {
  const res = await fetch(`${API}${path}`, { method: 'DELETE' });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

// ── Health check ────────────────────────────────────────────────────────────

async function checkHealth() {
  const dot = document.getElementById('status-dot');
  const label = document.getElementById('status-label');
  try {
    const data = await apiGet('/health');
    dot.classList.remove('offline');
    label.textContent = `Online · ${data.model}`;
  } catch {
    dot.classList.add('offline');
    label.textContent = 'Offline';
  }
}

// ── Load stats ──────────────────────────────────────────────────────────────

async function loadStats() {
  try {
    const s = await apiGet('/stats');
    document.getElementById('stat-total').textContent = s.total_tickets;
    document.getElementById('stat-flagged').textContent = s.flagged_tickets;
    document.getElementById('stat-sentiment').textContent = s.avg_sentiment.toFixed(1);
    document.getElementById('stat-urgency').textContent = s.avg_urgency.toFixed(1);
  } catch (err) {
    console.error('Failed to load stats:', err);
  }
}

// ── Refresh handler ─────────────────────────────────────────────────────────

async function handleRefresh(btn) {
  const ogText = btn.innerHTML;
  btn.innerHTML = '<span class="btn__icon">🔄</span> Refreshing...';
  btn.disabled = true;
  btn.style.opacity = '0.7';

  await Promise.all([loadTickets(), loadStats()]);

  setTimeout(() => {
    btn.innerHTML = ogText;
    btn.disabled = false;
    btn.style.opacity = '1';
    showToast('Data refreshed successfully', 'success');
  }, 400);
}

// ── Load tickets ────────────────────────────────────────────────────────────

async function loadTickets() {
  try {
    const flaggedOnly = currentFilter === 'flagged';
    const tickets = await apiGet(`/tickets?flagged_only=${flaggedOnly}`);
    renderTicketTable(tickets);

    // Update count badge
    const badge = document.getElementById('ticket-count-badge');
    if (badge) {
      badge.textContent = `${tickets.length} record${tickets.length !== 1 ? 's' : ''}`;
    }
  } catch (err) {
    console.error('Failed to load tickets:', err);
    showToast('Failed to load tickets', 'error');
  }
}

// ── Render ticket table ─────────────────────────────────────────────────────

function renderTicketTable(tickets) {
  const tbody = document.getElementById('tickets-tbody');
  const empty = document.getElementById('tickets-empty');

  if (!tickets.length) {
    tbody.innerHTML = '';
    empty.style.display = 'block';
    return;
  }

  empty.style.display = 'none';

  tbody.innerHTML = tickets.map(t => {
    const sentimentBadge = badgeClass(t.sentiment_score);
    const urgencyBadge = badgeClass(t.urgency_score, 8);
    const flagIcon = t.flagged ? '🚨' : '✅';
    const isExpanded = expandedTicketId === t.id;

    const sourceIcons = {
      zendesk: '🎧', email: '✉️', chat: '💬', manual: '✍️'
    };
    const sourceIcon = sourceIcons[t.source] || '📋';

    let html = `
      <tr data-id="${escapeHtml(t.id)}" class="ticket-row" onclick="toggleExpand('${escapeHtml(t.id)}')">
        <td>${escapeHtml(t.id)}</td>
        <td>${sourceIcon} ${escapeHtml(t.source || '—')}</td>
        <td><span class="badge badge--tone">${escapeHtml(t.tone || '—')}</span></td>
        <td><span class="table-badge ${sentimentBadge}">${t.sentiment_score}/10</span></td>
        <td><span class="table-badge ${urgencyBadge}">${t.urgency_score}/10</span></td>
        <td>${t.churn_risk ? '<span class="badge badge--churn-yes">⚠ Yes</span>' : '<span class="badge badge--churn-no">No</span>'}</td>
        <td>${flagIcon}</td>
        <td>${formatDate(t.created_at)}</td>
      </tr>
    `;

    if (isExpanded) {
      html += `
        <tr class="expanded-row">
          <td colspan="8">
            <div class="expanded-content">
              <div class="expanded-content__text">${escapeHtml(t.text || '')}</div>
              <div class="expanded-content__meta">
                ${t.reason ? `<div class="reason-text" style="flex:1;margin:0;">💡 ${escapeHtml(t.reason)}</div>` : ''}
              </div>
              ${t.draft_reply ? `
              <div class="draft-reply-box" style="margin-top: 14px;">
                <div class="draft-reply-box__header">
                  <span>🤖 AI Draft Reply</span>
                  <button class="btn btn--ghost btn--small" onclick="event.stopPropagation(); copyText(this, \`${escapeHtml(t.draft_reply).replace(/`/g, '\\`').replace(/\\/g, '\\\\')}\`)">📋 Copy</button>
                </div>
                <div class="draft-reply-box__content">${escapeHtml(t.draft_reply)}</div>
              </div>` : ''}
              <div style="display:flex;align-items:center;gap:10px;margin-top:14px;flex-wrap:wrap;">
                ${(t.key_phrases || []).map(p => `<span class="tag">${escapeHtml(p)}</span>`).join('')}
                ${t.alert_reason ? `<div class="alert-reason" style="flex:1;margin:0;"><span class="alert-reason__icon">🚨</span>${escapeHtml(t.alert_reason)}</div>` : ''}
                <button class="btn btn--danger" onclick="event.stopPropagation(); deleteTicket('${escapeHtml(t.id)}')">🗑 Delete</button>
              </div>
            </div>
          </td>
        </tr>
      `;
    }

    return html;
  }).join('');
}

function toggleExpand(id) {
  expandedTicketId = expandedTicketId === id ? null : id;
  loadTickets();
}

// ── Copy helper ─────────────────────────────────────────────────────────────

function copyText(btn, text) {
  navigator.clipboard.writeText(text).then(() => {
    const og = btn.innerHTML;
    btn.innerHTML = '✅ Copied!';
    setTimeout(() => { btn.innerHTML = og; }, 1500);
  });
}

// ── Delete ticket ───────────────────────────────────────────────────────────

async function deleteTicket(id) {
  try {
    await apiDelete(`/tickets/${encodeURIComponent(id)}`);
    showToast(`Ticket ${id} deleted`);
    expandedTicketId = null;
    loadTickets();
    loadStats();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

// ── Reset all tickets ───────────────────────────────────────────────────────

async function resetAllTickets(btn) {
  if (!confirm("Are you sure you want to permanently delete all analyzed tickets? This cannot be undone.")) {
    return;
  }

  const ogText = btn.innerHTML;
  btn.innerHTML = '<span class="btn__icon">⏳</span> Resetting...';
  btn.disabled = true;

  try {
    const result = await apiPost('/reset', {});
    showToast(`Successfully deleted ${result.deleted_count} tickets`, 'success');
    expandedTicketId = null;
    await Promise.all([loadTickets(), loadStats()]);
  } catch (err) {
    showToast(err.message, 'error');
  } finally {
    btn.innerHTML = ogText;
    btn.disabled = false;
  }
}

// ── Analyze ticket ──────────────────────────────────────────────────────────

async function analyzeTicket(e) {
  e.preventDefault();

  const btn = document.getElementById('analyze-btn');
  const ticketId = document.getElementById('ticket-id').value.trim();
  const source = document.getElementById('ticket-source').value;
  const text = document.getElementById('ticket-text').value.trim();

  if (!ticketId || !text) {
    showToast('Please fill in all required fields', 'error');
    return;
  }

  if (text.length < 10) {
    showToast('Ticket text must be at least 10 characters', 'error');
    return;
  }

  // Show loading
  btn.classList.add('btn--loading');
  btn.disabled = true;

  try {
    const result = await apiPost('/analyze', {
      ticket_id: ticketId,
      text: text,
      source: source,
    });

    renderResults(result);
    showToast(`Ticket ${ticketId} analyzed successfully`);

    // Refresh the sidebar data
    loadTickets();
    loadStats();

    // Generate next ID and clear text
    document.getElementById('ticket-id').value = generateTicketId();
    document.getElementById('ticket-text').value = '';

  } catch (err) {
    showToast(err.message, 'error');
  } finally {
    btn.classList.remove('btn--loading');
    btn.disabled = false;
  }
}

function renderResults(result) {
  const panel = document.getElementById('results-panel');
  const scores = result.scores;
  const sentScore = scores.sentiment_score || 0;
  const urgScore = scores.urgency_score || 0;

  // Scores
  const sentEl = document.getElementById('res-sentiment');
  sentEl.textContent = `${sentScore}/10`;
  sentEl.className = `score-item__value ${scoreClass(sentScore)}`;

  const urgEl = document.getElementById('res-urgency');
  urgEl.textContent = `${urgScore}/10`;
  urgEl.className = `score-item__value ${scoreClass(urgScore)}`;

  // Score rings
  setScoreRing('res-sentiment-ring', sentScore);
  setScoreRing('res-urgency-ring', urgScore);

  // Score bars
  const sentBar = document.getElementById('res-sentiment-bar');
  sentBar.style.width = `${sentScore * 10}%`;
  sentBar.className = `score-item__fill ${fillClass(sentScore)}`;

  const urgBar = document.getElementById('res-urgency-bar');
  urgBar.style.width = `${urgScore * 10}%`;
  urgBar.className = `score-item__fill ${fillClass(urgScore)}`;

  // Churn risk
  const churnEl = document.getElementById('res-churn');
  if (scores.churn_risk) {
    churnEl.innerHTML = '<span class="badge badge--churn-yes">⚠ High Risk</span>';
  } else {
    churnEl.innerHTML = '<span class="badge badge--churn-no">✅ Low Risk</span>';
  }

  // Tone
  document.getElementById('res-tone').innerHTML =
    `<span class="badge badge--tone">${escapeHtml(scores.tone || 'unknown')}</span>`;

  // Flagged status
  const flagEl = document.getElementById('res-flagged');
  if (result.flagged) {
    flagEl.innerHTML = '<span class="badge badge--flagged">🚨 FLAGGED</span>';
  } else {
    flagEl.innerHTML = '<span class="badge badge--safe">✅ Safe</span>';
  }

  // Alert reason
  const alertBox = document.getElementById('res-alert-reason');
  if (result.alert_reason) {
    alertBox.innerHTML = `
      <div class="alert-reason">
        <span class="alert-reason__icon">🚨</span>
        <span>${escapeHtml(result.alert_reason)}</span>
      </div>`;
    alertBox.style.display = 'block';
  } else {
    alertBox.style.display = 'none';
  }

  // Reason
  const reasonBox = document.getElementById('res-reason');
  if (scores.reason) {
    reasonBox.innerHTML = `<div class="reason-text">💡 ${escapeHtml(scores.reason)}</div>`;
    reasonBox.style.display = 'block';
  } else {
    reasonBox.style.display = 'none';
  }

  // Key phrases
  const tagsEl = document.getElementById('res-tags');
  const phrases = scores.key_phrases || [];
  if (phrases.length) {
    tagsEl.innerHTML = `
      <div class="tags">
        ${phrases.map(p => `<span class="tag">${escapeHtml(p)}</span>`).join('')}
      </div>`;
    tagsEl.style.display = 'block';
  } else {
    tagsEl.style.display = 'none';
  }

  // Draft Reply
  const draftBox = document.getElementById('res-draft-reply');
  if (result.draft_reply) {
    draftBox.innerHTML = `
      <div class="draft-reply-box">
        <div class="draft-reply-box__header">
          <span>🤖 AI Draft Reply</span>
          <button type="button" class="btn btn--ghost btn--small" onclick="copyText(this, \`${escapeHtml(result.draft_reply).replace(/`/g, '\\`').replace(/\\/g, '\\\\')}\`)">📋 Copy</button>
        </div>
        <div class="draft-reply-box__content">${escapeHtml(result.draft_reply)}</div>
      </div>
    `;
    draftBox.style.display = 'block';
  } else {
    draftBox.style.display = 'none';
  }

  // Show panel with animation
  panel.classList.add('visible');
  panel.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

// ── Filter controls ─────────────────────────────────────────────────────────

function setFilter(filter) {
  currentFilter = filter;
  expandedTicketId = null;

  $$('.filter-btn').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.filter === filter);
  });

  loadTickets();
}

// ── Scroll Reveal ───────────────────────────────────────────────────────────

function initScrollReveal() {
  const observerOptions = {
    root: null,
    rootMargin: '0px',
    threshold: 0.15
  };

  const observer = new IntersectionObserver((entries, obs) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('active');
        obs.unobserve(entry.target); // Reveal only once
      }
    });
  }, observerOptions);

  $$('.reveal, .reveal-zoom').forEach(el => {
    observer.observe(el);
  });
}

// ── Init ────────────────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
  // Init particles
  initParticles();

  // Init scroll animations
  initScrollReveal();

  // Set initial ticket ID
  document.getElementById('ticket-id').value = generateTicketId();

  // Bind form
  document.getElementById('analyze-form').addEventListener('submit', analyzeTicket);

  // Bind filters
  $$('.filter-btn').forEach(btn => {
    btn.addEventListener('click', () => setFilter(btn.dataset.filter));
  });

  // Initial data load
  checkHealth();
  loadStats();
  loadTickets();

  // Periodic health check
  setInterval(checkHealth, 30000);
});
