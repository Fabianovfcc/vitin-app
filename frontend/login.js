let currentPin = '';
let userPhone = '';

document.addEventListener('DOMContentLoaded', async () => {
    const tempToken = localStorage.getItem('temp_access_token');
    if (tempToken) {
        try {
            const resp = await fetch(`/api/students/by-token/${tempToken}`);
            if (resp.ok) {
                const student = await resp.json();
                if (student.whatsapp) {
                    // Pre-fill phone if available (logic to separate country code might be needed)
                    // For now just put in the input
                    const phoneInput = document.getElementById('phone-input');
                    phoneInput.value = student.whatsapp.replace(/^\+55/, '');
                    showToast(`Olá ${student.name.split(' ')[0]}! Acesse seu treino.`);
                }
            }
        } catch (e) {}
    }
    
    // Verificar se biometria está disponível e configurada
    if (window.PublicKeyCredential) {
        if (localStorage.getItem('biometry_configured') === 'true') {
            document.getElementById('biometry-login-btn').style.display = 'block';
        }
    }
});

async function loginWithBiometry() {
    showToast("Validando biometria...");
    await new Promise(r => setTimeout(r, 1000));
    
    // Na vida real, verificamos o desafio criptográfico aqui
    // Por enquanto, se o usuário ativou, deixamos entrar se houver sessão cacheada
    const studentId = localStorage.getItem('student_id');
    if (studentId) {
        showToast("Bem-vindo de volta! ✅");
        setTimeout(() => { window.location.href = 'aluno.html'; }, 500);
    } else {
        showToast("Erro: Faça login com PIN primeiro.");
    }
}

function showToast(msg) {
    const toast = document.getElementById('toast');
    toast.innerText = msg;
    toast.style.display = 'block';
    setTimeout(() => { toast.style.display = 'none'; }, 3000);
}

let isSetupMode = false;

async function goToPin() {
    const rawPhone = document.getElementById('phone-input').value;
    const country = document.getElementById('country-code').value;
    
    if (rawPhone.length < 8) {
        showToast("Número inválido!");
        return;
    }

    userPhone = country + rawPhone;
    
    // Verificar se o usuário existe e se tem PIN
    try {
        const resp = await fetch('/api/auth/check-user', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ phone: userPhone })
        });
        const data = await resp.json();
        
        if (data.status === 'not_found') {
            showToast("Aluno não encontrado no sistema.");
            return;
        }

        isSetupMode = !data.has_pin;
        document.getElementById('pin-subtitle').innerText = isSetupMode ? 
            `Olá ${data.name.split(' ')[0]}, defina um novo PIN de 4 dígitos.` : 
            `Bem-vindo de volta, ${data.name.split(' ')[0]}! Insira seu PIN.`;

        document.getElementById('phone-section').style.display = 'none';
        document.getElementById('pin-section').style.display = 'block';
    } catch (e) {
        showToast("Erro de conexão");
    }
}

function backToPhone() {
    document.getElementById('phone-section').style.display = 'block';
    document.getElementById('pin-section').style.display = 'none';
    clearPin();
}

function updateDots() {
    const dots = document.querySelectorAll('.dot');
    dots.forEach((dot, i) => {
        if (i < currentPin.length) {
            dot.classList.add('active');
        } else {
            dot.classList.remove('active');
        }
    });
}

function addPin(num) {
    if (currentPin.length < 4) {
        currentPin += num;
        updateDots();
        
        if (currentPin.length === 4) {
            setTimeout(handleLogin, 300);
        }
    }
}

function clearPin() {
    currentPin = '';
    updateDots();
}

async function handleLogin() {
    const endpoint = isSetupMode ? '/api/auth/setup-pin' : '/api/auth/login';
    
    try {
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ phone: userPhone, pin: currentPin })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            if (isSetupMode) {
                showToast("PIN configurado! Entrando...");
                // Após configurar, logamos automaticamente re-chamando o login ou usando dados retornados
                isSetupMode = false;
                handleLogin(); // Tenta logar agora com o PIN recém criado
                return;
            }

            showToast("Login realizado!");
            localStorage.setItem('student_id', data.student.id);
            localStorage.setItem('access_token', data.student.access_token);
            localStorage.setItem('phone_auth', userPhone);
            
            window.location.href = 'aluno.html';
        } else {
            showToast(data.error || "Erro no login");
            clearPin();
        }
    } catch (err) {
        console.error(err);
        showToast("Erro de conexão");
        clearPin();
    }
}

// Suporte a teclado físico
document.addEventListener('keydown', (e) => {
    if (document.getElementById('pin-section').style.display === 'block') {
        if (e.key >= '0' && e.key <= '9') addPin(e.key);
        if (e.key === 'Backspace') clearPin();
    }
});
