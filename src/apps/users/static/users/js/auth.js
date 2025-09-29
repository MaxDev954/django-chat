document.addEventListener("DOMContentLoaded", function () {
    const loginForm = document.getElementById("login-form");
    const signupForm = document.getElementById("signup-form");

    function getCSRFToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]').value;
    }

    function showFormErrors(form, errors) {
        // Clear previous errors
        form.querySelectorAll('.error-message').forEach(error => error.remove());

        // Check if form has form-errors div
        const formErrorsDiv = form.querySelector('#form-errors');
        if (formErrorsDiv) {
            formErrorsDiv.innerHTML = '';
        }

        if (Array.isArray(errors)){
            errors = {'detail': errors.join('\n')}
        }
        
        for (const [field, messages] of Object.entries(errors)) {
            if (field === 'non_field_errors' || field === 'detail') {
                const errorDiv = document.createElement('div');
                errorDiv.className = 'error-message';
                errorDiv.style.color = 'red';
                errorDiv.style.marginBottom = '10px';
                errorDiv.textContent = Array.isArray(messages) ? messages.join(', ') : messages;

                if (formErrorsDiv) {
                    formErrorsDiv.appendChild(errorDiv);
                } else {
                    form.insertBefore(errorDiv, form.firstChild);
                }
            } else {
                const fieldElement = form.querySelector(`#id_${field}`);
                if (fieldElement) {
                    const errorDiv = document.createElement('div');
                    errorDiv.className = 'error-message';
                    errorDiv.style.color = 'red';
                    errorDiv.style.fontSize = '0.9em';
                    errorDiv.textContent = Array.isArray(messages) ? messages.join(', ') : messages;

                    // If form-errors div exists, show field errors there too
                    if (formErrorsDiv) {
                        const fieldLabel = fieldElement.previousElementSibling?.textContent || field;
                        errorDiv.textContent = `${fieldLabel} ${errorDiv.textContent}`;
                        formErrorsDiv.appendChild(errorDiv);
                    } else {
                        fieldElement.parentNode.appendChild(errorDiv);
                    }
                }
            }
        }
    }

    if (loginForm) {
        loginForm.addEventListener("submit", async function (event) {
            event.preventDefault();

            const email = document.getElementById("id_email").value;
            const password = document.getElementById("id_password").value;

            if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
                showFormErrors(loginForm, {'email': ['Please enter a valid email address.']});
                return;
            }
            if (!password || password.length < 8) {
                showFormErrors(loginForm, {'password': ['Password must be at least 8 characters long.']});
                return;
            }

            try {
                const response = await fetch('/api/auth/login/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCSRFToken(),
                    },
                    body: JSON.stringify({
                        email: email,
                        password: password
                    }),
                });

                const data = await response.json();
                console.log(response.ok)
                console.log(response.statuss)
                if (response.ok) {
                    window.location.href = '/chat/select_room/';
                } else {
                    showFormErrors(loginForm, data);
                }
            } catch (error) {
                console.error('Login error:', error);
                showFormErrors(loginForm, {'detail': ['An error occurred. Please try again.']});
            }
        });
    }

    if (signupForm) {
        signupForm.addEventListener("submit", async function (event) {
            event.preventDefault();

            const firstName = document.getElementById("id_first_name").value;
            const lastName = document.getElementById("id_last_name").value;
            const email = document.getElementById("id_email").value;
            const password = document.getElementById("id_password").value;
            const password2 = document.getElementById("id_password2").value;

            if (!firstName || firstName.length < 2) {
                showFormErrors(signupForm, {'first_name': ['First name must be at least 2 characters long.']});
                return;
            }
            if (!lastName || lastName.length < 2) {
                showFormErrors(signupForm, {'last_name': ['Last name must be at least 2 characters long.']});
                return;
            }
            if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
                showFormErrors(signupForm, {'email': ['Please enter a valid email address.']});
                return;
            }
            if (!password || password.length < 8) {
                showFormErrors(signupForm, {'password': ['Password must be at least 8 characters long.']});
                return;
            }
            if (password !== password2) {
                showFormErrors(signupForm, {'password2': ['Passwords do not match.']});
                return;
            }

            try {
                const response = await fetch('/api/auth/register/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCSRFToken(),
                    },
                    body: JSON.stringify({
                        email: email,
                        first_name: firstName,
                        last_name: lastName,
                        password1: password,
                        password2: password2
                    }),
                });

                const data = await response.json();

                if (response.ok) {
                    window.location.href = '/chat/select_room/';
                } else {
                    showFormErrors(signupForm, data);
                }
            } catch (error) {
                console.error('Signup error:', error);
                showFormErrors(signupForm, {'detail': ['An error occurred. Please try again.']});
            }
        });
    }
});