(() => {
  const lightbox = document.getElementById('lightbox');
  document.querySelectorAll('[data-lightbox-src]').forEach(button => button.addEventListener('click', () => {
    lightbox.querySelector('img').src = button.dataset.lightboxSrc;
    lightbox.classList.add('active');
    lightbox.querySelector('button').focus();
  }));
  const closeLightbox = () => lightbox?.classList.remove('active');
  lightbox?.addEventListener('click', event => { if (event.target === lightbox || event.target.closest('[data-lightbox-close]')) closeLightbox(); });
  document.addEventListener('keydown', event => { if (event.key === 'Escape') closeLightbox(); });
})();
