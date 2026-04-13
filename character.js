/* character.js — shared logic for all individual character pages
 * Each page just needs to include this script; the character slug
 * is derived automatically from the HTML filename in the URL.
 */
(function () {
  'use strict';

  // ── View-only mode: frontend fallback ────────────────────────────
  // The server already injects window._IS_LOCAL and adds the view-only
  // class to <html> before the page paints. This is a redundancy check
  // in case the page is served by a different server or the injection fails.
  (function () {
    var isLocal = (typeof window._IS_LOCAL !== 'undefined')
      ? window._IS_LOCAL
      : (location.hostname === 'localhost' || location.hostname === '127.0.0.1');
    if (!isLocal) document.documentElement.classList.add('view-only');
  }());

  // Helper — true when edit controls are permitted
  function _editAllowed() {
    return !document.documentElement.classList.contains('view-only');
  }

  // ── Derive character slug from the page filename ──────────────────
  // e.g.  /characters/batman.html  →  "batman"
  const CHARACTER = location.pathname.split('/').pop().replace('.html', '');

  let pageData  = null;   // authoritative character data object
  let isEditing = false;  // current edit-mode state

  // ─────────────────────────────────────────────────────────────────
  // INIT
  // ─────────────────────────────────────────────────────────────────
  async function init() {
    try {
      const res = await fetch('../data/' + CHARACTER + '.json');
      if (!res.ok) throw new Error('not found');
      pageData = await res.json();
    } catch (_) {
      pageData = blankData();
    }

    applyTheme(pageData.theme || {});
    render();
  }

  function blankData() {
    const name = CHARACTER.charAt(0).toUpperCase() + CHARACTER.slice(1);
    return {
      character:  CHARACTER,
      title:      name,
      eyebrow:    '',
      tagline:    '',
      stats:      [],
      bio:        [],
      images:     [],
      theme: {
        accent:      '#ffffff',
        accentText:  '#000000',
        accentGlow:  'rgba(255,255,255,0.08)',
        bg:          '#111111',
        surface:     'rgba(255,255,255,0.05)',
        border:      'rgba(255,255,255,0.09)',
        text:        '#f5f5f7',
        textMuted:   'rgba(245,245,247,0.55)',
      },
    };
  }

  // ─────────────────────────────────────────────────────────────────
  // THEME  — set CSS custom properties from the JSON theme block
  // ─────────────────────────────────────────────────────────────────
  function applyTheme(theme) {
    const s = document.documentElement.style;
    const map = {
      '--accent':      theme.accent,
      '--accent-text': theme.accentText,
      '--accent-glow': theme.accentGlow,
      '--bg':          theme.bg,
      '--surface':     theme.surface,
      '--border':      theme.border,
      '--text':        theme.text,
      '--text-muted':  theme.textMuted,
    };
    Object.entries(map).forEach(([k, v]) => { if (v) s.setProperty(k, v); });
    document.title = pageData.title || CHARACTER;
  }

  // ─────────────────────────────────────────────────────────────────
  // RENDER
  // ─────────────────────────────────────────────────────────────────
  function render() {
    setText('char-eyebrow', pageData.eyebrow);
    setText('char-title',   pageData.title);
    setText('char-tagline', pageData.tagline);
    renderGallery();
    renderStats();
    renderBio();
  }

  function setText(id, value) {
    const el = document.getElementById(id);
    if (el) el.textContent = value || '';
  }

  function renderGallery() {
    const grid = document.getElementById('gallery-grid');
    if (!grid) return;
    grid.innerHTML = '';

    (pageData.images || []).forEach(function (img, i) {
      const item = document.createElement('div');
      item.className = 'gallery-item';

      const image = document.createElement('img');
      image.src     = img.src;
      image.alt     = img.alt || '';
      image.loading = i === 0 ? 'eager' : 'lazy';
      image.decoding = 'async';

      const del = document.createElement('button');
      del.className = 'delete-btn';
      del.setAttribute('aria-label', 'Remove photo');
      del.textContent = '×';
      del.onclick = function () { deleteImage(i); };

      item.appendChild(image);
      item.appendChild(del);
      grid.appendChild(item);
    });
  }

  function renderStats() {
    const grid = document.getElementById('stats-grid');
    if (!grid) return;
    grid.innerHTML = '';

    (pageData.stats || []).forEach(function (stat) {
      const card  = document.createElement('div');
      card.className = 'stat-card';

      const label = document.createElement('span');
      label.className = 'stat-label';
      label.textContent = stat.label;

      const value = document.createElement('span');
      value.className = 'stat-value';
      value.textContent = stat.value;

      card.appendChild(label);
      card.appendChild(value);
      grid.appendChild(card);
    });
  }

  function renderBio() {
    const wrap = document.getElementById('bio-wrap');
    if (!wrap) return;
    wrap.innerHTML = '';

    (pageData.bio || []).forEach(function (item) {
      const el = document.createElement(item.type === 'heading' ? 'h2' : 'p');
      el.className   = item.type === 'heading' ? 'bio-heading' : 'bio-para';
      el.textContent = item.text || '';
      wrap.appendChild(el);
    });
  }

  // ─────────────────────────────────────────────────────────────────
  // EDIT MODE
  // ─────────────────────────────────────────────────────────────────
  function toggleEdit() {
    if (!_editAllowed()) return;
    isEditing = !isEditing;
    document.body.classList.toggle('edit-mode', isEditing);

    // Fields that become contenteditable in edit mode
    const selectors = [
      '#char-eyebrow',
      '#char-title',
      '#char-tagline',
      '.stat-label',
      '.stat-value',
      '.bio-heading',
      '.bio-para',
    ];

    selectors.forEach(function (sel) {
      document.querySelectorAll(sel).forEach(function (el) {
        el.contentEditable = isEditing ? 'true' : 'false';
      });
    });

    // Toggle FAB icon
    const icon = document.querySelector('.fab-edit .fab-icon');
    if (icon) icon.textContent = isEditing ? '✕' : '✏';
  }

  // ─────────────────────────────────────────────────────────────────
  // SAVE  — collect DOM state → POST /__save__
  // ─────────────────────────────────────────────────────────────────
  async function saveData() {
    if (!_editAllowed()) return;
    // Collect editable text fields
    pageData.eyebrow = (document.getElementById('char-eyebrow') || {}).textContent.trim();
    pageData.title   = (document.getElementById('char-title')   || {}).textContent.trim();
    pageData.tagline = (document.getElementById('char-tagline') || {}).textContent.trim();

    pageData.stats = Array.from(document.querySelectorAll('.stat-card')).map(function (card) {
      return {
        label: (card.querySelector('.stat-label') || {}).textContent.trim(),
        value: (card.querySelector('.stat-value') || {}).textContent.trim(),
      };
    });

    pageData.bio = Array.from(document.querySelectorAll('#bio-wrap > *')).map(function (el) {
      return {
        type: el.tagName === 'H2' ? 'heading' : 'paragraph',
        text: el.textContent.trim(),
      };
    });

    // pageData.images is kept in sync by uploadFile / deleteImage

    try {
      const res = await fetch('/__save__', {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify(pageData),
      });

      if (res.ok) {
        showToast('Saved successfully', 'success');
        document.title = pageData.title || CHARACTER;
        applyTheme(pageData.theme || {});
        toggleEdit(); // exit edit mode after a successful save
      } else {
        showToast('Save failed — try again', 'error');
      }
    } catch (_) {
      showToast('Network error', 'error');
    }
  }

  // ─────────────────────────────────────────────────────────────────
  // PHOTO UPLOAD  — read files as data-URLs → POST /__upload__
  // ─────────────────────────────────────────────────────────────────
  function handlePhotoInput(e) {
    Array.from(e.target.files).forEach(function (file) {
      uploadFile(file);
    });
    e.target.value = ''; // allow re-selecting the same file
  }

  function uploadFile(file) {
    if (!_editAllowed()) return;
    const reader = new FileReader();
    reader.onload = async function (e) {
      try {
        const res = await fetch('/__upload__', {
          method:  'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            character: CHARACTER,
            filename:  file.name,
            data:      e.target.result, // base64 data-URL
          }),
        });

        if (res.ok) {
          const result = await res.json();
          pageData.images.push({
            src: result.url,
            alt: file.name.replace(/\.[^.]+$/, ''),
          });
          renderGallery();
          // Re-apply edit mode styles to new items
          if (isEditing) {
            document.querySelectorAll('.delete-btn').forEach(function (btn) {
              btn.style.display = 'flex';
            });
          }
          showToast('Photo added', 'success');
        } else {
          showToast('Upload failed', 'error');
        }
      } catch (_) {
        showToast('Network error', 'error');
      }
    };
    reader.readAsDataURL(file);
  }

  function deleteImage(idx) {
    if (!isEditing) return;
    pageData.images.splice(idx, 1);
    renderGallery();
  }

  // ─────────────────────────────────────────────────────────────────
  // TOAST
  // ─────────────────────────────────────────────────────────────────
  function showToast(msg, type) {
    const t = document.createElement('div');
    t.className = 'toast toast-' + (type || 'success');
    t.textContent = msg;
    document.body.appendChild(t);
    // Double rAF so the transition fires after the element is in the DOM
    requestAnimationFrame(function () {
      requestAnimationFrame(function () { t.classList.add('show'); });
    });
    setTimeout(function () {
      t.classList.remove('show');
      setTimeout(function () { t.remove(); }, 300);
    }, 2500);
  }

  // ─────────────────────────────────────────────────────────────────
  // EXPOSE PUBLIC API  (called by inline onclick attributes in HTML)
  // ─────────────────────────────────────────────────────────────────
  window.toggleEdit = toggleEdit;
  window.saveData   = saveData;

  // ─────────────────────────────────────────────────────────────────
  // BOOT
  // ─────────────────────────────────────────────────────────────────
  document.addEventListener('DOMContentLoaded', function () {
    var photoInput = document.getElementById('photo-input');
    if (photoInput) photoInput.addEventListener('change', handlePhotoInput);
    init();
  });

}());
