let currentWorkout = null;
let completedSets = {};
let currentDay = 'seg';
let currentStudentId = null;
let currentStudentName = '';
let fullCatalog = [];

// ────────────────────────────────────────
// INICIALIZAÇÃO: Token e Isolamento Total
// ────────────────────────────────────────
document.addEventListener('DOMContentLoaded', async () => {
    const pathParts = window.location.pathname.split('/');
    const token = pathParts.length > 2 ? pathParts[2] : null;

    if (!token) {
        showInvalidAccess();
        return;
    }
    
    // Navegação por abas
    window.switchStudentTab = (tab) => {
        const workoutContent = document.getElementById('workout-content');
        const discoverContent = document.getElementById('discover-content');
        const emptyState = document.getElementById('empty-state');
        const daySelector = document.getElementById('day-selector-aluno');
        
        document.querySelectorAll('.student-nav-btn').forEach(b => b.classList.remove('active'));
        
        if (tab === 'workout') {
            workoutContent.classList.remove('hidden');
            discoverContent.classList.add('hidden');
            daySelector.classList.remove('hidden');
            document.getElementById('tab-workout').classList.add('active');
            if (currentWorkout) {
                emptyState.classList.add('hidden');
                renderWorkout();
            } else {
                emptyState.classList.remove('hidden');
            }
        } else {
            workoutContent.classList.add('hidden');
            emptyState.classList.add('hidden');
            discoverContent.classList.remove('hidden');
            daySelector.classList.add('hidden');
            document.getElementById('tab-discover').classList.add('active');
            loadCatalog();
        }
    };

    try {
        const res = await fetch(`/api/students/by-token/${token}`);
        if (res.ok) {
            const student = await res.json();
            currentStudentId = student.id;
            currentStudentName = student.name;
            document.getElementById('workout-date').innerText = `Olá, ${student.name}! 💪`;
            document.getElementById('student-selector').classList.add('hidden');
            loadChallenge();
            loadWorkout(student.id);
            checkNotifications();
        } else {
            showInvalidAccess();
        }
    } catch (e) {
        showInvalidAccess();
    }
});

function showInvalidAccess() {
    document.getElementById('student-selector').classList.add('hidden');
    document.getElementById('workout-content').classList.add('hidden');
    const headerInfo = document.querySelector('header');
    if (headerInfo) {
        headerInfo.innerHTML += `
            <div style="text-align: center; margin-top: 50px;">
                <h2 style="color: #ef4444; margin-bottom: 10px;">Acesso Restrito 🚫</h2>
                <p style="color: var(--text-dim);">Para acessar seu treino, peça o seu Link de Acesso Exclusivo ao seu Personal Trainer.</p>
            </div>
        `;
    }
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
        const res = await fetch(`/api/notifications/unread-count/aluno?student_id=${currentStudentId}`);
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
        const response = await fetch(`/api/workouts/${studentId}`);
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
    document.getElementById('workout-date').innerText = `Treino de ${dayNames[currentDay]} (${currentWorkout.date || 'Hoje'})`;

    // Render Cardio
    const cardioSection = document.getElementById('cardio-content');
    if (dayCardio && dayCardio.type) {
        cardioSection.classList.remove('hidden');
        document.getElementById('cardio-info').innerText = `${dayCardio.type} - ${dayCardio.time} minutos`;
    } else {
        cardioSection.classList.add('hidden');
    }

    // Render Exercises
    const container = document.getElementById('workout-exercises');
    container.innerHTML = '';
    
    if (dayExercises) {
        dayExercises.forEach((ex, index) => {
            const globalIdx = `${currentDay}-${index}`;
            completedSets[globalIdx] = completedSets[globalIdx] || Array(parseInt(ex.sets)).fill(false);

            const card = document.createElement('div');
            card.className = 'exercise-card-student animate-fade-in';
            
            const setsHTML = completedSets[globalIdx].map((done, setIdx) => `
                <button class="set-btn ${done ? 'completed' : ''}" onclick="toggleSet('${globalIdx}', ${setIdx})">
                    ${done ? '✓' : setIdx + 1}
                </button>
            `).join('');

            card.innerHTML = `
                <div class="ex-image-container">
                    <img src="${ex.image}" loading="lazy" onerror="this.src='https://placehold.co/400x200/1a1a1a/ffffff?text=${encodeURIComponent(ex.name)}'">
                </div>
                <div class="student-ex-info">
                    <header class="ex-info-header">
                        <h3>${ex.name}</h3>
                        <span class="category-badge">${ex.category || 'Treino'}</span>
                    </header>
                    ${ex.obs ? `<p class="ex-obs">📝 <strong>Obs:</strong> ${ex.obs}</p>` : ''}
                    <div class="student-ex-details">
                        <div class="detail-pill">
                            <span class="value">${ex.sets}</span>
                            <span class="label">Séries</span>
                        </div>
                        <div class="detail-pill">
                            <span class="value">${ex.reps}</span>
                            <span class="label">Reps</span>
                        </div>
                        <div class="detail-pill">
                            <span class="value">${ex.load} <small>kg</small></span>
                            <span class="label">Carga</span>
                        </div>
                    </div>
                    <div class="sets-tracker">
                        <p class="sets-label">Marcar séries:</p>
                        <div class="sets-buttons">${setsHTML}</div>
                        <div class="feedback-row" style="margin-top: 1rem;">
                            <input type="text" placeholder="Dúvida ou dificuldade?" class="feedback-input" 
                                   value="${completedSets[globalIdx + '-fb'] || ''}"
                                   onchange="saveFeedback('${globalIdx}', this.value)">
                        </div>
                    </div>
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
    if (text) text.innerText = `${done} de ${total} séries concluídas (${pct}%)`;
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
                cardio: cardioStr
            })
        });
        alert('🔥 Parabéns! Treino finalizado! Seu personal foi notificado! 💪');
    } catch (e) {
        alert('🔥 Parabéns! Treino finalizado! Continue assim! 💪');
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

// PWA
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/service-worker.js');
    });
}
