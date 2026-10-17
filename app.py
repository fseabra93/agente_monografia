import streamlit as st
from openai import OpenAI
import os
from dotenv import load_dotenv
#from fpdf import FPDF
from io import BytesIO
from datetime import datetime

# 1. Configurações Iniciais
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

st.set_page_config(page_title="Agente Monografias", layout="wide")
st.title("🎓 Sistema de IA para escolha do tema e estratégia de pesquisa para Monografia. v1.1")
st.markdown("#### Sistema criado por Flávio Seabra (fseabra93@gmail.com)")

#st.title("")

# Estilização CSS personalizada para botões de confirmação vermelhos
st.markdown("""
<style>
/* Forçar estilo vermelho para todos os botões de confirmação (type="primary") */
button[kind="primary"],
button[data-testid="stBaseButton-primary"],
button[data-testid="baseButton-primary"],
div.stButton > button[kind="primary"],
div.stButton > button[data-testid="stBaseButton-primary"],
div.stButton > button[data-testid="baseButton-primary"],
div[data-testid="stButton"] > button[kind="primary"],
div[data-testid="stButton"] > button[data-testid="stBaseButton-primary"] {
    background-color: #d32f2f !important;
    border-color: #d32f2f !important;
    color: #ffffff !important;
    font-weight: 600 !important;
    border-radius: 6px !important;
}

button[kind="primary"]:hover,
button[data-testid="stBaseButton-primary"]:hover,
button[data-testid="baseButton-primary"]:hover,
div.stButton > button[kind="primary"]:hover,
div.stButton > button[data-testid="stBaseButton-primary"]:hover,
div.stButton > button[data-testid="baseButton-primary"]:hover,
div[data-testid="stButton"] > button[kind="primary"]:hover,
div[data-testid="stButton"] > button[data-testid="stBaseButton-primary"]:hover {
    background-color: #b71c1c !important;
    border-color: #b71c1c !important;
    color: #ffffff !important;
}

button[kind="primary"]:focus,
button[data-testid="stBaseButton-primary"]:focus,
div.stButton > button[kind="primary"]:focus,
div[data-testid="stButton"] > button[kind="primary"]:focus {
    box-shadow: 0 0 0 0.2rem rgba(211, 47, 47, 0.4) !important;
}

button[kind="primary"]:active,
button[data-testid="stBaseButton-primary"]:active,
div.stButton > button[kind="primary"]:active,
div[data-testid="stButton"] > button[kind="primary"]:active {
    background-color: #9a0007 !important;
    border-color: #9a0007 !important;
}
</style>
""", unsafe_allow_html=True)

if "step" not in st.session_state:
    st.session_state.step = 1
if "dados" not in st.session_state:
    st.session_state.dados = {}

def call_gpt(prompt):
    models = ["gpt-6-luna"]
    for m in models:
        try:
            response = client.chat.completions.create(
                model=m, 
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content
        except Exception as e:
            if m == models[-1]:
                return f"Erro na API: {e}"
            continue

area = ""

# --- AGENTE 1: ESCOLHA DO TEMA ---
if st.session_state.step == 1:
    st.header("Passo 1: Definição do Tema")
    st.subheader(f"""Digite a área do conhecimento e descreva uma ideia inicial\nLembre-se que eu sou uma IA,
     descreva a sua ideia o mais detalhado possível.""")
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    with col1:
        area = st.text_input("Área do Conhecimento", placeholder="Ex: Psicologia Organizacional")
    with col2:
        st.markdown("Descreva sua ideia aqui o mais detalhado possível", unsafe_allow_html=True)
        ideia_bruta = st.text_area(label="Descricao", label_visibility="collapsed", placeholder="Ex: Quero escrever sobre...")

    # Inicializa a lista de temas se não existir
    if "lista_temas_sugeridos" not in st.session_state:
        st.session_state.lista_temas_sugeridos = []

    def gerar_temas(adicional=False):
        # Se for uma nova busca, limpamos o que existia
        if not adicional:
            st.session_state.lista_temas_sugeridos = []

        # Criamos o contexto de exclusão com base em TUDO que já foi mostrado
        exclusao = "\n".join(st.session_state.lista_temas_sugeridos)
        contexto_exclusao = f"\nNÃO repita nenhum destes temas:\n{exclusao}" if exclusao else ""

        prompt = f"""Você é um especialista em metodologia de pesquisa científica com ampla experiência 
            em orientação de trabalhos de conclusão de curso na área de {area}.

            Sua tarefa é sugerir temas viáveis para uma monografia no formato de revisão 
            integrativa da literatura.

            Contexto fornecido pelo estudante:
            - Área de conhecimento: {area}
            - Ideia ou interesse inicial: {ideia_bruta}

            Critérios para os temas sugeridos:
            - Devem ser adequados ao escopo de uma revisão integrativa (ou seja, precisam 
            ter literatura científica suficiente para ser revisada)
            - Devem ser específicos o bastante para um TCC de graduação, sem serem amplos 
            demais nem restritos demais
            - Devem estar alinhados com o interesse inicial do estudante, explorando 
            variações, recortes e abordagens diferentes
            - Devem ser formulados como títulos acadêmicos, de forma clara e objetiva

            {contexto_exclusao}

            Gere exatamente 10 sugestões de temas, apresentadas em lista numerada de 1 a 10, 
            contendo apenas os títulos, sem explicações ou comentários adicionais."""
        
        resposta = call_gpt(prompt)
        linhas = resposta.strip().split('\n')
        # Extrai o texto ignorando o número inicial
        novos_temas = [l.split('.', 1)[-1].strip() for l in linhas if l.strip() and l[0].isdigit()]
        
        # CONCATENA: Adiciona os novos temas à lista existente
        st.session_state.lista_temas_sugeridos.extend(novos_temas)

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("Gerar Sugestões Iniciais"):
            # Lógica de validação obrigatória
            if not area.strip() and not ideia_bruta.strip():
                st.error("Por favor, preencha a **Área do Conhecimento** e a **Ideia Inicial**.")
            elif not area.strip():
                st.warning("O campo **Área do Conhecimento** é obrigatório.")
            elif not ideia_bruta.strip():
                st.warning("O campo **Descreva sua ideia** é obrigatório.")
            else:
                with st.spinner("O orientador IA está redigindo os temas..."):
                    gerar_temas(adicional=False)
                st.rerun()
            
    with col_btn2:
        # O botão "Gerar +10" herda a validação pois a lista só existirá se o Passo 1 for bem-sucedido
        if st.session_state.lista_temas_sugeridos:
            if st.button("🔄 Gerar +10 Sugestões (Acumular)"):
                with st.spinner("Buscando novas abordagens e acumulando..."):
                    gerar_temas(adicional=True)
                st.rerun()

    # Exibição acumulada
    if st.session_state.lista_temas_sugeridos:
  #      st.info(f"""Foram geradas {len(st.session_state.lista_temas_sugeridos)} sugestões até agora.<br>
   #         clique no botão Gerar Sugestões Iniciais para descartar as atuais e gerar novas ou no<br>
    #        botão Gerar +10 para manter as atuais e gerar mais 10.""")

        st.info(f"""{len(st.session_state.lista_temas_sugeridos)} sugestões geradas até agora.\n
                Clique em Gerar Sugestões Iniciais para descartar as atuais e começar do zero,
                ou em Gerar +10 para manter as atuais e adicionar mais 10 sugestões.""")        
        
        tema_selecionado = st.radio(
            "Selecione o tema que deseja utilizar:",
            st.session_state.lista_temas_sugeridos,
            index=None,
            help="Esta lista contém todas as sugestões geradas nesta sessão."
        )
        
        outra_opcao = st.text_input("Você pode também digitar livremente um outro tema aqui:")
        
        if st.button("Confirmar Tema e Avançar", type="primary", key="btn_confirmar_step1"):
            escolha_final = outra_opcao if outra_opcao.strip() else tema_selecionado
            if escolha_final:
                st.session_state.dados['area_usuario'] = area
                st.session_state.dados['ideia_usuario'] = ideia_bruta
                
                # Se o tema base mudou, reinicializa as escolhas posteriores
                if st.session_state.dados.get('tema_base') != escolha_final:
                    st.session_state.pop('subtemas_lista', None)
                    st.session_state.pop('probs_lista', None)
                    st.session_state.pop('lista_objs', None)
                    st.session_state.dados.pop('ref_classicas', None)
                    st.session_state.dados.pop('ref_atuais', None)
                
                st.session_state.dados['tema_base'] = escolha_final
                st.session_state.step = 2
                st.rerun()

# --- AGENTE 2: APROFUNDAMENTO ---
elif st.session_state.step == 2:
    st.header("Passo 2: Aprofundamento do Tema")
    
    st.info(f"**Tema Base Selecionado:** {st.session_state.dados['tema_base']}")
    st.divider()

    if "subtemas_lista" not in st.session_state or not st.session_state.subtemas_lista:
        area_atual = st.session_state.dados.get('area_usuario') or area or "sua área de estudo"
        with st.spinner("O orientador está gerando 6 subtemas específicos e abrangentes..."):

            prompt = f"""
                    Você é um especialista em metodologia de pesquisa científica com ampla experiência 
                    em revisões integrativas da literatura na área de {area_atual}.

                    Sua tarefa é mapear os principais subtemas que compõem ou se relacionam diretamente 
                    com o seguinte tema de pesquisa:

                    Tema central: {st.session_state.dados['tema_base']}

                    Entende-se por subtema um recorte temático específico que pode ser investigado 
                    de forma independente dentro do tema central, com literatura científica própria 
                    e relevância para uma revisão integrativa de TCC de graduação.

                    Critérios obrigatórios para as sugestões:
                    - Gere exatamente 6 sugestões de subtemas em lista numerada de 1 a 6.
                    - As 6 opções DEVEM ser abrangentes e contemplar todos os aspectos relevantes do tema abordado (por exemplo: dimensões conceituais/teóricas, metodológicas, populacionais/público-alvo, organizacionais/contextuais, tecnológicas/aplicadas e impactos/desfechos).
                    - É ESTRITAMENTE PROIBIDO que existam duas opções que tratem do tema de forma muito parecida ou redundante. Cada uma das 6 opções deve representar um eixo temático distinto e independente.
                    - Devem ser recortes diretos do tema central, com literatura científica disponível suficiente para uma revisão integrativa.
                    - Devem ser viáveis no escopo de um TCC de graduação.
                    
                    Output:
                    Gere exatamente 6 sugestões de subtemas em lista numerada de 1 a 6.
                    Cada item deve conter o título do subtema escrito em negrito seguido de uma breve justificativa 
                    acadêmica de sua relevância para o tema central, no seguinte formato:
                    **{{título do subtema}}**: {{justificativa}};
                    Use linguagem acadêmica formal.
                    """
            
            res = call_gpt(prompt)
            # Processa a resposta para garantir uma lista limpa com exatamente 6 opções
            st.session_state.subtemas_lista = [l.split('.', 1)[-1].strip() if '.' in l[:3] else l.strip() 
                                            for l in res.strip().split('\n') if l.strip()][:6]

    # Interface de Seleção por Clique
    sub_selecionado = st.radio(
        "Selecione um recorte específico para sua pesquisa (6 opções abrangentes):",
        st.session_state.subtemas_lista,
        index=None,
        help="Clique em uma das opções geradas pela IA"
    )
    
    outra_opcao = st.text_input("Ou digite livremente um subtema aqui:")

    col_voltar, col_acc2, col_acc1 = st.columns([1, 1, 1])
    with col_voltar:
        if st.button("⬅️ Retornar ao passo anterior", key="btn_voltar_step2"):
            st.session_state.step = 1
            st.rerun()

    with col_acc2:
        if st.button("⏩ Manter Tema Original", key="btn_manter_tema"):
            st.session_state.dados['tema_escolhido'] = st.session_state.dados['tema_base']
            st.session_state.step = 3
            st.rerun()

    with col_acc1:
        if st.button("Confirmar Subtema", type="primary", key="btn_confirmar_step2"):
            escolha_final = outra_opcao if outra_opcao.strip() else sub_selecionado
            if escolha_final:
                st.session_state.dados['tema_escolhido'] = escolha_final
                st.session_state.step = 3
                st.rerun()
            else:
                st.warning("Selecione uma opção ou descreva seu tema.")



# --- AGENTE 3: PROBLEMA DE PESQUISA ---
elif st.session_state.step == 3:
    st.header("Passo 3: Problema de Pesquisa")
    
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        st.info(f"**Tema Base:**\n\n{st.session_state.dados.get('tema_base', '')}")
    with col_c2:
        sub = st.session_state.dados.get('tema_escolhido', '')
        # Diferencia visualmente se o usuário pulou ou não o subtema
        if sub == st.session_state.dados.get('tema_base', ''):
            st.success("**Subtema:** Usando tema base original")
        else:
            st.success(f"**Subtema Escolhido:**\n\n{sub}")
    
    st.divider()

    if "probs_lista" not in st.session_state or not st.session_state.probs_lista:
        with st.spinner("Formulando 6 problemas de pesquisa abrangentes e distintos..."):
            prompt = f"""Você é um especialista em metodologia de pesquisa científica com ampla experiência 
                            em revisões integrativas da literatura.

                            Sua tarefa é formular problemas de pesquisa adequados para uma monografia no 
                            formato de revisão integrativa da literatura, a partir do seguinte tema:

                            Tema escolhido: {st.session_state.dados['tema_escolhido']}

                            Entende-se por problema de pesquisa uma pergunta clara, delimitada e investigável 
                            que orienta toda a revisão, cuja resposta pode ser construída a partir da análise 
                            crítica da literatura científica existente — sem coleta de dados primários.

                            Critérios obrigatórios para as sugestões:
                            - Gere exatamente 6 sugestões de problema de pesquisa em lista numerada de 1 a 6.
                            - As 6 opções DEVEM ser abrangentes e cobrir diferentes aspectos e dimensões relevantes do tema abordado (por exemplo: relações e associações entre variáveis, fatores condicionantes ou facilitadores/barreiras, impactos ou efetividade de abordagens, desafios operacionais ou metodológicos, lacunas conceituais e tendências evolutivas da literatura).
                            - É ESTRITAMENTE PROIBIDO que existam duas opções que tratem do tema de forma muito parecida ou com o mesmo foco investigativo. Cada pergunta deve propor um ângulo de análise claramente distinto.
                            - Devem ser perguntas respondíveis por meio de revisão da literatura, 
                            não por experimentos ou coleta de dados primários.
                            - Devem ter escopo adequado a um TCC de graduação: nem amplos demais 
                            (impossíveis de responder) nem restritos demais (literatura insuficiente).
                            - Devem ser formuladas de forma clara, objetiva e em linguagem acadêmica formal.

                            Output:
                            Gere exatamente 6 sugestões de problema de pesquisa em lista numerada de 1 a 6,
                            apresentando apenas as perguntas, sem comentários ou explicações adicionais."""
            
            res_bruta = call_gpt(prompt)
            st.session_state.probs_lista = [l.split('.', 1)[-1].strip() if '.' in l[:3] else l.strip() 
                                           for l in res_bruta.strip().split('\n') if l.strip()][:6]

    # Interface de Seleção por Clique
    prob_selecionado = st.radio(
        "Selecione a pergunta norteadora do seu trabalho (6 opções abrangentes):",
        st.session_state.probs_lista,
        index=None
    )

    ajuste_prob = st.text_area("Deseja editar ou escrever seu próprio problema?", 
                               placeholder="Se selecionou uma opção acima e quer mudar algo, escreva aqui.")

    col_voltar, col_confirmar = st.columns([1, 2])
    with col_voltar:
        if st.button("⬅️ Retornar ao passo anterior", key="btn_voltar_step3"):
            st.session_state.step = 2
            st.rerun()

    with col_confirmar:
        if st.button("Confirmar Problema de Pesquisa", type="primary", key="btn_confirmar_step3"):
            escolha_final = ajuste_prob if ajuste_prob.strip() else prob_selecionado
            if escolha_final:
                if st.session_state.dados.get('problema_pesquisa') != escolha_final:
                    st.session_state.pop('lista_objs', None)
                st.session_state.dados['problema_pesquisa'] = escolha_final
                st.session_state.step = 4
                st.rerun()
            else:
                st.warning("Por favor, selecione uma das opções acima.")

# --- AGENTE 4: OBJETIVOS ---
elif st.session_state.step == 4:
    st.header("Agente 4: Objetivos Específicos")

    # --- PAINEL DE CONTEXTO (Escolhas anteriores) ---
    st.markdown("### Resumo das definições anteriores")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.info(f"**1. Tema Base**\n\n{st.session_state.dados.get('tema_base', '')}")
    with c2:
        st.success(f"**2. Subtema**\n\n{st.session_state.dados.get('tema_escolhido', '')}")
    with c3:
        st.warning(f"**3. Problema**\n\n{st.session_state.dados.get('problema_pesquisa', '')}")
    
    st.divider()

    # Lógica Original de Geração
    if "lista_objs" not in st.session_state:
        with st.spinner("Gerando sugestões de objetivos..."):
            prompt = f"""Você é um especialista em metodologia de pesquisa científica com ampla experiência 
                em revisões integrativas da literatura.

                Sua tarefa é sugerir objetivos específicos adequados para uma monografia no 
                formato de revisão integrativa da literatura, com base no seguinte contexto:

                Tema: {st.session_state.dados['tema_escolhido']}
                Problema de pesquisa: {st.session_state.dados['problema_pesquisa']}

                Entende-se por objetivo específico um desdobramento operacional do objetivo geral, 
                que descreve uma etapa concreta e alcançável da pesquisa. Em uma revisão integrativa, 
                os objetivos específicos tipicamente envolvem ações como identificar, descrever, 
                analisar, comparar, sintetizar ou discutir aspectos da literatura sobre o tema.

                Critérios para as sugestões:
                - Devem ser diretamente derivados do problema de pesquisa apresentado
                - Devem ser alcançáveis exclusivamente por meio da análise da literatura científica,
                sem coleta de dados primários
                - Devem ser redigidos com verbo no infinitivo no início da frase, 
                conforme norma acadêmica (ex: Identificar, Analisar, Comparar, Sintetizar)
                - Devem ser complementares entre si, cobrindo diferentes dimensões do problema,
                sem sobreposição ou redundância
                - Devem ter escopo adequado a um TCC de graduação

                Gere exatamente 10 sugestões em lista numerada de 1 a 10.
                Cada item deve conter:
                - O objetivo específico redigido em uma frase iniciada por verbo no infinitivo
                - Uma explicação em até dois parágrafos justificando sua relevância e como 
                ele contribui para responder ao problema de pesquisa"""

            res = call_gpt(prompt)
            # Mantendo sua lógica de parsing original do arquivo app3.py
            st.session_state.lista_objs = [l.strip() for l in res.split('\n') if l.strip() and any(c.isdigit() for c in l[:3])]

    st.markdown("### Selecione os objetivos que farão parte do seu trabalho:")
    
    # Lógica Original de Seleção (Checkboxes)
    selecionados = []
    for i, obj in enumerate(st.session_state.lista_objs):
        if st.checkbox(obj, key=f"obj_{i}"):
            selecionados.append(obj)
            
    col_voltar, col_confirmar = st.columns([1, 2])
    with col_voltar:
        if st.button("⬅️ Retornar ao passo anterior", key="btn_voltar_step4"):
            st.session_state.step = 3
            st.rerun()

    with col_confirmar:
        if st.button("Confirmar Objetivos", type="primary", key="btn_confirmar_step4"):
            if selecionados:
                st.session_state.dados['objetivos'] = "\n".join(selecionados)
                st.session_state.step = 5
                st.rerun()
            else:
                st.warning("Selecione ao menos um objetivo antes de avançar.")

# # --- AGENTE 5 & 6: REFERÊNCIAS E ESTRATÉGIA ---
elif st.session_state.step == 5:
    st.header("Agentes 5 e 6: Curadoria e Estratégia de Pesquisa")
    
    # --- PAINEL DE CONTEXTO ACUMULADO (Dashboard de Revisão) ---
    st.markdown("### 📋 Resumo Consolidado do Projeto")
    c1, c2, c3 = st.columns(3)
    with c1: st.info(f"**Tema/Subtema**\n\n{st.session_state.dados.get('tema_escolhido', '')}")
    with c2: st.success(f"**Problema**\n\n{st.session_state.dados.get('problema_pesquisa', '')}")
    with c3: st.warning(f"**Objetivos**\n\n{st.session_state.dados.get('objetivos', '')}")
    st.divider()

    if "ref_classicas" not in st.session_state.dados:
        with st.spinner("Construindo base teórica e estratégia de busca... Essa etapa pode demorar alguns minutos"):
            # --- Agente 5: Referencial Teórico Categorizado ---
            p5 = f"""Você é um especialista em metodologia de pesquisa científica e revisão de literatura,
                com conhecimento aprofundado sobre o campo de {area}.

                Sua tarefa é mapear o panorama intelectual da literatura sobre o tema a seguir,
                auxiliando um estudante de graduação a compreender as bases teóricas antes de 
                iniciar sua revisão integrativa.

                Tema: {st.session_state.dados['tema_escolhido']}

                Sua resposta deve ser organizada em duas partes:

                PARTE 1 — MAPA DA LITERATURA

                Apresente uma tabela em formato Markdown com as seguintes colunas:
                Autor | Obra ou Linha de Pesquisa | Período de Influência | Contribuição para o Tema

                Inclua entre 8 e 12 entradas, distribuídas entre:
                - Autores e obras seminais que estabeleceram os fundamentos do tema
                - Autores contemporâneos de referência que consolidaram ou expandiram o campo

                ATENÇÃO: Inclua apenas autores e obras dos quais você tenha alta certeza de 
                existência e conteúdo. Se não tiver certeza sobre um título exato, descreva 
                a linha de pesquisa do autor em vez de arriscar um título incorreto.

                PARTE 2 — CORRENTES DE PENSAMENTO

                Em linguagem acadêmica formal, descreva em 2 a 3 parágrafos as principais 
                correntes teóricas ou perspectivas identificadas na literatura sobre o tema, 
                destacando convergências, divergências e eventuais lacunas que justificam 
                novas revisões sobre o assunto."""
            
            st.session_state.dados['ref_classicas'] = call_gpt(p5)

# --- Agente 6: Estratégia Avançada (Validada via DeCS/MeSH) ---
            ano_atual = datetime.now().year
            ano_inicial = ano_atual - 5
            
            p6 = f"""Você é um especialista em Biblioteconomia, Ciência da Informação e recuperação 
                de informação em bases de dados científicas, com amplo conhecimento sobre os 
                vocabulários controlados DeCS (Descritores em Ciências da Saúde) e MeSH 
                (Medical Subject Headings).

                Sua tarefa é construir uma estratégia de busca estruturada para uma revisão 
                integrativa da literatura sobre o tema a seguir:

                Tema: {st.session_state.dados['tema_escolhido']}
                Período: {ano_inicial} a {ano_atual}
                Idiomas: Português, Inglês e Espanhol

                INSTRUÇÃO CRÍTICA SOBRE DESCRITORES:
                Inclua APENAS descritores dos quais você tenha alta certeza de que são termos 
                controlados válidos no DeCS ou MeSH. Se não tiver certeza sobre um descritor 
                específico, substitua-o por um termo livre relevante e sinalize claramente 
                que se trata de termo livre (não controlado). Nunca apresente um termo livre 
                como se fosse descritor controlado.

                Organize sua resposta nas seguintes seções:

                SEÇÃO 1 — DESCRITORES IDENTIFICADOS

                Apresente uma tabela Markdown com as colunas:
                Descritor (PT) | Descritor (EN) | Fonte (DeCS / MeSH / Termo Livre) | Observação

                SEÇÃO 2 — STRINGS DE BUSCA

                Para cada base abaixo, apresente a string em bloco de código, 
                construída com operadores booleanos (AND, OR, NOT) e, quando aplicável, 
                com uso de aspas para expressões exatas e truncamento (*):
                ```pubmed
                [string para PubMed]
                ```
                ```scielo
                [string para SciELO]
                ```
                ```lilacs
                [string para Lilacs]
                ```
                ```google_academico
                [string para Google Acadêmico]
                ```

                SEÇÃO 3 — FILTROS RECOMENDADOS

                Descreva os filtros a serem aplicados em cada base para restringir os 
                resultados ao período {ano_inicial}–{ano_atual} e aos idiomas definidos,
                considerando as particularidades de cada plataforma.

                SEÇÃO 4 — ORIENTAÇÕES DE USO

                Em até um parágrafo por base, oriente o estudante sobre como aplicar 
                a string e os filtros na interface de cada plataforma, e recomende que 
                todos os descritores sejam verificados diretamente no portal DeCS 
                (decs.bvsalud.org) e no MeSH (meshb.nlm.nih.gov) antes do uso."""
            
            st.session_state.dados['ref_atuais'] = call_gpt(p6)
            
            st.session_state.step = 6
            st.rerun()

# --- AGENTE 7: CONSOLIDAÇÃO E EXPORTAÇÃO ---
elif st.session_state.step == 6:
    #st.header("Agente 7: Consolidação e Exportação")
    
    # Processamento dos objetivos para numeração progressiva
    objetivos_brutos = st.session_state.dados.get('objetivos', '')
    lista_objetivos = [obj.split('.', 1)[-1].strip() for obj in objetivos_brutos.split('\n') if obj.strip()]
    objetivos_numerados = ""
    for idx, obj in enumerate(lista_objetivos, 1):
        objetivos_numerados += f"{idx}. {obj}\n"

    # Preparação do conteúdo Markdown
# Preparação do conteúdo Markdown
    def gerar_conteudo_markdown():
        # Resgatando os dados exatos salvos no Agente 1
        area_user = st.session_state.dados.get('area_usuario', 'Não informada')
        ideia_user = st.session_state.dados.get('ideia_usuario', 'Não informada')

        md_text = f"""# Plano de Trabalho Acadêmico
---
**Data de Geração:** {datetime.now().strftime('%d/%m/%Y %H:%M')}

**Área informada:** {area_user}  
**Ideia original digitada pelo usuário:** {ideia_user}

---

## 1. Tema Principal
{st.session_state.dados.get('tema_base', 'Não definido')}

## 2. Subtema / Recorte Específico
{st.session_state.dados.get('tema_escolhido', 'Mesmo que o tema principal')}

## 3. Problema de Pesquisa
{st.session_state.dados.get('problema_pesquisa', 'Não definido')}

## 4. Objetivos Específicos
{objetivos_numerados}

## 5. Referencial Teórico (Autores e Obras)
{st.session_state.dados.get('ref_classicas', 'Não gerado')}

## 6. Estratégia de Busca (Metodologia)
{st.session_state.dados.get('ref_atuais', 'Não gerada')}

---
*Gerado pelo Sistema de IA para Monografia*
"""
        return md_text

    conteudo_md = gerar_conteudo_markdown()

    # Exibição na tela para conferência
    with st.expander("Visualizar rascunho completo", expanded=True):
        st.markdown(conteudo_md)

    st.divider()

    col_dl, col_voltar, col_reiniciar = st.columns([2, 1, 1])
    with col_dl:
        st.download_button(
            label="📥 Baixar Plano em Markdown (.md)",
            data=conteudo_md,
            file_name=f"plano_monografia_{datetime.now().strftime('%Y%m%d_%H%M')}.md",
            mime="text/markdown",
            use_container_width=True
        )

    with col_voltar:
        if st.button("⬅️ Retornar ao passo anterior", key="btn_voltar_step6", use_container_width=True):
            st.session_state.step = 4
            st.rerun()

    with col_reiniciar:
        if st.button("🔄 Reiniciar Sistema", key="btn_reiniciar", use_container_width=True):
            st.session_state.clear()
            st.rerun()