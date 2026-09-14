(function () {
  'use strict';

  if (!new URLSearchParams(window.location.search).has('q')) return;

  var headerOffset = 110;
  var aligned = false;

  function alignSearch() {
    var search = document.getElementById('site-search');
    if (!search || aligned) return false;

    aligned = true;
    window.setTimeout(function () {
      var top = search.getBoundingClientRect().top + window.scrollY - headerOffset;
      window.scrollTo({ top: Math.max(0, top), behavior: 'auto' });
    }, 150);
    return true;
  }

  if (alignSearch()) return;

  var observer = new MutationObserver(function () {
    if (alignSearch()) observer.disconnect();
  });

  observer.observe(document.getElementById('root') || document.body, {
    childList: true,
    subtree: true
  });
})();
