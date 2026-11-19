// Mobile menu: opens with the button, closes on a link tap or the Escape key
var t = document.querySelector('.menu-toggle'), n = document.getElementById('nav');
function setMenu(open) {
  n.classList.toggle('open', open);
  t.setAttribute('aria-expanded', open ? 'true' : 'false');
}
if (t && n) {
  t.addEventListener('click', function () { setMenu(!n.classList.contains('open')); });
  n.addEventListener('click', function (e) { if (e.target.closest('a')) setMenu(false); });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && n.classList.contains('open')) { setMenu(false); t.focus(); }
  });
}
// Load a YouTube video only when tapped
document.querySelectorAll('.video button[data-youtube]').forEach(function (b) {
  b.addEventListener('click', function () {
    var f = document.createElement('iframe');
    f.src = 'https://www.youtube-nocookie.com/embed/' + b.dataset.youtube + '?autoplay=1';
    f.title = b.getAttribute('aria-label') || 'Gasiin video';
    f.allow = 'autoplay; encrypted-media; picture-in-picture';
    f.allowFullscreen = true;
    b.replaceWith(f);
  });
});
