// NestFind v3 — Main JS
document.querySelectorAll('.toast').forEach(el => {
  setTimeout(() => { el.style.opacity='0'; el.style.transform='translateX(110%)'; }, 4000);
  setTimeout(() => el.remove(), 4500);
});
const ff = document.getElementById('filterForm');
if (ff) {
  ff.querySelectorAll('select').forEach(s => s.addEventListener('change', () => ff.submit()));
}
