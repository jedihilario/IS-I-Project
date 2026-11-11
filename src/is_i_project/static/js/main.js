/* =========================================================
   PLATAFORMA QA — Interactive JS
   ========================================================= */

'use strict';

// ─── Toast Notifications ────────────────────────────────────
const Toast = {
  container: null,

  init() {
    this.container = document.getElementById('toast-container');
    if (!this.container) {
      this.container = document.createElement('div');
      this.container.className = 'toast-container';
      this.container.id = 'toast-container';
      document.body.appendChild(this.container);
    }
  },

  show(message, type = 'info', duration = 3500) {
    const icons = { success: '✅', error: '❌', info: '💡' };
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `<span>${icons[type] || icons.info}</span><span>${message}</span>`;
    this.container.appendChild(toast);
    setTimeout(() => {
      toast.style.animation = 'slide-in 0.3s cubic-bezier(0.4,0,0.2,1) reverse';
      setTimeout(() => toast.remove(), 300);
    }, duration);
  }
};

// ─── Sidebar Toggle (mobile) ─────────────────────────────────
function initSidebar() {
  const toggle = document.getElementById('sidebar-toggle');
  const sidebar = document.getElementById('sidebar');
  const overlay = document.getElementById('sidebar-overlay');

  if (!toggle || !sidebar) return;

  function openSidebar() {
    sidebar.classList.add('open');
    overlay && overlay.classList.add('active');
    document.body.style.overflow = 'hidden';
  }

  function closeSidebar() {
    sidebar.classList.remove('open');
    overlay && overlay.classList.remove('active');
    document.body.style.overflow = '';
  }

  toggle.addEventListener('click', () => {
    sidebar.classList.contains('open') ? closeSidebar() : openSidebar();
  });

  overlay && overlay.addEventListener('click', closeSidebar);
}

// ─── Vote System ─────────────────────────────────────────────
function initVoting() {
  document.querySelectorAll('[data-vote-btn]').forEach(btn => {
    btn.addEventListener('click', async function () {
      const container = this.closest('[data-votable]');
      if (!container) return;

      const id   = container.dataset.votable;
      const type = container.dataset.type || 'question'; // 'question' | 'answer'
      const dir  = this.dataset.voteBtn; // 'up' | 'down'

      const scoreEl = container.querySelector('[data-vote-score]');
      const upBtn   = container.querySelector('[data-vote-btn="up"]');
      const downBtn = container.querySelector('[data-vote-btn="down"]');

      // Optimistic UI update
      const wasUp   = upBtn.classList.contains('upvoted');
      const wasDown = downBtn.classList.contains('downvoted');
      let score = parseInt(scoreEl.textContent, 10);

      if (dir === 'up') {
        if (wasUp) {
          upBtn.classList.remove('upvoted');
          score--;
        } else {
          upBtn.classList.add('upvoted');
          downBtn.classList.remove('downvoted');
          score = wasDown ? score + 2 : score + 1;
        }
      } else {
        if (wasDown) {
          downBtn.classList.remove('downvoted');
          score++;
        } else {
          downBtn.classList.add('downvoted');
          upBtn.classList.remove('upvoted');
          score = wasUp ? score - 2 : score - 1;
        }
      }

      scoreEl.textContent = score;
      scoreEl.style.transform = 'scale(1.3)';
      setTimeout(() => scoreEl.style.transform = '', 200);

      // API call (best-effort)
      try {
        const res = await fetch(`/api/${type}s/${id}/vote`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ direction: dir })
        });
        if (!res.ok) throw new Error('Vote failed');
        Toast.show('Voto registrado', 'success', 2000);
      } catch {
        // Silently ignore if API not yet wired
      }
    });
  });
}

// ─── Accept Answer ───────────────────────────────────────────
function initAcceptAnswer() {
  document.querySelectorAll('[data-accept-answer]').forEach(btn => {
    btn.addEventListener('click', async function () {
      const answerId = this.dataset.acceptAnswer;
      try {
        await fetch(`/api/answers/${answerId}/accept`, { method: 'POST' });
        // Mark as accepted visually
        document.querySelectorAll('.answer-card').forEach(c => c.classList.remove('accepted-answer'));
        const card = this.closest('.answer-card');
        card.classList.add('accepted-answer');
        document.querySelectorAll('[data-accept-answer]').forEach(b => {
          b.textContent = '✓ Aceptar';
          b.classList.remove('accept-btn');
        });
        this.textContent = '✅ Aceptada';
        this.classList.add('accept-btn');
        Toast.show('Respuesta marcada como aceptada', 'success');
      } catch {
        Toast.show('No se pudo aceptar la respuesta', 'error');
      }
    });
  });
}

// ─── Tabs ────────────────────────────────────────────────────
function initTabs() {
  document.querySelectorAll('[data-tabs]').forEach(container => {
    const buttons = container.querySelectorAll('[data-tab-btn]');
    const contents = container.querySelectorAll('[data-tab-content]');

    buttons.forEach(btn => {
      btn.addEventListener('click', () => {
        const target = btn.dataset.tabBtn;

        buttons.forEach(b => b.classList.remove('active'));
        contents.forEach(c => c.classList.remove('active'));

        btn.classList.add('active');
        const targetContent = container.querySelector(`[data-tab-content="${target}"]`);
        if (targetContent) targetContent.classList.add('active');
      });
    });
  });
}

// ─── Filter Buttons ───────────────────────────────────────────
function initFilters() {
  document.querySelectorAll('[data-filter-group]').forEach(group => {
    const buttons = group.querySelectorAll('[data-filter]');
    buttons.forEach(btn => {
      btn.addEventListener('click', () => {
        buttons.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');

        const filter = btn.dataset.filter;
        const list = document.getElementById('question-list');
        if (!list) return;

        list.querySelectorAll('[data-question-item]').forEach(item => {
          if (filter === 'all') {
            item.style.display = '';
          } else {
            const tags = item.dataset.tags || '';
            const hasAi = item.dataset.hasAi === 'true';
            const answered = item.dataset.answered === 'true';

            if (filter === 'unanswered' && !answered) item.style.display = '';
            else if (filter === 'ai' && hasAi) item.style.display = '';
            else if (filter !== 'unanswered' && filter !== 'ai') item.style.display = '';
            else item.style.display = 'none';
          }
        });
      });
    });
  });
}

// ─── Live Search ──────────────────────────────────────────────
function initSearch() {
  const searchInput = document.getElementById('search-input');
  const navSearch   = document.getElementById('navbar-search');

  function debounce(fn, ms) {
    let t;
    return (...args) => { clearTimeout(t); t = setTimeout(() => fn(...args), ms); };
  }

  function filterQuestions(query) {
    const list = document.getElementById('question-list');
    if (!list) return;
    const q = query.toLowerCase().trim();
    list.querySelectorAll('[data-question-item]').forEach(item => {
      const title = (item.dataset.title || '').toLowerCase();
      const tags  = (item.dataset.tags  || '').toLowerCase();
      item.style.display = (q === '' || title.includes(q) || tags.includes(q)) ? '' : 'none';
    });
  }

  if (searchInput) {
    searchInput.addEventListener('input', debounce(e => filterQuestions(e.target.value), 250));
  }

  if (navSearch) {
    navSearch.addEventListener('input', debounce(e => {
      const q = e.target.value.trim();
      if (q.length >= 3) {
        // Could redirect: window.location.href = `/buscar?q=${encodeURIComponent(q)}`;
        filterQuestions(q);
      } else if (q.length === 0) {
        filterQuestions('');
      }
    }, 300));

    navSearch.addEventListener('keydown', e => {
      if (e.key === 'Enter' && navSearch.value.trim()) {
        window.location.href = `/?q=${encodeURIComponent(navSearch.value.trim())}`;
      }
    });
  }
}

// ─── Markdown Preview ─────────────────────────────────────────
function initMarkdownPreview() {
  const textarea = document.getElementById('question-body');
  const preview  = document.getElementById('body-preview');
  const previewTab = document.getElementById('preview-tab');
  const writeTab   = document.getElementById('write-tab');
  const writeArea  = document.getElementById('write-area');
  const previewArea= document.getElementById('preview-area');

  if (!textarea) return;

  function simpleMarkdown(text) {
    return text
      .replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>')
      .replace(/`([^`]+)`/g, '<code>$1</code>')
      .replace(/^### (.*$)/gim, '<h3>$1</h3>')
      .replace(/^## (.*$)/gim, '<h2>$1</h2>')
      .replace(/^# (.*$)/gim, '<h1>$1</h1>')
      .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
      .replace(/\*([^*]+)\*/g, '<em>$1</em>')
      .replace(/\n\n/g, '</p><p>')
      .replace(/\n/g, '<br>')
      .replace(/^/, '<p>')
      .replace(/$/, '</p>');
  }

  if (previewTab && writeTab) {
    previewTab.addEventListener('click', () => {
      previewTab.classList.add('active');
      writeTab.classList.remove('active');
      writeArea.classList.add('hidden');
      previewArea.classList.remove('hidden');
      if (preview) preview.innerHTML = simpleMarkdown(textarea.value || '_Nada que previsualizar_');
    });

    writeTab.addEventListener('click', () => {
      writeTab.classList.add('active');
      previewTab.classList.remove('active');
      previewArea.classList.add('hidden');
      writeArea.classList.remove('hidden');
    });
  }
}

// ─── Character Counter ────────────────────────────────────────
function initCharCounter() {
  document.querySelectorAll('[data-maxlength]').forEach(el => {
    const max = parseInt(el.dataset.maxlength, 10);
    const counterId = el.dataset.counter;
    const counter = counterId ? document.getElementById(counterId) : null;
    if (!counter) return;

    el.addEventListener('input', () => {
      const remaining = max - el.value.length;
      counter.textContent = `${el.value.length} / ${max}`;
      counter.style.color = remaining < 20 ? 'var(--red-light)' : 'var(--text-muted)';
    });
  });
}

// ─── Tag Input ────────────────────────────────────────────────
function initTagInput() {
  const tagInput   = document.getElementById('tag-input');
  const tagList    = document.getElementById('tag-list');
  const tagHidden  = document.getElementById('tags-hidden');
  if (!tagInput || !tagList) return;

  let tags = [];

  function renderTags() {
    tagList.innerHTML = '';
    tags.forEach((tag, i) => {
      const span = document.createElement('span');
      span.className = 'tag';
      span.style.cursor = 'default';
      span.innerHTML = `${tag} <button type="button" onclick="removeTag(${i})" style="background:none;border:none;color:inherit;cursor:pointer;margin-left:4px;font-size:12px;">×</button>`;
      tagList.appendChild(span);
    });
    if (tagHidden) tagHidden.value = tags.join(',');
  }

  window.removeTag = function(i) {
    tags.splice(i, 1);
    renderTags();
  };

  tagInput.addEventListener('keydown', e => {
    if ((e.key === 'Enter' || e.key === ',') && tagInput.value.trim()) {
      e.preventDefault();
      const val = tagInput.value.trim().toLowerCase().replace(/[^a-z0-9-]/g, '');
      if (val && !tags.includes(val) && tags.length < 5) {
        tags.push(val);
        renderTags();
      }
      tagInput.value = '';
    }
  });
}

// ─── Form Validation ──────────────────────────────────────────
function initFormValidation() {
  document.querySelectorAll('form[data-validate]').forEach(form => {
    form.addEventListener('submit', e => {
      let valid = true;
      form.querySelectorAll('[required]').forEach(field => {
        const errEl = document.getElementById(`${field.id}-error`);
        if (!field.value.trim()) {
          valid = false;
          field.style.borderColor = 'var(--red)';
          if (errEl) errEl.textContent = 'Este campo es requerido';
        } else {
          field.style.borderColor = '';
          if (errEl) errEl.textContent = '';
        }
      });
      if (!valid) {
        e.preventDefault();
        Toast.show('Por favor completá todos los campos requeridos', 'error');
      }
    });
  });
}

// ─── Admin Role Change ────────────────────────────────────────
function initAdminRoles() {
  document.querySelectorAll('[data-role-select]').forEach(sel => {
    sel.addEventListener('change', async function () {
      const userId = this.dataset.roleSelect;
      const role   = this.value;
      try {
        await fetch(`/api/admin/users/${userId}/role`, {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ role })
        });
        Toast.show(`Rol actualizado a "${role}"`, 'success');
      } catch {
        Toast.show('No se pudo actualizar el rol', 'error');
      }
    });
  });
}

// ─── Smooth number count animation ────────────────────────────
function initCountUp() {
  const observer = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const el = entry.target;
        const target = parseInt(el.dataset.countUp, 10);
        const duration = 1200;
        const start = performance.now();
        const easeOut = t => 1 - Math.pow(1 - t, 3);

        function step(ts) {
          const elapsed = ts - start;
          const progress = Math.min(elapsed / duration, 1);
          el.textContent = Math.round(easeOut(progress) * target).toLocaleString();
          if (progress < 1) requestAnimationFrame(step);
        }

        requestAnimationFrame(step);
        observer.unobserve(el);
      }
    });
  }, { threshold: 0.4 });

  document.querySelectorAll('[data-count-up]').forEach(el => observer.observe(el));
}

// ─── Rep Bar Animation ─────────────────────────────────────────
function initRepBars() {
  const observer = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const bar = entry.target;
        const pct = bar.dataset.pct || '0';
        bar.style.width = pct + '%';
        observer.unobserve(bar);
      }
    });
  }, { threshold: 0.3 });

  document.querySelectorAll('.rep-bar-fill[data-pct]').forEach(el => {
    el.style.width = '0%';
    observer.observe(el);
  });
}

// ─── Keyboard Shortcuts ────────────────────────────────────────
function initKeyboardShortcuts() {
  document.addEventListener('keydown', e => {
    // Ctrl/Cmd + K → focus search
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
      e.preventDefault();
      const search = document.getElementById('navbar-search') || document.getElementById('search-input');
      search && search.focus();
    }
    // Escape → close modals / sidebar
    if (e.key === 'Escape') {
      const sidebar = document.getElementById('sidebar');
      if (sidebar && sidebar.classList.contains('open')) {
        sidebar.classList.remove('open');
        document.getElementById('sidebar-overlay')?.classList.remove('active');
        document.body.style.overflow = '';
      }
    }
  });
}

// ─── Active sidebar link ───────────────────────────────────────
function initActiveNav() {
  const path = window.location.pathname;
  document.querySelectorAll('.sidebar-link').forEach(link => {
    if (link.getAttribute('href') === path) {
      link.classList.add('active');
    }
  });
}

// ─── Bootstrap ────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  Toast.init();
  initSidebar();
  initVoting();
  initAcceptAnswer();
  initTabs();
  initFilters();
  initSearch();
  initMarkdownPreview();
  initCharCounter();
  initTagInput();
  initFormValidation();
  initAdminRoles();
  initCountUp();
  initRepBars();
  initKeyboardShortcuts();
  initActiveNav();
});
