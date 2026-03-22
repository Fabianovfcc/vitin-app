document.addEventListener('DOMContentLoaded', () => {
    fetchStudents();
    setupEventListeners();
    pollNotifications();
    setInterval(pollNotifications, 15000); // Verifica a cada 15s
});

let currentStudent = null;
let workoutExercises = [];
let exercisesLibrary = [];
let currentDay = 'seg';
let adminToken = localStorage.getItem('adminToken') || '';

if (!adminToken && window.location.pathname === '/') {
    adminToken = prompt('Digite a senha de acesso do Professor:');
    if (adminToken) localStorage.setItem('adminToken', adminToken);
}

let weeklyWorkouts = {
    seg: [], ter: [], qua: [], qui: [], sex: [], sab: [], dom: []
};
let weeklyCardio = {
    seg: { type: '', time: '' }, ter: { type: '', time: '' }, qua: { type: '', time: '' }, 
    qui: { type: '', time: '' }, sex: { type: '', time: '' }, sab: { type: '', time: '' }, dom: { type: '', time: '' }
};

// ────────────────────────────────────────
// NOTIFICAÇÕES DO PROFESSOR
// ────────────────────────────────────────
async function pollNotifications() {
    try {
        const res = await fetch('/api/notifications/unread-count/professor', {
            headers: { 'Authorization': `Bearer ${adminToken}` }
        });
        if (res.status === 401) {
            handleAuthError();
            return;
        }
        const data = await res.json();
        const badge = document.getElementById('notif-badge');
        if (data.count > 0) {
            badge.textContent = data.count;
            badge.classList.remove('hidden');
        } else {
            badge.classList.add('hidden');
        }
    } catch (e) { /* silêncio */ }
}

window.toggleNotifications = async () => {
    const panel = document.getElementById('notif-panel');
    panel.classList.toggle('hidden');
    
    if (!panel.classList.contains('hidden')) {
        try {
            const res = await fetch('/api/notifications/professor', {
                headers: { 'Authorization': `Bearer ${adminToken}` }
            });
            const notifs = await res.json();
            const list = document.getElementById('notif-list');
            
            if (notifs.length === 0) {
                list.innerHTML = '<p class="subtitle" style="text-align:center; padding:1rem;">Nenhuma notificação</p>';
                return;
            }
            
            list.innerHTML = notifs.map(n => {
                const icon = n.type === 'workout_finished' ? '🔥' : '📋';
                const timeAgo = formatTimeAgo(n.created_at);
                return `<div class="notif-item ${n.is_read ? '' : 'unread'}">
                    <span class="notif-icon">${icon}</span>
                    <div>
                        <p class="notif-msg">${n.message}</p>
                        <small class="notif-time">${timeAgo}</small>
                    </div>
                </div>`;
            }).join('');
        } catch (e) {
            console.error('Erro ao buscar notificações:', e);
        }
    }
};

window.markAllRead = async () => {
    await fetch('/api/notifications/mark-read', {
        method: 'POST',
        headers: { 
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${adminToken}`
        },
        body: JSON.stringify({ role: 'professor' })
    });
    document.getElementById('notif-badge').classList.add('hidden');
    document.getElementById('notif-panel').classList.add('hidden');
};

function formatTimeAgo(isoStr) {
    if (!isoStr) return '';
    const date = new Date(isoStr);
    const now = new Date();
    const diffMs = now - date;
    const diffMin = Math.floor(diffMs / 60000);
    if (diffMin < 1) return 'Agora';
    if (diffMin < 60) return `${diffMin}min atrás`;
    const diffH = Math.floor(diffMin / 60);
    if (diffH < 24) return `${diffH}h atrás`;
    return `${Math.floor(diffH / 24)}d atrás`;
}

// ────────────────────────────────────────
// ALUNOS
// ────────────────────────────────────────
async function fetchStudents() {
    try {
        const response = await fetch('/api/students', {
            headers: { 'Authorization': `Bearer ${adminToken}` }
        });
        if (response.status === 401) return handleAuthError();
        const students = await response.json();
        renderStudents(students);
        updateStats(students);
    } catch (error) {
        console.error('Erro ao carregar alunos:', error);
    }
}

function updateStats(students) {
    const total = students.length;
    const today = new Date().toLocaleDateString('pt-BR');
    const trainedToday = students.filter(s => s.last_workout === today).length;
    
    document.getElementById('stat-total').textContent = total;
    document.getElementById('stat-today').textContent = trainedToday;
}

function renderStudents(students) {
    const grid = document.getElementById('students-grid');
    grid.innerHTML = '';

    students.forEach(student => {
        const card = document.createElement('div');
        card.className = 'student-card glass-card';
        
        const statusColor = student.status === 'active' ? '#10b981' : '#f59e0b';
        
        card.innerHTML = `
            <div class="student-info">
                <h3>${student.name}</h3>
                <p>Último treino: ${student.last_workout || 'Nenhum'}</p>
            </div>
            <div style="display:flex; flex-direction:column; align-items:flex-end; gap:0.5rem;">
                <div class="status-dot" style="background:${statusColor};"></div>
                <button onclick="deleteStudent(${student.id}, event)" class="icon-btn" style="color:#ff4d4d; font-size:1.2rem;">×</button>
            </div>
        `;
        card.onclick = () => openWorkoutCreator(student);
        grid.appendChild(card);
    });
}

async function renderFullLibrary() {
    if (exercisesLibrary.length === 0) {
        const response = await fetch('/api/exercises', {
            headers: { 'Authorization': `Bearer ${adminToken}` }
        });
        if (response.status === 401) return handleAuthError();
        exercisesLibrary = await response.json();
    }
    
    const grid = document.getElementById('library-grid');
    grid.innerHTML = '';
    
    const grouped = {};
    exercisesLibrary.forEach(ex => {
        if (!grouped[ex.category]) grouped[ex.category] = [];
        grouped[ex.category].push(ex);
    });

    for (const [category, exercises] of Object.entries(grouped)) {
        const groupIcon = resolveImage(`icon:${category}`, category);
        const section = document.createElement('div');
        section.className = 'category-group';
        section.innerHTML = `
            <div class="category-header">
                <img src="${groupIcon}" class="category-icon">
                <h4>${category}</h4>
            </div>
            <div class="exercise-options" style="grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));">
                ${exercises.map(ex => `
                    <div class="exercise-option">
                        <img src="${resolveImage(ex.image, ex.category)}" class="exercise-thumb">
                        <strong>${ex.name}</strong>
                    </div>
                `).join('')}
            </div>
        `;
        grid.appendChild(section);
    }
}

// ────────────────────────────────────────
// SETUP & NAV
// ────────────────────────────────────────
function setupEventListeners() {
    document.getElementById('close-creator').onclick = closeWorkoutCreator;
    document.getElementById('add-exercise-btn').onclick = addExercise;
    document.getElementById('save-workout-btn').onclick = saveWorkout;
    
    document.getElementById('nav-students').onclick = () => switchTab('students-list', 'nav-students');
    document.getElementById('nav-exercises').onclick = () => {
        switchTab('exercises-library', 'nav-exercises');
        renderFullLibrary();
    };
    document.getElementById('nav-challenges').onclick = () => {
        switchTab('challenges-view', 'nav-challenges');
        loadAdminChallenge();
    };
    document.getElementById('nav-profile').onclick = () => switchTab('profile-view', 'nav-profile');

    // Day Tabs
    document.querySelectorAll('.day-tab').forEach(tab => {
        tab.onclick = () => {
            saveCurrentDayData();
            document.querySelectorAll('.day-tab').forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            currentDay = tab.dataset.day;
            loadDayData();
        };
    });

    // Cardio Inputs Sync
    document.getElementById('cardio-type').oninput = (e) => weeklyCardio[currentDay].type = e.target.value;
    document.getElementById('cardio-time').oninput = (e) => weeklyCardio[currentDay].time = e.target.value;
}

function switchTab(sectionId, navId) {
    ['students-list', 'exercises-library', 'challenges-view', 'profile-view', 'workout-creator'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.classList.add('hidden');
    });
    document.getElementById(sectionId).classList.remove('hidden');
    document.querySelectorAll('.nav-btn').forEach(btn => btn.classList.remove('active'));
    document.getElementById(navId).classList.add('active');
}

// ────────────────────────────────────────
// CRUD ALUNOS
// ────────────────────────────────────────
window.showNewStudentForm = () => {
    const name = prompt('Nome do novo aluno:');
    if (name) submitNewStudent(name);
};

async function submitNewStudent(name) {
    try {
        const response = await fetch('/api/students', {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${adminToken}`
            },
            body: JSON.stringify({ name })
        });
        if (response.ok) {
            const data = await response.json();
            fetchStudents();
            // Mostra o link de acesso
            const link = `${window.location.origin}/aluno/${data.access_token}`;
            alert(`Aluno "${name}" cadastrado!\n\nLink de acesso direto:\n${link}\n\nEnvie esse link pelo WhatsApp! 📲`);
        }
    } catch (error) {
        alert('Erro ao cadastrar aluno');
    }
}

window.deleteStudent = async (id, event) => {
    event.stopPropagation();
    if (!confirm('Deseja realmente remover este aluno?')) return;
    
    try {
        await fetch(`/api/students/${id}`, { 
            method: 'DELETE',
            headers: { 'Authorization': `Bearer ${adminToken}` }
        });
        fetchStudents();
    } catch (error) {
        alert('Erro ao remover aluno');
    }
};

// ────────────────────────────────────────
// WORKOUT CREATOR (7 DIAS + CARDIO)
// ────────────────────────────────────────
function saveCurrentDayData() {
    weeklyWorkouts[currentDay] = [...workoutExercises];
}

async function loadDayData() {
    workoutExercises = weeklyWorkouts[currentDay] || [];
    
    // Tenta buscar feedback do aluno para este dia
    try {
        const res = await fetch(`/api/progress/${currentStudent.id}/${currentDay}`, {
            headers: { 'Authorization': `Bearer ${adminToken}` }
        });
        if (res.ok) {
            const progress = await res.json();
            workoutExercises.forEach((ex, index) => {
                const fbKey = `${currentDay}-${index}-fb`;
                if (progress[fbKey]) {
                    ex.feedback = progress[fbKey];
                } else {
                    delete ex.feedback;
                }
            });
        }
    } catch (e) { /* silêncio */ }

    const cardio = weeklyCardio[currentDay] || { type: '', time: '' };
    document.getElementById('cardio-type').value = cardio.type;
    document.getElementById('cardio-time').value = cardio.time;
    renderExercises();
}

async function openWorkoutCreator(student) {
    currentStudent = student;
    document.getElementById('current-student-name').innerText = student.name;
    document.getElementById('students-list').classList.add('hidden');
    document.getElementById('workout-creator').classList.remove('hidden');
    
    currentDay = 'seg';
    document.querySelectorAll('.day-tab').forEach(t => {
        t.classList.remove('active');
        if(t.dataset.day === 'seg') t.classList.add('active');
    });
    
    window.scrollTo({ top: 0, behavior: 'smooth' });

    try {
        const response = await fetch(`/api/workouts/${student.id}`, {
            headers: { 'Authorization': `Bearer ${adminToken}` }
        });
        if (response.ok) {
            const data = await response.json();
            weeklyWorkouts = data.weeklyWorkouts || {
                seg: data.exercises || [],
                ter: [], qua: [], qui: [], sex: [], sab: [], dom: []
            };
            weeklyCardio = data.weeklyCardio || {
                seg: { type: '', time: '' }, ter: { type: '', time: '' }, qua: { type: '', time: '' }, 
                qui: { type: '', time: '' }, sex: { type: '', time: '' }, sab: { type: '', time: '' }, dom: { type: '', time: '' }
            };
        } else {
            weeklyWorkouts = { seg: [], ter: [], qua: [], qui: [], sex: [], sab: [], dom: [] };
            weeklyCardio = {
                seg: { type: '', time: '' }, ter: { type: '', time: '' }, qua: { type: '', time: '' }, 
                qui: { type: '', time: '' }, sex: { type: '', time: '' }, sab: { type: '', time: '' }, dom: { type: '', time: '' }
            };
        }
    } catch (e) {
        console.warn('Iniciando ficha nova');
    }
    loadDayData();
}

window.copyWorkoutFromDay = () => {
    const sourceDay = document.getElementById('copy-day-select').value;
    if (!sourceDay) return;
    if (sourceDay === currentDay) return alert('Selecione um dia diferente do atual');
    
    if (weeklyWorkouts[sourceDay].length === 0 && !weeklyCardio[sourceDay].type) {
        return alert('O dia selecionado está vazio');
    }

    if (confirm(`Deseja copiar o treino de ${sourceDay.toUpperCase()} para ${currentDay.toUpperCase()}? (Isso apagará o treino atual desse dia)`)) {
        weeklyWorkouts[currentDay] = JSON.parse(JSON.stringify(weeklyWorkouts[sourceDay]));
        weeklyCardio[currentDay] = JSON.parse(JSON.stringify(weeklyCardio[sourceDay]));
        loadDayData();
    }
};

function closeWorkoutCreator() {
    document.getElementById('workout-creator').classList.add('hidden');
    document.getElementById('students-list').classList.remove('hidden');
}

// ────────────────────────────────────────
// WHATSAPP LINK
// ────────────────────────────────────────
window.copyWhatsAppLink = () => {
    if (!currentStudent) return;
    const token = currentStudent.access_token || '';
    const link = `${window.location.origin}/aluno/${token}`;
    const msg = `Oi ${currentStudent.name}! 💪\n\nSeu treino está atualizado! Acesse pelo link:\n${link}\n\n- Seu Personal 🏋️`;
    
    // Tenta copiar para clipboard
    navigator.clipboard.writeText(msg).then(() => {
        alert('Link copiado para a área de transferência!\n\nCole no WhatsApp do aluno.');
    }).catch(() => {
        // Fallback: abre WhatsApp Web diretamente
        const waLink = `https://wa.me/?text=${encodeURIComponent(msg)}`;
        window.open(waLink, '_blank');
    });
};

// ────────────────────────────────────────
// EXERCÍCIOS
// ────────────────────────────────────────
async function addExercise() {
    if (exercisesLibrary.length === 0) {
        try {
            const response = await fetch('/api/exercises', {
                headers: { 'Authorization': `Bearer ${adminToken}` }
            });
            exercisesLibrary = await response.json();
        } catch (error) {
            console.error('Erro ao buscar exercícios:', error);
            return;
        }
    }
    showExerciseSelector();
}

function resolveImage(imgStr, category) {
    if (imgStr && imgStr.startsWith('icon:')) {
        const group = imgStr.replace('icon:', '');
        return window.MUSCLE_ICONS?.[group] || `https://placehold.co/60x60/1a1a1a/8b5cf6?text=${category?.[0] || '?'}`;
    }
    return imgStr || `https://placehold.co/60x60/1a1a1a/8b5cf6?text=?`;
}

function showExerciseSelector() {
    const existing = document.getElementById('exercise-selector');
    if (existing) existing.remove();

    const grouped = {};
    exercisesLibrary.forEach(ex => {
        if (!grouped[ex.category]) grouped[ex.category] = [];
        grouped[ex.category].push(ex);
    });

    let optionsHTML = '';
    for (const [category, exercises] of Object.entries(grouped)) {
        const groupIcon = resolveImage(`icon:${category}`, category);
        optionsHTML += `<div class="category-group">
            <div class="category-header">
                <img src="${groupIcon}" class="category-icon">
                <h4>${category}</h4>
            </div>`;
        exercises.forEach(ex => {
            const img = resolveImage(ex.image, ex.category);
            optionsHTML += `
                <div class="exercise-option" onclick="selectExercise(${ex.id})">
                    <img src="${img}" class="exercise-thumb" onerror="this.style.display='none'">
                    <div><strong>${ex.name}</strong></div>
                </div>`;
        });
        optionsHTML += `</div>`;
    }

    const modal = document.createElement('div');
    modal.id = 'exercise-selector';
    modal.className = 'modal-overlay';
    modal.innerHTML = `
        <div class="modal-content glass-card">
            <div class="exercise-header">
                <div>
                    <h3>Selecione o Exercício</h3>
                    <button class="btn-create-ex" onclick="showNewExerciseForm()">+ Criar Novo</button>
                </div>
                <button onclick="document.getElementById('exercise-selector').remove()" class="icon-btn">×</button>
            </div>
            <div class="exercise-options">${optionsHTML}</div>
        </div>
    `;
    document.body.appendChild(modal);
}

window.selectExercise = (id) => {
    const ex = exercisesLibrary.find(e => e.id === id);
    if (ex) {
        workoutExercises.push({
            name: ex.name, sets: 3, reps: 12, load: 10,
            image: resolveImage(ex.image, ex.category),
            category: ex.category
        });
        saveCurrentDayData();
        renderExercises();
    }
    const selector = document.getElementById('exercise-selector');
    if (selector) selector.remove();
};

window.showNewExerciseForm = () => {
    const selector = document.getElementById('exercise-selector');
    if (selector) selector.remove();

    const modal = document.createElement('div');
    modal.id = 'exercise-selector';
    modal.className = 'modal-overlay';
    modal.innerHTML = `
        <div class="modal-content glass-card">
            <div class="exercise-header">
                <h3>Novo Exercício</h3>
                <button onclick="document.getElementById('exercise-selector').remove()" class="icon-btn">×</button>
            </div>
            <div class="create-ex-form">
                <div class="input-group">
                    <label>Nome do Exercício</label>
                    <input type="text" id="new-ex-name" placeholder="Ex: Supino com Halteres">
                </div>
                <div class="input-group">
                    <label>Categoria</label>
                    <select id="new-ex-category">
                        <option>Peito</option><option>Costas</option><option>Ombros</option>
                        <option>Bíceps</option><option>Tríceps</option><option>Pernas</option>
                        <option>Glúteos</option><option>Abdômen</option><option>Panturrilha</option>
                        <option>Trapézio</option><option>Antebraço</option>
                    </select>
                </div>
                <div class="input-group">
                    <label>URL da Imagem (Opcional)</label>
                    <input type="text" id="new-ex-image" placeholder="https://exemplo.com/imagem.jpg" oninput="updateImagePreview(this.value)">
                </div>
                <div id="image-preview-container" class="preview-box">
                    <p class="subtitle">Preview da Imagem</p>
                    <img id="new-ex-preview" src="" style="display:none; max-width:100%; border-radius:10px; margin-top:5px;">
                </div>
                <button class="btn-success" onclick="submitNewExercise()" style="margin-top:1rem;">Salvar Exercício</button>
            </div>
        </div>
    `;
    document.body.appendChild(modal);
};

window.updateImagePreview = (url) => {
    const img = document.getElementById('new-ex-preview');
    if (url) { img.src = url; img.style.display = 'block'; }
    else { img.style.display = 'none'; }
};

window.submitNewExercise = async () => {
    const name = document.getElementById('new-ex-name').value;
    const category = document.getElementById('new-ex-category').value;
    const image = document.getElementById('new-ex-image').value || `icon:${category}`;
    if (!name) return alert('Por favor, insira o nome do exercício');

    try {
        const response = await fetch('/api/exercises', {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${adminToken}`
            },
            body: JSON.stringify({ name, category, image })
        });
        const savedEx = await response.json();
        exercisesLibrary.push(savedEx);
        alert('Exercício criado com sucesso!');
        addExercise();
    } catch (error) {
        alert('Erro ao criar exercício');
    }
};

// ────────────────────────────────────────
// RENDER & SAVE
// ────────────────────────────────────────
function renderExercises() {
    const list = document.getElementById('exercises-list');
    list.innerHTML = '';
    
    if (workoutExercises.length === 0) {
        list.innerHTML = '<p class="subtitle" style="text-align:center; padding:2rem;">Nenhum exercício para este dia. Clique em "+" para adicionar.</p>';
    }

    workoutExercises.forEach((ex, index) => {
        const div = document.createElement('div');
        div.className = 'exercise-item';
        div.innerHTML = `
            <div class="exercise-header">
                <img src="${ex.image || ''}" class="exercise-thumb" onerror="this.src='https://placehold.co/60x60/1a1a1a/ffffff?text=X'">
                <input type="text" value="${ex.name}" class="transparent-input" onchange="updateEx(${index}, 'name', this.value)">
                <button onclick="removeEx(${index})" class="icon-btn">×</button>
            </div>
            <div class="inputs-row">
                <div class="input-group">
                    <label>Séries</label>
                    <input type="number" value="${ex.sets}" onchange="updateEx(${index}, 'sets', this.value)">
                </div>
                <div class="input-group">
                    <label>Reps</label>
                    <input type="number" value="${ex.reps}" onchange="updateEx(${index}, 'reps', this.value)">
                </div>
                <div class="input-group">
                    <label>Carga (kg)</label>
                    <input type="number" value="${ex.load}" onchange="updateEx(${index}, 'load', this.value)">
                </div>
            </div>
            <div class="input-group" style="margin-top: 0.5rem;">
                <label>Observação (Instruções detalhadas)</label>
                <input type="text" value="${ex.obs || ''}" placeholder="Ex: Cadência 3131, pico de contração..." onchange="updateEx(${index}, 'obs', this.value)">
            </div>
            ${ex.feedback ? `
            <div class="student-feedback-alert" style="margin-top: 0.8rem; background: rgba(245, 158, 11, 0.1); border: 1px solid rgba(245, 158, 11, 0.3); padding: 0.6rem; border-radius: 8px; font-size: 0.85rem;">
                <span style="color: #f59e0b;">💬 <strong>Feedback do Aluno:</strong></span>
                <p style="margin-top: 5px; color: #fff;">${ex.feedback}</p>
            </div>` : ''}
        `;
        list.appendChild(div);
    });
}

window.updateEx = (index, field, value) => {
    workoutExercises[index][field] = value;
    saveCurrentDayData();
};

window.removeEx = (index) => {
    workoutExercises.splice(index, 1);
    saveCurrentDayData();
    renderExercises();
};

async function saveWorkout() {
    saveCurrentDayData();
    
    const workoutData = { 
        student_id: currentStudent.id, 
        student_name: currentStudent.name,
        weeklyWorkouts,
        weeklyCardio,
        date: new Date().toLocaleDateString('pt-BR')
    };

    try {
        const response = await fetch('/api/workouts', {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${adminToken}`
            },
            body: JSON.stringify(workoutData)
        });
        const res = await response.json();
        alert(res.message);
        closeWorkoutCreator();
        fetchStudents(); // Atualiza o dashboard
    } catch (error) {
        alert('Erro de conexão ao salvar treino');
    }
}

// ────────────────────────────────────────
// DESAFIOS GLOBAIS (ADMIN)
// ────────────────────────────────────────
function handleAuthError() {
    localStorage.removeItem('adminToken');
    alert('Sua sessão expirou ou a senha está incorreta.');
    window.location.reload();
}

async function loadAdminChallenge() {
    try {
        const res = await fetch('/api/challenges/active', {
            headers: { 'Authorization': `Bearer ${adminToken}` }
        });
        if (res.ok) {
            const challenge = await res.json();
            document.getElementById('challenge-title').value = challenge.title;
            document.getElementById('challenge-desc').value = challenge.description;
            document.getElementById('btn-remove-challenge').style.display = 'block';
        } else {
            document.getElementById('challenge-title').value = '';
            document.getElementById('challenge-desc').value = '';
            document.getElementById('btn-remove-challenge').style.display = 'none';
        }
    } catch (e) {
        console.error('Erro ao carregar desafio', e);
    }
}

document.getElementById('btn-save-challenge').onclick = async () => {
    const title = document.getElementById('challenge-title').value.trim();
    const desc = document.getElementById('challenge-desc').value.trim();
    
    if (!title || !desc) return alert('Preencha título e descrição!');
    
    try {
        const res = await fetch('/api/challenges/active', {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${adminToken}`
            },
            body: JSON.stringify({ title, description: desc })
        });
        if (res.ok) {
            alert('Desafio lançado com sucesso! Todos os alunos verão no topo do treino.');
            loadAdminChallenge();
        }
    } catch (e) {
        alert('Erro ao salvar desafio');
    }
};

document.getElementById('btn-remove-challenge').onclick = async () => {
    if (!confirm('Tem certeza que deseja encerrar o desafio atual?')) return;
    
    try {
        const res = await fetch('/api/challenges/active', { 
            method: 'DELETE',
            headers: { 'Authorization': `Bearer ${adminToken}` }
        });
        if (res.ok) {
            alert('Desafio encerrado!');
            loadAdminChallenge();
        }
    } catch (e) {
        alert('Erro ao remover desafio');
    }
};

// ────────────────────────────────────────
// LINK WHATSAPP (COMPARTILHAMENTO)
// ────────────────────────────────────────
window.copyWhatsAppLink = () => {
    if (!currentStudent || !currentStudent.access_token) {
        return alert("Erro: O token deste aluno não foi encontrado. Atualize a página.");
    }
    
    const baseUrl = window.location.origin;
    const link = `${baseUrl}/aluno/${currentStudent.access_token}`;
    const text = `Fala ${currentStudent.name.split(' ')[0]}!\n\nSeu treino está pronto. Acesse pelo link abaixo:\n\n🔗 ${link}`;
    
    if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(() => {
            alert('✅ Link copiado para a área de transferência:\n\n' + link + '\n\nCole no WhatsApp do aluno.');
        }).catch(err => {
            prompt('Copie o link manualmente:', link);
        });
    } else {
        prompt('Copie o link manualmente:', link);
    }
};
