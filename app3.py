import streamlit as st
import os
from dotenv import load_dotenv
from datetime import datetime
from typing import TypedDict, List, Annotated
import operator

# LangChain & LangGraph Imports
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, END

# 1. Configurações Iniciais
load_dotenv()

# Configuração da Página
st.set_page_config(page_title="Agente Monografias (LangGraph)", layout="wide")
st.title("🎓 Sistema de IA para escolha do tema e estratégia (LangGraph Edition)")

# --- DEFINIÇÃO DO ESTADO DO AGENTE (LangGraph) ---
class AgentState(TypedDict):
    # Inputs do Usuário
    area_conhecimento: str
    ideia_bruta: str
    
    # Controle de Fluxo
    step_atual: str  # 'temas', 'subtemas', 'problema', 'objetivos', 'referencias'
    
    # Dados Gerados/Selecionados
    lista_temas_sugeridos: Annotated[List[str], operator.add] # Permite acumular temas
    tema_selecionado: str
    
    lista_subtemas: List[str]
    subtema_selecionado: str
    
    lista_problemas: List[str]
    problema_selecionado: str
    
    lista_objetivos: List[str]
    objetivos_selecionados: str # String consolidada
    
    ref_teorica: str
    ref_estrategia: str

# --- INICIALIZAÇÃO DO LLM ---
# Nota: gpt-5.1 ainda não é público/estável. Mudei para gpt-4o para garantir funcionamento.
llm = ChatOpenAI(model="gpt-5.1", temperature=0.2, api_key=os.getenv("OPENAI_API_KEY"))

# --- DEFINIÇÃO DOS NÓS (NODES) DO GRAFO ---

def node_gerar_temas(state: AgentState):
    """Agente 1: Gera sugestões de temas"""
    area = state['area_conhecimento']
    ideia = state['ideia_bruta']
    
    # Contexto de exclusão (se já houver temas na lista, não repetir)
    exclusao = "\n".join(state.get('lista_temas_sugeridos', []))
    contexto_exclusao = f"\nNÃO repita nenhum destes temas:\n{exclusao}" if exclusao else ""

    prompt = f"""Você é um especialista em metodologia de pesquisa científica com ampla experiência 
            em orientação de trabalhos de conclusão de curso na área de {area}.

            Sua tarefa é sugerir temas viáveis para uma monografia no formato de revisão 
            integrativa da literatura.

            Contexto fornecido pelo estudante:
            - Área de conhecimento: {area}
            - Ideia ou interesse inicial: {ideia}

            Critérios para os temas sugeridos:
            - Devem ser adequados ao escopo de uma revisão integrativa.
            - Devem ser formulados como títulos acadêmicos.
            - Devem estar alinhados com o interesse inicial.

            {contexto_exclusao}

            Gere exatamente 10 sugestões de temas, apresentadas em lista numerada de 1 a 10, 
            contendo apenas os títulos, sem explicações."""
    
    response = llm.invoke([HumanMessage(content=prompt)])
    content = response.content
    
    # Parsing
    linhas = content.strip().split('\n')
    novos_temas = [l.split('.', 1)[-1].strip() for l in linhas if l.strip() and l[0].isdigit()]
    
    return {"lista_temas_sugeridos": novos_temas}

def node_aprofundamento(state: AgentState):
    """Agente 2: Gera subtemas"""
    tema_base = state['tema_selecionado']
    area = state['area_conhecimento']
    
    prompt = f"""
            Você é um especialista em revisões integrativas na área de {area}.
            Tema central: {tema_base}

            Sua tarefa é mapear 10 subtemas (recortes específicos) para este tema.
            
            Output:
            Lista numerada de 1 a 10.
            Formato: {{título do subtema}}: {{justificativa}}
            """
    
    response = llm.invoke([HumanMessage(content=prompt)])
    content = response.content
    
    # Parsing
    subtemas = [l.split('.', 1)[-1].strip() if '.' in l[:3] else l.strip() 
                for l in content.strip().split('\n') if l.strip()]
    
    return {"lista_subtemas": subtemas}

def node_problema_pesquisa(state: AgentState):
    """Agente 3: Formula problemas de pesquisa"""
    subtema = state['subtema_selecionado']
    
    prompt = f"""Você é um especialista em metodologia.
                Tema escolhido: {subtema}

                Formule 10 problemas de pesquisa (perguntas) para uma revisão integrativa.
                Gere apenas as perguntas em lista numerada."""
    
    response = llm.invoke([HumanMessage(content=prompt)])
    content = response.content
    
    probs = [l.split('.', 1)[-1].strip() if '.' in l[:3] else l.strip() 
             for l in content.strip().split('\n') if l.strip()]
    
    return {"lista_problemas": probs}

def node_objetivos(state: AgentState):
    """Agente 4: Gera objetivos específicos"""
    subtema = state['subtema_selecionado']
    problema = state['problema_selecionado']
    
    prompt = f"""Contexto:
                Tema: {subtema}
                Problema: {problema}

                Sugira 10 objetivos específicos para uma revisão integrativa.
                Verbos no infinitivo.
                Lista numerada de 1 a 10.
                Formato: Objetivo - Justificativa."""

    response = llm.invoke([HumanMessage(content=prompt)])
    content = response.content
    
    objs = [l.strip() for l in content.split('\n') if l.strip() and any(c.isdigit() for c in l[:3])]
    
    return {"lista_objetivos": objs}

def node_referencias_estrategia(state: AgentState):
    """Agentes 5 e 6: Gera referencial e estratégia de busca"""
    tema = state['subtema_selecionado']
    area = state['area_conhecimento']
    ano_atual = datetime.now().year
    ano_inicial = ano_atual - 5

    # Parte 1: Referencial Teórico
    p5 = f"""Você é especialista em {area}.
            Tema: {tema}
            
            PARTE 1: Gere uma tabela Markdown (Autor | Obra | Período | Contribuição) com 8-12 referências clássicas e contemporâneas.
            PARTE 2: Escreva 2-3 parágrafos sobre as principais correntes teóricas."""
    
    resp_teorica = llm.invoke([HumanMessage(content=p5)])

    # Parte 2: Estratégia de Busca
    p6 = f"""Especialista em Biblioteconomia.
            Tema: {tema}
            Período: {ano_inicial}-{ano_atual}.
            
            Crie uma estratégia de busca (Strings para PubMed, SciELO, Lilacs, Google Scholar) e sugira descritores (DeCS/MeSH)."""
    
    resp_estrategia = llm.invoke([HumanMessage(content=p6)])
    
    return {
        "ref_teorica": resp_teorica.content,
        "ref_estrategia": resp_estrategia.content
    }

# --- CONSTRUÇÃO DO GRAFO ---

workflow = StateGraph(AgentState)

# Adiciona os nós
workflow.add_node("gerar_temas", node_gerar_temas)
workflow.add_node("gerar_subtemas", node_aprofundamento)
workflow.add_node("gerar_problemas", node_problema_pesquisa)
workflow.add_node("gerar_objetivos", node_objetivos)
workflow.add_node("gerar_referencias", node_referencias_estrategia)

# Define o Router (Ponto de Entrada Dinâmico)
# Como o Streamlit é orientado a eventos, definimos qual nó executar com base no 'step_atual'
def route_step(state: AgentState):
    step = state['step_atual']
    if step == 'temas':
        return "gerar_temas"
    elif step == 'subtemas':
        return "gerar_subtemas"
    elif step == 'problema':
        return "gerar_problemas"
    elif step == 'objetivos':
        return "gerar_objetivos"
    elif step == 'referencias':
        return "gerar_referencias"
    return END

workflow.set_conditional_entry_point(
    route_step,
    {
        "gerar_temas": "gerar_temas",
        "gerar_subtemas": "gerar_subtemas",
        "gerar_problemas": "gerar_problemas",
        "gerar_objetivos": "gerar_objetivos",
        "gerar_referencias": "gerar_referencias"
    }
)

# Todos os nós finalizam a execução após rodar (retornam ao Streamlit para input do usuário)
workflow.add_edge("gerar_temas", END)
workflow.add_edge("gerar_subtemas", END)
workflow.add_edge("gerar_problemas", END)
workflow.add_edge("gerar_objetivos", END)
workflow.add_edge("gerar_referencias", END)

app_graph = workflow.compile()

# --- INTEGRAÇÃO COM STREAMLIT ---

if "step_visual" not in st.session_state:
    st.session_state.step_visual = 1

# Inicializa state_data se não existir (Persistência manual simples para o Streamlit)
if "state_data" not in st.session_state:
    st.session_state.state_data = {
        "area_conhecimento": "",
        "ideia_bruta": "",
        "step_atual": "",
        "lista_temas_sugeridos": [],
        "tema_selecionado": "",
        "lista_subtemas": [],
        "subtema_selecionado": "",
        "lista_problemas": [],
        "problema_selecionado": "",
        "lista_objetivos": [],
        "objetivos_selecionados": "",
        "ref_teorica": "",
        "ref_estrategia": ""
    }

# Atalho para acesso fácil aos dados
dados = st.session_state.state_data

# --- UI: PASSO 1 (TEMAS) ---
if st.session_state.step_visual == 1:
    st.header("Passo 1: Definição do Tema")
    st.markdown("---")
    
    c1, c2 = st.columns(2)
    with c1:
        dados['area_conhecimento'] = st.text_input("Área do Conhecimento", value=dados['area_conhecimento'])
    with c2:
        dados['ideia_bruta'] = st.text_area("Ideia Inicial", value=dados['ideia_bruta'])

    col_btn1, col_btn2 = st.columns(2)
    
    # Função auxiliar para rodar o grafo
    def run_graph_step(step_name, clear_previous_list=False):
        if clear_previous_list and step_name == 'temas':
             dados['lista_temas_sugeridos'] = []
             
        dados['step_atual'] = step_name
        
        with st.spinner("IA processando..."):
            # Invoca o grafo com o estado atual
            result = app_graph.invoke(dados)
            # Atualiza o estado do Streamlit com o resultado do grafo
            st.session_state.state_data.update(result)

    with col_btn1:
        if st.button("Gerar Sugestões Iniciais"):
            if not dados['area_conhecimento'] or not dados['ideia_bruta']:
                st.warning("Preencha a área e a ideia.")
            else:
                run_graph_step('temas', clear_previous_list=True)
                st.rerun()
            
    with col_btn2:
        if dados['lista_temas_sugeridos']:
            if st.button("🔄 Gerar +10 (Acumular)"):
                run_graph_step('temas', clear_previous_list=False)
                st.rerun()

    if dados['lista_temas_sugeridos']:
        st.info(f"{len(dados['lista_temas_sugeridos'])} sugestões geradas.")
        
        sel = st.radio("Selecione o tema:", dados['lista_temas_sugeridos'], index=None)
        custom = st.text_input("Ou digite um novo:")
        
        if st.button("Avançar"):
            final = custom if custom else sel
            if final:
                dados['tema_selecionado'] = final
                st.session_state.step_visual = 2
                st.rerun()

# --- UI: PASSO 2 (SUBTEMAS) ---
elif st.session_state.step_visual == 2:
    st.header("Passo 2: Aprofundamento")
    st.info(f"Tema Base: {dados['tema_selecionado']}")
    
    # Executa automaticamente se a lista estiver vazia
    if not dados['lista_subtemas']:
        dados['step_atual'] = 'subtemas'
        with st.spinner("Gerando subtemas..."):
            res = app_graph.invoke(dados)
            st.session_state.state_data.update(res)
            st.rerun()

    sel_sub = st.radio("Selecione o recorte:", dados['lista_subtemas'], index=None)
    custom_sub = st.text_input("Ajuste o subtema:")
    
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Confirmar Subtema"):
            final = custom_sub if custom_sub else sel_sub
            if final:
                dados['subtema_selecionado'] = final
                st.session_state.step_visual = 3
                st.rerun()
    with c2:
        if st.button("Manter Tema Original"):
            dados['subtema_selecionado'] = dados['tema_selecionado']
            st.session_state.step_visual = 3
            st.rerun()

# --- UI: PASSO 3 (PROBLEMA) ---
elif st.session_state.step_visual == 3:
    st.header("Passo 3: Problema de Pesquisa")
    st.success(f"Subtema: {dados['subtema_selecionado']}")
    
    if not dados['lista_problemas']:
        dados['step_atual'] = 'problema'
        with st.spinner("Formulando perguntas..."):
            res = app_graph.invoke(dados)
            st.session_state.state_data.update(res)
            st.rerun()
            
    sel_prob = st.radio("Selecione a pergunta:", dados['lista_problemas'], index=None)
    custom_prob = st.text_area("Edite seu problema:")
    
    if st.button("Confirmar Problema"):
        final = custom_prob if custom_prob else sel_prob
        if final:
            dados['problema_selecionado'] = final
            st.session_state.step_visual = 4
            st.rerun()

# --- UI: PASSO 4 (OBJETIVOS) ---
elif st.session_state.step_visual == 4:
    st.header("Passo 4: Objetivos Específicos")
    st.warning(f"Problema: {dados['problema_selecionado']}")
    
    if not dados['lista_objetivos']:
        dados['step_atual'] = 'objetivos'
        with st.spinner("Criando objetivos..."):
            res = app_graph.invoke(dados)
            st.session_state.state_data.update(res)
            st.rerun()

    st.write("Selecione os objetivos:")
    selecionados = []
    for i, obj in enumerate(dados['lista_objetivos']):
        if st.checkbox(obj, key=f"obj_{i}"):
            selecionados.append(obj)
            
    if st.button("Confirmar Objetivos"):
        if selecionados:
            # Consolida lista em string
            dados['objetivos_selecionados'] = "\n".join(selecionados)
            st.session_state.step_visual = 5
            st.rerun()
        else:
            st.warning("Selecione pelo menos um.")

# --- UI: PASSO 5 (REFERÊNCIAS - Agentes 5 e 6) ---
elif st.session_state.step_visual == 5:
    st.header("Passo 5: Estratégia e Referências")
    
    if not dados['ref_teorica']:
        dados['step_atual'] = 'referencias'
        with st.spinner("Consultando bases de dados e gerando estratégia (Agentes 5 e 6)..."):
            res = app_graph.invoke(dados)
            st.session_state.state_data.update(res)
            st.rerun()
            
    st.markdown("### Referencial Teórico")
    st.markdown(dados['ref_teorica'])
    st.markdown("---")
    st.markdown("### Estratégia de Busca")
    st.markdown(dados['ref_estrategia'])
    
    if st.button("Ir para Resumo Final"):
        st.session_state.step_visual = 6
        st.rerun()

# --- UI: PASSO 6 (CONSOLIDAÇÃO) ---
elif st.session_state.step_visual == 6:
    st.header("Plano de Trabalho Final")
    
    # --- MUDANÇA AQUI: Exibição da Ideia Inicial ---
    st.info(f"**Ideia Inicial do Usuário:** {dados['ideia_bruta']}")
    # -----------------------------------------------
    
    # Processa numeração dos objetivos para exibição final
    objs_raw = dados['objetivos_selecionados'].split('\n')
    objs_fmt = "\n".join([f"{i+1}. {o.split('.', 1)[-1].strip() if '.' in o[:3] else o}" for i, o in enumerate(objs_raw)])
    
    md_text = f"""# Plano de Trabalho Acadêmico
---
**Data de Geração:** {datetime.now().strftime('%d/%m/%Y %H:%M')}
**Área:** {dados['area_conhecimento']}

## 0. Contexto Inicial
**Ideia Original:** {dados['ideia_bruta']}

## 1. Tema Principal
{dados['tema_selecionado']}

## 2. Subtema / Recorte
{dados['subtema_selecionado']}

## 3. Problema de Pesquisa
{dados['problema_selecionado']}

## 4. Objetivos Específicos
{objs_fmt}

## 5. Referencial Teórico
{dados['ref_teorica']}

## 6. Estratégia de Busca
{dados['ref_estrategia']}

---
*Gerado via LangGraph Monografia Agent*
"""

    with st.expander("Visualizar Documento Completo", expanded=True):
        st.markdown(md_text)
        
    st.download_button(
        label="📥 Baixar Plano (.md)",
        data=md_text,
        file_name="plano_monografia.md",
        mime="text/markdown"
    )
    
    if st.button("Reiniciar"):
        st.session_state.clear()
        st.rerun()