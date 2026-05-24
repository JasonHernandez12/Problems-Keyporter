document.addEventListener('DOMContentLoaded', () => {
    const submitBtn = document.getElementById('recovery-submit');
    const btnText = document.getElementById('recovery-btn-text');
    const emailInput = document.getElementById('recovery-email');
    const alertBox = document.getElementById('recovery-alert');

    const showAlert = (message, type) => {
        alertBox.innerHTML = `<div class="alert alert-${type} py-2 small">${message}</div>`;
    };

    const validateEmail = (email) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);

    const resetButton = () => {
        btnText.innerHTML = 'Enviar enlace <i class="bi bi-send ms-2"></i>';
        submitBtn.disabled = false;
    };

    submitBtn.addEventListener('click', async () => {
        const email = emailInput.value.trim();
        alertBox.innerHTML = '';

        if (!email || !validateEmail(email)) {
            showAlert('Por favor ingresa un correo válido.', 'warning');
            return;
        }

        // Estado: procesando
        submitBtn.disabled = true;
        btnText.innerHTML = '<span class="spinner-mini"></span>Procesando...';

        try {
            const response = await fetch('/recover-password', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email })
            });

            const data = await response.json();

            if (response.ok && data.success) {
                showAlert('Correo enviado. Revisa tu bandeja de entrada.', 'success');
                btnText.innerHTML = 'Enviado <i class="bi bi-check-circle ms-2"></i>';
                emailInput.value = '';

                setTimeout(() => {
                    const modal = bootstrap.Modal.getInstance(document.getElementById('recoveryModal'));
                    if (modal) modal.hide();
                    resetButton();
                    alertBox.innerHTML = '';
                }, 2500);
            } else {
                showAlert(data.message || 'Error al procesar la solicitud.', 'danger');
                resetButton();
            }
        } catch (err) {
            showAlert('No se pudo conectar con el servidor.', 'danger');
            resetButton();
        }
    });
});