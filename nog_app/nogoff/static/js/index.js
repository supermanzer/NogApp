// alert("Hello, world!");

document.addEventListener("DOMContentLoaded", function () {
    const nogForm = document.querySelector("form.nog-form");
    if (!nogForm) return;
    const errorDiv = document.querySelector(".errors");
    const submitBtn = nogForm.querySelector('input[type="submit"], button[type="submit"]');
    const maxVotes = parseInt(nogForm.getAttribute("data-nvotes"), 10);

    // Add increment/decrement button functionality
    nogForm.querySelectorAll('.vote-input-group').forEach(group => {
        const input = group.querySelector('input[type="number"]');
        const decBtn = group.querySelector('.vote-btn[data-action="decrement"]');
        const incBtn = group.querySelector('.vote-btn[data-action="increment"]');
        if (decBtn) {
            decBtn.addEventListener('click', function () {
                let val = parseInt(input.value, 10) || 0;
                if (val > 0) {
                    input.value = val - 1;
                    input.dispatchEvent(new Event('input', { bubbles: true }));
                }
            });
        }
        if (incBtn) {
            incBtn.addEventListener('click', function () {
                let val = parseInt(input.value, 10) || 0;
                input.value = val + 1;
                input.dispatchEvent(new Event('input', { bubbles: true }));
            });
        }
    });

    function showError(message) {
        if (!errorDiv) return;
        errorDiv.innerHTML = `<span class="error-msg">${message}</span><span class="error-close" title="Dismiss">&times;</span>`;
        errorDiv.style.display = "flex";
        if (submitBtn) submitBtn.disabled = true;
        // Add click handler for close icon
        const closeBtn = errorDiv.querySelector('.error-close');
        if (closeBtn) {
            closeBtn.onclick = function () {
                errorDiv.style.display = "none";
                errorDiv.innerHTML = '';
            };
        }
    }

    nogForm.addEventListener("input", function (e) {
        const voteInputs = nogForm.querySelectorAll('input[type="number"]');
        let totalVotes = 0;
        voteInputs.forEach(input => {
            const val = parseInt(input.value, 10);
            if (!isNaN(val) && val > 0) totalVotes += val;
        });

        if (totalVotes > maxVotes) {
            showError(`You may only cast a total of ${maxVotes} votes.`);
        } else {
            if (errorDiv) {
                errorDiv.style.display = "none";
                errorDiv.innerHTML = '';
            }
            if (submitBtn) submitBtn.disabled = false;
        }
    });

    function showModal() {
        const modal = document.getElementById('voteSuccessModal');
        if (modal) {
            modal.classList.add('show');
        }
    }

    nogForm.addEventListener("submit", function (e) {
        e.preventDefault();

        if ((submitBtn && submitBtn.disabled) || (errorDiv && errorDiv.style.display === "flex")) {
            return;
        }

        const formData = new FormData(nogForm);

        // Disable the submit button during submission
        if (submitBtn) submitBtn.disabled = true;

        fetch(nogForm.action, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    showModal();
                } else {
                    showError(data.message || 'An error occurred while submitting your votes');
                    if (submitBtn) submitBtn.disabled = false;
                }
            })
            .catch(error => {
                showError('An error occurred while submitting your votes. Please try again.');
                if (submitBtn) submitBtn.disabled = false;
            });
    });

    const resetBtn = document.getElementById("reset-votes");
    if (resetBtn) {
        resetBtn.addEventListener("click", function () {
            // Get the current URL and extract the event ID
            const pathParts = window.location.pathname.split('/');
            const eventId = pathParts[pathParts.indexOf("event") + 1];

            // Disable the reset button and show loading state
            resetBtn.disabled = true;
            resetBtn.textContent = 'Resetting...';

            // Get CSRF token
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
            if (!csrfToken) {
                showError('CSRF token not found. Please refresh the page.');
                resetBtn.disabled = false;
                resetBtn.textContent = 'Reset Votes';
                return;
            }

            // Make the AJAX request
            fetch(`/event/${eventId}/reset-votes`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfToken.value,
                    'Content-Type': 'application/json'
                },
            })
                .then(response => {
                    if (!response.ok) {
                        // Try to get JSON error message, fall back to status text
                        return response.json()
                            .catch(() => ({
                                message: `Server error: ${response.statusText || response.status}`
                            }))
                            .then(data => Promise.reject(data));
                    }
                    // On success, reload the page
                    window.location.reload();
                })
                .catch(error => {
                    // Handle network errors
                    if (error instanceof TypeError) {
                        showError('Network error. Please check your connection.');
                    } else {
                        // Use the existing showError function for consistency
                        showError(error.message || 'An error occurred while resetting votes');
                    }
                    // Reset button state
                    resetBtn.disabled = false;
                    resetBtn.textContent = 'Reset Votes';
                });
        });
    }
});