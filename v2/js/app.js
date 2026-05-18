document.addEventListener('DOMContentLoaded', async () => {
  try {
    const [metaRes, promisesRes] = await Promise.all([
      fetch('data/meta.json'),
      fetch('data/promises.json')
    ]);

    if (!metaRes.ok || !promisesRes.ok) {
      throw new Error('Data files could not be loaded. Serve v2 through a static web server.');
    }

    const meta = await metaRes.json();
    const promises = await promisesRes.json();

    window.siteData = { meta, promises };
    window.currentFilter = 'all';
    window.autoRotateInterval = null; // Global reference for the ticker interval

    document.title = `${meta.title} - West Bengal Promise Tracker 2026-2031`;
    document.getElementById('site-subtitle').textContent = meta.subtitle;
    document.getElementById('last-updated-footer').textContent =
      'Last updated: ' + new Date(meta.lastUpdated).toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric' });

    renderMastheadMeta(meta);
    updateTodayDate();
    setInterval(updateTodayDate, 60000);

    initTimer(meta);

    renderNav(meta.categories);
    renderMobileNav(meta.categories);
    renderStats();
    renderLatestUpdates();
    renderKeyPromises();
    renderCategories();
    setupFilters();
    updateFiltersUI();
    updateResultSummary();

    // Deep link handling
    if (window.location.hash) {
      const targetId = window.location.hash.substring(1);
      setTimeout(() => scrollToPromise(targetId), 500);
    }

    // Home button handling
    const homeBtn = document.getElementById('fab-home');
    if (homeBtn) {
      homeBtn.addEventListener('click', () => {
        window.scrollTo({ top: 0, behavior: 'smooth' });
        // Clear hash without reload
        history.replaceState(null, null, ' ');
      });
    }
  } catch (error) {
    console.error('Failed to load data:', error);
    document.getElementById('categories-container').innerHTML =
      '<div class="loading error-state">Failed to load promises data. Run this through a local server or deploy to Cloudflare Pages.</div>';
  }
});

// ── MASTHEAD META ─────────────────────────────────────────────────────────
function renderMastheadMeta(meta) {
  const container = document.getElementById('masthead-meta');
  if (!container) return;

  const OATH_DATE = new Date(meta.oathDate);
  const TERM_END = new Date(meta.termEnd);
  const now = new Date();
  const daysIn = Math.max(1, Math.floor((now - OATH_DATE) / 86400000) + 1);
  const daysLeft = Math.max(0, Math.floor((TERM_END - now) / 86400000));

  const items = [
    { label: 'Chief Minister', value: meta.chiefMinister },
    { label: 'Oath Ceremony', value: meta.oathCeremony },
    { label: 'Term Ends', value: 'May 2031' },
    { label: 'Days in Office', value: daysIn + (daysIn === 1 ? ' day' : ' days'), id: 'days-in-office' },
    { label: 'Days Remaining', value: daysLeft + ' days', id: 'days-remaining' }
  ];

  container.innerHTML = items.map(item =>
    `<div class="meta-item">
      <span class="meta-label">${escapeHtml(item.label)}</span>
      <span class="meta-value"${item.id ? ` id="${item.id}"` : ''}>${escapeHtml(item.value)}</span>
    </div>`
  ).join('');
}

// ── DATE & TIMER ──────────────────────────────────────────────────────────
function updateTodayDate() {
  const todayEl = document.getElementById('today-date');
  if (!todayEl) return;
  todayEl.textContent = new Date().toLocaleDateString('en-IN', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  });
}

function pad(n) { return String(n).padStart(2, '0'); }

function initTimer(meta) {
  const OATH_DATE = new Date(meta.oathDate);
  const TERM_END = new Date(meta.termEnd);

  function updateTimer() {
    const now = new Date();

    // Days in office / remaining
    const daysIn = Math.max(1, Math.floor((now - OATH_DATE) / 86400000) + 1);
    const daysLeft = Math.max(0, Math.floor((TERM_END - now) / 86400000));
    const dioEl = document.getElementById('days-in-office');
    const drEl = document.getElementById('days-remaining');
    if (dioEl) dioEl.textContent = daysIn + (daysIn === 1 ? ' day' : ' days');
    if (drEl) drEl.textContent = daysLeft + ' days';

    // Countdown to TERM_END
    const diff = TERM_END - now;
    if (diff > 0) {
      const yrs = Math.floor(diff / (365.25 * 24 * 3600 * 1000));
      const rem1 = diff % (365.25 * 24 * 3600 * 1000);
      const mths = Math.floor(rem1 / (30.44 * 24 * 3600 * 1000));
      const rem2 = rem1 % (30.44 * 24 * 3600 * 1000);
      const days = Math.floor(rem2 / (24 * 3600 * 1000));
      const rem3 = rem2 % (24 * 3600 * 1000);
      const hrs = Math.floor(rem3 / (3600 * 1000));
      const mins = Math.floor((rem3 % (3600 * 1000)) / 60000);
      const secs = Math.floor((rem3 % 60000) / 1000);

      document.getElementById('t-years').textContent = pad(yrs);
      document.getElementById('t-months').textContent = pad(mths);
      document.getElementById('t-days').textContent = pad(days);
      document.getElementById('t-hours').textContent = pad(hrs);
      document.getElementById('t-mins').textContent = pad(mins);
      document.getElementById('t-secs').textContent = pad(secs);
    } else {
      ['t-years', 't-months', 't-days', 't-hours', 't-mins', 't-secs']
        .forEach(id => document.getElementById(id).textContent = '00');
    }
  }

  updateTimer();
  setInterval(updateTimer, 1000);
}

function escapeHtml(value) {
  return String(value ?? '').replace(/[&<>"']/g, (char) => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;'
  }[char]));
}

function formatCount(count, singular, plural = `${singular}s`) {
  return `${count} ${count === 1 ? singular : plural}`;
}

function formatStatus(status) {
  switch (status) {
    case 'done': return '✓ Fulfilled';
    case 'inprogress': return '◑ In Progress';
    case 'evaded': return '✗ Evaded';
    default: return 'Pending';
  }
}

function highlightText(text, highlight) {
  if (!highlight) return escapeHtml(text);
  const full = String(text);
  const idx = full.toLowerCase().indexOf(String(highlight).toLowerCase());
  if (idx < 0) return escapeHtml(full);
  return `${escapeHtml(full.slice(0, idx))}<span class="highlight">${escapeHtml(full.slice(idx, idx + highlight.length))}</span>${escapeHtml(full.slice(idx + highlight.length))}`;
}

function filterPromises(promises) {
  return promises.filter((p) => window.currentFilter === 'all' || p.status === window.currentFilter);
}

function rerenderMain() {
  renderStats();
  renderLatestUpdates(); // Ensure it respects the filter
  renderKeyPromises();
  renderCategories();
  updateResultSummary();
  if (window.siteData && window.siteData.meta) {
    renderNav(window.siteData.meta.categories);
    renderMobileNav(window.siteData.meta.categories);
  }
}

function renderNav(categories) {
  const nav = document.getElementById('desktop-nav');
  if (!nav) return;
  const key15Link = (window.currentFilter === 'all') 
    ? '<a href="#key-15">⭐ 15 Key</a>' 
    : '';
  nav.innerHTML =
    key15Link +
    categories.map((c) => `<a href="#${escapeHtml(c.id)}">${escapeHtml(c.icon)} ${escapeHtml(c.title.split(' ')[0])}</a>`).join('');
}

function renderMobileNav(categories) {
  const dropdown = document.getElementById('nav-dropdown');
  if (!dropdown) return;
  
  const key15Link = (window.currentFilter === 'all')
    ? '<a href="#key-15" onclick="closeMobileNav()">⭐ 15 Key Promises</a>'
    : '';

  dropdown.innerHTML =
    key15Link +
    categories.map((c) => `<a href="#${escapeHtml(c.id)}" onclick="closeMobileNav()">${escapeHtml(c.icon)} ${escapeHtml(c.title)}</a>`).join('');

  const trigger = document.getElementById('nav-trigger');
  if (trigger && !trigger.hasAttribute('data-listener-set')) {
    trigger.addEventListener('click', toggleMobileNav);
    trigger.setAttribute('data-listener-set', 'true');
  }

  // Close mobile nav when tapping outside
  if (!window.mobileNavOutsideListenerSet) {
    document.addEventListener('click', function (e) {
      const nav = document.querySelector('.cat-nav-mobile');
      if (nav && !nav.contains(e.target)) closeMobileNav();
    });
    window.mobileNavOutsideListenerSet = true;
  }
}

function toggleMobileNav() {
  const trigger = document.getElementById('nav-trigger');
  const dropdown = document.getElementById('nav-dropdown');
  const isOpen = dropdown.classList.contains('open');
  if (isOpen) {
    dropdown.classList.remove('open');
    trigger.classList.remove('open');
    trigger.setAttribute('aria-expanded', 'false');
  } else {
    dropdown.classList.add('open');
    trigger.classList.add('open');
    trigger.setAttribute('aria-expanded', 'true');
  }
}

function closeMobileNav() {
  const trigger = document.getElementById('nav-trigger');
  const dropdown = document.getElementById('nav-dropdown');
  if (dropdown) dropdown.classList.remove('open');
  if (trigger) {
    trigger.classList.remove('open');
    trigger.setAttribute('aria-expanded', 'false');
  }
}

function renderStats() {
  const allPromises = window.siteData.promises;
  const total = allPromises.length;
  const counts = { done: 0, inprogress: 0, evaded: 0, pending: 0 };
  allPromises.forEach((p) => { counts[p.status] += 1; });

  document.getElementById('stat-total').textContent = total;
  document.getElementById('stat-done').textContent = counts.done;
  document.getElementById('stat-inprogress').textContent = counts.inprogress;
  document.getElementById('stat-evaded').textContent = counts.evaded;
  document.getElementById('stat-pending').textContent = counts.pending;

  // Completion rate (always based on all promises)
  const pct = total > 0 ? Math.round((counts.done / total) * 100) : 0;
  const pctEl = document.getElementById('stat-pct');
  if (pctEl) pctEl.textContent = pct + '%';

  const donePct = total ? (counts.done / total) * 100 : 0;
  const inProgPct = total ? (counts.inprogress / total) * 100 : 0;
  const evadedPct = total ? (counts.evaded / total) * 100 : 0;
  document.getElementById('bar-done').style.width = `${donePct}%`;
  document.getElementById('bar-inprog').style.width = `${inProgPct}%`;
  document.getElementById('bar-evaded').style.width = `${evadedPct}%`;
}

async function renderLatestUpdates() {
  const section = document.getElementById('dispatch-section');
  const ticker = document.getElementById('dispatch-ticker');
  if (!ticker || !section) return;

  // Hide ticker if any filter is active
  if (window.currentFilter !== 'all') {
    section.style.display = 'none';
    if (window.autoRotateInterval) clearInterval(window.autoRotateInterval);
    return;
  }

  // If already rendered and filter is 'all', just show it
  if (ticker.querySelector('.dispatch-item') && section.style.display !== 'none') {
    return; 
  }
  
  section.style.display = 'block';

  try {
    const [updatesRes, initiativesRes] = await Promise.all([
      fetch('data/updates.json'),
      fetch('data/initiative_updates.json')
    ]);
    
    let updates = [];
    let initiatives = [];
    
    if (updatesRes.ok) updates = await updatesRes.json();
    if (initiativesRes.ok) initiatives = await initiativesRes.json();
    
    // Mark initiatives
    initiatives = initiatives.map(i => ({ ...i, isInitiative: true }));
    
    const allUpdates = [...updates, ...initiatives];
    
    // Sort by date desc
    allUpdates.sort((a, b) => b.date.localeCompare(a.date));
    
    const latest = allUpdates.slice(0, 10);

    if (!latest.length) {
      section.style.display = 'none';
      return;
    }

    let currentIndex = 0;

    function renderTickerItem(index) {
      const u = latest[index];
      const dateFormatted = new Date(u.date).toLocaleDateString('en-IN', { day: 'numeric', month: 'short' });
      const metaPrefix = u.isInitiative ? '<span style="color:var(--saffron); font-weight:700">INITIATIVE</span> • ' : '';
      const linkHref = u.isInitiative ? `initiatives.html#${u.promiseId}` : `#${u.promiseId}`;
      const linkOnClick = u.isInitiative ? '' : `onclick="scrollToPromise('${escapeHtml(u.promiseId)}')"`;
      const linkText = u.isInitiative ? 'View Initiative Details →' : 'Read Full Promise Details →';
      
      return `
        <div class="dispatch-item">
          <span class="dispatch-meta">${metaPrefix}${escapeHtml(u.category.replace('-', ' '))} • ${dateFormatted}</span>
          <span class="dispatch-text">${escapeHtml(u.note.substring(0, 140))}${u.note.length > 140 ? '...' : ''}</span>
          <a href="${linkHref}" class="dispatch-link" ${linkOnClick}>${linkText}</a>
        </div>
      `;
    }

    function showNext() {
      currentIndex = (currentIndex + 1) % latest.length;
      updateDisplay();
    }

    function showPrev() {
      currentIndex = (currentIndex - 1 + latest.length) % latest.length;
      updateDisplay();
    }

    function updateDisplay() {
      const container = document.getElementById('dispatch-ticker');
      const current = container.querySelector('.dispatch-item');
      if (current) {
        current.classList.add('exit');
        current.classList.remove('active');
      }

      setTimeout(() => {
        container.innerHTML = renderTickerItem(currentIndex);
        // Small delay to trigger the entrance animation
        setTimeout(() => {
           const newItem = container.querySelector('.dispatch-item');
           if (newItem) newItem.classList.add('active');
        }, 50);
      }, 400);
    }

    ticker.innerHTML = renderTickerItem(0);
    setTimeout(() => {
        const first = ticker.querySelector('.dispatch-item');
        if (first) first.classList.add('active');
    }, 50);

    // Setup Controls
    const nextBtn = document.getElementById('dispatch-next');
    const prevBtn = document.getElementById('dispatch-prev');
    const dispatchCard = document.querySelector('.dispatch-card');

    const startRotation = () => {
        clearInterval(window.autoRotateInterval);
        window.autoRotateInterval = setInterval(showNext, 3500);
    };

    nextBtn.addEventListener('click', () => {
      clearInterval(window.autoRotateInterval);
      showNext();
    });

    prevBtn.addEventListener('click', () => {
      clearInterval(window.autoRotateInterval);
      showPrev();
    });

    // Pause on hover
    dispatchCard.addEventListener('mouseenter', () => clearInterval(window.autoRotateInterval));
    dispatchCard.addEventListener('mouseleave', startRotation);

    startRotation();

  } catch (e) {
    console.error(e);
    ticker.innerHTML = '<div class="loading error-state">Failed to load live feed.</div>';
  }
}

function renderKeyPromises() {
  const grid = document.getElementById('key-promises-grid');
  const section = document.getElementById('key-15');
  const keyPromises = window.siteData.promises
    .filter((p) => p.keyPromise !== null)
    .sort((a, b) => a.keyPromise - b.keyPromise);

  if (!keyPromises.length || window.currentFilter !== 'all') {
    section.classList.add('hidden');
    return;
  }

  section.classList.remove('hidden');
  
  // Group promises by keyPromise ID
  const groups = {};
  window.siteData.promises.forEach(p => {
    if (p.keyPromise !== null) {
      if (!groups[p.keyPromise]) groups[p.keyPromise] = [];
      groups[p.keyPromise].push(p);
    }
  });

  const sortedKeys = Object.keys(groups).map(Number).sort((a, b) => a - b);

  const getGroupStatus = (group) => {
    if (group.some(p => p.status === 'done')) return 'done';
    if (group.some(p => p.status === 'inprogress')) return 'inprogress';
    if (group.some(p => p.status === 'evaded')) return 'evaded';
    return 'pending';
  };

  const kpBadge = (s) => {
    if (s === 'done') return '✓ Fulfilled';
    if (s === 'inprogress') return '◑ In Progress';
    if (s === 'evaded') return '✗ Evaded';
    return 'Pending';
  };

  grid.innerHTML = sortedKeys.map(key => {
    const group = groups[key];
    const primary = group[0]; // First promise in group is the scroll target
    const status = getGroupStatus(group);
    return `
      <button class="kp-card ${escapeHtml(status)}" type="button" onclick="openKeyPromiseGroup(${key})">
        <span class="kp-num">${escapeHtml(String(key))}</span>
        <p class="kp-text">${escapeHtml(primary.highlight || `${primary.text.slice(0, 80)}...`)}</p>
        <span class="kp-badge">${kpBadge(status)}</span>
      </button>
    `;
  }).join('');
}

function openKeyPromiseGroup(keyNum) {
  if (!window.siteData) return;
  window.currentFilter = 'all';
  updateFiltersUI();
  rerenderMain();

  const group = window.siteData.promises.filter(p => p.keyPromise === keyNum);
  if (!group.length) return;

  // Wait a tiny bit for DOM to be ready after rerender
  setTimeout(() => {
    group.forEach((p, index) => {
      const el = document.getElementById(`item-${p.id}`);
      if (!el) return;

      const list = el.closest('.promise-list');
      if (list?.classList.contains('collapsed')) {
        toggleCat(list.previousElementSibling);
      }

      if (index === 0) {
        el.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }

      el.style.backgroundColor = 'rgba(232, 98, 10, 0.1)';
      setTimeout(() => { el.style.backgroundColor = ''; }, 2000);

      togglePromiseDetails(p.id, true);
    });
  }, 50);
}

function renderCategories() {
  const { meta, promises } = window.siteData;
  const filteredPromises = filterPromises(promises);
  const container = document.getElementById('categories-container');

  if (!filteredPromises.length) {
    container.innerHTML = '<div class="loading">No promises match this filter.</div>';
    return;
  }

  let html = '';
  meta.categories.forEach((cat) => {
    const catPromises = filteredPromises.filter((p) => p.category === cat.id);
    if (!catPromises.length) return;

    const completed = catPromises.filter(p => p.status === 'done').length;
    const active = catPromises.filter(p => p.status === 'inprogress').length;

    const parts = [];
    if (completed > 0) parts.push(`${completed} completed`);
    if (active > 0) parts.push(`${active} active`);
    parts.push(`${catPromises.length} ${catPromises.length === 1 ? 'promise' : 'promises'}`);

    const badgeText = parts.join(' · ');

    html += `
      <section class="category" id="${escapeHtml(cat.id)}">
        <div class="cat-header" role="button" tabindex="0" aria-expanded="true" onclick="toggleCat(this)" onkeydown="handleCatKey(event, this)">
          <span class="cat-icon">${escapeHtml(cat.icon)}</span>
          <div class="cat-title-wrap">
            <h2 class="cat-title">${escapeHtml(cat.title)}</h2>
            <p class="cat-subtitle">${escapeHtml(cat.subtitle)}</p>
          </div>
          <div class="cat-stats"><span class="badge">${escapeHtml(badgeText)}</span></div>
          <span class="cat-toggle">▾</span>
        </div>
        <ul class="promise-list">
          ${catPromises.map((p) => `
            <li class="promise-item ${escapeHtml(p.status)}" id="item-${escapeHtml(p.id)}">
              <span class="promise-num">${escapeHtml(p.number)}</span>
              <div class="promise-content">
                <div class="promise-header">
                  <button class="promise-text ${(p.updateCount > 0 || p.counterCount > 0) ? 'has-details' : ''}" type="button" ${(p.updateCount > 0 || p.counterCount > 0) ? `onclick="togglePromiseDetails('${escapeHtml(p.id)}')" ` : ''}>${highlightText(p.text, p.highlight)}</button>
                  <span class="note-tag note-${escapeHtml(p.status)}">${formatStatus(p.status)}</span>
                </div>
                <div class="promise-actions">
                  ${(p.updateCount > 0 || p.counterCount > 0) ? `
                    <button class="promise-meta" type="button" onclick="togglePromiseDetails('${escapeHtml(p.id)}')">
                      ${p.updateCount > 0 ? formatCount(p.updateCount, 'update') : ''}
                      ${p.updateCount > 0 && p.counterCount > 0 ? ' | ' : ''}
                      ${p.counterCount > 0 ? formatCount(p.counterCount, 'counter-note') : ''}
                      →
                    </button>
                  ` : ''}
                  ${(p.status === 'done' || p.status === 'evaded' || p.updateCount > 5) ? `
                    <a href="details/${escapeHtml(p.id)}.html" class="btn-full-details" onclick="event.stopPropagation();">
                      Full Details
                    </a>
                  ` : ''}
                </div>
                <div class="promise-details" id="details-${escapeHtml(p.id)}"><div class="loading">Loading details...</div></div>
              </div>
            </li>
          `).join('')}
        </ul>
      </section>
    `;
  });

  container.innerHTML = html;
}

function setupFilters() {
  document.querySelectorAll('.stat-card[data-filter]').forEach((card) => {
    card.addEventListener('click', () => {
      const filter = card.getAttribute('data-filter');
      window.currentFilter = window.currentFilter === filter ? 'all' : filter;
      updateFiltersUI();
      rerenderMain();
    });
  });
}

window.clearCurrentFilter = () => {
  window.currentFilter = 'all';
  updateFiltersUI();
  rerenderMain();
};

function updateFiltersUI() {
  document.querySelectorAll('.stat-card').forEach((c) => c.classList.remove('active'));
  if (window.currentFilter !== 'all') {
    document.querySelector(`.stat-card[data-filter="${window.currentFilter}"]`)?.classList.add('active');
  }

  const staticGuide = document.getElementById('tracker-guide-static');
  const banner = document.getElementById('active-filters-banner');
  if (!staticGuide || !banner) return;

  if (window.currentFilter === 'all') {
    staticGuide.style.display = 'block';
    banner.style.display = 'none';
    banner.innerHTML = '';
  } else {
    staticGuide.style.display = 'none';
    banner.style.display = 'block';

    const visibleCount = filterPromises(window.siteData.promises).length;
    let badgeHtml = '';
    if (window.currentFilter === 'done') {
      badgeHtml = '<span class="badge badge-done">✓ Fulfilled</span>';
    } else if (window.currentFilter === 'inprogress') {
      badgeHtml = '<span class="badge badge-progress">◑ In Progress</span>';
    } else if (window.currentFilter === 'evaded') {
      badgeHtml = '<span class="badge badge-evaded">✗ Evaded</span>';
    } else if (window.currentFilter === 'pending') {
      badgeHtml = '<span class="badge badge-pending">○ Pending</span>';
    }

    banner.innerHTML = `
      <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 12px; width: 100%;">
        <div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap;">
          <span style="font-family: 'Space Mono', monospace; font-size: 11px; text-transform: uppercase; letter-spacing: 0.05em; color: var(--ink-faint); font-weight: 700;">Filtered Status:</span>
          <div class="legend-inline" style="margin: 0; display: inline-flex;">
            ${badgeHtml}
          </div>
          <span style="font-family: 'Space Mono', monospace; font-size: 12px; font-weight: 700; color: var(--ink-mid); margin-left: 8px;">
            — ${formatCount(visibleCount, 'Promise')} Found
          </span>
        </div>
        <button onclick="window.clearCurrentFilter()" style="font-family: 'Space Mono', monospace; font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; color: var(--ink-light); background: var(--surface); border: 1px solid var(--rule); padding: 4px 10px; border-radius: 4px; cursor: pointer; transition: all 0.15s;">
          Clear Filter ✕
        </button>
      </div>
    `;
  }
}

function updateResultSummary() {
  const summary = document.getElementById('result-summary');
  if (summary) {
    summary.style.display = 'none';
  }
}

function toggleCat(header) {
  header.classList.toggle('collapsed');
  header.setAttribute('aria-expanded', String(!header.classList.contains('collapsed')));
  const list = header.nextElementSibling;
  if (list?.classList.contains('promise-list')) list.classList.toggle('collapsed');
}

function handleCatKey(event, header) {
  if (event.key !== 'Enter' && event.key !== ' ') return;
  event.preventDefault();
  toggleCat(header);
}

function scrollToPromise(id) {
  window.currentFilter = 'all';
  updateFiltersUI();
  rerenderMain();

  const el = document.getElementById(`item-${id}`);
  if (!el) return;
  const list = el.closest('.promise-list');
  if (list?.classList.contains('collapsed')) toggleCat(list.previousElementSibling);
  el.scrollIntoView({ behavior: 'smooth', block: 'center' });
  el.style.backgroundColor = 'rgba(232, 98, 10, 0.1)';
  setTimeout(() => { el.style.backgroundColor = ''; }, 2000);
  togglePromiseDetails(id, true);
}



// Initialize global memory cache for details rendering
window.promiseDetailsCache = window.promiseDetailsCache || {};

async function togglePromiseDetails(id, forceOpen = false) {
  const promise = window.siteData.promises.find((p) => p.id === id);
  if (!promise || (promise.updateCount === 0 && promise.counterCount === 0)) return;

  const detailsDiv = document.getElementById(`details-${id}`);
  if (!detailsDiv) return;

  const isOpen = detailsDiv.classList.contains('open');
  if (isOpen && !forceOpen) {
    detailsDiv.classList.remove('open');
    return;
  }

  // 1. Render instantly from cache if data is already loaded to avoid layout jumps
  if (window.promiseDetailsCache[id]) {
    detailsDiv.innerHTML = window.promiseDetailsCache[id];
    detailsDiv.classList.add('open');
    return;
  }

  // 2. Fetch and render on first expand
  detailsDiv.innerHTML = '<div class="loading">Loading details...</div>';
  detailsDiv.classList.add('open');

  try {
    const res = await fetch(`data/updates/${id}.json`);
    if (!res.ok) throw new Error('No updates file');
    const data = await res.json();

    let html = '<div class="update-timeline">';
    const cleanNote = (note) => String(note || '').replace(/\s*(?:↗|\u00e2\u2020\u2014)[^\n]*$/g, '').trim();

    // Helper to escape HTML and format multi-paragraph text
    const formatMultiParagraph = (text) => {
      if (!text) return '';
      return String(text)
        .split(/\n\s*\n/)
        .map(p => `<p>${escapeHtml(p.trim())}</p>`)
        .join('');
    };

    const isOverflow = (promise.status === 'inprogress' && data.updates.length > 5);
    const displayUpdates = isOverflow ? data.updates.slice(0, 3) : data.updates;

    if (Array.isArray(displayUpdates) && displayUpdates.length) {
      displayUpdates.forEach((u, i) => {
        const updateNumber = data.updates.length - i;
        const sources = Array.isArray(u.sources) ? u.sources : [];
        const noteText = sources.length ? cleanNote(u.note) : String(u.note || '');
        const dateLabel = sources.length > 0
          ? sources[0].name.split(/[·|]/).pop().trim()
          : '';
        
        let updateHtml = `
          <div class="update-block">
            <div class="update-header">
              <span class="update-badge">Update ${updateNumber}</span>
              ${dateLabel ? `<span class="update-date">${escapeHtml(dateLabel)}</span>` : ''}
            </div>
            <div class="update-note">${formatMultiParagraph(noteText)}</div>
            ${sources.length ? `<div class="source-list">
              ${sources.map((s) => `<a class="source-link" href="${escapeHtml(s.url)}" target="_blank" rel="noopener">${escapeHtml(s.name)}</a>`).join('')}
            </div>` : ''}
        `;

        // Handle nested counter evidence
        if (Array.isArray(u.counterEvidence) && u.counterEvidence.length) {
          u.counterEvidence.forEach((c) => {
            const cSources = Array.isArray(c.sources) ? c.sources : [];
            const cNoteText = cSources.length ? cleanNote(c.text) : String(c.text || '');
            updateHtml += `
              <div class="counter-block" style="margin-top: 12px;">
                <span class="counter-label">🛑 Counter evidence: ${escapeHtml(c.label || '')}</span>
                <div class="update-note">${formatMultiParagraph(cNoteText)}</div>
                ${cSources.length ? `<div class="source-list" style="margin-top:8px">
                  ${cSources.map((s) => `<a class="source-link" href="${escapeHtml(s.url)}" target="_blank" rel="noopener">${escapeHtml(s.name)}</a>`).join('')}
                </div>` : ''}
              </div>
            `;
          });
        }

        updateHtml += `</div>`;
        html += updateHtml;
      });
    }

    if (isOverflow) {
      const remainingCount = data.updates.length - 3;
      html += `
        <div class="overflow-banner">
          <span class="overflow-text">◑ Previewing the 3 latest updates. There are ${remainingCount} older updates for this active promise.</span>
          <a href="details/${escapeHtml(id)}.html" class="btn-view-overflow">View Full History & Evidence →</a>
        </div>
      `;
    }

    if (Array.isArray(data.counterEvidence) && data.counterEvidence.length) {
      data.counterEvidence.forEach((c) => {
        const sources = Array.isArray(c.sources) ? c.sources : [];
        const noteText = sources.length ? cleanNote(c.text) : String(c.text || '');
        html += `
          <div class="counter-block">
            <span class="counter-label">🛑 Counter evidence: ${escapeHtml(c.label || '')}</span>
            <div class="update-note">${formatMultiParagraph(noteText)}</div>
            ${sources.length ? `<div class="source-list" style="margin-top:8px">
              ${sources.map((s) => `<a class="source-link" href="${escapeHtml(s.url)}" target="_blank" rel="noopener">${escapeHtml(s.name)}</a>`).join('')}
            </div>` : ''}
          </div>
        `;
      });
    }

    if ((!data.updates || !data.updates.length) && (!data.counterEvidence || !data.counterEvidence.length)) {
      html += '<div class="empty-details">No detailed history available for this item yet.</div>';
    }

    html += '</div>';
    
    // Save generated markup to cache
    window.promiseDetailsCache[id] = html;
    
    // Render markup
    detailsDiv.innerHTML = html;
  } catch {
    const errorHtml = '<div style="color:var(--ink-light);font-size:13px;font-style:italic">No detailed history available for this item.</div>';
    window.promiseDetailsCache[id] = errorHtml;
    detailsDiv.innerHTML = errorHtml;
  }
}