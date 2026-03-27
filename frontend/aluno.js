let currentWorkout = null;
let completedSets = {};
let currentDay = 'seg';
let currentStudentId = null;
let currentStudentName = '';
let currentPlanType = 'free'; // default
let fullCatalog = [];

// ────────────────────────────────────────
// INICIALIZAÇÃO: Token e Isolamento Total
// ────────────────────────────────────────
document.addEventListener('DOMContentLoaded', async () => {
    // 1. Verificar se há sessão ativa via PIN
    const sessionStudentId = localStorage.getItem('student_id');
    const sessionToken = localStorage.getItem('access_token');
    
    // Se não houver sessão ativa, precisamos identificar o aluno
    if (!sessionStudentId || !sessionToken) {
        // Tentar identificar se veio via link com token
        const pathParts = window.location.pathname.split('/').filter(p => p !== "");
        let urlToken = null;
        const alunoIdx = pathParts.indexOf('aluno');
        if (alunoIdx !== -1 && pathParts[alunoIdx + 1]) {
            urlToken = pathParts[alunoIdx + 1];
        } else {
            const urlParams = new URLSearchParams(window.location.search);
            urlToken = urlParams.get('token');
        }

        if (urlToken) {
            // Se veio com token, guardamos o token temporariamente para o login associar
            localStorage.setItem('temp_access_token', urlToken);
        }
        
        // Redirecionar para login
        console.log("Sem sessão ativa. Redirecionando para login...");
        window.location.href = 'login.html';
        return;
    }

    let token = sessionToken;
    currentStudentId = sessionStudentId;
    
    // Navegação por abas
window.switchStudentTab = (tab) => {
        const sections = ['workout-content', 'discover-content', 'feed-content', 'stats-content', 'my-protocols-content'];
        sections.forEach(s => {
            const el = document.getElementById(s);
            if (el) el.classList.add('hidden');
        });
        
        const emptyState = document.getElementById('empty-state');
        const daySelector = document.getElementById('day-selector-aluno');
        document.querySelectorAll('.student-nav-btn').forEach(b => b.classList.remove('active'));
        
        if (tab === 'workout') {
            const wc = document.getElementById('workout-content');
            if (wc) wc.classList.remove('hidden');
            if (daySelector) daySelector.classList.remove('hidden');
            if (!currentWorkout && emptyState) emptyState.classList.remove('hidden');
            else if (emptyState) { emptyState.classList.add('hidden'); renderWorkout(); }
        } else if (tab === 'discover') {
            const dc = document.getElementById('discover-content');
            if (dc) dc.classList.remove('hidden');
            if (emptyState) emptyState.classList.add('hidden');
            if (daySelector) daySelector.classList.add('hidden');
            loadCatalog();
        } else if (tab === 'feed') {
            const fc = document.getElementById('feed-content');
            if (fc) fc.classList.remove('hidden');
            if (emptyState) emptyState.classList.add('hidden');
            if (daySelector) daySelector.classList.add('hidden');
            loadFeed();
        } else if (tab === 'stats') {
            const sc = document.getElementById('stats-content');
            if (sc) sc.classList.remove('hidden');
            if (emptyState) emptyState.classList.add('hidden');
            if (daySelector) daySelector.classList.add('hidden');
            applyPlanRestrictions(); // Carrega histórico e renderiza charts
            trackConversionEvent('open_stats_tab');
        } else if (tab === 'my-protocols') {
            const mpc = document.getElementById('my-protocols-content');
            if (mpc) mpc.classList.remove('hidden');
            if (emptyState) emptyState.classList.add('hidden');
            if (daySelector) daySelector.classList.add('hidden');
            loadMyProtocols();
        }

        const activeBtn = document.getElementById(`tab-${tab}`);
        if (activeBtn) activeBtn.classList.add('active');
    };

    try {
        const res = await fetch(`/api/students/by-token/${token}?t=${Date.now()}`);
    if (res.ok) {
        let studentData = await res.json();
        const student = Array.isArray(studentData) ? studentData[0] : studentData;
        console.log("VitinDebug: Dados do Aluno Recebidos:", student);
        
        if (!student || !student.id) {
            console.error("VitinDebug: Falha ao carregar aluno", studentData);
            showInvalidAccess();
            return;
        }

        currentStudentId = student.id;
        currentStudentName = student.name || "Aluno";
        currentPlanType = student.plan_type || 'free';
        
        applyPlanRestrictions();
        updateStreak(); 
        checkAnamnesis(student); 

        const dateEl = document.getElementById('workout-date');
        if (dateEl) dateEl.innerText = `Olá, ${currentStudentName}! 💪`;
        
        // Sugerir ativação de Biometria caso suportado e não configurado
        if (window.PublicKeyCredential && !localStorage.getItem('biometry_configured')) {
            showBiometryInvite();
        }
        
        const selectorEl = document.getElementById('student-selector');
        if (selectorEl) selectorEl.classList.add('hidden');
        
        loadChallenge();
        loadWorkout(student.id);
        checkNotifications();
    } else {
        showInvalidAccess();
    }
    } catch (e) {
        console.error("VitinDebug: Erro crítico na inicialização do aluno", e);
        showInvalidAccess();
    }
});

// ────────────────────────────────────────
// ANAMNESE E COLETA DE DADOS
// ────────────────────────────────────────
function checkAnamnesis(student) {
    if (!student.weight || !student.height) {
        document.getElementById('modal-anamnesis').classList.remove('hidden');
    }
}

window.submitAnamnesis = async () => {
    const weight = document.getElementById('q-weight').value;
    const height = document.getElementById('q-height').value;
    const goal = document.getElementById('q-goal').value;

    if (!weight || !height) return alert('Por favor, preencha peso e altura.');

    try {
        await fetch('/api/students/profile', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                id: currentStudentId,
                weight: weight,
                height: height,
                goal: goal
            })
        });
        document.getElementById('modal-anamnesis').classList.add('hidden');
        alert('Perfil atualizado! Bons treinos! 🚀');
    } catch (e) {
        alert('Erro ao salvar. Pode continuar o treino normalmente.');
        document.getElementById('modal-anamnesis').classList.add('hidden');
    }
};

// ────────────────────────────────────────
// GAMIFICAÇÃO: OFENSIVAS (STREAKS)
// ────────────────────────────────────────
function updateStreak() {
    const today = new Date().toLocaleDateString('pt-BR');
    let data;
    try {
        data = JSON.parse(localStorage.getItem(`vitin_streak_${currentStudentId}`)) || { count: 0, lastDate: '' };
    } catch (e) {
        data = { count: 0, lastDate: '' };
    }
    
    // Se já treinou hoje, não faz nada
    if (data.lastDate === today) {
        document.getElementById('streak-count').innerText = data.count;
        return;
    }

    const last = data.lastDate ? new Date(data.lastDate.split('/').reverse().join('-')) : null;
    const now = new Date();
    const diffDays = last ? Math.floor((now - last) / (1000 * 60 * 60 * 24)) : 0;

    if (diffDays === 1) {
        // Sequência mantida
        document.getElementById('streak-count').innerText = data.count;
    } else if (diffDays > 1 || !last) {
        // Quebrou a sequência ou primeiro treino
        data.count = data.count > 0 ? data.count : 0;
        document.getElementById('streak-count').innerText = data.count;
    }
    
    // O incremento real acontece no finishWorkout()
    document.getElementById('streak-count').innerText = data.count;
}

function incrementStreak() {
    const today = new Date().toLocaleDateString('pt-BR');
    let data = JSON.parse(localStorage.getItem(`vitin_streak_${currentStudentId}`)) || { count: 0, lastDate: '' };
    
    if (data.lastDate !== today) {
        data.count++;
        data.lastDate = today;
        localStorage.setItem(`vitin_streak_${currentStudentId}`, JSON.stringify(data));
        document.getElementById('streak-count').innerText = data.count;
    }
}

function showBiometryInvite() {
    if (document.getElementById('biometry-invite')) return;
    
    const invite = document.createElement('div');
    invite.id = 'biometry-invite';
    invite.className = 'glass-card animate-fade-in';
    invite.style.cssText = 'margin: 1rem; padding: 1.2rem; background: linear-gradient(135deg, rgba(0,122,255,0.1) 0%, rgba(0,199,190,0.1) 100%); border: 1px solid rgba(0,122,255,0.3);';
    invite.innerHTML = `
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <div>
                <h4 style="margin:0; color:var(--primary);">Acesso Rápido ⚡</h4>
                <p style="margin:4px 0 0; font-size:0.8rem; color:var(--text-secondary);">Deseja ativar o Face ID / Digital para os próximos acessos?</p>
            </div>
            <button class="btn-primary" style="width:auto; padding:8px 16px; font-size:0.8rem;" onclick="configureBiometry()">Ativar</button>
        </div>
    `;
    const header = document.querySelector('.progress-section');
    if (header) header.parentNode.insertBefore(invite, header);
}

window.configureBiometry = async () => {
    try {
        // Simulação de WebAuthn por enquanto (para Wow factor)
        // No futuro, aqui entra a chamada real navigator.credentials.create()
        showToast("Solicitando permissão do sistema...");
        
        // Simulando delay de hardware
        await new Promise(r => setTimeout(r, 1500));
        
        localStorage.setItem('biometry_configured', 'true');
        document.getElementById('biometry-invite').remove();
        showToast("Biometria configurada com sucesso! ✅");
        
    } catch (e) {
        showToast("Erro ao configurar biometria.");
    }
};

function showToast(msg) {
    const toast = document.createElement('div');
    toast.style.cssText = 'position:fixed; bottom:100px; left:50%; transform:translateX(-50%); background:rgba(255,255,255,0.9); color:black; padding:12px 24px; border-radius:20px; font-weight:600; z-index:9999; box-shadow:0 10px 30px rgba(0,0,0,0.5);';
    toast.innerText = msg;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
}

// ────────────────────────────────────────
// DESAFIOS GLOBAIS
// ────────────────────────────────────────
async function loadChallenge() {
    try {
        const res = await fetch('/api/challenges/active');
        if (res.ok) {
            const challenge = await res.json();
            const container = document.getElementById('challenge-container');
            container.innerHTML = `
                <div class="challenge-pill glass-card">
                    <span class="challenge-icon">🏆</span>
                    <div>
                        <h4 class="challenge-label">Desafio da Semana</h4>
                        <h3 class="challenge-title">${challenge.title}</h3>
                        <p class="challenge-desc">${challenge.description}</p>
                    </div>
                </div>
            `;
        }
    } catch (e) { /* sem desafio ativo */ }
}

// ────────────────────────────────────────
// NOTIFICAÇÕES DO ALUNO
// ────────────────────────────────────────
async function checkNotifications() {
    if (!currentStudentId) return;
    try {
        const res = await fetch(`/api/notifications/unread-count/aluno?student_id=${currentStudentId}&t=${Date.now()}`);
        const data = await res.json();
        const alert = document.getElementById('new-workout-alert');
        if (data.count > 0) {
            alert.classList.remove('hidden');
        } else {
            alert.classList.add('hidden');
        }
    } catch (e) { /* silêncio */ }
}

window.dismissAlert = async () => {
    document.getElementById('new-workout-alert').classList.add('hidden');
    await fetch('/api/notifications/mark-read', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ role: 'aluno', student_id: currentStudentId })
    });
};

// ────────────────────────────────────────
// CARREGAMENTO DE TREINO
// ────────────────────────────────────────
async function loadWorkout(studentId) {
    try {
        const response = await fetch(`/api/workouts/${studentId}?t=${Date.now()}`);
        if (response.ok) {
            currentWorkout = await response.json();
            document.getElementById('day-selector-aluno').classList.remove('hidden');
            await loadProgress();
            renderWorkout();
        } else {
            currentWorkout = null;
            showEmptyState();
        }
    } catch (error) {
        showEmptyState();
    }
}

// ────────────────────────────────────────
// PERSISTÊNCIA DE PROGRESSO 
// ────────────────────────────────────────
async function loadProgress() {
    if (!currentStudentId) return;
    try {
        const res = await fetch(`/api/progress/${currentStudentId}/${currentDay}`);
        if (res.ok) {
            const saved = await res.json();
            Object.keys(saved).forEach(key => {
                completedSets[key] = saved[key];
            });
        }
    } catch (e) { /* silêncio */ }
}

async function saveProgress() {
    if (!currentStudentId) return;
    const dayProgress = {};
    Object.keys(completedSets).forEach(key => {
        if (key.startsWith(currentDay + '-')) {
            dayProgress[key] = completedSets[key];
        }
    });
    try {
        await fetch(`/api/progress/${currentStudentId}/${currentDay}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ completedSets: dayProgress })
        });
    } catch (e) { /* silêncio */ }
}

// Day Tabs setup
document.querySelectorAll('.day-tab').forEach(tab => {
    tab.onclick = async () => {
        document.querySelectorAll('.day-tab').forEach(t => t.classList.remove('active'));
        tab.classList.add('active');
        currentDay = tab.dataset.day;
        await loadProgress();
        renderWorkout();
    };
});

function showEmptyState() {
    document.getElementById('empty-state').classList.remove('hidden');
    document.getElementById('workout-content').classList.add('hidden');
}

function renderWorkout() {
    if (!currentWorkout) return showEmptyState();

    const dayExercises = currentWorkout.weeklyWorkouts 
        ? currentWorkout.weeklyWorkouts[currentDay] 
        : (currentDay === 'seg' ? currentWorkout.exercises : []);
    const dayCardio = currentWorkout.weeklyCardio 
        ? currentWorkout.weeklyCardio[currentDay] 
        : null;

    if ((!dayExercises || dayExercises.length === 0) && (!dayCardio || !dayCardio.type)) {
        return showEmptyState();
    }

    document.getElementById('empty-state').classList.add('hidden');
    document.getElementById('workout-content').classList.remove('hidden');
    
    const dayNames = { seg: 'Segunda', ter: 'Terça', qua: 'Quarta', qui: 'Quinta', sex: 'Sexta', sab: 'Sábado', dom: 'Domingo' };
    document.getElementById('workout-date').innerText = `Treino de ${dayNames[currentDay]}`;

    // Render Cardio
    const cardioSection = document.getElementById('cardio-content');
    if (dayCardio && dayCardio.type) {
        cardioSection.classList.remove('hidden');
        document.getElementById('cardio-info').innerText = `${dayCardio.type} - ${dayCardio.time} minutos`;
    } else {
        cardioSection.classList.add('hidden');
    }

    // Render Exercises (Redesign Elite)
    const container = document.getElementById('workout-exercises');
    container.innerHTML = '';
    
    if (dayExercises) {
        dayExercises.forEach((ex, index) => {
            const globalIdx = `${currentDay}-${index}`;
            completedSets[globalIdx] = completedSets[globalIdx] || Array(parseInt(ex.sets)).fill(false);

            const card = document.createElement('div');
            card.className = 'exercise-card-elite animate-fade-in';
            
            const setsHTML = completedSets[globalIdx].map((done, setIdx) => `
                <button class="set-pill ${done ? 'active' : ''}" onclick="toggleSet('${globalIdx}', ${setIdx})">
                    ${done ? '✓' : setIdx + 1}
                </button>
            `).join('');

            card.innerHTML = `
                <div class="exercise-card-header">
                    <h3 class="exercise-card-title">${ex.name}</h3>
                    <span class="exercise-card-subtitle">${ex.category || 'Performance'}</span>
                </div>
                
                <img src="${ex.image}" class="exercise-visual" onerror="this.src='https://placehold.co/400x250/1a1a1a/ffffff?text=${encodeURIComponent(ex.name)}'">
                
                <div class="performance-info">
                    <div class="perf-badge">
                        <span class="perf-value">${ex.sets}</span>
                        <span class="perf-label">Séries</span>
                    </div>
                    <div class="perf-badge">
                        <span class="perf-value">${ex.reps}</span>
                        <span class="perf-label">Reps</span>
                    </div>
                    <div class="perf-badge">
                        <span class="perf-value">${ex.load || '0'}</span>
                        <span class="perf-label">Peso (kg)</span>
                    </div>
                </div>

                ${ex.obs ? `<div class="ex-obs" style="margin: 1rem 1.2rem;">📝 <strong>Dica:</strong> ${ex.obs}</div>` : ''}

                <div class="sets-pills-container">
                    <div class="sets-pills">${setsHTML}</div>
                </div>

                <div class="feedback-row" style="padding: 0 1.2rem 1.2rem;">
                    <input type="text" placeholder="Como foi o peso? Feedback..." class="feedback-input" 
                           value="${completedSets[globalIdx + '-fb'] || ''}"
                           onchange="saveFeedback('${globalIdx}', this.value)">
                </div>
            `;
            container.appendChild(card);
        });
    }

    updateProgress();
}

window.toggleSet = (globalIdx, setIndex) => {
    completedSets[globalIdx][setIndex] = !completedSets[globalIdx][setIndex];
    renderWorkout();
    saveProgress();
};

window.saveFeedback = (globalIdx, value) => {
    completedSets[globalIdx + '-fb'] = value;
    saveProgress();
};

function updateProgress() {
    let total = 0, done = 0;
    Object.keys(completedSets).forEach(key => {
        if (key.startsWith(currentDay + '-')) {
            total += completedSets[key].length;
            done += completedSets[key].filter(s => s).length;
        }
    });
    
    const pct = total > 0 ? Math.round((done / total) * 100) : 0;
    
    const fill = document.getElementById('progress-fill');
    if (fill) fill.style.width = pct + '%';
    
    const text = document.getElementById('progress-text');
    if (text) text.innerText = `${done} de ${total} séries concluídas`;
    
    const pctLabel = document.getElementById('progress-percentage');
    if (pctLabel) pctLabel.innerText = pct + '%';

    // Estimativa de calorias (5 kcal por série intensa)
    const kcal = done * 5; 
    const kcalCounter = document.getElementById('kcal-count');
    if (kcalCounter) {
        kcalCounter.innerText = kcal;
        // Adicionar nota visual uma única vez
        if (!window.kcalNoteAdded) {
            const progressSec = document.querySelector('.progress-section');
            if (progressSec) {
                const note = document.createElement('p');
                note.style.cssText = 'font-size: 0.6rem; color: var(--text-dim); text-align: center; margin-top: 5px;';
                note.innerText = '* Estimativa baseada em 5 kcal por série concluída';
                progressSec.appendChild(note);
                window.kcalNoteAdded = true;
            }
        }
    }

    // Celebração de 100%
    if (pct === 100 && total > 0 && !window.celebratedToday) {
        triggerSuccessCelebration();
        window.celebratedToday = true;
    }
}

function triggerSuccessCelebration() {
    confetti({
        particleCount: 150,
        spread: 70,
        origin: { y: 0.6 },
        colors: ['#8b5cf6', '#0ea5e9', '#10b981']
    });
}

window.finishWorkout = async () => {
    let total = 0, done = 0;
    Object.keys(completedSets).forEach(key => {
        if (key.startsWith(currentDay + '-')) {
            total += completedSets[key].length;
            done += completedSets[key].filter(s => s).length;
        }
    });

    if (total === 0) return alert('Nenhum exercício concluído.');

    if (done < total) {
        if (!confirm(`Você completou ${done} de ${total} séries. Deseja finalizar mesmo assim?`)) return;
    }

    const kcal = done * 5;
    incrementStreak();

    const dayCardio = currentWorkout?.weeklyCardio?.[currentDay];
    const cardioStr = dayCardio?.type ? `${dayCardio.type} - ${dayCardio.time}min` : '';

    try {
        await fetch('/api/workouts/finish', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                student_id: currentStudentId,
                student_name: currentStudentName,
                day: currentDay,
                total_sets: total,
                completed_sets: done,
                completed_sets_json: completedSets, // ADDED: Send full exercise data for Premium Charts
                cardio: cardioStr,
                calories: kcal
            })
        });
        alert(`🔥 Treino Finalizado! Queimou aprox. ${kcal} kcal. Seu personal foi notificado! 💪`);
    } catch (e) {
        alert('🔥 Parabéns! Treino finalizado! Continue assim! 💪');
    }
};

// ────────────────────────────────────────
// LÓGICA DO FEED (24H) - COM CÂMERA
// ────────────────────────────────────────

window.showPostModal = () => {
    const modal = document.createElement('div');
    modal.id = 'post-modal';
    modal.className = 'modal-overlay';
    modal.innerHTML = `
        <div class="modal-content glass-card animate-slide-up">
            <h3>Compartilhar Treino 🔥</h3>
            <p class="subtitle">Motive sua comunidade!</p>
            
            <div class="visibility-selector" style="margin: 1.5rem 0;">
                <p style="font-size:0.7rem; color:var(--text-secondary); margin-bottom:0.5rem; text-align:left;">QUEM PODE VER? (Selecione 1 ou mais)</p>
                <div class="segmented-control checkbox-control" style="display: flex; gap: 4px;">
                    <input type="checkbox" id="v-trainer" name="visibility" value="trainer" checked>
                    <label for="v-trainer">Personal</label>
                    <input type="checkbox" id="v-gym" name="visibility" value="gym">
                    <label for="v-gym">Academia</label>
                    <input type="checkbox" id="v-public" name="visibility" value="public">
                    <label for="v-public">Público</label>
                </div>
            </div>

            <!-- SEM capture="camera" para permitir Galeria no mobile -->
            <input type="file" id="post-file" accept="image/*" class="hidden" onchange="previewPost(this)">
            <label for="post-file" class="upload-area" id="post-preview">
                <div style="font-size: 2rem;">📸</div>
                <p>Tirar Foto ou Galeria</p>
            </label>

            <textarea id="post-caption" placeholder="Legenda (ex: Tá pago!)" style="width:100%; margin-top:1rem; background:rgba(255,255,255,0.05); color:white; border:none; padding:10px; border-radius:8px;"></textarea>
            
            <div style="display:flex; gap:10px; margin-top:1.5rem;">
                <button id="btn-submit-post" class="btn-success" style="flex:2" onclick="submitPost()">Postar Agora 🚀</button>
                <button class="btn-cancel" style="flex:1" onclick="document.getElementById('post-modal').remove()">Sair</button>
            </div>
        </div>
    `;
    document.body.appendChild(modal);
};

window.previewPost = (input) => {
    if (input.files && input.files[0]) {
        const file = input.files[0];
        const reader = new FileReader();
        
        reader.onload = (e) => {
            const img = new Image();
            img.onload = () => {
                // Resize image via Canvas to max 800px width/height and compress to 0.7 quality
                const canvas = document.createElement('canvas');
                let width = img.width;
                let height = img.height;
                const MAX_DIM = 800;
                
                if (width > height) {
                    if (width > MAX_DIM) { height *= MAX_DIM / width; width = MAX_DIM; }
                } else {
                    if (height > MAX_DIM) { width *= MAX_DIM / height; height = MAX_DIM; }
                }
                
                canvas.width = width;
                canvas.height = height;
                const ctx = canvas.getContext('2d');
                ctx.drawImage(img, 0, 0, width, height);
                
                const compressedDataUrl = canvas.toDataURL('image/jpeg', 0.7);
                
                const preview = document.getElementById('post-preview');
                preview.innerHTML = `<img src="${compressedDataUrl}" style="width:100%; height:150px; object-fit:cover; border-radius:12px;">`;
                preview.dataset.imgValue = compressedDataUrl;
            };
            img.src = e.target.result;
        };
        reader.readAsDataURL(file);
    }
};

window.submitPost = async () => {
    const previewArea = document.getElementById('post-preview');
    const imgData = previewArea ? previewArea.dataset.imgValue : null;
    const caption = document.getElementById('post-caption').value || "Tá pago! 💪";
    
    // Coleta múltiplas opções de visibilidade
    const checkedVisibilities = Array.from(document.querySelectorAll('input[name="visibility"]:checked')).map(cb => cb.value);
    
    if (!imgData) return alert('Por favor, adicione uma foto!');
    if (checkedVisibilities.length === 0) return alert('Escolha quem pode ver sua postagem!');

    const btnSubmit = document.getElementById('btn-submit-post');
    btnSubmit.disabled = true;
    btnSubmit.innerText = "Enviando... ⏳";

    try {
        // Envia como Array ou comma-separated. O backend precisará tratar se for Public+Trainer, etc.
        // Por hora, enviaremos a primeira (maior visibilidade) ou public se selecionado
        const visibilityToSend = checkedVisibilities.includes('public') ? 'public' : 
                               checkedVisibilities.includes('gym') ? 'gym' : 'trainer';

        const res = await fetch('/api/feed', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                student_id: currentStudentId,
                image_base64: imgData,
                caption: caption,
                visibility: visibilityToSend // mandamos o nível mais 'aberto' selecionado
            })
        });

        if (res.ok) {
            document.getElementById('post-modal').remove();
            loadFeed();
        } else {
            alert('Erro ao postar. Tente novamente.');
            btnSubmit.disabled = false;
            btnSubmit.innerText = "Postar Agora 🚀";
        }
    } catch (e) {
        alert('Erro ao postar.');
        btnSubmit.disabled = false;
        btnSubmit.innerText = "Postar Agora 🚀";
    }
};



// --- PREMIUM LOGIC & HISTÓRICO COM PAYWALL ---
function applyPlanRestrictions() {
    const overlays = document.querySelectorAll('.premium-overlay');
    const blurred = document.querySelectorAll('.blurred-content');
    
    if (currentPlanType === 'premium') {
        overlays.forEach(ov => ov.style.display = 'none');
        blurred.forEach(bc => bc.classList.remove('blurred-content'));
    }
    // Always load history and charts, regardless of plan (charts function handles internal locks)
    loadHistory();
}

async function loadHistory() {
    const container = document.getElementById('history-container');
    if (!currentStudentId) return;

    try {
        const res = await fetch(`/api/workouts/history?student_id=${currentStudentId}`);
        const history = await res.json();
        
        if (history.length === 0) {
            container.innerHTML = '<p class="subtitle">Nenhum treino registrado ainda. Go! 🏋️</p>';
            renderCharts(history);
            return;
        }

        const now = new Date();
        container.innerHTML = history.map((h, idx) => {
            const hDate = new Date(h.date);
            const diffDays = Math.floor((now - hDate) / (1000 * 60 * 60 * 24));
            
            // Bloqueio de 7 dias para usuários FREE
            const isLocked = currentPlanType !== 'premium' && diffDays > 7;

            return `
                <div class="glass-card history-card ${isLocked ? 'blurred-content' : ''}" style="margin-bottom: 0.8rem; padding: 1rem; position: relative;">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <span style="font-size:1.1rem;"><b>${h.day}</b></span>
                        <span style="font-size:0.75rem; color:var(--text-secondary); background:rgba(255,255,255,0.05); padding:4px 8px; border-radius:12px;">
                            ${new Date(h.created_at).toLocaleDateString('pt-BR')}
                        </span>
                    </div>
                    <div style="margin-top:8px; display:flex; gap:10px;">
                        <span style="font-size:0.85rem; color:var(--accent);">🔥 ${h.completed_sets} séries</span>
                        <span style="font-size:0.85rem; color:#f59e0b;">⚡ ${h.calories || (h.completed_sets * 5)} Kcal</span>
                    </div>
                    ${isLocked ? `
                        <div class="premium-overlay" style="background: rgba(0,0,0,0.6); border-radius:16px; display:flex; flex-direction:column; justify-content:center; align-items:center;" onclick="showUpgradeModal('Histórico Antigo')">
                            <span style="font-size:1.5rem; margin-bottom:5px;">🔒</span>
                            <span style="font-size:0.8rem; font-weight:bold; text-transform:uppercase;">Treino Pro</span>
                        </div>
                    ` : ''}
                </div>
            `;
        }).join('');
        
        renderCharts(history);
    } catch (e) {
        container.innerHTML = '<p class="subtitle">Histórico indisponível no momento.</p>';
    }
}

let weeklyChartInstance = null;
let muscleChartInstance = null;
let exerciseChartInstance = null;

function renderCharts(history) {
    if (!window.Chart) return;
    
    // 1. Chart Semanal (FREE)
    const ctxWeekly = document.getElementById('chartWeekly');
    if (ctxWeekly) {
        // Conta treinos por dia da semana
        const counts = { 'Dom':0, 'Seg':0, 'Ter':0, 'Qua':0, 'Qui':0, 'Sex':0, 'Sáb':0 };
        const past7Days = history.filter(h => {
            const hDate = new Date(h.date);
            return (new Date() - hDate) / (1000*60*60*24) <= 7;
        });
        
        past7Days.forEach(h => {
             // Tratamento básico. Se backend mandar nome do dia no BD:
             const dayName = h.day.substring(0,3); 
             if(counts[dayName] !== undefined) counts[dayName]++;
        });

        if (weeklyChartInstance) weeklyChartInstance.destroy();
        weeklyChartInstance = new Chart(ctxWeekly, {
            type: 'bar',
            data: {
                labels: Object.keys(counts),
                datasets: [{
                    label: 'Treinos',
                    data: Object.values(counts),
                    backgroundColor: 'rgba(139, 92, 246, 0.8)',
                    borderRadius: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: { y: { display:false }, x: { grid: { display:false } } },
                plugins: { legend: { display:false } }
            }
        });
    }

    // Se não for premium, paramos por aqui as renderizações reais dos graficos bloqueados
    if (currentPlanType !== 'premium') return;

    // 2. Chart Musculo (PRO)
    const ctxMuscle = document.getElementById('chartMuscle');
    if (ctxMuscle) {
        if (muscleChartInstance) muscleChartInstance.destroy();
        muscleChartInstance = new Chart(ctxMuscle, {
            type: 'doughnut',
            data: {
                labels: ['Peito', 'Costas', 'Perna', 'Braço'],
                datasets: [{
                    data: [30, 25, 35, 10], // Mock até backend mandar real
                    backgroundColor: ['#8b5cf6', '#3b82f6', '#10b981', '#f59e0b'],
                    borderWidth: 0
                }]
            },
            options: { responsive: true, maintainAspectRatio: false, plugins:{ legend: {position: 'right', labels:{color:'white'}}} }
        });
    }

    // 3. Chart Exercicio (PRO)
    const ctxEx = document.getElementById('chartExercise');
    if (ctxEx) {
        if (exerciseChartInstance) exerciseChartInstance.destroy();
        exerciseChartInstance = new Chart(ctxEx, {
            type: 'line',
            data: {
                labels: ['Sem 1', 'Sem 2', 'Sem 3', 'Sem 4'],
                datasets: [{
                    label: 'Supino (kg)',
                    data: [40, 42, 45, 50], // Mock até o backend enviar real
                    borderColor: '#10b981',
                    tension: 0.4,
                    fill: true,
                    backgroundColor: 'rgba(16, 185, 129, 0.1)'
                }]
            },
            options: { responsive: true, maintainAspectRatio: false, scales: { x:{grid:{display:false}}, y:{display:false} } }
        });
    }
}


window.showHealthConnectModal = () => {
    document.getElementById('modal-health').classList.remove('hidden');
};

window.showUpgradeModal = (context) => {
    trackConversionEvent('open_upgrade_modal_' + context.replace(/\s+/g, '_'));
    document.getElementById('upgrade-context').innerText = `O recurso de ${context} é exclusivo para alunos Pro. Não perca sua evolução!`;
    document.getElementById('modal-upgrade').classList.remove('hidden');
};

window.closeUpgradeModal = () => document.getElementById('modal-upgrade').classList.add('hidden');

window.upgradeToPremium = async () => {
    trackConversionEvent('click_upgrade_button');
    // Em produção, aqui abriria o Checkout (Stripe/Mercado Pago)
    if (confirm('Deseja ativar o Plano Pro Experimental? (Simulação de Pagamento)')) {
        try {
            await fetch('/api/super/students', {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ id: currentStudentId, plan_type: 'premium', name: currentStudentName })
            });
            alert('Parabéns! Você agora é um aluno PRO! ✨ Recarregando...');
            location.reload();
        } catch (e) { alert('Erro ao processar upgrade.'); }
    }
};

async function trackConversionEvent(type) {
    console.log('Analytics Event:', type);
    // Em produção: fetch('/api/analytics/track', { method: 'POST', ... })
}

// --- MARKETPLACE & MEUS PROTOCOLOS ---
async function loadMyProtocols() {
    if (!currentStudentId) return;
    try {
        const res = await fetch(`/api/student/purchases?student_id=${currentStudentId}`);
        const protocols = await res.json();
        const container = document.getElementById('my-protocols-list');
        
        if (protocols.length === 0) {
            container.innerHTML = `<div class="empty-state"><p class="subtitle">Você ainda não adquiriu nenhum protocolo elite.</p></div>`;
            return;
        }

        container.innerHTML = protocols.map(p => `
            <div class="protocol-card glass-card animate-fade-in">
                <div class="protocol-info">
                    <h4>${p.title}</h4>
                    <p>Treinador: <b>${p.trainer_name}</b></p>
                </div>
                <button class="buy-btn-small" onclick="activateProtocol(${p.id}, '${p.title}')">Ativar Protocolo 🔥</button>
            </div>
        `).join('');
    } catch (e) { console.error(e); }
}

window.activateProtocol = (id, title) => {
    if (confirm(`Deseja substituir sua ficha atual pelo protocolo "${title}"?\n\n(Atenção: Seu treino atual será arquivado).`)) {
        alert('Protocolo ativado com sucesso! (Em desenvolvimento)');
        // Lógica de ativação real envolveria trocar o workout_id ou copiar exercícios
    }
};

// ────────────────────────────────────────
// MARKETPLACE LOGIC
// ────────────────────────────────────────
async function loadCatalog() {
    try {
        const res = await fetch('/api/catalog');
        if (!res.ok) throw new Error('Falha no fetch: ' + res.status);
        fullCatalog = await res.json();
        renderTrainers();
    } catch (e) {
        console.error('Erro ao carregar catálogo', e);
        document.getElementById('trainer-grid').innerHTML = `<p style="color:var(--text-dim)">Erro ao carregar treinadores: ${e.message}</p>`;
    }
}

function renderTrainers() {
    const grid = document.getElementById('trainer-grid');
    grid.innerHTML = fullCatalog.map(t => `
        <div class="trainer-card animate-fade-in" onclick="showTrainerDetails(${t.id})">
            <div class="elite-badge">ELITE</div>
            <img src="${t.image}" loading="lazy" class="trainer-img" onerror="this.src='https://placehold.co/200x200/1a1a1a/ffffff?text=ELITE'">
            <div class="trainer-info">
                <p class="trainer-spec">${t.specialty}</p>
                <h4 class="trainer-name">${t.name}</h4>
            </div>
        </div>
    `).join('');
    document.getElementById('trainer-details').classList.add('hidden');
    document.getElementById('trainer-grid').classList.remove('hidden');
}

window.showTrainerDetails = (id) => {
    const trainer = fullCatalog.find(t => t.id === id);
    if (!trainer) return;

    document.getElementById('trainer-grid').classList.add('hidden');
    const details = document.getElementById('trainer-details');
    details.classList.remove('hidden');

    document.getElementById('selected-trainer-info').innerHTML = `
        <div class="glass-card trainer-detail-header animate-fade-in">
            <img src="${trainer.image}" class="trainer-avatar">
            <div>
                <h3 class="trainer-title">${trainer.name}</h3>
                <p class="trainer-badge">🏆 ${trainer.achievement}</p>
                <p class="trainer-bio-text">${trainer.bio}</p>
            </div>
        </div>
    `;

    const list = document.getElementById('protocol-list');
    list.innerHTML = trainer.workouts.map(w => `
        <div class="protocol-card animate-fade-in">
            <div class="protocol-info">
                <h4>${w.title}</h4>
                <p>${w.description}</p>
            </div>
            <div class="protocol-price">
                <span class="price-tag">R$ ${w.price.toFixed(2)}</span>
                <button class="buy-btn-small" onclick="buyProtocol(${w.id}, '${w.title}', '${trainer.name}')">Adquirir Protocolo 🔥</button>
            </div>
        </div>
    `).join('');
    
    window.scrollTo({ top: 0, behavior: 'smooth' });
};

window.hideTrainerDetails = () => {
    document.getElementById('trainer-details').classList.add('hidden');
    document.getElementById('trainer-grid').classList.remove('hidden');
};

window.buyProtocol = async (id, title, trainerName) => {
    // Redirecionamento real para o WhatsApp para fechar a venda
    const msg = `Olá! Tenho interesse no Protocolo Elite: *${title}* do treinador *${trainerName}*. Pode me ajudar com a aquisição? 🏋️‍♂️💎`;
    const waLink = `https://wa.me/5500000000000?text=${encodeURIComponent(msg)}`; // O professor deve configurar seu número
    
    if (confirm(`Você está prestes a adquirir o protocolo "${title}".\n\nDeseja falar com o Personal agora para liberar seu acesso?`)) {
        window.open(waLink, '_blank');
        
        // Simula o registro da intenção de compra no backend
        try {
            await fetch('/api/catalog/buy', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ student_id: currentStudentId, workout_id: id })
            });
        } catch (e) { /* silêncio */ }
    }
};

// ────────────────────────────────────────
// LÓGICA DO FEED (24H)
// ────────────────────────────────────────
async function loadFeed() {
    if (!currentStudentId) return;
    try {
        const res = await fetch(`/api/feed?student_id=${currentStudentId}`);
        const posts = await res.json();
        renderFeed(posts);
    } catch (e) {
        console.error('Erro ao carregar feed', e);
    }
}

function renderFeed(posts) {
    const container = document.getElementById('feed-list');
    if (posts.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <p class="subtitle">Nenhum post nas últimas 24h. Seja o primeiro! 🔥</p>
            </div>
        `;
        return;
    }

    container.innerHTML = posts.map(post => {
        const expires = new Date(post.expires_at);
        const diff = Math.max(0, Math.floor((expires - new Date()) / (1000 * 60))); // minutos restantes
        const hours = Math.floor(diff / 60);
        const mins = diff % 60;

        return `
            <div class="feed-card animate-fade-in">
                <div class="feed-card-header">
                    <div class="feed-avatar">${post.student_name[0]}</div>
                    <div class="feed-user-info">
                        <h4>${post.student_name}</h4>
                        <div style="display:flex; align-items:center; gap:5px;">
                            <span class="feed-time">${new Date(post.created_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</span>
                            <span class="badge-mini ${post.visibility}">${post.visibility === 'trainer' ? 'Personal' : (post.visibility === 'gym' ? 'Academia' : 'Público')}</span>
                        </div>
                    </div>
                </div>
                <img src="${post.image_url}" class="feed-img" onerror="this.src='https://placehold.co/400x400/1a1a1a/ffffff?text=Treino+Finalizado'">
                <div class="feed-footer">
                    <p class="feed-caption">${post.caption}</p>
                    <span class="expires-tag">⏳ Expira em ${hours}h ${mins}m</span>
                </div>
            </div>
        `;
    }).join('');
}

// PWA
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/service-worker.js');
    });
}

async function initStudentSelector() {
    const headerTitle = document.querySelector('header h1');
    if (headerTitle) headerTitle.innerText = "Simulador de Aluno";
    
    const selector = document.getElementById('student-selector');
    if (selector) selector.classList.remove('hidden');
    
    try {
        const res = await fetch(`/api/workouts/students/all?t=${Date.now()}`);
        const students = await res.json();
        const btnContainer = document.getElementById('student-btns');
        if (btnContainer) {
            btnContainer.innerHTML = students.map(s => {
                const targetToken = s.token || s.id;
                return `
                    <button class="btn-primary" onclick="window.location.href='/aluno/${targetToken}'" style="width:100%; margin-bottom:8px; display:block; padding:15px; border-radius:12px;">
                        ${s.name} (${s.trainer_name || 'Personal Vitin'})
                    </button>
                `;
            }).join('');
        }
    } catch (e) {
        if (selector) selector.innerHTML = '<p style="color:#ef4444">Nenhum aluno cadastrado no sistema ainda.</p>';
    }
}
