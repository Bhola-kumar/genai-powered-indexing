// This will be a modified version of update.js with inline feedback controls and downloadable feedback report in JSON format.

const updateButton = document.getElementById('updateButton');
const updatedIndexPreview = document.getElementById('updatedIndexPreview');
const feedbackLog = [];

function hasChaptersUploaded() {
  return document.querySelectorAll('#chapterTabContent .tab-pane').length > 0;
}

function showToast(msg, type = 'success') {
  const container = document.getElementById('toastContainer');
  const toast = document.createElement('div');
  toast.className = `toast align-items-center text-white bg-${type} border-0 mb-2 fade show`;
  toast.role = 'alert';
  toast.ariaLive = 'assertive';
  toast.ariaAtomic = 'true';
  toast.innerHTML = `
    <div class="d-flex">
      <div class="toast-body">${msg}</div>
      <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
    </div>`;
  container.appendChild(toast);
  new bootstrap.Toast(toast).show();
  toast.addEventListener('hidden.bs.toast', () => toast.remove());
}

function showCardSpinner(id) {
  const el = document.getElementById(id);
  el.innerHTML = `
    <div class="preview-spinner text-muted">
      <div class="spinner-border text-primary mb-2" role="status"></div>
      <p class="mt-2">Processing, please wait...</p>
    </div>`;
}

function hideCardSpinner(id) {
  const el = document.getElementById(id);
  el.querySelector('.spinner-border')?.remove();
  el.querySelector('p')?.remove();
}

function downloadFeedbackJSON() {
  const blob = new Blob([JSON.stringify(feedbackLog, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = 'feedback_report.json';
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

document.getElementById('downloadFeedback')?.addEventListener('click', downloadFeedbackJSON);

updateButton.addEventListener('click', async () => {
  const indexFile = document.getElementById('indexFileInput').files[0];
  const chapterFiles = window.GlobalUploadStore.chapters;

  console.log(indexFile);
  console.log(chapterFiles);
  if (!indexFile || !hasChaptersUploaded()) {
    showToast('Please upload an index document and at least one chapter document before updating.', 'warning');
    return;
  }

  showCardSpinner('updatedIndexPreview');
  feedbackLog.length = 0; // clear previous feedbacks
  const formData = new FormData();
  formData.append('index_file', indexFile);
  chapterFiles.forEach((ch, i) => {
    if (ch.file instanceof File) {
      formData.append('chapter_files', ch.file);
    } else {
      console.warn(`Chapter ${i} is missing a valid File object`, ch);
    }
  });
  try {
    const res = await fetch('/data/index_audit_result3.json');
    const audit = await res.json();
    // console.log([...formData.entries()])
    // const res = await fetch('http://localhost:8080/api/process-documents', {
    //   method: 'POST',
    //   body: formData
    // });

    // if (!res.ok) {
    //   throw new Error('Failed to process documents');
    // }

    // const audit = await res.json();
    updatedIndexPreview.innerHTML = '';

    if (!Array.isArray(audit)) {
      updatedIndexPreview.innerHTML = '<div class="text-danger">Invalid response.</div>';
      return;
    }

    const container = document.createElement('div');
    container.className = 'updated-index-structured';

    audit.forEach(term => {
      const termBlock = document.createElement('div');
      termBlock.className = 'mb-4 p-3 border rounded shadow-sm';

      const h5 = document.createElement('h5');
      h5.className = 'fw-bold';
      h5.textContent = term.term;
      termBlock.appendChild(h5);

      term.subentries.forEach(sub => {
        const row = document.createElement('div');
        row.className = 'd-flex flex-column py-1 px-2 rounded';
        if (sub.highlight) row.classList.add('bg-warning-subtle');

        const topLine = document.createElement('div');
        topLine.className = 'd-flex justify-content-between align-items-center';

        const left = document.createElement('div');
        left.textContent = `${sub.text} → ${sub.refs.join(', ')}`;

        const buttonGroup = document.createElement('div');
        buttonGroup.className = 'd-flex align-items-center gap-2';

        if (sub.highlight && sub.match_details) {
          const md = sub.match_details;
          // console.log(md);
          const chapter = GlobalUploadStore.chapters.find(c => c.chapterKey === md.chapter_key);

          if (!chapter) {
            console.error(`Chapter '${md.chapter_key}' not found for highlighting.`);
            return; // Skip this subentry if the chapter isn't loaded.
          }

          const matchBtn = document.createElement('button');
          matchBtn.className = 'btn btn-outline-primary btn-sm';
          matchBtn.textContent = sub.status;
          matchBtn.dataset.chapterKey = md.chapter_key;
          matchBtn.dataset.page = md.page_number;
          matchBtn.dataset.boundingBox = md.bounding_box;
          matchBtn.dataset.bundingBoxPageNumber = md.bounding_box_page_numbers;
          console.log(md.bounding_box);
          // console.log(matchBtn.dataset);
          // matchBtn.onclick = () => window.highlightPageBorder(
          //   matchBtn.dataset.chapterKey,
          //   +matchBtn.dataset.page
          // );
          matchBtn.onclick = async () => {
            await highlightPageBorder(md.chapter_key, +md.page_number);
            await highlightParagraph(md.chapter_key, +md.page_number, md.bounding_box, md.bounding_box_page_numbers);
          };

          const feedbackBtn = document.createElement('button');
          feedbackBtn.className = 'btn btn-outline-secondary btn-sm';
          feedbackBtn.innerHTML = '<i class="bi bi-chat-left-dots"></i>';
          feedbackBtn.title = 'Give Feedback';

          const feedbackActions = document.createElement('div');
          feedbackActions.className = 'inline-feedback';

          const acceptBtn = document.createElement('button');
          acceptBtn.className = 'btn btn-sm btn-success';
          acceptBtn.textContent = 'Accept';

          const declineBtn = document.createElement('button');
          declineBtn.className = 'btn btn-sm btn-danger';
          declineBtn.textContent = 'Decline';

          const confirmationText = document.createElement('span');
          confirmationText.className = 'feedback-confirmed visually-hidden';

          acceptBtn.onclick = () => {
            feedbackActions.classList.remove('show');
            confirmationText.textContent = '✓ Accepted';
            confirmationText.classList.remove('visually-hidden');
            showToast('Feedback accepted. Thank you!', 'success');

            feedbackLog.push({
              term: term.term,
              subentry: sub.text,
              refs: sub.refs,
              status: sub.status,
              feedback: 'accepted'
            });
          };

          declineBtn.onclick = () => {
            feedbackActions.classList.remove('show');
            confirmationText.textContent = '✗ Declined';
            confirmationText.classList.remove('visually-hidden');
            showToast('Feedback declined. Thank you!', 'warning');

            feedbackLog.push({
              term: term.term,
              subentry: sub.text,
              refs: sub.refs,
              status: sub.status,
              feedback: 'declined'
            });
          };

          feedbackBtn.onclick = () => {
            feedbackActions.classList.toggle('show');
          };

          feedbackActions.append(acceptBtn, declineBtn);
          buttonGroup.append(matchBtn, feedbackBtn, confirmationText);

          topLine.append(left, buttonGroup);
          row.appendChild(topLine);
          row.appendChild(feedbackActions);

        } else {
          const badge = document.createElement('span');
          badge.className = 'badge';
          badge.textContent = sub.status;
          badge.classList.add(
            sub.status.includes('Found') ? 'bg-success' :
              sub.status.includes('Not') ? 'bg-danger' :
                'bg-secondary'
          );
          topLine.append(left, badge);
          row.appendChild(topLine);
        }

        termBlock.appendChild(row);
      });

      container.appendChild(termBlock);
    });

    updatedIndexPreview.appendChild(container);
    showToast('Updated index displayed successfully!');
  } catch (err) {
    console.error(err);
    updatedIndexPreview.innerHTML = '<div class="text-danger">Failed to update index.</div>';
    showToast('Error loading audit JSON', 'danger');
  }

  hideCardSpinner('updatedIndexPreview');
});
