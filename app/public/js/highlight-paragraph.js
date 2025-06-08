// ────────────────────────────────────────────────────────────
//  highlight‑paragraph.js – single‑selection + solid overlay
//  NOW: fills **all** pages spanned by the paragraph, not just
//  the first & last.
// ────────────────────────────────────────────────────────────
(() => {
  /*------------------------------------------------------------
   * Geometry helpers
   *-----------------------------------------------------------*/
  function ptToPx(pt, pwIn, phIn, pwPx, phPx, pageX, pageY) {
    return {
      x: pageX + (pt.x / pwIn) * pwPx,
      y: pageY + (pt.y / phIn) * phPx
    };
  }

  /*------------------------------------------------------------
   * Draw highlight for ONE rendered PDF page (already in DOM)
   *-----------------------------------------------------------*/
  async function drawOnPage(chap, pageNo, pagesSpan, bboxPts, bboxPages) {
    const pane    = document.querySelector(`#chapter-pane-${chap.id}`);
    const wrapper = pane?.querySelector('.pdf-preview-wrapper');
    const canvas  = wrapper?.querySelector('canvas');
    if (!wrapper || !canvas) return;

    if (getComputedStyle(wrapper).position === 'static') {
      wrapper.style.position = 'relative';
    }

    /* purge stale rectangles for THIS page */
    wrapper.querySelectorAll(`.paragraph-highlight[data-page="${pageNo}"]`)?.forEach(el => el.remove());

    const canRect  = canvas.getBoundingClientRect();
    const wrapRect = wrapper.getBoundingClientRect();
    const pageX    = canRect.left - wrapRect.left;
    const pageY    = canRect.top  - wrapRect.top;
    const pwPx     = canRect.width;
    const phPx     = canRect.height;

    /* pdf.js metrics → inches */
    const pdfPage  = await chap.pdf.getPage(pageNo);
    const [, , xMaxPts, yMaxPts] = pdfPage.view;
    const pwIn = xMaxPts / 72;
    const phIn = yMaxPts / 72;

    /* choose bounds depending on position in span */
    const firstP = pagesSpan[0];
    const lastP  = pagesSpan[pagesSpan.length - 1];
    const isFirst = pageNo === firstP;
    const isLast  = pageNo === lastP;
    const isSingle = firstP === lastP;

    /* convert bbox points belonging to this page */
    const ptsThisPage = bboxPts
      .filter((_, i) => (bboxPages[i] ?? pageNo) === pageNo)
      .map(pt => ptToPx(pt, pwIn, phIn, pwPx, phPx, pageX, pageY));

    let topPx, bottomPx;

    if (isSingle) {
      if (!ptsThisPage.length) return; // nothing to draw
      topPx    = Math.min(...ptsThisPage.map(p => p.y));
      bottomPx = Math.max(...ptsThisPage.map(p => p.y));
      /* tiny bbox? pad ≥0.8‑inch */
      const minHpx = (0.8 / phIn) * phPx;
      if (bottomPx - topPx < minHpx) bottomPx = topPx + minHpx;
    } else {
      if (isFirst) {
        topPx    = ptsThisPage.length ? Math.min(...ptsThisPage.map(p => p.y)) : pageY;
        bottomPx = pageY + phPx;
      } else if (isLast) {
        topPx    = pageY;
        bottomPx = ptsThisPage.length ? Math.max(...ptsThisPage.map(p => p.y)) : pageY + phPx;
      } else { // middle page → full page
        topPx    = pageY;
        bottomPx = pageY + phPx;
      }
    }

    /* create overlay */
    const hl = document.createElement('div');
    hl.dataset.page = pageNo;
    hl.className    = 'paragraph-highlight';
    Object.assign(hl.style, {
      position:      'absolute',
      left:          `${pageX}px`,
      top:           `${topPx}px`,
      width:         `${pwPx}px`,
      height:        `${bottomPx - topPx}px`,
      background:    'rgba(255, 165, 0, 0.25)', // translucent orange fill
      // border:        '2px solid rgba(255, 140, 0, 0.9)',
      borderRadius:  '4px',
      pointerEvents: 'none',
      zIndex:        100
    });

    wrapper.appendChild(hl);
  }

  /*------------------------------------------------------------
   * Monkey‑patch renderChapterPage so highlight auto‑redraws
   *-----------------------------------------------------------*/
  const origRender = GlobalUploadStore.renderChapterPage;
  GlobalUploadStore.renderChapterPage = async function (chap, pane) {
    await origRender(chap, pane);
    const h = chap._paraHighlight;
    if (h && h.pagesSpan.includes(chap.current)) {
      drawOnPage(chap, chap.current, h.pagesSpan, h.bboxPoints, h.bboxPages);
    }
  };

  /*------------------------------------------------------------
   * Public API – called from update.js, etc.
   * Signature kept backward‑compatible:
   *   highlightParagraph(chKey, startPage, bbox, pageList)
   *-----------------------------------------------------------*/
  window.highlightParagraph = async function (
    chapterKey,
    startPage,
    bboxPoints = null,
    pageList   = []
  ) {
    const chap = GlobalUploadStore.chapters.find(c => c.chapterKey === chapterKey);
    if (!chap) return window.showToast(`Chapter '${chapterKey}' not loaded`, 'danger');

    /* wipe previous highlight (DOM + memory) */
    document.querySelectorAll(`#chapter-pane-${chap.id} .paragraph-highlight`).forEach(el => el.remove());
    chap._paraHighlight = null;

    /* build full, consecutive pages span */
    const allPages = [startPage, ...(Array.isArray(pageList) ? pageList : [])];
    const minP = Math.min(...allPages);
    const maxP = Math.max(...allPages);
    const pagesSpan = Array.from({ length: maxP - minP + 1 }, (_, i) => minP + i);

    chap._paraHighlight = {
      pagesSpan,
      bboxPoints: bboxPoints || [],
      bboxPages:  Array.isArray(pageList) ? pageList : []
    };

    /* jump to the paragraph’s first page */
    await highlightPageBorder(chapterKey, pagesSpan[0]);
    drawOnPage(chap, pagesSpan[0], pagesSpan, bboxPoints || [], chap._paraHighlight.bboxPages);
  };
})();
