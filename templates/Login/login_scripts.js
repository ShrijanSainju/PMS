        // Tab switching functionality
        function switchTab(tab) {
            // Update tab buttons
            document.querySelectorAll('.tab-button').forEach(btn => btn.classList.remove('active'));
            event.target.classList.add('active');

            // Update form sections
            document.querySelectorAll('.form-section').forEach(section => section.classList.remove('active'));
            document.getElementById(tab + '-form').classList.add('active');
        }

        // Password visibility toggle
        function togglePassword(inputId) {
            const input = document.getElementById(inputId);
            const button = input.nextElementSibling;
            
            if (input.type === 'password') {
                input.type = 'text';
                button.textContent = '🙈';
            } else {
                input.type = 'password';
                button.textContent = '👁️';
            }
        }

        // Login form handler
        function handleLogin(event) {
            event.preventDefault();
            
            const formData = new FormData(event.target);
            const loginData = {
                role: formData.get('role'),
                email: formData.get('email'),
                password: formData.get('password')
            };

            console.log('Login attempt:', loginData);
            
            // Replace this with your actual login logic
            alert(`Login attempt for ${loginData.role}: ${loginData.email}`);
        }

        // Sign up form handler
        function handleSignup(event) {
            event.preventDefault();
            
            const formData = new FormData(event.target);
            const signupData = {
                role: formData.get('role'),
                firstName: formData.get('firstName'),
                lastName: formData.get('lastName'),
                email: formData.get('email'),
                password: formData.get('password'),
                confirmPassword: formData.get('confirmPassword'),
                terms: formData.get('terms')
            };

            // Validate passwords match
            if (signupData.password !== signupData.confirmPassword) {
                document.getElementById('password-error').style.display = 'block';
                return;
            } else {
                document.getElementById('password-error').style.display = 'none';
            }

            // Validate terms acceptance
            if (!signupData.terms) {
                alert('Please agree to the terms and conditions');
                return;
            }

            console.log('Signup attempt:', signupData);
            
            // Replace this with your actual signup logic
            alert(`Account created for ${signupData.role}: ${signupData.firstName} ${signupData.lastName}`);
        }

        // Real-time password confirmation validation
        document.addEventListener('DOMContentLoaded', function() {
            const password = document.getElementById('signup-password');
            const confirmPassword = document.getElementById('confirm-password');
            const errorMessage = document.getElementById('password-error');

            function validatePasswords() {
                if (confirmPassword.value && password.value !== confirmPassword.value) {
                    errorMessage.style.display = 'block';
                } else {
                    errorMessage.style.display = 'none';
                }
            }

            password.addEventListener('input', validatePasswords);
            confirmPassword.addEventListener('input', validatePasswords);
        });