/* Progressive enhancement: selections immediately request the read-only result. */
const form = document.querySelector('.facet-form');
if (form) {
  const status = document.getElementById('filter-status');
  const submit = form.querySelector('button[type="submit"]');
  submit.hidden = true;
  status.textContent = '勾选或取消后立即更新结果。';
  form.addEventListener('change', event => {
    if (event.target.type !== 'checkbox') return;
    status.textContent = '正在更新结果，请稍候…';
    status.setAttribute('aria-busy', 'true');
    // A normal GET navigation keeps one source of filtering truth on the server.
    // Anchor the refreshed page to the dimension the user was editing.
    form.action = `${window.location.pathname}#${event.target.closest('fieldset').id}`;
    form.requestSubmit();
  });
  // Browser back/forward may restore a page from the navigation cache.
  window.addEventListener('pageshow', event => {
    if (event.persisted) {
      window.location.reload();
      return;
    }
    status.textContent = '勾选或取消后立即更新结果。';
    status.removeAttribute('aria-busy');
  });
}
