const API_URL = "http://127.0.0.1:8000";
let authToken = localStorage.getItem("authToken");
let chartStatus = null, chartMetodo = null, chartClientes = null;
let pendingAction = null;
let pinVerified = false;

const savedTheme = localStorage.getItem("darkMode");
if (savedTheme === "true") {
    document.body.classList.add("dark-mode");
    updateThemeUI(true);
}

function toggleDarkMode() {
    const isDark = document.body.classList.toggle("dark-mode");
    localStorage.setItem("darkMode", isDark);
    updateThemeUI(isDark);
    updateChartsTheme(isDark);
}

function updateThemeUI(isDark) {
    const topbarIcon = document.getElementById("topbarThemeIcon");
    if (topbarIcon) {
        if (isDark) {
            topbarIcon.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="5"></circle><line x1="12" y1="1" x2="12" y2="3"></line><line x1="12" y1="21" x2="12" y2="3"></line><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line><line x1="1" y1="12" x2="3" y2="12"></line><line x1="21" y1="12" x2="23" y2="12"></line><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line></svg>';
        } else {
            topbarIcon.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12.79A9 9 0 1111.21 3 7 7 0 0021 12.79z"></path></svg>';
        }
    }
}

function toggleSidebar() {
    const sidebar = document.getElementById("sidebar");
    const overlay = document.getElementById("sidebarOverlay");
    const dashboard = document.getElementById("dashboard");
    const isOpen = sidebar.classList.toggle("sidebar-open");
    const isMobile = window.innerWidth <= 480;

    dashboard.classList.toggle("sidebar-expanded", isOpen);
    overlay.classList.toggle("active", isOpen && isMobile);
    document.body.style.overflow = isOpen && isMobile ? "hidden" : "";
}

function closeSidebar() {
    const sidebar = document.getElementById("sidebar");
    const overlay = document.getElementById("sidebarOverlay");
    const dashboard = document.getElementById("dashboard");
    sidebar.classList.remove("sidebar-open");
    dashboard.classList.remove("sidebar-expanded");
    overlay.classList.remove("active");
    document.body.style.overflow = "";
}

function closeSidebarIfMobile() {
    if (window.innerWidth <= 480) {
        closeSidebar();
    }
}

function updateChartsTheme(isDark) {
    if (chartStatus || chartMetodo || chartClientes) {
        const gridColor = isDark ? "#1e293b" : "#f1f5f9";
        if (chartClientes) {
            chartClientes.options.scales.x.grid.color = gridColor;
            chartClientes.update();
        }
    }
}

const pageTitles = {
    homeSection: "Início",
    dashboardSection: "Dashboard",
    buscaSection: "Clientes",
    clientesSection: "Lista de Clientes",
    servicosSection: "Serviços",
    financeiroSection: "Financeiro"
};

if (authToken) showDashboard();

function setCurrentDate() {
    const now = new Date();
    const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
    const el = document.getElementById("currentDate");
    if (el) el.textContent = now.toLocaleDateString('pt-BR', options);

    const heroDateEl = document.getElementById("heroDate");
    if (heroDateEl) heroDateEl.textContent = now.toLocaleDateString('pt-BR', { day: '2-digit', month: 'short', year: 'numeric' });
}

function updatePageTitle(sectionId) {
    const title = pageTitles[sectionId] || "CRM";
    const el = document.getElementById("pageTitle");
    if (el) el.textContent = title;
}

function updateNavActive(sectionId) {
    document.querySelectorAll(".nav-item").forEach(item => {
        item.classList.toggle("active", item.dataset.section === sectionId);
    });
}

async function fazerLogin(event) {
    event.preventDefault();
    const username = document.getElementById("username").value;
    const password = document.getElementById("password").value;
    const formData = new URLSearchParams();
    formData.append("username", username);
    formData.append("password", password);

    try {
        const res = await fetch(`${API_URL}/login`, {
            method: "POST",
            headers: { "Content-Type": "application/x-www-form-urlencoded" },
            body: formData.toString()
        });

        if (res.ok) {
            const data = await res.json();
            authToken = data.access_token;
            localStorage.setItem("authToken", authToken);
            document.getElementById("loginError").style.display = "none";
            showDashboard();
        } else {
            document.getElementById("loginError").style.display = "block";
        }
    } catch (error) {
        document.getElementById("loginError").textContent = "Erro de conexão.";
        document.getElementById("loginError").style.display = "block";
    }
}

function fazerLogout() {
    authToken = null;
    localStorage.removeItem("authToken");
    pinVerified = false;
    document.getElementById("loginScreen").style.display = "flex";
    document.getElementById("dashboard").style.display = "none";
}

function showDashboard() {
    document.getElementById("loginScreen").style.display = "none";
    document.getElementById("dashboard").style.display = "block";
    setCurrentDate();
    
    const tokenData = authToken.split('.')[1];
    if (tokenData) {
        try {
            const payload = JSON.parse(atob(tokenData));
            const username = payload.sub || "Admin";
            document.getElementById("userName").textContent = username;
            document.getElementById("userAvatar").textContent = username.charAt(0).toUpperCase();
            document.getElementById("heroUserName").textContent = username.split(' ')[0];
            document.getElementById("heroGreeting").textContent = getGreeting();
        } catch (e) {}
    }
    
    showSection("homeSection");
    loadHomeStats();
}

function getGreeting() {
    const hour = new Date().getHours();
    if (hour < 12) return "Bom dia 👋";
    if (hour < 18) return "Boa tarde 👋";
    return "Boa noite 👋";
}

async function loadHomeStats() {
    try {
        const [clientesRes, resumoRes] = await Promise.all([
            fetch(`${API_URL}/clientes`, { headers: { "Authorization": `Bearer ${authToken}` } }),
            fetch(`${API_URL}/dashboard/resumo`, { headers: { "Authorization": `Bearer ${authToken}` } })
        ]);
        
        if (clientesRes.ok) {
            const clientes = await clientesRes.json();
            document.getElementById("statTotal").textContent = clientes.length;
        }
        
        if (resumoRes.ok) {
            const resumo = await resumoRes.json();
            document.getElementById("statActive").textContent = resumo.total_servicos || 0;
            document.getElementById("statRevenue").textContent = (resumo.total_recebido || 0).toLocaleString("pt-BR", { minimumFractionDigits: 2 });
        }
    } catch (error) {
        console.error("Erro ao carregar estatísticas:", error);
    }
}

function showSection(sectionId) {
    document.querySelectorAll(".section").forEach(section => {
        section.classList.toggle("active", section.id === sectionId);
    });
    updatePageTitle(sectionId);
    updateNavActive(sectionId);
    
    if (window.innerWidth <= 480) {
        closeSidebar();
    }
}

function showHome() {
    showSection("homeSection");
    resetPinSession();
}
function showClientes() {
    resetPinSession();
    showSection("buscaSection");
    updatePinBadge();
    document.getElementById("clienteDetails").innerHTML = "";
}

function showDashboardView() {
    showSection("dashboardSection");
    document.getElementById("dashPlaceholder").style.display = "block";
    document.getElementById("dashContent").style.display = "none";
}

function showServicos() {
    showSection("servicosSection");
    document.getElementById("servicosBody").innerHTML = "";
    document.getElementById("servicosLoading").style.display = "block";
    document.getElementById("servicosTotal").textContent = "";
}

function showFinanceiro() {
    showSection("financeiroSection");
    document.getElementById("financeiroBody").innerHTML = "";
    document.getElementById("financeiroLoading").style.display = "block";
    document.getElementById("financeiroTotal").textContent = "";
}

function fmt(v) {
    return "R$ " + parseFloat(v || 0).toLocaleString("pt-BR", { minimumFractionDigits: 2 });
}

function statusBadge(status, descricao) {
    const cls = `badge badge-${(status || "").toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "").replace(/\s/g, "-").replace(/^-/, "")}`;
    const isCancelado = (status || "").toLowerCase() === "cancelado";
    if (isCancelado && descricao) {
        return `<span class="${cls}" style="cursor:pointer" onclick="event.stopPropagation(); showCancelReason('${descricao.replace(/'/g, "\\'")}')">${status}</span>`;
    }
    return `<span class="${cls}">${status}</span>`;
}

function showCancelReason(reason) {
    const existing = document.getElementById("cancelReasonModal");
    if (existing) existing.remove();

    const overlay = document.createElement("div");
    overlay.id = "cancelReasonModal";
    overlay.className = "modal-overlay active";
    overlay.innerHTML = `
        <div class="modal modal-sm">
            <div class="modal-header">
                <h2>
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
                    Serviço Cancelado
                </h2>
                <button class="modal-close" onclick="this.closest('.modal-overlay').remove()">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
                </button>
            </div>
            <div class="cancel-reason-box">
                <strong>Motivo:</strong>
                <p>${reason}</p>
            </div>
            <div class="form-actions">
                <button class="btn btn-primary" onclick="this.closest('.modal-overlay').remove()">Fechar</button>
            </div>
        </div>
    `;
    overlay.addEventListener("click", (e) => { if (e.target === overlay) overlay.remove(); });
    document.body.appendChild(overlay);
}

async function loadDashboard() {
    const dataInicio = document.getElementById("dashDataInicio").value;
    const dataFim = document.getElementById("dashDataFim").value;

    let url = `${API_URL}/dashboard/resumo`;
    const params = [];
    if (dataInicio) params.push(`data_inicio=${dataInicio}`);
    if (dataFim) params.push(`data_fim=${dataFim}`);
    if (params.length) url += "?" + params.join("&");

    try {
        const res = await fetch(url, { headers: { "Authorization": `Bearer ${authToken}` } });
        if (res.status === 401) { fazerLogout(); return; }
        const d = await res.json();

        console.log("Dados do dashboard:", JSON.stringify(d, null, 2));

        document.getElementById("dashPlaceholder").style.display = "none";
        document.getElementById("dashContent").style.display = "block";

        document.getElementById("statTotalServicos").textContent = d.total_servicos || 0;
        document.getElementById("statPagos").textContent = d.servicos_pagos || 0;
        document.getElementById("statPendentes").textContent = d.servicos_pendentes || 0;
        document.getElementById("statRecebido").textContent = fmt(d.total_recebido);
        document.getElementById("statPendente").textContent = fmt(d.total_pendente);
        document.getElementById("statValorTotal").textContent = fmt(d.valor_total_contratos);

        const total = d.total_servicos || 1;
        const pctPagos = total > 0 ? Math.round(d.servicos_pagos / total * 100) : 0;
        const pctPendentes = total > 0 ? Math.round(d.servicos_pendentes / total * 100) : 0;

        document.getElementById("statPagosPct").textContent = pctPagos + "% do total";
        document.getElementById("statPendentesPct").textContent = pctPendentes + "% do total";

        const totalFiltrado = document.getElementById("dashTotalFiltrado");
        if (dataInicio || dataFim) {
            totalFiltrado.style.display = "block";
            totalFiltrado.textContent = `Total filtrado: ${fmt(d.valor_total_contratos)} (${d.total_servicos} serviço(s))`;
        } else {
            totalFiltrado.style.display = "none";
        }

        renderCharts(d);
    } catch (e) {
        console.error(e);
    }
}

function toggleServiceDesc(serviceId) {
    const descRow = document.getElementById(`desc-${serviceId}`);
    if (!descRow) return;

    const isHidden = descRow.style.display === "none";
    descRow.style.display = isHidden ? "table-row" : "none";

    const titleCell = descRow.previousElementSibling.querySelector(".service-title-cell");
    if (titleCell) {
        titleCell.classList.toggle("expanded", isHidden);
    }
}

function renderCharts(d) {
    if (chartStatus) chartStatus.destroy();
    if (chartMetodo) chartMetodo.destroy();
    if (chartClientes) chartClientes.destroy();

    const statusLabels = d.por_status.map(s => s.status);
    const statusData = d.por_status.map(s => s.quantidade);
    const statusColors = ["#10b981", "#3b82f6", "#f59e0b", "#ef4444"];

    chartStatus = new Chart(document.getElementById("chartStatus"), {
        type: "doughnut",
        data: {
            labels: statusLabels,
            datasets: [{ data: statusData, backgroundColor: statusColors, borderWidth: 0 }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { position: "bottom", labels: { padding: 16, usePointStyle: true, pointStyle: "circle" } }
            }
        }
    });

    const metodoLabels = d.por_metodo.map(m => m.metodo_pagamento);
    const metodoData = d.por_metodo.map(m => parseFloat(m.total));
    const metodoColors = ["#3b82f6", "#10b981", "#f59e0b", "#8b5cf6", "#f97316"];

    chartMetodo = new Chart(document.getElementById("chartMetodo"), {
        type: "doughnut",
        data: {
            labels: metodoLabels,
            datasets: [{ data: metodoData, backgroundColor: metodoColors.slice(0, metodoLabels.length), borderWidth: 0 }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { position: "bottom", labels: { padding: 16, usePointStyle: true, pointStyle: "circle" } }
            }
        }
    });

    const clientLabels = d.top_clientes.map(c => c.nome);
    const clientData = d.top_clientes.map(c => parseFloat(c.valor_total));

    chartClientes = new Chart(document.getElementById("chartClientes"), {
        type: "bar",
        data: {
            labels: clientLabels,
            datasets: [{ label: "Valor Total", data: clientData, backgroundColor: "#3b82f6", borderRadius: 6, barThickness: 24 }]
        },
        options: {
            indexAxis: "y",
            responsive: true,
            plugins: { legend: { display: false } },
            scales: {
                x: { beginAtZero: true, grid: { color: "#f1f5f9" } },
                y: { grid: { display: false } }
            }
        }
    });
}

async function loadServicos() {
    const status = document.getElementById("filtroServicoStatus").value;
    const clienteBusca = document.getElementById("filtroServicoCliente").value.trim();
    const dataInicio = document.getElementById("filtroServicoInicio").value;
    const dataFim = document.getElementById("filtroServicoFim").value;

    let url = `${API_URL}/dashboard/servicos`;
    const params = [];
    if (status) params.push(`status=${encodeURIComponent(status)}`);
    if (clienteBusca) params.push(`cliente_busca=${encodeURIComponent(clienteBusca)}`);
    if (dataInicio) params.push(`data_inicio=${dataInicio}`);
    if (dataFim) params.push(`data_fim=${dataFim}`);
    if (params.length) url += "?" + params.join("&");

    const tbody = document.getElementById("servicosBody");
    const loading = document.getElementById("servicosLoading");
    tbody.innerHTML = "";
    loading.style.display = "block";
    document.getElementById("servicosTotal").textContent = "";

    try {
        const res = await fetch(url, { headers: { "Authorization": `Bearer ${authToken}` } });
        if (res.status === 401) { fazerLogout(); return; }
        const data = await res.json();
        const servicos = data.servicos;
        loading.style.display = "none";

        if (servicos.length === 0) {
            loading.innerHTML = `<div class="empty-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="2" y="3" width="20" height="14" rx="2" ry="2"></rect><line x1="8" y1="21" x2="16" y2="21"></line><line x1="12" y1="17" x2="12" y2="21"></line></svg></div><span>Nenhum serviço encontrado.</span>`;
            loading.style.display = "flex";
            loading.style.flexDirection = "column";
            loading.style.alignItems = "center";
            return;
        }

        tbody.innerHTML = servicos.map(s => {
            const criadoEm = s.criado_em ? new Date(s.criado_em).toLocaleDateString('pt-BR') : "-";
            return `
            <tr class="service-row" data-id="${s.id}">
                <td>${s.id}</td>
                <td class="service-title-cell" onclick="toggleServiceDesc('${s.id}')">
                    <span class="service-title-text">${s.titulo}</span>
                    <span class="service-expand-icon">▼</span>
                </td>
                <td>${s.cliente_nome}</td>
                <td>${criadoEm}</td>
                <td>${s.prazo_entrega || "-"}</td>
                <td>${statusBadge(s.status, s.descricao)}</td>
            </tr>
            <tr class="service-desc-row" id="desc-${s.id}" style="display: none;">
                <td colspan="6" class="service-desc-cell">
                    <div class="service-desc-content">
                        <strong>Descrição:</strong>
                        <p>${s.descricao || "Sem descrição cadastrada."}</p>
                    </div>
                </td>
            </tr>
        `}).join("");
        document.getElementById("servicosTotal").textContent = `Total: ${data.total} serviço(s) | ${fmt(data.total_valor)}`;
    } catch (e) {
        loading.textContent = "Erro ao carregar.";
    }
}

async function loadFinanceiro() {
    const dataInicio = document.getElementById("filtroFinInicio").value;
    const dataFim = document.getElementById("filtroFinFim").value;
    const status = document.getElementById("filtroFinStatus").value;
    const clienteBusca = document.getElementById("filtroFinCliente").value.trim();
    const metodo = document.getElementById("filtroFinMetodo").value;

    let url = `${API_URL}/dashboard/financeiro`;
    const params = [];
    if (dataInicio) params.push(`data_inicio=${dataInicio}`);
    if (dataFim) params.push(`data_fim=${dataFim}`);
    if (status) params.push(`status=${encodeURIComponent(status)}`);
    if (clienteBusca) params.push(`cliente_busca=${encodeURIComponent(clienteBusca)}`);
    if (metodo) params.push(`metodo=${encodeURIComponent(metodo)}`);
    if (params.length) url += "?" + params.join("&");

    const tbody = document.getElementById("financeiroBody");
    const loading = document.getElementById("financeiroLoading");
    tbody.innerHTML = "";
    loading.style.display = "block";
    document.getElementById("financeiroTotal").textContent = "";

    try {
        const res = await fetch(url, { headers: { "Authorization": `Bearer ${authToken}` } });
        if (res.status === 401) { fazerLogout(); return; }
        const data = await res.json();
        const pagamentos = data.pagamentos;
        loading.style.display = "none";

        if (pagamentos.length === 0) {
            loading.innerHTML = `<div class="empty-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><line x1="12" y1="1" x2="12" y2="23"></line><path d="M17 5H9.5a3.5 3.5 0 000 7h5a3.5 3.5 0 010 7H6"></path></svg></div><span>Nenhum pagamento encontrado.</span>`;
            loading.style.display = "flex";
            loading.style.flexDirection = "column";
            loading.style.alignItems = "center";
            return;
        }

        tbody.innerHTML = pagamentos.map(p => `
            <tr>
                <td>${p.id}</td>
                <td>${p.cliente_nome}</td>
                <td>${p.servico_titulo}</td>
                <td>${fmt(p.valor_recebido)}</td>
                <td>${p.metodo_pagamento}</td>
                <td>${statusBadge(p.servico_status, p.descricao)}</td>
                <td>${p.data_pagamento || "-"}</td>
            </tr>
        `).join("");
        document.getElementById("financeiroTotal").textContent = `Total: ${data.total} pagamento(s) | ${fmt(data.total_valor)}`;
    } catch (e) {
        loading.textContent = "Erro ao carregar.";
    }
}

async function loadClientes() {
    const tbody = document.getElementById("clientesBody");
    const loading = document.getElementById("loading");
    tbody.innerHTML = "";
    loading.style.display = "block";

    try {
        const res = await fetch(`${API_URL}/clientes`, {
            headers: { "Authorization": `Bearer ${authToken}` }
        });
        if (res.status === 401) { fazerLogout(); return; }
        const clientes = await res.json();
        loading.style.display = "none";

        clientes.forEach(cliente => {
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td><strong>${cliente.nome}</strong></td>
                <td>${cliente.documento}</td>
                <td>${cliente.whatsapp}</td>
                <td>${cliente.email}</td>
                <td><button class="btn btn-outline" onclick="verDetalhes(${cliente.id})">Ver detalhes</button></td>
            `;
            tbody.appendChild(tr);
        });
    } catch (e) {
        loading.innerText = "Erro ao carregar clientes.";
    }
}

function abrirBusca(nome) {
    showSection("buscaSection");
    document.getElementById("searchInput").value = nome;
    buscarCliente();
}

async function buscarCliente() {
    if (!pinVerified) {
        pendingAction = () => buscarCliente();
        openPinModal();
        return;
    }

    const query = document.getElementById("searchInput").value.trim();
    const detailsDiv = document.getElementById("clienteDetails");

    if (!query) {
        detailsDiv.innerHTML = "<p class='no-results'>Digite algo para buscar.</p>";
        return;
    }

    detailsDiv.innerHTML = "<div class='no-results'><div class='spinner'></div>Buscando...</div>";

    try {
        const res = await fetch(`${API_URL}/clientes/buscar?q=${encodeURIComponent(query)}`, {
            headers: { "Authorization": `Bearer ${authToken}` }
        });
        if (res.status === 401) { fazerLogout(); return; }
        const clientes = await res.json();

        if (clientes.length === 0) {
            detailsDiv.innerHTML = "<p class='no-results'>Nenhum cliente encontrado.</p>";
            return;
        }

        detailsDiv.innerHTML = clientes.map(c => `
            <div class="cliente-details">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
                    <h3>${c.nome}</h3>
                    <button class="btn btn-outline" onclick="verDetalhes(${c.id})">Ver todos os detalhes</button>
                </div>
                <div class="info-grid">
                    <div class="info-item"><label>ID</label><span>${c.id}</span></div>
                    <div class="info-item"><label>Documento</label><span>${c.documento}</span></div>
                    <div class="info-item"><label>WhatsApp</label><span>${c.whatsapp}</span></div>
                    <div class="info-item"><label>Email</label><span>${c.email}</span></div>
                </div>
            </div>
        `).join("");
    } catch (e) {
        detailsDiv.innerHTML = "<p class='no-results'>Erro ao buscar.</p>";
    }
}

async function verDetalhes(clienteId) {
    if (!pinVerified) {
        pendingAction = () => verDetalhes(clienteId);
        openPinModal();
        return;
    }

    showSection("buscaSection");
    const detailsDiv = document.getElementById("clienteDetails");
    detailsDiv.innerHTML = "<div class='no-results'><div class='spinner'></div>Carregando detalhes...</div>";

    try {
        const res = await fetch(`${API_URL}/clientes/${clienteId}`, {
            headers: { "Authorization": `Bearer ${authToken}` }
        });
        if (res.status === 401) { fazerLogout(); return; }
        if (res.status === 404) {
            detailsDiv.innerHTML = "<p class='no-results'>Cliente não encontrado.</p>";
            return;
        }
        const data = await res.json();
        const { cliente, servicos, pagamentos } = data;

        const totalServicos = servicos.length;
        const totalContratos = servicos.reduce((acc, s) => acc + parseFloat(s.valor_total || 0), 0);

        const finalizados = servicos.filter(s => s.status === "Finalizado");
        const valorRecebido = finalizados.reduce((acc, s) => acc + parseFloat(s.valor_total || 0), 0);

        const pendentesEProd = servicos.filter(s => s.status === "Pendente" || s.status === "Em Produção");
        const valorPendente = pendentesEProd.reduce((acc, s) => acc + parseFloat(s.valor_total || 0), 0);

        let html = `
            <div class="cliente-details">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
                    <h2>${cliente.nome}</h2>
                    <button class="btn btn-outline" onclick="showClientes()">Voltar</button>
                </div>
                <div class="info-grid">
                    <div class="info-item"><label>ID</label><span>${cliente.id}</span></div>
                    <div class="info-item"><label>Documento</label><span>${cliente.documento}</span></div>
                    <div class="info-item"><label>WhatsApp</label><span>${cliente.whatsapp}</span></div>
                    <div class="info-item"><label>Email</label><span>${cliente.email}</span></div>
                </div>
            </div>

            <div class="stats-grid" style="margin: 20px 0;">
                <div class="stat-card">
                    <div class="stat-icon blue">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="3" width="20" height="14" rx="2" ry="2"></rect><line x1="8" y1="21" x2="16" y2="21"></line><line x1="12" y1="17" x2="12" y2="21"></line></svg>
                    </div>
                    <div class="stat-info">
                        <div class="stat-label">Serviços</div>
                        <div class="stat-value">${totalServicos}</div>
                    </div>
                </div>
                <div class="stat-card">
                    <div class="stat-icon green">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="1" x2="12" y2="23"></line><path d="M17 5H9.5a3.5 3.5 0 000 7h5a3.5 3.5 0 010 7H6"></path></svg>
                    </div>
                    <div class="stat-info">
                        <div class="stat-label">Valor Contratado</div>
                        <div class="stat-value">${fmt(totalContratos)}</div>
                    </div>
                </div>
                <div class="stat-card">
                    <div class="stat-icon green">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"></polyline></svg>
                    </div>
                    <div class="stat-info">
                        <div class="stat-label">Total Recebido</div>
                        <div class="stat-value">${fmt(valorRecebido)}</div>
                        <div class="stat-sub">${finalizados.length} serviço(s)</div>
                    </div>
                </div>
                <div class="stat-card">
                    <div class="stat-icon ${valorPendente > 0 ? 'yellow' : 'green'}">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>
                    </div>
                    <div class="stat-info">
                        <div class="stat-label">Pendente</div>
                        <div class="stat-value">${fmt(valorPendente)}</div>
                        <div class="stat-sub">${pendentesEProd.length} serviço(s)</div>
                    </div>
                </div>
            </div>

                    <div class="card" style="margin-bottom: 20px;">
                <h3 style="padding: 20px; margin: 0; font-size: 16px; font-weight: 600; border-bottom: 1px solid var(--border);">Serviços</h3>
                <div class="table-wrapper">
                    <table>
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>Título</th>
                                <th>Criado em</th>
                                <th>Valor</th>
                                <th>Prazo</th>
                                <th>Status</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${servicos.length ? servicos.map(s => {
                                const criadoEm = s.criado_em ? new Date(s.criado_em).toLocaleDateString('pt-BR') : "-";
                                return `
                                <tr class="service-row" data-id="${s.id}">
                                    <td>${s.id}</td>
                                    <td class="service-title-cell" onclick="toggleServiceDesc('${s.id}')">
                                        <span class="service-title-text">${s.titulo}</span>
                                        <span class="service-expand-icon">▼</span>
                                    </td>
                                    <td>${criadoEm}</td>
                                    <td>${fmt(s.valor_total)}</td>
                                    <td>${s.prazo_entrega || "-"}</td>
                <td>${statusBadge(s.status, s.descricao)}</td>
                                </tr>
                                <tr class="service-desc-row" id="desc-${s.id}" style="display: none;">
                                    <td colspan="6" class="service-desc-cell">
                                        <div class="service-desc-content">
                                            <strong>Descrição do serviço:</strong>
                                            <p>${s.descricao || "Sem descrição cadastrada."}</p>
                                        </div>
                                    </td>
                                </tr>
                            `}).join("") : `<tr><td colspan="6" class="no-results">Nenhum serviço registrado.</td></tr>`}
                        </tbody>
                    </table>
                </div>
            </div>

            <div class="card">
                <h3 style="padding: 20px; margin: 0; font-size: 16px; font-weight: 600; border-bottom: 1px solid var(--border);">Histórico de Pagamentos</h3>
                <div class="table-wrapper">
                    <table>
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>Serviço</th>
                                <th>Valor Recebido</th>
                                <th>Método</th>
                                <th>Data</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${pagamentos.length ? pagamentos.map(p => `
                                <tr>
                                    <td>${p.id}</td>
                                    <td>Serviço #${p.servico_id}</td>
                                    <td>${fmt(p.valor_recebido)}</td>
                                    <td>${p.metodo_pagamento}</td>
                                    <td>${p.data_pagamento || "-"}</td>
                                </tr>
                            `).join("") : `<tr><td colspan="5" class="no-results">Nenhum pagamento registrado.</td></tr>`}
                        </tbody>
                    </table>
                </div>
            </div>
        `;

        detailsDiv.innerHTML = html;
    } catch (e) {
        detailsDiv.innerHTML = "<p class='no-results'>Erro ao carregar detalhes.</p>";
    }
}

async function salvarCliente(event) {
    event.preventDefault();

    const clienteData = {
        nome: document.getElementById("nome").value,
        documento: document.getElementById("documento").value,
        whatsapp: document.getElementById("whatsapp").value,
        email: document.getElementById("email").value
    };

    const servicoData = {
        titulo: document.getElementById("servicoTitulo").value,
        descricao: document.getElementById("servicoDescricao").value,
        valor_total: parseFloat(document.getElementById("servicoValor").value) || 0,
        prazo_entrega: document.getElementById("servicoPrazo").value || null,
        status: document.getElementById("servicoStatus").value
    };

    const finData = {
        valor_recebido: parseFloat(document.getElementById("finValorRecebido").value) || 0,
        metodo_pagamento: document.getElementById("finMetodo").value
    };

    try {
        const res = await fetch(`${API_URL}/clientes/completo`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${authToken}`
            },
            body: JSON.stringify({
                cliente: clienteData,
                servico: servicoData,
                financeiro: finData
            })
        });

        if (res.ok) {
            closeModal();
            document.getElementById("clienteForm").reset();
            loadClientes();
        } else {
            const err = await res.json();
            alert("Erro: " + (err.detail || "Erro ao salvar."));
        }
    } catch (e) {
        alert("Erro de conexão.");
    }
}

function openModal() { document.getElementById("modalOverlay").classList.add("active"); }
function closeModal() { document.getElementById("modalOverlay").classList.remove("active"); }
document.getElementById("modalOverlay").addEventListener("click", function(e) { if (e.target === this) closeModal(); });
document.getElementById("searchInput").addEventListener("keypress", function(e) { if (e.key === "Enter") buscarCliente(); });

function openPinModal() {
    document.getElementById("pinModalOverlay").classList.add("active");
    document.getElementById("pinInput").value = "";
    document.getElementById("pinError").style.display = "none";
    setTimeout(() => document.getElementById("pinInput").focus(), 100);
}

function closePinModal() {
    document.getElementById("pinModalOverlay").classList.remove("active");
    pendingAction = null;
}

async function verificarPin(event) {
    event.preventDefault();
    const pin = document.getElementById("pinInput").value;

    try {
        const res = await fetch(`${API_URL}/clientes/verificar-pin`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${authToken}`
            },
            body: JSON.stringify({ pin })
        });

        if (res.ok) {
            pinVerified = true;
            updatePinBadge();
            closePinModal();
            if (pendingAction) {
                pendingAction();
                pendingAction = null;
            }
        } else {
            document.getElementById("pinError").style.display = "block";
            document.getElementById("pinInput").value = "";
            document.getElementById("pinInput").focus();
        }
    } catch (e) {
        document.getElementById("pinError").textContent = "Erro de conexão.";
        document.getElementById("pinError").style.display = "block";
    }
}

document.getElementById("pinModalOverlay").addEventListener("click", function(e) { if (e.target === this) closePinModal(); });
document.getElementById("pinInput").addEventListener("keypress", function(e) { if (e.key === "Enter") verificarPin(e); });

function resetPinSession() {
    pinVerified = false;
    updatePinBadge();
}

function updatePinBadge() {
    const badge = document.getElementById("pinStatusBadge");
    if (!badge) return;
    const text = badge.querySelector(".pin-text");
    if (pinVerified) {
        badge.classList.remove("locked");
        badge.classList.add("unlocked");
        text.textContent = "Desbloqueado";
    } else {
        badge.classList.remove("unlocked");
        badge.classList.add("locked");
        text.textContent = "Bloqueado";
    }
}

function showListaCompleta() {
    if (!pinVerified) {
        pendingAction = () => loadClientes();
        openPinModal();
        return;
    }
    loadClientes();
    showSection("clientesSection");
}
