/**
 * Food Tracker & UI Interactions
 * - Live Food Search Filter
 * - Live Serving/Nutrient Preview Chip
 * - Flash Message Auto-Dismiss
 * - Active Navigation Link Highlighting
 */

document.addEventListener('DOMContentLoaded', function () {
    // 1. Highlight Active Navbar Link
    var currentPath = window.location.pathname;
    var navLinks = document.querySelectorAll('.nav-links a');
    navLinks.forEach(function (link) {
        var href = link.getAttribute('href');
        if (href === currentPath || (href !== '/' && currentPath.indexOf(href) === 0)) {
            link.classList.add('active');
        }
    });

    // 2. Auto-Dismiss Flash Messages
    var alerts = document.querySelectorAll('.alert');
    alerts.forEach(function (alert) {
        // Add close button
        var closeBtn = document.createElement('button');
        closeBtn.className = 'alert-close';
        closeBtn.innerHTML = '&times;';
        closeBtn.title = 'Dismiss';
        closeBtn.addEventListener('click', function () {
            alert.style.opacity = '0';
            alert.style.transform = 'translateY(-6px)';
            setTimeout(function () { alert.remove(); }, 300);
        });
        alert.appendChild(closeBtn);

        // Auto-dismiss after 4.5 seconds
        setTimeout(function () {
            if (alert.parentElement) {
                alert.style.opacity = '0';
                alert.style.transform = 'translateY(-6px)';
                setTimeout(function () { alert.remove(); }, 300);
            }
        }, 4500);
    });

    // 3. Live Food Search Filter
    var searchInput = document.getElementById('food-search');
    var foodSelect = document.getElementById('food-select');
    var quantityInput = document.getElementById('quantity');

    if (searchInput && foodSelect) {
        var allOptions = Array.from(foodSelect.options);

        searchInput.addEventListener('input', function () {
            var query = searchInput.value.toLowerCase().trim();
            foodSelect.innerHTML = '';

            allOptions.forEach(function (option) {
                if (!query || option.text.toLowerCase().indexOf(query) !== -1) {
                    foodSelect.appendChild(option.cloneNode(true));
                }
            });

            if (foodSelect.options.length > 0) {
                foodSelect.selectedIndex = 0;
            }
            updateLivePreview();
        });
    }

    // 4. Live Food Selection Nutrient Preview
    var addBtn = document.querySelector('form[action*="food"] button[type="submit"]');
    if (foodSelect && addBtn) {
        var previewContainer = document.createElement('span');
        previewContainer.className = 'live-preview-chip';
        previewContainer.style.display = 'none';
        addBtn.parentElement.appendChild(previewContainer);

        function updateLivePreview() {
            var selectedOpt = foodSelect.options[foodSelect.selectedIndex];
            var qty = parseFloat(quantityInput ? quantityInput.value : 1) || 1;

            if (selectedOpt && selectedOpt.value) {
                var text = selectedOpt.text;
                // Parse calories from option text e.g. "Roti (1 piece, 70 kcal)"
                var match = text.match(/(\d+(?:\.\d+)?)\s*kcal/i);
                if (match) {
                    var calsPerUnit = parseFloat(match[1]);
                    var totalCals = Math.round(calsPerUnit * qty);
                    previewContainer.innerHTML = '⚡ <strong>' + qty + 'x</strong> = ~' + totalCals + ' kcal';
                    previewContainer.style.display = 'inline-flex';
                    return;
                }
            }
            previewContainer.style.display = 'none';
        }

        foodSelect.addEventListener('change', updateLivePreview);
        if (quantityInput) {
            quantityInput.addEventListener('input', updateLivePreview);
        }
        updateLivePreview();
    }
});
