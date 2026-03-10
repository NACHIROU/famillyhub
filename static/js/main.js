document.addEventListener('DOMContentLoaded', function() {
    const mobileMenuToggle = document.getElementById('mobileMenuToggle');
    const sidebar = document.getElementById('sidebar');
    
    if (mobileMenuToggle && sidebar) {
        const sidebarClose = document.getElementById('sidebarClose');
        
        mobileMenuToggle.addEventListener('click', function() {
            sidebar.classList.toggle('open');
        });
        
        if (sidebarClose) {
            sidebarClose.addEventListener('click', function() {
                sidebar.classList.remove('open');
            });
        }
        
        document.querySelectorAll('.nav-item').forEach(item => {
            item.addEventListener('click', function() {
                if (window.innerWidth <= 1024) {
                    sidebar.classList.remove('open');
                }
            });
        });
    }

    const dropdowns = document.querySelectorAll('.dropdown-toggle');
    dropdowns.forEach(dropdown => {
        dropdown.addEventListener('click', function(e) {
            e.stopPropagation();
            const menu = this.nextElementSibling;
            menu.classList.toggle('show');
        });
    });

    document.addEventListener('click', function() {
        document.querySelectorAll('.dropdown-menu.show').forEach(menu => {
            menu.classList.remove('show');
        });
    });

    const voteOptions = document.querySelectorAll('.vote-option');
    voteOptions.forEach(option => {
        option.addEventListener('click', function() {
            const parent = this.closest('.vote-options');
            parent.querySelectorAll('.vote-option').forEach(opt => {
                opt.classList.remove('selected');
            });
            this.classList.add('selected');
            const radio = this.querySelector('input[type="radio"]');
            if (radio) {
                radio.checked = true;
            }
        });
    });

    const flashAlerts = document.querySelectorAll('.alert');
    flashAlerts.forEach(alert => {
        setTimeout(() => {
            alert.style.opacity = '0';
            setTimeout(() => alert.remove(), 300);
        }, 5000);
    });

    const searchInput = document.querySelector('.global-search');
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            const query = this.value.toLowerCase();
            const results = document.querySelectorAll('.searchable-item');
            results.forEach(item => {
                const text = item.textContent.toLowerCase();
                item.style.display = text.includes(query) ? '' : 'none';
            });
        });
    }

    const fileInput = document.getElementById('file-upload-input');
    const fileUpload = document.querySelector('.file-upload');
    
    if (fileInput && fileUpload) {
        fileInput.addEventListener('change', function() {
            if (this.files && this.files[0]) {
                fileUpload.querySelector('p').textContent = 'File selected: ' + this.files[0].name;
            }
        });

        fileUpload.addEventListener('click', function() {
            fileInput.click();
        });
    }

    const deleteButtons = document.querySelectorAll('.delete-btn');
    deleteButtons.forEach(btn => {
        btn.addEventListener('click', function(e) {
            if (!confirm('Are you sure you want to delete this item?')) {
                e.preventDefault();
            }
        });
    });

    const navItems = document.querySelectorAll('.nav-item');
    const currentPath = window.location.pathname;
    navItems.forEach(item => {
        if (item.getAttribute('href') === currentPath) {
            item.classList.add('active');
        }
    });

    const notificationItems = document.querySelectorAll('.notification-item');
    notificationItems.forEach(item => {
        item.addEventListener('click', function() {
            const badge = this.querySelector('.badge');
            if (badge) {
                badge.classList.remove('badge-danger');
                badge.classList.add('badge-success');
            }
        });
    });

    const contributionCards = document.querySelectorAll('.contribution-card');
    contributionCards.forEach(card => {
        const status = card.dataset.status;
        if (status === 'overdue') {
            card.classList.add('border-danger');
        }
    });

    const selectAllCheckbox = document.getElementById('select-all');
    if (selectAllCheckbox) {
        selectAllCheckbox.addEventListener('change', function() {
            const checkboxes = document.querySelectorAll('.item-checkbox');
            checkboxes.forEach(cb => {
                cb.checked = this.checked;
            });
        });
    }

    const tabs = document.querySelectorAll('.tab');
    tabs.forEach(tab => {
        tab.addEventListener('click', function() {
            const target = this.dataset.target;
            tabs.forEach(t => t.classList.remove('active'));
            this.classList.add('active');
            
            document.querySelectorAll('.tab-content').forEach(content => {
                content.style.display = 'none';
            });
            
            const targetContent = document.getElementById(target);
            if (targetContent) {
                targetContent.style.display = 'block';
            }
        });
    });

    const deadlineInputs = document.querySelectorAll('input[type="datetime-local"]');
    deadlineInputs.forEach(input => {
        const now = new Date();
        now.setMinutes(now.getMinutes() - now.getTimezoneOffset());
        input.min = now.toISOString().slice(0, 16);
    });
});
