import os
from typing import TypedDict, List
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI
from langgraph.graph import StateGraph, END

# Carrega chaves de ambiente
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 1. Definição do Estado (Memória do Grafo)
# Este dicionário carrega os dados entre um agente e outro
class MonografiaState(TypedDict):
    area: str
    ideia_bruta: str
    lista_temas_sugeridos: List[str]
    tema_base: str
    tema_escolhido: str
    subtemas_lista: List[str]
    probs_lista: List[str]
    problema_pesquisa: str
    lista_objs: List[str]
    objetivos_selecionados: str
    ref_classicas: str
    ref_atuais: str

# Função de auxílio para chamada da API
def call_gpt(prompt):
    try:
        response = client.chat.completions.create(
            model="gpt-4o",  # Recomendado para manter a qualidade dos prompts longos
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Erro na API: {e}"

# --- NODES (AGENTES COM SEUS PROMPTS ORIGINAIS) ---

def agente_gerar_temas(state: MonografiaState):
    # Mantendo sua lógica de exclusão para não repetir temas se rodar de novo
    exclusao = "\n".join(state.get('lista_temas_sugeridos', []))
    contexto_exclusao = f"\nNÃO repita nenhum destes temas:\n{exclusao}" if exclusao else ""

    prompt = f"""Você é um especialista em metodologia de pesquisa científica com ampla experiência 
            em orientação de trabalhos de conclusão de curso na área de {state['area']}.
            
            Sua tarefa é sugerir temas viáveis para uma monografia no formato de revisão 
            integrativa da literatura.
            
            Contexto fornecido pelo estudante:
            - Área de conhecimento: {state['area']}
            - Ideia ou interesse inicial: {state['ideia_bruta']}
            
            Critérios para os temas sugeridos:
            - Devem ser adequados ao escopo de uma revisão integrativa.
            - Devem ser atuais e ter relevância acadêmica/social.
            - Devem permitir a busca em bases de dados científicas.
            {contexto_exclusao}
            
            Gere exatamente 10 sugestões de temas, apresentadas em lista numerada de 1 a 10. 
            Não adicione introduções ou conclusões, apenas a lista."""
    
    resposta = call_gpt(prompt)
    # Parsing para extrair a lista numerada
    linhas = resposta.strip().split('\n')
    temas = [l.split('.', 1)[-1].strip() for l in linhas if l.strip() and l[0].isdigit()]
    return {"lista_temas_sugeridos": temas}

def agente_gerar_subtemas(state: MonografiaState):
    prompt = f"""Você é um especialista em metodologia de pesquisa científica com ampla experiência 
            em revisões integrativas da literatura na área de {state['area']}.
            
            Tema central: {state['tema_base']}
            
            Sua tarefa é realizar um recorte ou aprofundamento deste tema para torná-lo mais específico 
            e viável para uma pesquisa acadêmica.
            
            Output: Gere exatamente 10 sugestões de subtemas ou recortes específicos em lista numerada."""
    
    res = call_gpt(prompt)
    subtemas = [l.split('.', 1)[-1].strip() if '.' in l[:3] else l.strip() 
                for l in res.strip().split('\n') if l.strip()]
    return {"subtemas_lista": subtemas}

def agente_gerar_problema(state: MonografiaState):
    prompt = f"""Você é um especialista em metodologia de pesquisa científica.
            
            Tema escolhido: {state['tema_escolhido']}
            
            Sua tarefa é formular problemas de pesquisa (perguntas norteadoras) que sejam 
            compatíveis com uma revisão integrativa da literatura.
            
            Gere exatamente 10 sugestões de problema de pesquisa em lista numerada."""
    
    res = call_gpt(prompt)
    probs = [l.split('.', 1)[-1].strip() if '.' in l[:3] else l.strip() 
             for l in res.strip().split('\n') if l.strip()]
    return {"probs_lista": probs}

def agente_gerar_objetivos(state: MonografiaState):
    prompt = f"""Você é um especialista em metodologia de pesquisa científica.
            
            Tema: {state['tema_escolhido']}
            Problema de pesquisa: {state['problema_pesquisa']}
            
            Sua tarefa é sugerir objetivos específicos (Geralmente 3 ou 4) que respondam 
            ao problema de pesquisa e descrevam as etapas da revisão integrativa.
            
            Gere exatamente 10 sugestões de conjuntos de objetivos em lista numerada."""
    
    res = call_gpt(prompt)
    objs = [l.strip() for l in res.split('\n') if l.strip() and any(c.isdigit() for c in l[:3])]
    return {"lista_objs": objs}

def agente_gerar_estrategia(state: MonografiaState):
    # Unificando seus agentes 5 e 6 de estratégia de busca
    ano_atual = datetime.now().year
    ano_inicial = ano_atual - 5
    
    # Prompt 5: Referencial Teórico
    prompt_ref = f"""Você é um especialista em pesquisa bibliográfica.
            Tema: {state['tema_escolhido']}
            
            PARTE 1 — MAPA DA LITERATURA:
            Sugira os principais eixos temáticos e autores clássicos que fundamentam este tema."""
    
    # Prompt 6: Estratégia DeCS/MeSH
    prompt_busca = f"""Você é um bibliotecário clínico e especialista em busca em bases de dados.
            Tema: {state['tema_escolhido']}
            
            SEÇÃO 1 — DESCRITORES (DeCS/MeSH):
            Apresente os descritores e a string de busca booleana para bases como PubMed e BVS."""
    
    return {
        "ref_classicas": call_gpt(prompt_ref),
        "ref_atuais": call_gpt(prompt_busca)
    }

# --- MONTAGEM DO GRAFO ---

workflow = StateGraph(MonografiaState)

# Adicionando os nós
workflow.add_node("gerar_temas", agente_gerar_temas)
workflow.add_node("gerar_subtemas", agente_gerar_subtemas)
workflow.add_node("gerar_problema", agente_gerar_problema)
workflow.add_node("gerar_objetivos", agente_gerar_objetivos)
workflow.add_node("gerar_estrategia", agente_gerar_estrategia)

# Definindo o fluxo
workflow.set_entry_point("gerar_temas")
workflow.add_edge("gerar_temas", "gerar_subtemas")
workflow.add_edge("gerar_subtemas", "gerar_problema")
workflow.add_edge("gerar_problema", "gerar_objetivos")
workflow.add_edge("gerar_objetivos", "gerar_estrategia")
workflow.add_edge("gerar_estrategia", END)

# Compilação
app_graph = workflow.compile()