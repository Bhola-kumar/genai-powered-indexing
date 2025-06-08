// === script.js ===

/* =========================================================
   INDEX DOCUMENT SECTION
=========================================================*/
const indexInput       = document.getElementById('indexFileInput');
const indexPreview     = document.getElementById('indexPreview');
window.GlobalUploadStore = {
  chapters: [],
  indexPdf: null,
  indexCurrentPage: 1,
  indexTotalPages: 0,
  renderChapterPage: null,
  renderIndexPage: null
};
// let   indexPdf         = null;
// let   indexCurrentPage = 1;
// let   indexTotalPages  = 0;



indexInput.addEventListener('change', async () => {
  const file = indexInput.files[0];
  if (!file) return showToast('Please upload a file.', 'warning');

  const formData = new FormData();
  formData.append('file', file);
  showCardSpinner('indexCardSpinner');

  try {
    const res  = await fetch('/api/upload-index', { method:'POST', body:formData });
    const data = await res.json();
    console.log(data);
    hideCardSpinner('indexCardSpinner');

    indexPreview.innerHTML = '';
    if (file.type === 'application/pdf') {
      const url = encodeURI(`/uploads/${data.file.filename}`);
      GlobalUploadStore.indexPdf  = await pdfjsLib.getDocument(url).promise;
      GlobalUploadStore.indexTotalPages  = GlobalUploadStore.indexPdf.numPages;
      GlobalUploadStore.indexCurrentPage = 1;
      GlobalUploadStore.renderIndexPage(GlobalUploadStore.indexCurrentPage);
      showToast('Index PDF uploaded successfully!');
    } else if (file.type === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document') {
      indexPreview.innerHTML = `<div class="docx-preview">${data.html || '<em>Failed to extract DOCX.</em>'}</div>`;
      showToast('Index DOCX uploaded successfully!');
    } else {
      showToast('Unsupported file format.', 'warning');
    }
  } catch (err) {
    console.error(err);
    hideCardSpinner('indexCardSpinner');
    showToast('Error processing index file.', 'danger');
  }
});

GlobalUploadStore.renderIndexPage = async function renderIndexPage(pageNo) {
  if (!GlobalUploadStore.indexPdf) return;
  const page     = await GlobalUploadStore.indexPdf.getPage(pageNo);
  const canvas   = document.createElement('canvas');
  const context  = canvas.getContext('2d');
  const viewport = page.getViewport({ scale:1.5 });
  canvas.width   = viewport.width;
  canvas.height  = viewport.height;
  await page.render({ canvasContext:context, viewport }).promise;

  indexPreview.innerHTML = '';
  const wrapper = document.createElement('div');
  wrapper.className = 'pdf-preview-wrapper';
  wrapper.appendChild(canvas);
  indexPreview.appendChild(wrapper);
  indexPreview.appendChild(buildNav(
    pageNo,
    GlobalUploadStore.indexTotalPages,
    () => { if (GlobalUploadStore.indexCurrentPage>1) { GlobalUploadStore.indexCurrentPage--; GlobalUploadStore.renderIndexPage(GlobalUploadStore.indexCurrentPage);} },
    () => { if (GlobalUploadStore.indexCurrentPage<GlobalUploadStore.indexTotalPages) { GlobalUploadStore.indexCurrentPage++; GlobalUploadStore.renderIndexPage(GlobalUploadStore.indexCurrentPage);} }
  ));
}

/* =========================================================
   CHAPTER DOCUMENTS – MULTI-ADD + TABBED PREVIEW
=========================================================*/
const chapterInput       = document.getElementById('chapterFileInput');
const chapterNav         = document.getElementById('chapterTabNav');
const chapterContent     = document.getElementById('chapterTabContent');
const chapterPlaceholder = document.getElementById('chapterPlaceholder');

GlobalUploadStore.chapters = []; // { id, filename, chapterKey, size, type, pdf, html, current, total }

chapterInput.addEventListener('change', async () => {
  const newFiles = Array.from(chapterInput.files || []);
  if (!newFiles.length) return;
  showCardSpinner('chapterCardSpinner');

  for (const file of newFiles) {
    if (GlobalUploadStore.chapters.some(c => c.filename === file.name && c.size === file.size)) {
      showToast(`${file.name} already uploaded.`, 'warning');
      continue;
    }

    const formData = new FormData();
    formData.append('file', file);

    try {
      const res  = await fetch('/api/upload-chapter', { method:'POST', body:formData });
      const data = await res.json();
      console.log(data)
      const idx = GlobalUploadStore.chapters.length;
      const paneId = `chapter-pane-${idx}`;
      const tabId  = `${paneId}-tab`;
      const chapterKey = file.name.replace(/\.[^/.]+$/, '');

      const li  = document.createElement('li');
      li.className = 'nav-item'; li.role='presentation';
      const btn = document.createElement('button');
      btn.className = `nav-link ${idx===0?'active':''}`;
      btn.id = tabId;
      btn.type='button'; btn.role='tab';
      btn.dataset.bsToggle='pill';
      btn.dataset.bsTarget=`#${paneId}`;
      btn.ariaControls=paneId;
      btn.textContent=file.name;
      btn.dataset.chapterKey = chapterKey;
      li.appendChild(btn);
      chapterNav.appendChild(li);
      chapterNav.classList.remove('d-none');

      const pane=document.createElement('div');
      pane.className=`tab-pane fade ${idx===0?'show active':''}`;
      pane.id=paneId; pane.role='tabpanel'; pane.ariaLabelledBy=tabId;
      chapterContent.appendChild(pane);
      chapterPlaceholder?.remove();

      const chap={ id:idx, filename:file.name, chapterKey, size:file.size, current:1, file: file };

      if (file.type==='application/pdf') {
        chap.type='pdf';
        const url=encodeURI(`/uploads/${data.file.filename}`);
        chap.pdf=await pdfjsLib.getDocument(url).promise;
        chap.total=chap.pdf.numPages;
        await GlobalUploadStore.renderChapterPage(chap, pane);
      } else if (file.type==='application/vnd.openxmlformats-officedocument.wordprocessingml.document') {
        chap.type='docx';
        chap.html=data.html || '<em>Could not extract DOCX content.</em>';
        pane.innerHTML=`<div class="docx-preview">${chap.html}</div>`;
      } else {
        pane.innerHTML='<p class="text-danger">Unsupported file type.</p>';
      }
      GlobalUploadStore.chapters.push(chap);
      showToast(`${file.name} uploaded successfully!`);
    } catch (err) {
      console.error(err);
      showToast(`Failed to upload ${file.name}`, 'danger');
    }
  }
  hideCardSpinner('chapterCardSpinner');
  // chapterInput.value='';
});

GlobalUploadStore.renderChapterPage = async function renderChapterPage(chap, pane) {
  const page  = await chap.pdf.getPage(chap.current);
  const canvas=document.createElement('canvas');
  const ctx   =canvas.getContext('2d');
  const vp    =page.getViewport({ scale:1.5 });
  canvas.width=vp.width;
  canvas.height=vp.height;
  await page.render({ canvasContext:ctx, viewport:vp }).promise;

  pane.innerHTML='';
  const wrapper=document.createElement('div');
  wrapper.className='pdf-preview-wrapper position-relative';
  wrapper.appendChild(canvas);

  // Draw red outline if highlight is active
  if (chap._highlightBorder) {
    requestAnimationFrame(() => {
      const border = document.createElement('div');
      border.className = 'highlight-border';
      Object.assign(border.style, {
        position: 'absolute',
        top: canvas.offsetTop + 'px',
        left: canvas.offsetLeft + 'px',
        width: canvas.offsetWidth + 'px',
        height: canvas.offsetHeight + 'px',
        border: '3px dashed red',
        boxSizing: 'border-box',
        pointerEvents: 'none',
        zIndex: 10
      });
      wrapper.appendChild(border);
    });
    chap._highlightBorder = false;
  }


  pane.appendChild(wrapper);
  pane.appendChild(buildNav(
    chap.current,
    chap.total,
    () => { if (chap.current>1){ chap.current--; GlobalUploadStore.renderChapterPage(chap,pane);} },
    () => { if (chap.current<chap.total){ chap.current++; GlobalUploadStore.renderChapterPage(chap,pane);} }
  ));
}

// window.renderChapterPage = renderChapterPage; // Expose globally

function buildNav(pageNo,total,onPrev,onNext){
  const nav=document.createElement('div');
  nav.className='pdf-nav d-flex align-items-center gap-2 mt-2';
  const prevBtn=document.createElement('button');
  prevBtn.className='btn btn-sm btn-outline-secondary';
  prevBtn.textContent='Previous';
  prevBtn.disabled=pageNo===1;
  prevBtn.onclick=onPrev;
  const nextBtn=document.createElement('button');
  nextBtn.className='btn btn-sm btn-outline-secondary';
  nextBtn.textContent='Next';
  nextBtn.disabled=pageNo===total;
  nextBtn.onclick=onNext;
  const info=document.createElement('span');
  info.textContent=`Page ${pageNo} of ${total}`;
  nav.append(prevBtn,info,nextBtn);
  return nav;
}

function showToast(msg,type='success'){
  const container=document.getElementById('toastContainer');
  const toast=document.createElement('div');
  toast.className=`toast text-white bg-${type} border-0 mb-2 fade show`;
  toast.role='alert';
  toast.innerHTML=`<div class="d-flex"><div class="toast-body">${msg}</div><button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button></div>`;
  container.appendChild(toast);
  new bootstrap.Toast(toast).show();
  toast.addEventListener('hidden.bs.toast',()=>toast.remove());
}

function showCardSpinner(id){document.getElementById(id)?.classList.remove('d-none');}
function hideCardSpinner(id){document.getElementById(id)?.classList.add('d-none');}
