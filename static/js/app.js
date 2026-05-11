/* ===================================================
   REMS – app.js
   Sidebar toggle + submenu accordion + form enhancements
   =================================================== */

document.addEventListener('DOMContentLoaded', function () {

    // ─── Sidebar Toggle (Desktop) ─────────────────────────────────────────────
    const wrapper        = document.getElementById('remsWrapper');
    const toggleBtn      = document.getElementById('sidebarToggleBtn');
    const sidebar        = document.getElementById('remsSidebar');
    const overlay        = document.getElementById('sidebarOverlay');
    const closeBtn       = document.getElementById('sidebarCloseBtn');

    const COLLAPSED_KEY  = 'rems_sidebar_collapsed';
    const isMobile       = () => window.innerWidth < 992;

    // Restore saved desktop state
    if (!isMobile() && localStorage.getItem(COLLAPSED_KEY) === '1') {
        wrapper && wrapper.classList.add('sidebar-collapsed');
    }

    function collapseSidebar() {
        if (isMobile()) {
            sidebar && sidebar.classList.remove('mobile-open');
            overlay && overlay.classList.remove('active');
        } else {
            wrapper && wrapper.classList.add('sidebar-collapsed');
            localStorage.setItem(COLLAPSED_KEY, '1');
        }
    }

    function expandSidebar() {
        if (isMobile()) {
            sidebar && sidebar.classList.add('mobile-open');
            overlay && overlay.classList.add('active');
        } else {
            wrapper && wrapper.classList.remove('sidebar-collapsed');
            localStorage.setItem(COLLAPSED_KEY, '0');
        }
    }

    function toggleSidebar() {
        if (isMobile()) {
            const isOpen = sidebar && sidebar.classList.contains('mobile-open');
            isOpen ? collapseSidebar() : expandSidebar();
        } else {
            const isCollapsed = wrapper && wrapper.classList.contains('sidebar-collapsed');
            isCollapsed ? expandSidebar() : collapseSidebar();
        }
    }

    toggleBtn  && toggleBtn.addEventListener('click',  toggleSidebar);
    closeBtn   && closeBtn.addEventListener('click',   collapseSidebar);
    overlay    && overlay.addEventListener('click',    collapseSidebar);

    // Re-evaluate on resize
    window.addEventListener('resize', function () {
        if (!isMobile()) {
            sidebar  && sidebar.classList.remove('mobile-open');
            overlay  && overlay.classList.remove('active');
            // restore saved desktop state
            if (localStorage.getItem(COLLAPSED_KEY) === '1') {
                wrapper && wrapper.classList.add('sidebar-collapsed');
            } else {
                wrapper && wrapper.classList.remove('sidebar-collapsed');
            }
        }
    });

    // ─── Submenu Accordion ────────────────────────────────────────────────────
    const parentBtns = document.querySelectorAll('.nav-link--parent');

    parentBtns.forEach(function (btn) {
        btn.addEventListener('click', function (e) {
            e.preventDefault();
            const targetId  = btn.getAttribute('data-target');
            const submenu   = document.getElementById(targetId);
            const parentLi  = btn.closest('.nav-item--has-sub');

            if (!submenu || !parentLi) return;

            const isOpen = parentLi.classList.contains('open');

            // Close all other open submenus
            document.querySelectorAll('.nav-item--has-sub.open').forEach(function (openLi) {
                if (openLi !== parentLi) {
                    openLi.classList.remove('open');
                    const openSub = openLi.querySelector('.nav-submenu');
                    if (openSub) openSub.classList.remove('open');
                    const openBtn = openLi.querySelector('.nav-link--parent');
                    if (openBtn) openBtn.setAttribute('aria-expanded', 'false');
                }
            });

            // Toggle this one
            if (isOpen) {
                parentLi.classList.remove('open');
                submenu.classList.remove('open');
                btn.setAttribute('aria-expanded', 'false');
            } else {
                parentLi.classList.add('open');
                submenu.classList.add('open');
                btn.setAttribute('aria-expanded', 'true');
            }
        });
    });

    // ─── Responsive tables (stacked rows + labels on small screens) ──────────
    initResponsiveRemsTables();

    // ─── Form Enhancements ────────────────────────────────────────────────────
    initFormEnhancements();
    
    // ─── Payment Collection Calculator ────────────────────────────────────────
    initPaymentCalculator();
});

/**
 * Copies thead labels onto each body cell as data-label so CSS can show
 * key/value rows under 768px without horizontal scrolling.
 * Skips rows with colspan (empty states, expandable detail rows).
 */
function initResponsiveRemsTables() {
    document.querySelectorAll('table.rems-table').forEach(function (table) {
        if (table.classList.contains('rems-table--no-mobile-stack')) {
            return;
        }

        var theadRow = table.querySelector('thead tr');
        if (!theadRow) {
            return;
        }

        var headers = [];
        theadRow.querySelectorAll('th').forEach(function (th) {
            headers.push(th.textContent.replace(/\s+/g, ' ').trim());
        });

        table.querySelectorAll('tbody tr').forEach(function (tr) {
            tr.classList.remove('rems-table__row--full');
            var tds = Array.prototype.slice.call(tr.querySelectorAll(':scope > td'));

            if (tds.length === 1) {
                var span0 = parseInt(tds[0].getAttribute('colspan') || '1', 10);
                if (span0 > 1) {
                    tr.classList.add('rems-table__row--full');
                    tds[0].removeAttribute('data-label');
                    return;
                }
            }

            var i;
            for (i = 0; i < tds.length; i++) {
                if (parseInt(tds[i].getAttribute('colspan') || '1', 10) > 1) {
                    tr.classList.add('rems-table__row--full');
                    tds.forEach(function (td) {
                        td.removeAttribute('data-label');
                    });
                    return;
                }
            }

            var colIndex = 0;
            tds.forEach(function (td) {
                td.removeAttribute('data-label');
                var cs = parseInt(td.getAttribute('colspan') || '1', 10);
                if (headers[colIndex]) {
                    td.setAttribute('data-label', headers[colIndex]);
                }
                colIndex += cs;
            });
        });

        table.classList.add('rems-table--labeled');
    });
}

// ─── Form Enhancements ────────────────────────────────────────────────────────
function initFormEnhancements() {
    // Submission validation
    const forms = document.querySelectorAll('form');
    forms.forEach(function (form) {
        form.addEventListener('submit', function (e) {
            const requiredFields = form.querySelectorAll('[required]');
            let isValid = true;

            requiredFields.forEach(function (field) {
                if (!field.value.trim()) {
                    isValid = false;
                    field.classList.add('is-invalid');
                    field.style.animation = 'shake 0.4s ease';
                    setTimeout(function () { field.style.animation = ''; }, 400);
                } else {
                    field.classList.remove('is-invalid');
                }
            });

            if (!isValid) {
                e.preventDefault();
            }
        });
    });

    // Real-time blur validation
    const inputs = document.querySelectorAll('input, select, textarea');
    inputs.forEach(function (input) {
        input.addEventListener('blur', function () { validateField(this); });
        input.addEventListener('input', function () {
            if (this.classList.contains('is-invalid')) validateField(this);
        });
    });
}

function validateField(field) {
    const value      = field.value.trim();
    const isRequired = field.hasAttribute('required');

    if (isRequired && !value) {
        field.classList.add('is-invalid');
        field.classList.remove('is-valid');
        return false;
    }

    // Email
    if (field.type === 'email' && value) {
        if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) {
            field.classList.add('is-invalid');
            field.classList.remove('is-valid');
            return false;
        }
    }

    // Phone
    if (field.type === 'tel' && value) {
        if (!/^[\+]?[1-9][\d]{0,15}$/.test(value.replace(/\s/g, ''))) {
            field.classList.add('is-invalid');
            field.classList.remove('is-valid');
            return false;
        }
    }

    field.classList.remove('is-invalid');
    if (value) field.classList.add('is-valid');
    return true;
}

// ─── Payment Collection Calculator ────────────────────────────────────────────
function initPaymentCalculator() {
    // Find all collect payment forms
    const collectForms = document.querySelectorAll('[id^="collectPaymentForm"]');
    
    collectForms.forEach(function(form) {
        const rentInput = form.querySelector('[name="rent_amount"]');
        const garbageInput = form.querySelector('[name="garbage_amount"]');
        const waterInput = form.querySelector('[name="water_amount"]');
        
        if (!rentInput || !garbageInput || !waterInput) return;
        
        const totalDisplay = form.querySelector('.payment-total-display');
        if (!totalDisplay) return;
        
        const totalAmountSpan = totalDisplay.querySelector('.total-amount');
        
        function calculateTotal() {
            const rent = parseFloat(rentInput.value) || 0;
            const garbage = parseFloat(garbageInput.value) || 0;
            const water = parseFloat(waterInput.value) || 0;
            const total = rent + garbage + water;
            
            if (totalAmountSpan) {
                totalAmountSpan.textContent = total.toFixed(2);
            }
            
            // Show/hide based on whether any payment is entered
            if (total > 0) {
                totalDisplay.style.display = 'block';
            } else {
                totalDisplay.style.display = 'none';
            }
            
            // Validate amounts don't exceed max
            validatePaymentAmount(rentInput);
            validatePaymentAmount(garbageInput);
            validatePaymentAmount(waterInput);
        }
        
        function validatePaymentAmount(input) {
            const value = parseFloat(input.value) || 0;
            const max = parseFloat(input.getAttribute('max')) || 0;
            
            if (value > max) {
                input.classList.add('is-invalid');
                input.classList.remove('is-valid');
            } else if (value > 0) {
                input.classList.remove('is-invalid');
                input.classList.add('is-valid');
            } else {
                input.classList.remove('is-invalid', 'is-valid');
            }
        }
        
        // Calculate on input change
        rentInput.addEventListener('input', calculateTotal);
        garbageInput.addEventListener('input', calculateTotal);
        waterInput.addEventListener('input', calculateTotal);
        
        // Initial calculation
        calculateTotal();
        
        // Form submission validation
        form.addEventListener('submit', function(e) {
            const rent = parseFloat(rentInput.value) || 0;
            const garbage = parseFloat(garbageInput.value) || 0;
            const water = parseFloat(waterInput.value) || 0;
            const total = rent + garbage + water;
            
            if (total <= 0) {
                e.preventDefault();
                alert('Please enter at least one payment amount greater than 0.');
                return false;
            }
            
            // Validate max amounts
            const rentMax = parseFloat(rentInput.getAttribute('max')) || 0;
            const garbageMax = parseFloat(garbageInput.getAttribute('max')) || 0;
            const waterMax = parseFloat(waterInput.getAttribute('max')) || 0;
            
            if (rent > rentMax || garbage > garbageMax || water > waterMax) {
                e.preventDefault();
                alert('Payment amounts cannot exceed the due amounts.');
                return false;
            }
        });
    });
}
