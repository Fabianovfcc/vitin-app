let currentPin = '';
let userPhone = '';
let currentRole = 'aluno';

document.addEventListener('DOMContentLoaded', async () => {
    const tempToken = localStorage.getItem('temp_access_token');
    if (tempToken) {
        try {
            const resp = await fetch(`/api/students/by-token/${tempToken}`);
            if (resp.ok) {
                const student = await resp.json();
                if (student.whatsapp) {
                    const phoneInput = document.getElementById('phone-input');
                    // Tenta extrair o número sem +55 se for BR
                    phoneInput.value = student.whatsapp.replace(/^\+55/, '');
                    showToast(`Olá ${student.name.split(' ')[0]}! Acesse seu treino.`);
                }
            }
        } catch (e) {}
    }
    
    if (window.PublicKeyCredential) {
        if (localStorage.getItem('biometry_configured') === 'true') {
            document.getElementById('biometry-login-btn').style.display = 'block';
        }
    }
});

window.switchTab = (role) => {
    currentRole = role;
    const isAlu = role === 'aluno';
    
    // UI Tabs
    document.getElementById('tab-aluno').style.background = isAlu ? 'var(--primary)' : 'transparent';
    document.getElementById('tab-aluno').style.color = isAlu ? 'white' : 'var(--text-secondary)';
    document.getElementById('tab-prof').style.background = !isAlu ? 'var(--primary)' : 'transparent';
    document.getElementById('tab-prof').style.color = !isAlu ? 'white' : 'var(--text-secondary)';
    
    // Labels
    document.getElementById('welcome-msg').innerText = isAlu ? 'Bem-vindo!' : 'Painel do Professor';
    document.getElementById('subtitle-msg').innerText = isAlu ? 
        'Insira seu número para acessar seus treinos.' : 
        'Identifique-se para gerenciar seus alunos.';
    
    // Password field for Professor
    document.getElementById('prof-password-group').style.display = isAlu ? 'none' : 'flex';
    document.getElementById('main-login-btn').innerText = isAlu ? 'Continuar' : 'Acessar Painel 🚀';
};

window.handleContinue = () => {
    if (currentRole === 'aluno') {
        goToPin();
    } else {
        handleProfessorLogin();
    }
};

async function handleProfessorLogin() {
    const rawPhone = document.getElementById('phone-input').value;
    const country = document.getElementById('country-code').value;
    const password = document.getElementById('password-input').value;
    
    if (rawPhone.length < 8 || !password) {
        showToast("WhatsApp e Senha são obrigatórios!");
        return;
    }

    const fullPhone = country + rawPhone.replace(/\D/g, '');
    const compositeToken = `${fullPhone}:${password}`;

    showToast("Autenticando...");
    
    // Armazena temporariamente para testar acesso
    localStorage.setItem('adminToken', compositeToken);
    
    // Redireciona para index.html que fará a validação final
    window.location.href = 'index.html';
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

    userPhone = country + rawPhone.replace(/\D/g, '');
    
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
                isSetupMode = false;
                handleLogin(); 
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

document.addEventListener('keydown', (e) => {
    if (document.getElementById('pin-section').style.display === 'block') {
        if (e.key >= '0' && e.key <= '9') addPin(e.key);
        if (e.key === 'Backspace') clearPin();
    }
});
