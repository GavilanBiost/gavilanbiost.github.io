(function () {
  'use strict';

  var toggle = document.getElementById('menu-toggle');
  var panel = document.getElementById('mobile-navigation');

  if (toggle && panel) {
    toggle.addEventListener('click', function () {
      var open = panel.hidden;
      panel.hidden = !open;
      toggle.setAttribute('aria-expanded', String(open));
    });
  }

  var normalize = function (text) {
    return text.toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '');
  };

  var root = document.querySelector('[data-archive]');
  if (!root) return;

  var search = root.querySelector('[data-archive-search]');
  var yearFilter = root.querySelector('[data-archive-year]');
  var journalFilter = root.querySelector('[data-archive-journal]');
  var counter = root.querySelector('[data-archive-count]');
  var empty = root.querySelector('[data-archive-empty]');
  var cards = Array.prototype.slice.call(root.querySelectorAll('.card'));
  var headings = Array.prototype.slice.call(root.querySelectorAll('.archive-year'));

  cards.forEach(function (card) {
    card.dataset.haystack = normalize(card.textContent || '');
  });

  function apply() {
    var term = normalize(search ? search.value.trim() : '');
    var year = yearFilter ? yearFilter.value : 'all';
    var journal = journalFilter ? journalFilter.value : 'all';
    var shown = 0;

    cards.forEach(function (card) {
      var matchesTerm = !term || card.dataset.haystack.indexOf(term) !== -1;
      var matchesYear = year === 'all' || card.dataset.year === year;
      var matchesJournal = journal === 'all' || card.dataset.journal === journal;
      var visible = matchesTerm && matchesYear && matchesJournal;
      card.hidden = !visible;
      if (visible) shown += 1;
    });

    headings.forEach(function (heading) {
      var visibleInGroup = false;
      var node = heading.nextElementSibling;
      while (node && !node.classList.contains('archive-year')) {
        if (node.classList.contains('card') && !node.hidden) {
          visibleInGroup = true;
          break;
        }
        node = node.nextElementSibling;
      }
      heading.hidden = !visibleInGroup;
    });

    if (counter) {
      counter.textContent = shown + (shown === 1 ? ' resultado' : ' resultados');
    }
    if (empty) {
      empty.hidden = shown !== 0;
    }
  }

  if (search) search.addEventListener('input', apply);
  if (yearFilter) yearFilter.addEventListener('change', apply);
  if (journalFilter) journalFilter.addEventListener('change', apply);

  var initial = new URLSearchParams(window.location.search).get('q');
  if (initial && search) {
    search.value = initial;
  }
  apply();
})();
