document.addEventListener("DOMContentLoaded", function () {
    const loginForm = document.getElementById("login-form");
    const signupForm = document.getElementById("signup-form");

    if (loginForm) {
        loginForm.addEventListener("submit", function (event) {
            const email = document.getElementById("id_email").value;
            const password = document.getElementById("id_password").value;

            if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
                alert("Please enter a valid email address.");
                event.preventDefault();
            } else if (!password || password.length < 8) {
                alert("Password must be at least 8 characters long.");
                event.preventDefault();
            }
        });
    }

    if (signupForm) {
        signupForm.addEventListener("submit", function (event) {
            const firstName = document.getElementById("id_first_name").value;
            const lastName = document.getElementById("id_last_name").value;
            const email = document.getElementById("id_email").value;
            const password = document.getElementById("id_password").value;
            const password2 = document.getElementById("id_password2").value;

            if (!firstName || firstName.length < 2) {
                alert("First name must be at least 2 characters long.");
                event.preventDefault();
            } else if (!lastName || lastName.length < 2) {
                alert("Last name must be at least 2 characters long.");
                event.preventDefault();
            } else if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
                alert("Please enter a valid email address.");
                event.preventDefault();
            } else if (!password || password.length < 8) {
                alert("Password must be at least 8 characters long.");
                event.preventDefault();
            } else if (password !== password2) {
                alert("Passwords do not match.");
                event.preventDefault();
            }
        });
    }
});