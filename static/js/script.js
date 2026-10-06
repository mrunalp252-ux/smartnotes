/**
 * SmartNotes - Client-Side Functionality
 * "Capture. Organize. Remember."
 */

document.addEventListener('DOMContentLoaded', () => {
    initTheme();
    initDeleteModal();
    initPinToggles();
    initToasts();
    initCharCounters();
    initFormValidation();
});

/* ===================================================================
   1. Theme Management (Light / Dark Mode with localStorage)
   =================================================================== */
function initTheme() {
    const themeToggleBtn = document.getElementById('theme-toggle-btn');
    const root = document.documentElement;

    // Check localStorage or system preference
    const savedTheme = localStorage.getItem('smartnotes-theme');
    const systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    
    const initialTheme = savedTheme ? savedTheme : (systemPrefersDark ? 'dark' : 'light');
    applyTheme(initialTheme);

    if (themeToggleBtn) {
        themeToggleBtn.addEventListener('click', () => {
            const currentTheme = root.getAttribute('data-theme') || 'light';
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            applyTheme(newTheme);
            localStorage.setItem('smartnotes-theme', newTheme);
        });
    }
}

function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
}

/* ===================================================================
   2. Delete Confirmation Modal
   =================================================================== */
function initDeleteModal() {
    const modal = document.getElementById('delete-modal');
    const cancelBtn = document.getElementById('modal-cancel-btn');

    if (!modal) return;

    // Close on cancel button
    if (cancelBtn) {
        cancelBtn.addEventListener('click', closeDeleteModal);
    }

    // Close on clicking backdrop
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            closeDeleteModal();
        }
    });

    // Close on Escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && modal.classList.contains('active')) {
            closeDeleteModal();
        }
    });
}

function openDeleteModal(noteId, noteTitle) {
    const modal = document.getElementById('delete-modal');
    const form = document.getElementById('delete-modal-form');
    const titleSpan = document.getElementById('delete-note-title');

    if (!modal || !form) return;

    form.action = `/notes/${encodeURIComponent(noteId)}/delete`;
    if (titleSpan) {
        titleSpan.textContent = `"${noteTitle}"`;
    }

    modal.classList.add('active');
    modal.setAttribute('aria-hidden', 'false');
}

function closeDeleteModal() {
    const modal = document.getElementById('delete-modal');
    if (modal) {
        modal.classList.remove('active');
        modal.setAttribute('aria-hidden', 'true');
    }
}

// Make openDeleteModal globally available for inline onclick handlers
window.openDeleteModal = openDeleteModal;
window.closeDeleteModal = closeDeleteModal;

/* ===================================================================
   3. Pin / Unpin AJAX Enhancement
   =================================================================== */
function initPinToggles() {
    const pinForms = document.querySelectorAll('.pin-form');

    pinForms.forEach(form => {
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const btn = form.querySelector('.btn-pin-toggle');
            const noteCard = form.closest('.note-card');
            const actionUrl = form.getAttribute('action');

            try {
                const response = await fetch(actionUrl, {
                    method: 'POST',
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest',
                        'Accept': 'application/json'
                    }
                });

                if (response.ok) {
                    const data = await response.json();
                    if (data.success) {
                        const isPinned = data.is_pinned;
                        
                        // Toggle visual classes
                        if (btn) {
                            btn.classList.toggle('is-pinned', isPinned);
                            btn.setAttribute('title', isPinned ? 'Unpin note' : 'Pin note');
                            btn.setAttribute('aria-label', isPinned ? 'Unpin note' : 'Pin note');
                            
                            const svg = btn.querySelector('svg');
                            if (svg) {
                                svg.setAttribute('fill', isPinned ? 'currentColor' : 'none');
                            }

                            // Pinned tag
                            let pinnedTag = btn.querySelector('.pinned-tag');
                            if (isPinned && !pinnedTag) {
                                pinnedTag = document.createElement('span');
                                pinnedTag.className = 'pinned-tag';
                                pinnedTag.textContent = 'Pinned';
                                btn.appendChild(pinnedTag);
                            } else if (!isPinned && pinnedTag) {
                                pinnedTag.remove();
                            }
                        }

                        if (noteCard) {
                            noteCard.classList.toggle('note-card-pinned', isPinned);
                        }

                        // Update pinned counter on dashboard
                        const pinnedCountEl = document.getElementById('stat-pinned-notes');
                        if (pinnedCountEl) {
                            let count = parseInt(pinnedCountEl.textContent, 10) || 0;
                            count = isPinned ? count + 1 : Math.max(0, count - 1);
                            pinnedCountEl.textContent = count;
                        }

                        showToast(isPinned ? 'Note pinned successfully' : 'Note unpinned successfully', 'success');

                        // Smoothly re-sort or reload if order changed significantly
                        setTimeout(() => {
                            window.location.reload();
                        }, 500);
                    }
                } else {
                    // Fallback to normal form submit on error
                    form.submit();
                }
            } catch (err) {
                // If fetch failed, fallback to standard form submit
                form.submit();
            }
        });
    });
}

/* ===================================================================
   4. Toast Notifications
   =================================================================== */
function initToasts() {
    const existingToasts = document.querySelectorAll('.toast-message');
    existingToasts.forEach(toast => {
        autoDismissToast(toast);
    });
}

function autoDismissToast(toast, delay = 4000) {
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(30px)';
        setTimeout(() => toast.remove(), 300);
    }, delay);
}

function showToast(message, type = 'success') {
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.className = 'toast-container';
        container.id = 'toast-container';
        document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.className = `toast-message toast-${type}`;
    
    const iconSvg = type === 'success' 
        ? '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"></polyline></svg>'
        : '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"></circle><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line></svg>';

    toast.innerHTML = `
        <div class="toast-icon">${iconSvg}</div>
        <div class="toast-text">${escapeHtml(message)}</div>
        <button type="button" class="toast-close" onclick="this.parentElement.remove()" aria-label="Close notification">&times;</button>
    `;

    container.appendChild(toast);
    autoDismissToast(toast);
}

function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

/* ===================================================================
   5. Dynamic Character Counters
   =================================================================== */
function initCharCounters() {
    const contentTextarea = document.getElementById('content');
    const counterEl = document.getElementById('char-counter');

    if (contentTextarea && counterEl) {
        const updateCount = () => {
            const count = contentTextarea.value.length;
            counterEl.textContent = `${count.toLocaleString()} character${count === 1 ? '' : 's'}`;
        };

        contentTextarea.addEventListener('input', updateCount);
        updateCount();
    }
}

/* ===================================================================
   6. Client-Side Form Validation
   =================================================================== */
function initFormValidation() {
    const forms = document.querySelectorAll('form#create-note-form, form#edit-note-form');

    forms.forEach(form => {
        form.addEventListener('submit', (e) => {
            const titleInput = form.querySelector('input[name="title"]');
            const contentTextarea = form.querySelector('textarea[name="content"]');

            if (titleInput && !titleInput.value.trim()) {
                e.preventDefault();
                titleInput.focus();
                showToast('Please enter a note title.', 'error');
                return false;
            }

            if (contentTextarea && !contentTextarea.value.trim()) {
                e.preventDefault();
                contentTextarea.focus();
                showToast('Please enter note content.', 'error');
                return false;
            }
        });
    });
}
