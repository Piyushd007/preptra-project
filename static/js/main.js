// ===== PREPTRA MAIN JS =====

// Sidebar toggle
document.addEventListener('DOMContentLoaded', () => {
  const sidebarOpen = document.getElementById('sidebarOpen');
  const sidebarClose = document.getElementById('sidebarClose');
  const sidebar = document.getElementById('sidebar');
  const mainContent = document.getElementById('mainContent');

  if (sidebarOpen) {
    sidebarOpen.addEventListener('click', () => {
      sidebar.classList.add('open');
      document.body.style.overflow = 'hidden';
    });
  }
  if (sidebarClose) {
    sidebarClose.addEventListener('click', () => {
      sidebar.classList.remove('open');
      document.body.style.overflow = '';
    });
  }
  // Close sidebar on outside click (mobile)
  document.addEventListener('click', (e) => {
    if (sidebar && sidebar.classList.contains('open')) {
      if (!sidebar.contains(e.target) && !sidebarOpen?.contains(e.target)) {
        sidebar.classList.remove('open');
        document.body.style.overflow = '';
      }
    }
  });

  // Auto-dismiss flash messages
  document.querySelectorAll('.flash-msg').forEach(msg => {
    setTimeout(() => msg.style.opacity = '0', 4000);
    setTimeout(() => msg.remove(), 4400);
  });

  // Add Jinja now() helper via JS
  window.now = () => new Date();
});

// Utility: format date
function formatDate(dateStr) {
  if (!dateStr) return '—';
  const d = new Date(dateStr);
  return d.toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' });
}

// Utility: show toast notification
function showToast(msg, type = 'success') {
  const toast = document.createElement('div');
  toast.className = `flash-msg flash-${type}`;
  toast.style.cssText = 'position:fixed;bottom:24px;right:24px;z-index:9999;min-width:280px;box-shadow:0 8px 32px rgba(0,0,0,0.5);animation:fadeIn 0.3s ease';
  const icons = { success: 'check-circle-fill', error: 'x-circle-fill', info: 'info-circle-fill' };
  toast.innerHTML = `<i class="bi bi-${icons[type]||'info-circle-fill'}"></i>${msg}`;
  document.body.appendChild(toast);
  setTimeout(() => { toast.style.opacity = '0'; toast.style.transition = 'opacity 0.4s'; }, 3000);
  setTimeout(() => toast.remove(), 3400);
}
