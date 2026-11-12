/**
 * NOit Mermaid Interactive - Makes ALL Mermaid diagrams on the MkDocs site interactive
 * (pan/zoom/fullscreen). Loaded via extra_javascript in mkdocs.yml.
 * Built by NOit (https://noit2.com)
 */
(function () {
  'use strict';
  function waitForMermaid() {
    return new Promise((resolve) => {
      if (window.mermaid && typeof mermaid.run === 'function') {
        mermaid.run().then(resolve).catch(resolve);
      } else {
        const check = setInterval(() => {
          if (window.mermaid && typeof mermaid.run === 'function') {
            clearInterval(check);
            mermaid.run().then(resolve).catch(resolve);
          }
        }, 100);
        setTimeout(() => { clearInterval(check); resolve(); }, 5000);
      }
    });
  }
  function loadPanZoom() {
    return new Promise((resolve, reject) => {
      if (window.svgPanZoom) {
        resolve(window.svgPanZoom);
        return;
      }
      const script = document.createElement('script');
      script.src = 'https://cdn.jsdelivr.net/npm/svg-pan-zoom@3.6.1/dist/svg-pan-zoom.min.js';
      script.onload = () => resolve(window.svgPanZoom);
      script.onerror = reject;
      document.head.appendChild(script);
    });
  }
  async function initPanZoom(svgEl, container) {
    const svgPanZoom = await loadPanZoom();
    svgEl.removeAttribute('style');
    svgEl.setAttribute('width', '100%');
    svgEl.setAttribute('height', '100%');
    let controls = container.querySelector('.mermaid-zoom-controls');
    if (!controls) {
      controls = document.createElement('div');
      controls.className = 'mermaid-zoom-controls';
      controls.innerHTML = `
        <button class="zoom-in" title="Zoom in">+</button>
        <button class="zoom-out" title="Zoom out">−</button>
        <button class="zoom-reset" title="Reset view">↻</button>
        <button class="zoom-fit" title="Fit to screen">⛶</button>
        <button class="zoom-fullscreen" title="Fullscreen">⛶</button>
      `;
      container.style.position = 'relative';
      container.appendChild(controls);
    }
    let badge = container.querySelector('.mermaid-zoom-badge');
    if (!badge) {
      badge = document.createElement('div');
      badge.className = 'mermaid-zoom-badge';
      badge.textContent = '100%';
      container.appendChild(badge);
    }
    let help = container.querySelector('.mermaid-zoom-help');
    if (!help) {
      help = document.createElement('div');
      help.className = 'mermaid-zoom-help';
      help.textContent = 'Scroll to zoom • Drag to pan • Double-click to reset';
      container.appendChild(help);
    }
    const panZoom = svgPanZoom(svgEl, {
      zoomEnabled: true,
      panEnabled: true,
      controlIconsEnabled: false,
      dblClickZoomEnabled: false,
      mouseWheelZoomEnabled: true,
      preventMouseEventsDefault: true,
      minZoom: 0.3,
      maxZoom: 5,
      fit: true,
      center: true,
      beforeZoom: () => updateBadge(badge, panZoom),
      onZoom: () => updateBadge(badge, panZoom)
    });
    svgEl.addEventListener('dblclick', (e) => {
      e.preventDefault();
      panZoom.reset();
      setTimeout(() => { panZoom.fit(); panZoom.center(); updateBadge(badge, panZoom); }, 50);
    });
    controls.querySelector('.zoom-in').addEventListener('click', () => { panZoom.zoomIn(); updateBadge(badge, panZoom); });
    controls.querySelector('.zoom-out').addEventListener('click', () => { panZoom.zoomOut(); updateBadge(badge, panZoom); });
    controls.querySelector('.zoom-reset').addEventListener('click', () => { panZoom.reset(); setTimeout(() => { panZoom.fit(); panZoom.center(); updateBadge(badge, panZoom); }, 50); });
    controls.querySelector('.zoom-fit').addEventListener('click', () => { panZoom.fit(); panZoom.center(); updateBadge(badge, panZoom); });
    controls.querySelector('.zoom-fullscreen').addEventListener('click', () => toggleFullscreen(container, panZoom, badge));
    setTimeout(() => { help.style.opacity = '0'; }, 5000);
    container._panZoom = panZoom;
  }
  function updateBadge(badge, panZoom) {
    if (badge && panZoom) {
      badge.textContent = Math.round(panZoom.getZoom() * 100) + '%';
    }
  }
  function toggleFullscreen(container, panZoom, badge) {
    const refit = () => setTimeout(() => {
      if (panZoom) {
        panZoom.resize();
        panZoom.fit();
        panZoom.center();
        updateBadge(badge, panZoom);
      }
    }, 200);
    if (!document.fullscreenElement) {
      container.requestFullscreen().then(refit).catch(err => console.log('Fullscreen denied', err));
    } else {
      document.exitFullscreen().then(refit);
    }
  }
  async function initAll() {
    await waitForMermaid();
    const containers = document.querySelectorAll('.mermaid');
    for (const container of containers) {
      const svg = container.querySelector('svg');
      if (svg && !container._panZoom) {
        try {
          await initPanZoom(svg, container);
        } catch (err) {
          console.error('Mermaid interactive init failed:', err);
        }
      }
    }
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initAll);
  } else {
    initAll();
  }
  document.addEventListener('pjax:end', initAll);
  document.addEventListener('pjax:complete', initAll);
  window.initMermaidInteractive = initAll;
})();
