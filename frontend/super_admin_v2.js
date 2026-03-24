let masterToken = localStorage.getItem('masterToken') || '';
let charts = {};
let allStudentsData = [];

if (!masterToken) {
    masterToken = prompt('Digite a Chave Master do Aplicativo:');
    if (masterToken) localStorage.setItem('masterToken', masterToken);
}

document.addEventListener('DOMContentLoaded', () => {
    loadDashboard();
});

window.switchMasterTab = (tab) => {
    document.querySelectorAll('.sidebar-nav .nav-btn').forEach(btn => btn.classList.remove('active'));
    document.getElementById(`btn-${tab === 'dashboard' ? 'dash' : tab}`).classList.add('active');

    document.querySelectorAll('.master-section').forEach(s => s.classList.add('hidden'));
    document.getElementById(`section-${tab}`).classList.remove('hidden');

    if (tab === 'dashboard') loadDashboard();
    if (tab === 'trainers') loadTrainersDetailed();
    if (tab === 'gyms') loadGyms();
    if (tab === 'all-students') loadAllStudents();
    if (tab === 'marketplace') loadMarketplaceData();
    if (tab === 'catalog') loadCatalogMgmt();
    if (tab === 'feed-mod') loadFeedMod();
    if (tab === 'billing') loadBillingData();
    if (tab === 'exercises') loadExercises();

    const titles = {
        dashboard: "Dashboard Global",
        trainers: "Gestão de Professores",
        gyms: "Academias Parceiras",
        'all-students': "Gestão Global de Alunos",
        marketplace: "Vendas do Marketplace",
        catalog: "Gestão do Catálogo Elite",
        'feed-mod': "Moderação do Feed",
        billing: "Faturamento e Assinaturas",
        exercises: "Gestão da Biblioteca Global de Exercícios"
    };
    document.getElementById('view-title').textContent = titles[tab];
};

// --- DASHBOARD ---
async function loadDashboard() {
    try {
        const res = await fetch(`/api/super/stats?t=${Date.now()}`, {
            headers: { 'Authorization': `Bearer ${masterToken}` }
        });
        if (res.status === 403 || res.status === 401) {
            localStorage.removeItem('masterToken');
            alert('Chave Master Incorreta ou Expirada! Redirecionando...');
            location.reload();
            return;
        }
        const stats = await res.json();
        
        document.getElementById('kpi-revenue').textContent = `R$ ${(stats.active_subscriptions * 29.90).toLocaleString('pt-BR', {minimumFractionDigits: 2})}`;
        document.getElementById('kpi-students').textContent = stats.total_students;
        document.getElementById('kpi-churn').textContent = `${stats.churn_rate}%`;
        document.getElementById('kpi-activity').textContent = stats.recent_activity;

        initCharts(stats);
    } catch (e) { console.error(e); }
}

function initCharts(stats) {
    try {
        const ctxGrowth = document.getElementById('chart-growth').getContext('2d');
        if (charts.growth) charts.growth.destroy();
        charts.growth = new Chart(ctxGrowth, {
            type: 'line',
            data: {
                labels: ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun'],
                datasets: [{ label: 'Alunos Ativos', data: [10, 25, 45, 80, 120, stats.total_students], borderColor: '#8b5cf6', tension: 0.4 }]
            },
            options: { responsive: true, plugins: { legend: { display: false } } }
        });

        const ctxDist = document.getElementById('chart-distribution').getContext('2d');
        if (charts.dist) charts.dist.destroy();
        charts.dist = new Chart(ctxDist, {
            type: 'doughnut',
            data: {
                labels: ['Musculação', 'Crossfit', 'Funcional'],
                datasets: [{ data: [stats.total_students, 5, 2], backgroundColor: ['#8b5cf6', '#d946ef', '#ec4899'] }]
            },
            options: { responsive: true }
        });
    } catch (e) { console.warn('Erro ao carregar gráficos:', e); }
}

// --- TRAINERS ---
async function loadTrainersDetailed() {
    try {
        const res = await fetch(`/api/super/trainers-detailed?t=${Date.now()}`, {
            headers: { 'Authorization': `Bearer ${masterToken}` }
        });
        const trainers = await res.json();
        const tbody = document.getElementById('trainers-table-body');
        tbody.innerHTML = trainers.map(t => `
            <tr>
                <td><strong>${t.name}</strong></td>
                <td>${t.gym_name || 'Autônomo'}</td>
                <td>${t.student_count} alunos</td>
                <td><span class="status-badge active">${t.status || 'Ativo'}</span></td>
                <td>
                    <button class="icon-btn" onclick="openTrainerModal(${JSON.stringify(t).replace(/"/g, '&quot;')})">✏️</button>
                    <button class="icon-btn" onclick="viewTrainerStudents(${t.id})">👥</button>
                    <button class="icon-btn" style="color:#ef4444" onclick="deleteTrainer(${t.id})">🗑️</button>
                </td>
            </tr>
        `).join('');
    } catch (e) { console.error(e); }
}

window.openTrainerModal = async (trainer = null) => {
    const modal = document.getElementById('modal-trainer');
    const gymSelect = document.getElementById('trainer-gym-id');
    
    // Carregar academias para o select
    try {
        const gRes = await fetch(`/api/super/gyms?t=${Date.now()}`, { headers: { 'Authorization': `Bearer ${masterToken}` } });
        if (gRes.ok) {
            const gyms = await gRes.json();
            gymSelect.innerHTML = '<option value="">Autônomo</option>' + gyms.map(g => `<option value="${g.id}">${g.name}</option>`).join('');
        } else {
             gymSelect.innerHTML = '<option value="">Autônomo</option>';
        }
    } catch (e) {
        console.error('Erro ao carregar academias', e);
        gymSelect.innerHTML = '<option value="">Autônomo</option>';
    }

    if (trainer) {
        document.getElementById('trainer-modal-title').textContent = 'Editar Professor';
        document.getElementById('trainer-id').value = trainer.id;
        document.getElementById('trainer-name').value = trainer.name;
        document.getElementById('trainer-whatsapp').value = trainer.whatsapp || '';
        document.getElementById('trainer-gym-id').value = trainer.gym_id || '';
        document.getElementById('pass-group').style.display = 'none';
    } else {
        document.getElementById('trainer-modal-title').textContent = 'Novo Professor';
        document.getElementById('trainer-id').value = '';
        document.getElementById('trainer-name').value = '';
        document.getElementById('trainer-whatsapp').value = '';
        document.getElementById('trainer-gym-id').value = '';
        document.getElementById('pass-group').style.display = 'block';
    }
    modal.classList.remove('hidden');
};

window.closeTrainerModal = () => document.getElementById('modal-trainer').classList.add('hidden');

window.saveTrainer = async (e) => {
    e.preventDefault();
    const id = document.getElementById('trainer-id').value;
    const data = {
        name: document.getElementById('trainer-name').value,
        whatsapp: document.getElementById('trainer-whatsapp').value,
        gym_id: document.getElementById('trainer-gym-id').value || null,
        password: document.getElementById('trainer-password').value
    };

    const method = id ? 'PUT' : 'POST';
    const url = id ? `/api/super/trainers/${id}` : '/api/super/trainers';

    try {
        const res = await fetch(url, {
            method,
            headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${masterToken}` },
            body: JSON.stringify(data)
        });
        if (res.ok) {
            alert('Professor salvo!');
            closeTrainerModal();
            loadTrainersDetailed();
        }
    } catch (e) { alert('Erro ao salvar.'); }
};

window.deleteTrainer = async (id) => {
    if (!confirm('Excluir professor? Alunos serão desvinculados.')) return;
    await fetch(`/api/super/trainers/${id}`, { method: 'DELETE', headers: { 'Authorization': `Bearer ${masterToken}` } });
    loadTrainersDetailed();
};

window.viewTrainerStudents = async (id) => {
    const res = await fetch(`/api/super/trainer-students/${id}`, { headers: { 'Authorization': `Bearer ${masterToken}` } });
    const students = await res.json();
    const tbody = document.getElementById('trainer-students-list');
    tbody.innerHTML = students.map(s => `<tr><td>${s.name}</td><td>${s.whatsapp}</td><td>${s.status}</td></tr>`).join('') || '<tr><td colspan="3">Nenhum aluno.</td></tr>';
    document.getElementById('modal-trainer-students').classList.remove('hidden');
};

window.closeStudentsModal = () => document.getElementById('modal-trainer-students').classList.add('hidden');

// --- GYMS ---
async function loadGyms() {
    const res = await fetch(`/api/super/gyms?t=${Date.now()}`, { headers: { 'Authorization': `Bearer ${masterToken}` } });
    const gyms = await res.json();
    document.getElementById('gyms-grid').innerHTML = gyms.map(g => `
        <div class="glass-card gym-card">
            <h4>${g.name}</h4>
            <p>Resp: ${g.owner_name}</p>
            <p>Plano: <strong>${g.plan}</strong></p>
            <div class="gym-actions" style="margin-top: 1rem; display: flex; gap: 0.5rem;">
                <button class="icon-btn" onclick="openGymModal(${JSON.stringify(g).replace(/"/g, '&quot;')})">✏️</button>
                <button class="icon-btn" style="color:#ef4444" onclick="deleteGym(${g.id})">🗑️</button>
            </div>
        </div>
    `).join('');
}

window.deleteGym = async (id) => {
    if (!confirm('Deseja excluir esta academia? Professores vinculados ficarão como autônomos.')) return;
    await fetch(`/api/super/gyms/${id}`, { method: 'DELETE', headers: { 'Authorization': `Bearer ${masterToken}` } });
    loadGyms();
};

window.openGymModal = (gym = null) => {
    const modal = document.getElementById('modal-gym');
    if (gym) {
        document.getElementById('gym-modal-title').textContent = 'Editar Academia';
        document.getElementById('gym-id').value = gym.id;
        document.getElementById('gym-name').value = gym.name;
        document.getElementById('gym-owner').value = gym.owner_name;
        document.getElementById('gym-plan').value = gym.plan;
    } else {
        document.getElementById('gym-modal-title').textContent = 'Nova Academia';
        document.getElementById('gym-id').value = '';
        document.getElementById('gym-form').reset();
    }
    modal.classList.remove('hidden');
};

window.closeGymModal = () => document.getElementById('modal-gym').classList.add('hidden');

window.saveGym = async (e) => {
    e.preventDefault();
    const id = document.getElementById('gym-id').value;
    const data = {
        name: document.getElementById('gym-name').value,
        owner_name: document.getElementById('gym-owner').value,
        plan: document.getElementById('gym-plan').value
    };
    
    const method = id ? 'PUT' : 'POST';
    const url = id ? `/api/super/gyms/${id}` : '/api/super/gyms';

    await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${masterToken}` },
        body: JSON.stringify(data)
    });
    alert('Academia salva!');
    closeGymModal();
    loadGyms();
};

// --- GLOBAL STUDENTS ---
async function loadAllStudents() {
    const res = await fetch(`/api/super/students-all?t=${Date.now()}`, { headers: { 'Authorization': `Bearer ${masterToken}` } });
    allStudentsData = await res.json();
    renderAllStudents(allStudentsData);
}

function renderAllStudents(students) {
    const tbody = document.getElementById('all-students-table-body');
    tbody.innerHTML = students.map(s => `
        <tr>
            <td>${s.name}</td>
            <td>${s.whatsapp}</td>
            <td>${s.trainer_name || 'Sem Professor'}</td>
            <td>${s.status}</td>
            <td>
                <button class="icon-btn" onclick="openStudentModal(${JSON.stringify(s).replace(/"/g, '&quot;')})">✏️</button>
                <button class="icon-btn" style="color:#ef4444" onclick="deleteStudentGlobal(${s.id})">🗑️</button>
            </td>
        </tr>
    `).join('');
}

window.filterStudents = (val) => {
    const filtered = allStudentsData.filter(s => s.name.toLowerCase().includes(val.toLowerCase()) || (s.whatsapp && s.whatsapp.includes(val)));
    renderAllStudents(filtered);
};

window.deleteStudentGlobal = async (id) => {
    if (!confirm('Deseja excluir este aluno permanentemente?')) return;
    await fetch(`/api/super/students/${id}`, { method: 'DELETE', headers: { 'Authorization': `Bearer ${masterToken}` } });
    loadAllStudents();
};

window.openStudentModal = async (student = null) => {
    const modal = document.getElementById('modal-student');
    const trainerSelect = document.getElementById('student-trainer-id');

    // Carregar professores
    try {
        const tRes = await fetch('/api/super/trainers-detailed', { headers: { 'Authorization': `Bearer ${masterToken}` } });
        if (tRes.ok) {
            const trainers = await tRes.json();
            trainerSelect.innerHTML = '<option value="">Sem Professor</option>' + trainers.map(t => `<option value="${t.id}">${t.name}</option>`).join('');
        } else {
            trainerSelect.innerHTML = '<option value="">Sem Professor</option>';
        }
    } catch (e) {
        console.error('Erro ao carregar professores', e);
        trainerSelect.innerHTML = '<option value="">Sem Professor</option>';
    }

    if (student) {
        document.getElementById('student-modal-title').textContent = 'Editar Aluno';
        document.getElementById('student-id-input').value = student.id;
        document.getElementById('student-name').value = student.name;
        document.getElementById('student-whatsapp').value = student.whatsapp || '';
        document.getElementById('student-trainer-id').value = student.trainer_id || '';
    } else {
        document.getElementById('student-modal-title').textContent = 'Novo Aluno';
        document.getElementById('student-id-input').value = '';
        document.getElementById('student-form').reset();
    }
    modal.classList.remove('hidden');
};

window.closeStudentModal = () => document.getElementById('modal-student').classList.add('hidden');

window.saveStudent = async (e) => {
    e.preventDefault();
    const id = document.getElementById('student-id-input').value;
    const data = {
        id: id,
        name: document.getElementById('student-name').value,
        whatsapp: document.getElementById('student-whatsapp').value,
        trainer_id: document.getElementById('student-trainer-id').value || null,
        age: document.getElementById('student-age')?.value || null,
        weight: document.getElementById('student-weight')?.value || null,
        goal: document.getElementById('student-goal')?.value || null,
        status: document.getElementById('student-status')?.value || 'Ativo'
    };

    const method = id ? 'PUT' : 'POST';
    try {
        const res = await fetch('/api/super/students', {
            method,
            headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${masterToken}` },
            body: JSON.stringify(data)
        });
        if (res.ok) {
            alert('Aluno salvo!');
            closeStudentModal();
            loadAllStudents();
        }
    } catch (e) { alert('Erro ao salvar aluno.'); }
};

// --- MARKETPLACE ---
async function loadMarketplaceData() {
    const res = await fetch(`/api/super/marketplace-data?t=${Date.now()}`, { headers: { 'Authorization': `Bearer ${masterToken}` } });
    const data = await res.json();
    
    document.getElementById('market-revenue').textContent = `R$ ${data.stats.total_revenue.toLocaleString('pt-BR', {minimumFractionDigits: 2})}`;
    document.getElementById('market-sales').textContent = data.stats.total_sales;
    document.getElementById('market-top-trainer').textContent = data.stats.top_trainer;

    document.getElementById('market-ranking-body').innerHTML = data.ranking.map(r => `
        <tr>
            <td><strong>${r.name}</strong></td>
            <td>${r.sales_count}</td>
            <td>R$ ${r.revenue.toLocaleString('pt-BR', {minimumFractionDigits: 2})}</td>
        </tr>
    `).join('') || '<tr><td colspan="3">Nenhuma venda.</td></tr>';

    document.getElementById('market-recent-body').innerHTML = data.recent_sales.map(s => `
        <tr>
            <td>${new Date(s.created_at).toLocaleDateString()}</td>
            <td>${s.student_name}</td>
            <td>${s.workout_title}</td>
            <td>R$ ${s.price.toFixed(2)}</td>
        </tr>
    `).join('') || '<tr><td colspan="4">Nenhuma venda recente.</td></tr>';
}

// --- BILLING ---
async function loadBillingData() {
    const res = await fetch(`/api/super/billing-data?t=${Date.now()}`, { headers: { 'Authorization': `Bearer ${masterToken}` } });
    const data = await res.json();
    document.getElementById('billing-mrr').textContent = `R$ ${data.mrr.toLocaleString('pt-BR', {minimumFractionDigits: 2})}`;
    document.getElementById('billing-gyms').textContent = `R$ ${data.gym_revenue.toLocaleString('pt-BR', {minimumFractionDigits: 2})}`;
    
    document.getElementById('billing-table-body').innerHTML = data.transactions.map(t => `
        <tr>
            <td>${t.client}</td>
            <td>R$ ${t.value.toFixed(2)}</td>
            <td>${t.date}</td>
            <td><span class="status-badge active">Pago</span></td>
        </tr>
    `).join('');
}

// --- CATALOG MANAGEMENT ---
async function loadCatalogMgmt() {
    const res = await fetch(`/api/super/catalog-mgmt?t=${Date.now()}`, { headers: { 'Authorization': `Bearer ${masterToken}` } });
    const workouts = await res.json();
    const tbody = document.getElementById('catalog-table-body');
    tbody.innerHTML = workouts.map(w => `
        <tr>
            <td><strong>${w.title}</strong></td>
            <td>${w.trainer_name}</td>
            <td>R$ ${w.price.toFixed(2)}</td>
            <td>
                <button class="icon-btn" onclick="openCatalogModal(${JSON.stringify(w).replace(/"/g, '&quot;')})">✏️</button>
                <button class="icon-btn" style="color:#ef4444" onclick="deleteCatalogWorkout(${w.id})">🗑️</button>
            </td>
        </tr>
    `).join('') || '<tr><td colspan="4">Nenhum protocolo cadastrado.</td></tr>';
}

window.openCatalogModal = async (workout = null) => {
    const modal = document.getElementById('modal-catalog');
    const trainerSelect = document.getElementById('catalog-trainer-id');
    
    // Carregar professores para o select
    const tRes = await fetch('/api/super/trainers-detailed', { headers: { 'Authorization': `Bearer ${masterToken}` } });
    const trainers = await tRes.json();
    trainerSelect.innerHTML = trainers.map(t => `<option value="${t.id}">${t.name}</option>`).join('');

    if (workout) {
        document.getElementById('catalog-modal-title').textContent = 'Editar Protocolo';
        document.getElementById('catalog-id').value = workout.id;
        document.getElementById('catalog-title').value = workout.title;
        document.getElementById('catalog-trainer-id').value = workout.trainer_id;
        document.getElementById('catalog-desc').value = workout.description;
        document.getElementById('catalog-price').value = workout.price;
        document.getElementById('catalog-image').value = workout.image || '';
    } else {
        document.getElementById('catalog-modal-title').textContent = 'Novo Protocolo Elite';
        document.getElementById('catalog-id').value = '';
        document.getElementById('catalog-form').reset();
    }
    modal.classList.remove('hidden');
};

window.closeCatalogModal = () => document.getElementById('modal-catalog').classList.add('hidden');

window.saveCatalogWorkout = async (e) => {
    e.preventDefault();
    const id = document.getElementById('catalog-id').value;
    const data = {
        id: id,
        trainer_id: document.getElementById('catalog-trainer-id').value,
        title: document.getElementById('catalog-title').value,
        description: document.getElementById('catalog-desc').value,
        price: document.getElementById('catalog-price').value,
        image: document.getElementById('catalog-image').value
    };

    const method = id ? 'PUT' : 'POST';
    await fetch('/api/super/catalog-mgmt', {
        method,
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${masterToken}` },
        body: JSON.stringify(data)
    });
    alert('Protocolo salvo com sucesso!');
    closeCatalogModal();
    loadCatalogMgmt();
};

window.deleteCatalogWorkout = async (id) => {
    if (!confirm('Deseja excluir este protocolo do marketplace?')) return;
    await fetch(`/api/super/catalog-mgmt/${id}`, { method: 'DELETE', headers: { 'Authorization': `Bearer ${masterToken}` } });
    loadCatalogMgmt();
};

// --- FEED MODERATION ---
async function loadFeedMod() {
    const res = await fetch('/api/super/feed', { headers: { 'Authorization': `Bearer ${masterToken}` } });
    const posts = await res.json();
    const grid = document.getElementById('feed-mod-grid');
    grid.innerHTML = posts.map(p => `
        <div class="glass-card" style="padding: 0; overflow: hidden;">
            <img src="${p.image_url}" style="width: 100%; height: 150px; object-fit: cover;">
            <div style="padding: 10px;">
                <p style="font-size: 0.8rem; color: #8b5cf6;">@${p.student_name}</p>
                <p style="font-size: 0.9rem; margin: 5px 0;">${p.caption || ''}</p>
                <button class="btn-cancel" style="width: 100%; margin-top: 5px; padding: 8px; font-size: 0.8rem;" 
                        onclick="deletePostMod(${p.id})">🗑️ Remover Post</button>
            </div>
        </div>
    `).join('') || '<p>Nenhum post no feed.</p>';
}

window.deletePostMod = async (id) => {
    if (!confirm('Deseja remover este post do feed permanentemente?')) return;
    await fetch(`/api/super/feed/${id}`, { method: 'DELETE', headers: { 'Authorization': `Bearer ${masterToken}` } });
    loadFeedMod();
};

// --- EXERCISES ---
async function loadExercises() {
    try {
        const res = await fetch(`/api/super/exercises?t=${Date.now()}`, {
            headers: { 'Authorization': `Bearer ${masterToken}` }
        });
        const exercises = await res.json();
        const tbody = document.getElementById('exercises-table-body');
        
        // Agrupar por categoria
        const grouped = {};
        exercises.forEach(ex => {
            if (!grouped[ex.category]) grouped[ex.category] = [];
            grouped[ex.category].push(ex);
        });

        let html = '';
        const categories = Object.keys(grouped).sort();

        categories.forEach(cat => {
            // Linha de Categoria
            html += `
                <tr class="category-row" style="background: rgba(139, 92, 246, 0.1); font-weight: bold;">
                    <td colspan="4" style="padding: 12px; color: #8b5cf6; text-transform: uppercase; letter-spacing: 1px;">
                        📂 ${cat}
                    </td>
                </tr>
            `;

            // Exercícios da Categoria
            grouped[cat].forEach(ex => {
                html += `
                    <tr>
                        <td><img src="${resolveExImage(ex.image, ex.category)}" style="width: 50px; height: 50px; object-fit: cover; border-radius: 8px;"></td>
                        <td><strong>${ex.name}</strong></td>
                        <td>${ex.category}</td>
                        <td>
                            <button class="icon-btn" onclick="openExerciseModal(${JSON.stringify(ex).replace(/"/g, '&quot;')})">✏️</button>
                            <button class="icon-btn" style="color:#ef4444" onclick="deleteExercise(${ex.id})">🗑️</button>
                        </td>
                    </tr>
                `;
            });
        });

        tbody.innerHTML = html || '<tr><td colspan="4">Nenhum exercício cadastrado.</td></tr>';
    } catch (e) { console.error(e); }
}

function resolveExImage(imgStr, category) {
    if (imgStr && imgStr.startsWith('icon:')) {
        return `https://placehold.co/60x60/1a1a1a/8b5cf6?text=${category?.[0] || '?'}`;
    }
    return imgStr || `https://placehold.co/60x60/1a1a1a/8b5cf6?text=?`;
}

window.openExerciseModal = (ex = null) => {
    const modal = document.getElementById('modal-exercise');
    if (ex) {
        document.getElementById('exercise-modal-title').textContent = 'Editar Exercício Global';
        document.getElementById('ex-id').value = ex.id;
        document.getElementById('ex-name').value = ex.name;
        document.getElementById('ex-category').value = ex.category;
        document.getElementById('ex-image').value = ex.image || '';
        document.getElementById('ex-preview').style.backgroundImage = ex.image ? `url(${ex.image})` : '';
    } else {
        document.getElementById('exercise-modal-title').textContent = 'Novo Exercício Global';
        document.getElementById('ex-id').value = '';
        document.getElementById('exercise-form').reset();
        document.getElementById('ex-preview').style.backgroundImage = '';
    }
    modal.classList.remove('hidden');
};

window.closeExerciseModal = () => document.getElementById('modal-exercise').classList.add('hidden');

// Preview da imagem ao selecionar no Super Admin
document.addEventListener('change', (e) => {
    if (e.target.id === 'ex-file-input') {
        const file = e.target.files[0];
        console.log('Arquivo selecionado:', file);
        if (file) {
            const reader = new FileReader();
            reader.onload = function(e) {
                document.getElementById('ex-preview').style.backgroundImage = `url(${e.target.result})`;
            }
            reader.readAsDataURL(file);
        }
    }
});

async function uploadFile(inputId) {
    const input = document.getElementById(inputId);
    if (!input || !input.files[0]) {
        console.log('Nenhum arquivo para upload em:', inputId);
        return null;
    }

    const formData = new FormData();
    formData.append('file', input.files[0]);

    console.log('Iniciando upload de arquivo...');
    try {
        const res = await fetch('/api/upload', {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${masterToken}` },
            body: formData
        });
        
        if (res.ok) {
            const data = await res.json();
            console.log('Upload concluído com sucesso:', data.url);
            return data.url;
        } else if (res.status === 401 || res.status === 403) {
            localStorage.removeItem('masterToken');
            alert('Sessão expirada ou Chave Incorreta! Por favor, recarregue a página.');
            return null;
        } else {
            const error = await res.json();
            console.error('Falha no upload:', error);
            alert('Erro no upload: ' + (error.error || 'Erro desconhecido'));
        }
    } catch (e) { 
        console.error('Erro de rede no upload:', e);
        alert('Erro de rede ao fazer upload.');
    }
    return null;
}

window.saveExercise = async (e) => {
    e.preventDefault();
    console.log('Salvando exercício...');
    
    const id = document.getElementById('ex-id').value;
    
    // Upload primeiro
    const uploadedUrl = await uploadFile('ex-file-input');
    const existingUrl = document.getElementById('ex-image').value;

    const data = {
        id: id,
        name: document.getElementById('ex-name').value,
        category: document.getElementById('ex-category').value,
        image: uploadedUrl || existingUrl || `icon:${document.getElementById('ex-category').value}`
    };

    console.log('Dados do exercício a salvar:', data);

    try {
        const res = await fetch('/api/super/exercises', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${masterToken}` },
            body: JSON.stringify(data)
        });
        
        if (res.ok) {
            console.log('Exercício salvo com sucesso!');
            alert('Exercício salvo com sucesso!');
            closeExerciseModal();
            loadExercises();
        } else {
            const error = await res.json();
            console.error('Erro ao salvar exercício:', error);
            alert('Erro ao salvar: ' + (error.error || 'Erro no servidor'));
        }
    } catch (e) { 
        console.error('Erro de rede ao salvar:', e);
        alert('Erro de rede ao salvar exercício.');
    }
};

window.deleteExercise = async (id) => {
    if (!confirm('Deseja excluir este exercício da biblioteca global?')) return;
    await fetch(`/api/super/exercises/${id}`, { 
        method: 'DELETE', 
        headers: { 'Authorization': `Bearer ${masterToken}` } 
    });
    loadExercises();
};

window.clearAppCache = () => {
    if (confirm('Deseja limpar o cache e atualizar o app?')) {
        localStorage.removeItem('masterToken');
        if ('serviceWorker' in navigator) {
            navigator.serviceWorker.getRegistrations().then(registrations => {
                for (let registration of registrations) {
                    registration.unregister();
                }
                alert('Cache limpo! A página será reiniciada.');
                location.reload(true);
            });
        } else {
            location.reload(true);
        }
    }
};
