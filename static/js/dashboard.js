/**
 * BlogAutomationAgent (ZYGA) Dashboard JavaScript
 * Handles interactive UI elements and dashboard functionality
 */

// Initialize tooltips when the DOM is fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize Bootstrap tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl, {
            boundary: document.body
        });
    });

    // Initialize popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Set current year in footer
    const yearElement = document.querySelector('.footer .text-muted');
    if (yearElement) {
        const currentYear = new Date().getFullYear();
        yearElement.innerHTML = yearElement.innerHTML.replace(/\d{4}/, currentYear);
    }

    // Format JSON in textareas
    const jsonTextareas = document.querySelectorAll('textarea[id="categories"]');
    jsonTextareas.forEach(textarea => {
        try {
            const content = textarea.value;
            if (content && content.trim() !== '') {
                const jsonObj = JSON.parse(content);
                textarea.value = JSON.stringify(jsonObj, null, 2);
            }
        } catch (e) {
            console.warn('Failed to format JSON:', e);
        }
    });

    // Add confirmation for delete buttons
    const deleteButtons = document.querySelectorAll('.btn-delete-confirm');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            if (!confirm('Are you sure you want to delete this item? This action cannot be undone.')) {
                e.preventDefault();
            }
        });
    });

    // Process blog buttons (if present on the page)
    const processButtons = document.querySelectorAll('.process-blog');
    if (processButtons.length > 0) {
        processButtons.forEach(button => {
            button.addEventListener('click', function() {
                const blogId = this.getAttribute('data-blog-id');
                const originalHtml = this.innerHTML;
                
                // Update button to loading state
                this.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
                this.disabled = true;
                
                // Send API request
                fetch(`/api/process_blog/${blogId}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        // Success state
                        this.innerHTML = '<i class="fas fa-check"></i> Success';
                        this.classList.remove('btn-primary');
                        this.classList.add('btn-success');
                        
                        // Reset after delay
                        setTimeout(() => {
                            this.innerHTML = originalHtml;
                            this.classList.remove('btn-success');
                            this.classList.add('btn-primary');
                            this.disabled = false;
                        }, 3000);
                    } else {
                        // Error state
                        this.innerHTML = '<i class="fas fa-times"></i> Failed';
                        this.classList.remove('btn-primary');
                        this.classList.add('btn-danger');
                        
                        // Add tooltip with error message
                        this.setAttribute('data-bs-toggle', 'tooltip');
                        this.setAttribute('title', data.message || 'Unknown error');
                        new bootstrap.Tooltip(this).show();
                        
                        // Reset after delay
                        setTimeout(() => {
                            this.innerHTML = originalHtml;
                            this.classList.remove('btn-danger');
                            this.classList.add('btn-primary');
                            this.disabled = false;
                        }, 3000);
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    
                    // Error state
                    this.innerHTML = '<i class="fas fa-times"></i> Error';
                    this.classList.remove('btn-primary');
                    this.classList.add('btn-danger');
                    
                    // Reset after delay
                    setTimeout(() => {
                        this.innerHTML = originalHtml;
                        this.classList.remove('btn-danger');
                        this.classList.add('btn-primary');
                        this.disabled = false;
                    }, 3000);
                });
            });
        });
    }

    // Auto-refresh dashboard stats if on dashboard page
    if (window.location.pathname === '/' || window.location.pathname === '/dashboard') {
        // Set a timer to refresh the page every 5 minutes
        setTimeout(() => {
            window.location.reload();
        }, 5 * 60 * 1000); // 5 minutes
    }
});

// Format timestamp display
function formatTimestamp(timestamp) {
    if (!timestamp) return 'N/A';
    
    const date = new Date(timestamp);
    return date.toLocaleString();
}

// Dynamic select for categories based on selected blog
function updateCategoriesForBlog(blogId, categorySelectId) {
    const categorySelect = document.getElementById(categorySelectId);
    if (!categorySelect) return;
    
    // Clear current options
    categorySelect.innerHTML = '<option value="" selected disabled>Select category</option>';
    
    if (!blogId) return;
    
    // TODO: In a future enhancement, we could fetch categories via API
    // For now, this is a placeholder for that functionality
    fetch(`/api/blogs/${blogId}/categories`)
        .then(response => response.json())
        .then(categories => {
            categories.forEach(category => {
                const option = document.createElement('option');
                option.value = category.id;
                option.textContent = category.name;
                categorySelect.appendChild(option);
            });
        })
        .catch(error => {
            console.error('Error fetching categories:', error);
        });
}
