document.addEventListener('DOMContentLoaded', () => {
    const toggleBtn = document.getElementById('toggle-visibility');
    const saldoText = document.getElementById('saldo-text');
    const saldoReal = "{{ saldo }}"; 

    toggleBtn.addEventListener('click', () => {
        if (saldoText.textContent === '*****') {
            saldoText.textContent = `$${saldoReal}`; 
            toggleBtn.innerHTML = '<i class="fas fa-eye-slash"></i>'; 
        } else {
            saldoText.textContent = '*****'; 
            toggleBtn.innerHTML = '<i class="fas fa-eye"></i>'; 
        }
    });
});

document.addEventListener('DOMContentLoaded', () => {
    const collapsibleButtons = document.querySelectorAll('[data-toggle="collapse"]');

    collapsibleButtons.forEach((button) => {
        button.addEventListener('click', () => {
            const target = document.querySelector(button.dataset.target);
            if (target.classList.contains('show')) {
                target.classList.remove('show');
            } else {
                target.classList.add('show'); 
            }
        });
    });
});

$(document).ready(function() {
    $('#debit-cards').on('shown.bs.collapse', function() {
        $('#debit-icon').removeClass('fa-chevron-down').addClass('fa-chevron-up'); 
    }).on('hidden.bs.collapse', function() {
        $('#debit-icon').removeClass('fa-chevron-up').addClass('fa-chevron-down'); 
    });
});

document.addEventListener('DOMContentLoaded', () => {
    const toggleBtn = document.getElementById('toggle-visibility');
    const saldoText = document.getElementById('saldo-text');
    const saldoReal = "{{ saldo }}";  // Asegúrate de que esta variable se pasa desde el backend.

    toggleBtn.addEventListener('click', () => {
        if (saldoText.textContent === '*****') {
            saldoText.textContent = `$${saldoReal}`;  // Mostrar saldo real
            toggleBtn.innerHTML = '<i class="fas fa-eye-slash"></i> Ocultar saldo';  // Cambiar icono y texto
        } else {
            saldoText.textContent = '*****';  // Ocultar saldo
            toggleBtn.innerHTML = '<i class="fas fa-eye"></i> Mostrar saldo';  // Cambiar icono y texto
        }
    });
});
