// highlight-pageborder.js
window.highlightPageBorder = async function (chapterKey, pageNo) {
  const tab = document.querySelector(
    `#chapterTabNav .nav-link[data-chapter-key="${chapterKey}"]`
  );
  if (!tab) return showToast(`Chapter '${chapterKey}' not loaded`, 'danger');

  bootstrap.Tab.getOrCreateInstance(tab).show();
  await new Promise((res) => setTimeout(res, 300));

  const chap = GlobalUploadStore.chapters.find(
    (c) => c.chapterKey === chapterKey
  );
  if (!chap) return showToast(`Chapter data not found`, 'danger');

  chap.current = pageNo;
  chap._highlightBorder = true;

  //Crucially, remove the bbox-related logic.
  //No need for bbox parameter or handling.
  //The page border highlighting logic should now be based on the page number alone.
  delete chap._highlightPageBorderBBox; //No longer needed

  const pane = document.querySelector(`#chapter-pane-${chap.id}`);
  await GlobalUploadStore.renderChapterPage(chap, pane);
};