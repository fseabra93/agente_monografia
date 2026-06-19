// ==========================================================================
// ESTADO GLOBAL DA APLICAÇÃO
// ==========================================================================
const state = {
    area: "",
    ideiaBruta: "",
    listaTemas: [],
    temaSelecionado: "",
    customTema: "",
    temaEscolhido: "",
    
    listaSubtemas: [],
    subtemaSelecionado: "",
    customSubtema: "",
    subtemaEscolhido: "",
    
    listaProblemas: [],
    problemaSelecionado: "",
    customProblema: "",
    problemaEscolhido: "",
    
    listaObjetivos: [],
    objetivosSelecionados: [], // Array de strings dos objetivos marcados
    
    refClassicas: "",
    refAtuais: "",
    
    planoConsolidado: "",
    monografiaFinal: "",
    
    currentStep: 1
};

// Configurações do Marked (Markdown parser)
marked.setOptions({
    breaks: true,
    gfm: true
});

// ==========================================================================
// CONFIGURAÇÕES VISUAIS E DESCRITIVAS DOS PASSOS
// ==========================================================================
const stepConfigs = {
    1: {
        title: "Passo 1: Definição do Tema",
        desc: "Digite a área do conhecimento e descreva sua ideia inicial para receber sugestões personalizadas.",
        progress: "14%"
    },
    2: {
        title: "Passo 2: Aprofundamento do Tema",
        desc: "Mapeie os principais subtemas ou recortes de pesquisa relevantes sugeridos pelo Orientador IA.",
        progress: "28%"
    },
    3: {
        title: "Passo 3: Problema de Pesquisa",
        desc: "Selecione a pergunta norteadora que será a base para a investigação da literatura científica.",
        progress: "42%"
    },
    4: {
        title: "Passo 4: Objetivos Específicos",
        desc: "Defina os desdobramentos operacionais e etapas fundamentais para responder ao problema selecionado.",
        progress: "56%"
    },
    5: {
        title: "Passo 5: Curadoria & Estratégia de Busca",
        desc: "Base teórica recomendada e metodologia de busca booleana para recuperação em bases científicas (PubMed, SciELO, etc.).",
        progress: "70%"
    },
    6: {
        title: "Passo 6: Plano de Trabalho Consolidado",
        desc: "Confira e faça o download do plano de trabalho completo gerado e estruturado para seu TCC.",
        progress: "85%"
    },
    8: {
        title: "Passo 7: Redação da Monografia Completa",
        desc: "Esboço completo do TCC escrito pela IA seguindo as normas ABNT e baseado no plano de trabalho.",
        progress: "100%"
    }
};

// ==========================================================================
// CONTROLE DE NAVEGAÇÃO ENTRE OS PASSOS (SPA)
// ==========================================================================
function goToStep(step) {
    state.currentStep = step;
    
    // Ocultar todas as seções e mostrar apenas a ativa
    document.querySelectorAll('.step-section').forEach(sec => sec.classList.remove('active'));
    const targetSection = document.getElementById(`section-step-${step}`);
    if (targetSection) targetSection.classList.add('active');
    
    // Atualizar Sidebar links
    document.querySelectorAll('.steps-nav .step-nav-item').forEach(item => {
        const itemStep = parseInt(item.getAttribute('data-step'));
        item.classList.remove('active');
        
        if (itemStep === step) {
            item.classList.add('active');
        }
        
        // Marcar completos
        if (itemStep < step) {
            item.classList.add('completed');
        } else {
            item.classList.remove('completed');
        }
    });
    
    // Atualizar Barra de Progresso Superior e Cabeçalho
    const config = stepConfigs[step];
    if (config) {
        document.getElementById('current-step-title').textContent = config.title;
        document.getElementById('current-step-desc').textContent = config.desc;
        document.getElementById('progress-bar').style.width = config.progress;
    }
    
    // Executar gatilhos específicos de cada passo
    onStepEnter(step);
    
    // Rolar página para o topo
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// Gatilhos de carregamento automático ao entrar em etapas
function onStepEnter(step) {
    if (step === 2) {
        document.getElementById('display-tema-base').textContent = state.temaEscolhido;
        if (state.listaSubtemas.length === 0) {
            fetchSubtemas();
        }
    } else if (step === 3) {
        document.getElementById('display-step3-tema-base').textContent = state.temaEscolhido;
        document.getElementById('display-step3-subtema').textContent = state.subtemaEscolhido;
        if (state.listaProblemas.length === 0) {
            fetchProblemas();
        }
    } else if (step === 4) {
        document.getElementById('display-step4-tema-base').textContent = state.temaEscolhido;
        document.getElementById('display-step4-subtema').textContent = state.subtemaEscolhido;
        document.getElementById('display-step4-problema').textContent = state.problemaEscolhido;
        if (state.listaObjetivos.length === 0) {
            fetchObjetivos();
        }
    } else if (step === 5) {
        document.getElementById('display-step5-subtema').textContent = state.subtemaEscolhido;
        document.getElementById('display-step5-problema').textContent = state.problemaEscolhido;
        document.getElementById('display-step5-objetivos-count').textContent = `${state.objetivosSelecionados.length} objetivos selecionados`;
        if (!state.refClassicas) {
            fetchEstrategia();
        }
    } else if (step === 6) {
        renderPlanoConsolidado();
    }
}

// ==========================================================================
// CONTROLE DO MODAL DE LOADING
// ==========================================================================
let progressInterval = null;

function showLoader(title, message) {
    const overlay = document.getElementById('loading-overlay');
    document.getElementById('loading-title').textContent = title;
    document.getElementById('loading-message').textContent = message;
    
    const fill = document.getElementById('loading-progress-fill');
    fill.style.width = '0%';
    overlay.classList.remove('hidden');
    
    // Animação falsa de progresso para manter o usuário engajado
    let width = 0;
    progressInterval = setInterval(() => {
        if (width < 90) {
            width += (90 - width) * 0.05; // Vai desacelerando conforme chega perto do fim
            fill.style.width = `${width}%`;
        }
    }, 400);
}

function hideLoader() {
    clearInterval(progressInterval);
    const overlay = document.getElementById('loading-overlay');
    const fill = document.getElementById('loading-progress-fill');
    fill.style.width = '100%';
    setTimeout(() => {
        overlay.classList.add('hidden');
    }, 300);
}

// ==========================================================================
// CHAMADAS DE API (BACKEND)
// ==========================================================================

// PASSO 1: Gerar Temas
async function fetchTemas(adicional = false) {
    const areaInput = document.getElementById('area-input').value.trim();
    const ideiaInput = document.getElementById('ideia-input').value.trim();
    
    if (!areaInput || !ideiaInput) {
        alert("Por favor, preencha a Área do Conhecimento e descreva sua Ideia Inicial.");
        return;
    }
    
    state.area = areaInput;
    state.ideiaBruta = ideiaInput;
    
    if (!adicional) {
        state.listaTemas = [];
    }
    
    showLoader(
        adicional ? "Acumulando Sugestões..." : "Redigindo Sugestões...", 
        "O orientador IA está estruturando temas viáveis para uma revisão integrativa da literatura."
    );
    
    try {
        const response = await fetch('/api/gerar-temas', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                area: state.area,
                ideia_bruta: state.ideiaBruta,
                temas_existentes: state.listaTemas
            })
        });
        
        const data = await response.json();
        if (response.ok && data.temas) {
            state.listaTemas = state.listaTemas.concat(data.temas);
            renderTemas();
        } else {
            alert(data.error || "Ocorreu um erro ao gerar os temas.");
        }
    } catch (error) {
        console.error(error);
        alert("Erro na conexão com o servidor.");
    } finally {
        hideLoader();
    }
}

// PASSO 2: Gerar Subtemas
async function fetchSubtemas() {
    showLoader("Aprofundando Tema...", "Buscando recortes conceituais, populacionais e aplicados na literatura científica.");
    try {
        const response = await fetch('/api/gerar-subtemas', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                area: state.area,
                tema_base: state.temaEscolhido
            })
        });
        
        const data = await response.json();
        if (response.ok && data.subtemas) {
            state.listaSubtemas = data.subtemas;
            renderSubtemas();
        } else {
            alert(data.error || "Ocorreu um erro ao gerar os subtemas.");
        }
    } catch (error) {
        console.error(error);
        alert("Erro na conexão com o servidor.");
    } finally {
        hideLoader();
    }
}

// PASSO 3: Gerar Problemas de Pesquisa
async function fetchProblemas() {
    showLoader("Formulando Perguntas...", "Elaborando perguntas claras e delimitadas, adequadas para revisão integrativa.");
    try {
        const response = await fetch('/api/gerar-problemas', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                tema_chosen: state.temaEscolhido, // manter compatível
                tema_escolhido: state.subtemaEscolhido
            })
        });
        
        const data = await response.json();
        if (response.ok && data.problemas) {
            state.listaProblemas = data.problemas;
            renderProblemas();
        } else {
            alert(data.error || "Ocorreu um erro ao gerar as perguntas de pesquisa.");
        }
    } catch (error) {
        console.error(error);
        alert("Erro na conexão com o servidor.");
    } finally {
        hideLoader();
    }
}

// PASSO 4: Gerar Objetivos
async function fetchObjetivos() {
    showLoader("Estruturando Objetivos...", "Identificando etapas concretas e metas fundamentais para responder ao problema.");
    try {
        const response = await fetch('/api/gerar-objetivos', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                tema_escolhido: state.subtemaEscolhido,
                problema_pesquisa: state.problemaEscolhido
            })
        });
        
        const data = await response.json();
        if (response.ok && data.objetivos) {
            state.listaObjetivos = data.objetivos;
            renderObjetivos();
        } else {
            alert(data.error || "Ocorreu um erro ao gerar os objetivos.");
        }
    } catch (error) {
        console.error(error);
        alert("Erro na conexão com o servidor.");
    } finally {
        hideLoader();
    }
}

// PASSO 5: Gerar Estratégia e Referencial
async function fetchEstrategia() {
    showLoader("Mapeando Base Científica...", "Construindo o referencial teórico categorizado e as strings booleanas de busca. Isso pode levar até um minuto.");
    try {
        const response = await fetch('/api/gerar-estrategia', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                area: state.area,
                tema_escolhido: state.subtemaEscolhido
            })
        });
        
        const data = await response.json();
        if (response.ok && data.ref_classicas && data.ref_atuais) {
            state.refClassicas = data.ref_classicas;
            state.refAtuais = data.ref_atuais;
            renderEstrategia();
        } else {
            alert(data.error || "Ocorreu um erro ao gerar o referencial e a estratégia de busca.");
        }
    } catch (error) {
        console.error(error);
        alert("Erro na conexão com o servidor.");
    } finally {
        hideLoader();
    }
}

// PASSO 8: Gerar Redação Completa da Monografia
async function fetchMonografia() {
    showLoader("Redigindo Monografia...", "Estruturando e redigindo o esboço completo do TCC de acordo com as normas ABNT. Esta etapa costuma demorar de 1 a 3 minutos.");
    try {
        const response = await fetch('/api/gerar-monografia', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                area: state.area,
                plano_final_texto: state.planoConsolidado
            })
        });
        
        const data = await response.json();
        if (response.ok && data.monografia) {
            state.monografiaFinal = data.monografia;
            document.getElementById('monografia-final-rendered').innerHTML = marked.parse(state.monografiaFinal);
            goToStep(8);
        } else {
            alert(data.error || "Ocorreu um erro ao gerar o texto completo da monografia.");
        }
    } catch (error) {
        console.error(error);
        alert("Erro de conexão ao gerar monografia.");
    } finally {
        hideLoader();
    }
}

// ==========================================================================
// RENDERIZAÇÃO DOS ELEMENTOS INTERATIVOS DA UI
// ==========================================================================

// Renders do Passo 1
function renderTemas() {
    const wrapper = document.getElementById('temas-container-wrapper');
    const content = wrapper.querySelector('.results-content');
    const emptyState = wrapper.querySelector('.empty-state');
    
    emptyState.classList.add('hidden');
    wrapper.classList.remove('empty');
    content.classList.remove('hidden');
    
    // Mostrar botão de adicionar mais
    document.getElementById('btn-gerar-mais-temas').classList.remove('hidden');
    
    document.getElementById('temas-count-badge').innerHTML = `<i class="fa-solid fa-layer-group"></i> <strong>${state.listaTemas.length}</strong> sugestões geradas até agora.`;
    
    const optionsGrid = document.getElementById('temas-options');
    optionsGrid.innerHTML = '';
    
    state.listaTemas.forEach((tema, index) => {
        const card = document.createElement('div');
        card.className = `option-card ${state.temaSelecionado === tema ? 'selected' : ''}`;
        card.innerHTML = `
            <div class="option-radio-visual"></div>
            <div class="option-text-wrapper">
                <div class="option-title">${tema}</div>
            </div>
        `;
        
        card.addEventListener('click', () => {
            document.querySelectorAll('#temas-options .option-card').forEach(c => c.classList.remove('selected'));
            card.classList.add('selected');
            state.temaSelecionado = tema;
            document.getElementById('custom-tema-input').value = tema;
        });
        
        optionsGrid.appendChild(card);
    });
}

// Renders do Passo 2
function renderSubtemas() {
    const optionsGrid = document.getElementById('subtemas-options');
    optionsGrid.innerHTML = '';
    
    state.listaSubtemas.forEach((subtema, index) => {
        // Formato esperado de subtema: "Título: Justificativa"
        let titulo = subtema;
        let desc = "Relevância para o tema principal.";
        
        if (subtema.includes(':')) {
            const partes = subtema.split(':');
            titulo = partes[0].trim();
            desc = partes.slice(1).join(':').trim();
        }
        
        const card = document.createElement('div');
        card.className = `option-card ${state.subtemaSelecionado === subtema ? 'selected' : ''}`;
        card.innerHTML = `
            <div class="option-radio-visual"></div>
            <div class="option-text-wrapper">
                <div class="option-title">${titulo}</div>
                <div class="option-description">${desc}</div>
            </div>
        `;
        
        card.addEventListener('click', () => {
            document.querySelectorAll('#subtemas-options .option-card').forEach(c => c.classList.remove('selected'));
            card.classList.add('selected');
            state.subtemaSelecionado = subtema;
            document.getElementById('custom-subtema-input').value = titulo;
        });
        
        optionsGrid.appendChild(card);
    });
}

// Renders do Passo 3
function renderProblemas() {
    const optionsGrid = document.getElementById('problemas-options');
    optionsGrid.innerHTML = '';
    
    state.listaProblemas.forEach((prob, index) => {
        const card = document.createElement('div');
        card.className = `option-card ${state.problemaSelecionado === prob ? 'selected' : ''}`;
        card.innerHTML = `
            <div class="option-radio-visual"></div>
            <div class="option-text-wrapper">
                <div class="option-title">${prob}</div>
            </div>
        `;
        
        card.addEventListener('click', () => {
            document.querySelectorAll('#problemas-options .option-card').forEach(c => c.classList.remove('selected'));
            card.classList.add('selected');
            state.problemaSelecionado = prob;
            document.getElementById('custom-problema-input').value = prob;
        });
        
        optionsGrid.appendChild(card);
    });
}

// Renders do Passo 4
function renderObjetivos() {
    const optionsGrid = document.getElementById('objetivos-options');
    optionsGrid.innerHTML = '';
    
    state.listaObjetivos.forEach((obj, index) => {
        // O formato esperado costuma conter o objetivo e sua justificativa
        let titulo = obj;
        let desc = "";
        
        // Tenta separar caso venha no formato "Objetivo - Explicação"
        if (obj.includes(' - ')) {
            const parts = obj.split(' - ');
            titulo = parts[0].trim();
            desc = parts.slice(1).join(' - ').trim();
        } else if (obj.includes(': ')) {
            const parts = obj.split(': ');
            titulo = parts[0].trim();
            desc = parts.slice(1).join(': ').trim();
        }
        
        // Remove número inicial "1. ", "2. "
        if (titulo.match(/^\d+[\.\-\s]+/)) {
            titulo = titulo.replace(/^\d+[\.\-\s]+/, '');
        }
        
        const isSelected = state.objetivosSelecionados.includes(obj);
        
        const card = document.createElement('div');
        card.className = `checkbox-card ${isSelected ? 'selected' : ''}`;
        card.innerHTML = `
            <div class="option-checkbox-visual">
                <i class="fa-solid fa-check"></i>
            </div>
            <div class="option-text-wrapper">
                <div class="option-title">${titulo}</div>
                ${desc ? `<div class="option-description">${desc}</div>` : ''}
            </div>
        `;
        
        card.addEventListener('click', () => {
            if (state.objetivosSelecionados.includes(obj)) {
                state.objetivosSelecionados = state.objetivosSelecionados.filter(item => item !== obj);
                card.classList.remove('selected');
            } else {
                state.objetivosSelecionados.push(obj);
                card.classList.add('selected');
            }
        });
        
        optionsGrid.appendChild(card);
    });
}

// Renders do Passo 5
function renderEstrategia() {
    document.getElementById('estrategia-outputs').classList.remove('hidden');
    document.getElementById('estrategia-container-wrapper').querySelector('.section-instructions').textContent = "Referencial e estratégia gerados com sucesso! Revise nas abas abaixo:";
    
    document.getElementById('ref-teorico-rendered').innerHTML = marked.parse(state.refClassicas);
    document.getElementById('ref-estrategia-rendered').innerHTML = marked.parse(state.refAtuais);
    
    document.getElementById('btn-avancar-step-6').classList.remove('hidden');
}

// Renders do Passo 6: Consolidação de Dados
function renderPlanoConsolidado() {
    const dataAtual = new Date().toLocaleDateString('pt-BR', {
        day: '2-digit', month: '2-digit', year: 'numeric',
        hour: '2-digit', minute: '2-digit'
    });
    
    // Processamento da numeração dos objetivos
    let objetivosFmt = "";
    state.objetivosSelecionados.forEach((obj, idx) => {
        // Limpa numerações antigas
        let cleanObj = obj;
        if (cleanObj.match(/^\d+[\.\-\s]+/)) {
            cleanObj = cleanObj.replace(/^\d+[\.\-\s]+/, '');
        }
        objetivosFmt += `${idx + 1}. ${cleanObj}\n`;
    });
    
    state.planoConsolidado = `# Plano de Trabalho Acadêmico
---
**Data de Geração:** ${dataAtual}  
**Área do Conhecimento:** ${state.area}  
**Ideia Original do Aluno:** ${state.ideiaBruta}  

---

## 1. Tema Principal
${state.temaEscolhido}

## 2. Subtema / Recorte Específico
${state.subtemaEscolhido}

## 3. Problema de Pesquisa
${state.problemaEscolhido}

## 4. Objetivos Específicos
${objetivosFmt}

## 5. Referencial Teórico (Autores e Obras)
${state.refClassicas}

## 6. Estratégia de Busca (Metodologia)
${state.refAtuais}

---
*Gerado por MonografIA - Orientador Acadêmico com Inteligência Artificial*
`;
    
    document.getElementById('plano-consolidado-rendered').innerHTML = marked.parse(state.planoConsolidado);
}

// ==========================================================================
// FUNÇÕES DE EXPORTAÇÃO E DOWNLOAD
// ==========================================================================
function downloadMarkdown(filename, text) {
    const element = document.createElement('a');
    element.setAttribute('href', 'data:text/markdown;charset=utf-8,' + encodeURIComponent(text));
    element.setAttribute('download', filename);
    element.style.display = 'none';
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
}

// ==========================================================================
// BIND DE EVENTOS E TRIGGERS DE BOTÕES
// ==========================================================================
document.addEventListener("DOMContentLoaded", () => {
    
    // --- PASSO 1 ---
    document.getElementById('btn-gerar-temas').addEventListener('click', () => {
        fetchTemas(false);
    });
    
    document.getElementById('btn-gerar-mais-temas').addEventListener('click', () => {
        fetchTemas(true);
    });
    
    document.getElementById('btn-avancar-step-2').addEventListener('click', () => {
        const inputCustom = document.getElementById('custom-tema-input').value.trim();
        const selected = state.temaSelecionado;
        const finalTema = inputCustom || selected;
        
        if (!finalTema) {
            alert("Por favor, selecione uma das sugestões ou digite seu tema.");
            return;
        }
        
        state.temaEscolhido = finalTema;
        goToStep(2);
    });
    
    // --- PASSO 2 ---
    document.getElementById('btn-voltar-step-1').addEventListener('click', () => {
        goToStep(1);
    });
    
    document.getElementById('btn-manter-tema-original').addEventListener('click', () => {
        state.subtemaEscolhido = state.temaEscolhido;
        state.subtemaSelecionado = "";
        goToStep(3);
    });
    
    document.getElementById('btn-avancar-step-3').addEventListener('click', () => {
        const inputCustom = document.getElementById('custom-subtema-input').value.trim();
        const selected = state.subtemaSelecionado;
        
        // Se houver um selecionado mas nenhum customizado, processamos
        let finalSub = inputCustom;
        if (!finalSub && selected) {
            // Extrai só o título se for "Título: Justificativa"
            finalSub = selected.includes(':') ? selected.split(':')[0].trim() : selected;
        }
        
        if (!finalSub) {
            alert("Por favor, escolha uma opção ou configure seu subtema.");
            return;
        }
        
        state.subtemaEscolhido = finalSub;
        goToStep(3);
    });
    
    // --- PASSO 3 ---
    document.getElementById('btn-voltar-step-2').addEventListener('click', () => {
        goToStep(2);
    });
    
    document.getElementById('btn-avancar-step-4').addEventListener('click', () => {
        const inputCustom = document.getElementById('custom-problema-input').value.trim();
        const selected = state.problemaSelecionado;
        const finalProb = inputCustom || selected;
        
        if (!finalProb) {
            alert("Por favor, selecione uma das perguntas ou escreva sua própria pergunta.");
            return;
        }
        
        state.problemaEscolhido = finalProb;
        goToStep(4);
    });
    
    // --- PASSO 4 ---
    document.getElementById('btn-voltar-step-3').addEventListener('click', () => {
        goToStep(3);
    });
    
    document.getElementById('btn-avancar-step-5').addEventListener('click', () => {
        if (state.objetivosSelecionados.length === 0) {
            alert("Selecione pelo menos um objetivo para prosseguir.");
            return;
        }
        goToStep(5);
    });
    
    // --- PASSO 5 ---
    document.getElementById('btn-voltar-step-4').addEventListener('click', () => {
        goToStep(4);
    });
    
    document.getElementById('btn-avancar-step-6').addEventListener('click', () => {
        goToStep(6);
    });
    
    // Controle de Abas no Passo 5
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            
            btn.classList.add('active');
            const targetTab = btn.getAttribute('data-tab');
            document.getElementById(`tab-${targetTab}`).classList.add('active');
        });
    });
    
    // --- PASSO 6 ---
    document.getElementById('btn-voltar-step-5').addEventListener('click', () => {
        goToStep(5);
    });
    
    document.getElementById('btn-download-plano').addEventListener('click', () => {
        const filename = `plano_trabalho_monografia_${new Date().toISOString().slice(0,10)}.md`;
        downloadMarkdown(filename, state.planoConsolidated || state.planoConsolidado);
    });
    
    document.getElementById('btn-gerar-monografia-abnt').addEventListener('click', () => {
        fetchMonografia();
    });
    
    document.getElementById('btn-reiniciar-fluxo').addEventListener('click', () => {
        if (confirm("Deseja realmente apagar todo o progresso e iniciar um novo projeto?")) {
            reiniciarOrientador();
        }
    });
    
    // --- PASSO 8 (Redação Final) ---
    document.getElementById('btn-voltar-plano-step-6').addEventListener('click', () => {
        goToStep(6);
    });
    
    document.getElementById('btn-download-monografia').addEventListener('click', () => {
        const filename = `monografia_completa_${new Date().toISOString().slice(0,10)}.md`;
        downloadMarkdown(filename, state.monografiaFinal);
    });
    
    document.getElementById('btn-reiniciar-fluxo-2').addEventListener('click', () => {
        if (confirm("Deseja iniciar um novo trabalho científico?")) {
            reiniciarOrientador();
        }
    });
    
    // Adicionar cliques nos itens da barra lateral (apenas se já foram concluídos)
    document.querySelectorAll('.steps-nav .step-nav-item').forEach(item => {
        item.addEventListener('click', () => {
            const stepNum = parseInt(item.getAttribute('data-step'));
            if (item.classList.contains('completed') || item.classList.contains('active')) {
                goToStep(stepNum);
            }
        });
    });
});

// Reinicialização total do estado da aplicação
function reiniciarOrientador() {
    state.area = "";
    state.ideiaBruta = "";
    state.listaTemas = [];
    state.temaSelecionado = "";
    state.customTema = "";
    state.temaEscolhido = "";
    state.listaSubtemas = [];
    state.subtemaSelecionado = "";
    state.customSubtema = "";
    state.subtemaEscolhido = "";
    state.listaProblemas = [];
    state.problemaSelecionado = "";
    state.customProblema = "";
    state.problemaEscolhido = "";
    state.listaObjetivos = [];
    state.objetivosSelecionados = [];
    state.refClassicas = "";
    state.refAtuais = "";
    state.planoConsolidado = "";
    state.monografiaFinal = "";
    
    // Reset dos elementos de input da interface
    document.getElementById('area-input').value = "";
    document.getElementById('ideia-input').value = "";
    document.getElementById('custom-tema-input').value = "";
    document.getElementById('custom-subtema-input').value = "";
    document.getElementById('custom-problema-input').value = "";
    
    // Ocultar elementos de resultado
    document.getElementById('btn-gerar-mais-temas').classList.add('hidden');
    document.getElementById('temas-container-wrapper').classList.add('empty');
    document.getElementById('temas-container-wrapper').querySelector('.empty-state').classList.remove('hidden');
    document.getElementById('temas-container-wrapper').querySelector('.results-content').classList.add('hidden');
    
    document.getElementById('estrategia-outputs').classList.add('hidden');
    document.getElementById('btn-avancar-step-6').classList.add('hidden');
    
    // Voltar para o Passo 1
    goToStep(1);
}
