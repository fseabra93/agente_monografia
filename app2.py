import streamlit as st
from openai import OpenAI
import os
from dotenv import load_dotenv
from fpdf import FPDF # Nova importação para PDF
from io import BytesIO
from datetime import datetime
from docx import Document


# Carregar chave API do arquivo .env
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

st.set_page_config(page_title="Agente Monografia", layout="wide")
st.title("🎓 Sistema Agente Monografia")

# --- Inicialização da Memória dos Agentes ---
if "step" not in st.session_state:
    st.session_state.step = 1
if "dados" not in st.session_state:
    st.session_state.dados = {}

def call_gpt(prompt):
    try:
        response = client.chat.completions.create(
            model="gpt-4o", 
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Erro na API: {e}"

# --- AGENTE 1: ESCOLHA DO TEMA ---
if st.session_state.step == 1:
    st.header("Agente 1: Escolha do Tema")
    area = st.text_input("Qual sua área de interesse?")
    
    if st.button("Analisar Tendências"):
        with st.spinner("Analisando periódicos internacionais..."):
            #prompt = f"""Usando o google search, faça uma análise dos títulos dos artigos dos últimos 5
            #anos dos 3 periódicos científicos internacionais mais importantes atualmente na área {area},
            #identifique os 5 temas mais relevantes com base na quantidade de publicações e apresente-os como sugestões
            #de temas para a monografia do usuário. Escreva na tela apenas as sugestões. 
            #"""
            prompt = f"""Com base na literatura acadêmica recente (últimos 10 anos), 
            liste e descreva sucintamente os 5 temas mais relevantes, atuais e debatidos no campo de 
            {area}, considerando sua importância teórica, impacto prático e potencial para futuras pesquisas.
              Para cada tema, inclua:
                1. Uma breve definição ou explicação;
                2. Principais autores ou correntes teóricas associadas;
                3. Por que esse tema é relevante para uma revisão da literatura acadêmica hoje."""
        st.session_state.temas_sugeridos = call_gpt(prompt)
        st.rerun()

    if "temas_sugeridos" in st.session_state:
        st.info("Sugestões encontradas:")
        st.markdown(st.session_state.temas_sugeridos)
        escolha = st.text_input("Digite o tema que deseje trabalhar:")
        if st.button("Enviar para Agente 2"):
            st.session_state.dados['tema_base'] = escolha
            st.session_state.step = 2
            st.rerun()

# --- AGENTE 2: APROFUNDAMENTO (MODIFICADO: INPUT DE TEXTO) ---
elif st.session_state.step == 2:
    st.header("Agente 2: Aprofundamento do Tema")
    
    if "subtemas_texto" not in st.session_state:
        with st.spinner("Gerando subtemas específicos..."):
            prompt = f"O usuário demonstrou interesse no tema {st.session_state.dados['tema_base']}. Apresente ao usuário 10 sugestões de subtemas mais específicos para eu escrever a monografia sobre ele. Considere sempre que a monografia será uma revisão da literatura."
            st.session_state.subtemas_texto = call_gpt(prompt)

    st.subheader(f"Tema macro: {st.session_state.dados['tema_base']}")
    st.markdown(st.session_state.subtemas_texto)
    
    # Campo de texto em vez de Selectbox/Radio
    tema_final_digitado = st.text_input("Digite (ou cole) o tema/subtema que devemos trabalhar daqui para frente:")
    
    if st.button("Confirmar e Enviar para Agentes 3, 4, 5 e 6"):
        if tema_final_digitado:
            st.session_state.dados['tema_escolhido'] = tema_final_digitado
            st.session_state.step = 3
            st.rerun()
        else:
            st.warning("Por favor, digite o tema antes de confirmar.")

# --- AGENTE 3: PROBLEMA DE PESQUISA ---
elif st.session_state.step == 3:
    st.header("Agente 3: Problema de Pesquisa")
    if "problemas_sugeridos" not in st.session_state:
        prompt = f"""Quero escrever uma monografia que será uma revisão da literatura sobre o 
        tema {st.session_state.dados['tema_escolhido']}. 
        Crie 5 sugestões de 'Problema de pesquisa'."""
        st.session_state.problemas_sugeridos = call_gpt(prompt)

    st.write(f"**Tema Escolhido:** {st.session_state.dados['tema_escolhido']}")
    st.markdown(st.session_state.problemas_sugeridos)
    
    problema_input = st.text_area("Escolha um dos problemas digitando o seu número ou digite um novo problema:")
    
    if st.button("Confirmar Problema e Enviar para Agentes 4, 5 e 6"):
        st.session_state.dados['problema_pesquisa'] = problema_input
        st.session_state.step = 4
        st.rerun()

# --- AGENTE 4: OBJETIVOS ESPECÍFICOS ---
elif st.session_state.step == 4:
    st.header("Agente 4: Objetivos Específicos")
    if "lista_objs" not in st.session_state:
        prompt = f"Considerando que o tema será {st.session_state.dados['tema_escolhido']} e o Problema de Pesquisa {st.session_state.dados['problema_pesquisa']}, crie 10 sugestões de objetivos específicos."
        res = call_gpt(prompt)
        # Limpeza simples para gerar a lista de checkboxes
        st.session_state.lista_objs = [l.strip() for l in res.split('\n') if l.strip() and (l.strip()[0].isdigit() or l.strip().startswith('-'))]

    st.write("Selecione os objetivos desejados:")
    selecionados = []
    for i, obj in enumerate(st.session_state.lista_objs):
        if st.checkbox(obj, key=f"obj_{i}"):
            selecionados.append(obj)
            
    if st.button("Confirmar Objetivos e Iniciar Pesquisa Bibliográfica"):
        if selecionados:
            st.session_state.dados['objetivos'] = "\n".join(selecionados)
            st.session_state.step = 5
            st.rerun()
        else:
            st.error("Selecione ao menos um objetivo.")

# --- AGENTE 5 & 6: PROCESSAMENTO DE REFERÊNCIAS ---
elif st.session_state.step == 5:
    st.header("Agentes 5 e 6: Levantamento Bibliográfico")
    
    with st.spinner("O Agente 5 está buscando referências clássicas..."):
        p5 = f"Quero escrever uma monografia que será uma revisão da literatura sobre o tema {st.session_state.dados['tema_escolhido']} trabalhando o problema de pesquisa {st.session_state.dados['problema_pesquisa']} com os seguintes objetivos específicos: {st.session_state.dados['objetivos']}. Quais os trabalhos mais clássicos sobre o tema, que eu não posso deixar de referenciar, e os autores mais importantes na atualidade?"
        st.session_state.dados['ref_classicas'] = call_gpt(p5)
        
    with st.spinner("O Agente 6 está construindo a estratégia atualizada..."):
        ano_atual = datetime.now().year
        p6 = f"""Atue como um especialista em metodologia de pesquisa acadêmica. Estou desenvolvendo uma revisão bibliográfica.
        Contexto:
        - Tema: {st.session_state.dados['tema_escolhido']}
        - Problema: {st.session_state.dados['problema_pesquisa']}
        - Objetivos: {st.session_state.dados['objetivos']}
        Parâmetros: Busca entre {ano_atual} e {ano_atual-5}. Idiomas: Português, Inglês, Espanhol.
        Bases: SciELO, Scopus, Web of Science, PubMed.
        Forneça: Conceitos atuais, referências recentes, lacunas, tendências e estratégias booleanas."""
        st.session_state.dados['ref_atuais'] = call_gpt(p6)
    
    st.session_state.step = 6
    st.rerun()

import streamlit as st
from openai import OpenAI
import os
from dotenv import load_dotenv
from fpdf import FPDF # Nova importação para PDF
from io import BytesIO
from datetime import datetime

# ... (Mantenha o restante do código dos Agentes 1 a 6 igual) ...

# --- AGENTE 7: CONSOLIDAÇÃO E DOWNLOAD (VERSÃO PDF + EXIBIÇÃO NA TELA) ---
elif st.session_state.step == 6:
    st.header("Agente 7: Consolidação Final")
    
    st.subheader("Conteúdo do Projeto de Monografia")
    
    # Criar uma string formatada para exibir na tela e usar no PDF
    relatorio_texto = ""
    ordem = [
        ('Tema Final', 'tema_escolhido'),
        ('Problema de Pesquisa', 'problema_pesquisa'),
        ('Objetivos Específicos', 'objetivos'),
        ('Referências Clássicas (Agente 5)', 'ref_classicas'),
        ('Estratégia e Referências Atuais (Agente 6)', 'ref_atuais')
    ]

    # Exibição na tela para o usuário revisar
    for label, chave in ordem:
        conteudo = st.session_state.dados.get(chave, "Não informado")
        st.markdown(f"### {label}")
        st.write(conteudo)
        st.divider()
        relatorio_texto += f"{label.upper()}\n{conteudo}\n\n"

    # Função para gerar o PDF
    def gerar_pdf(dados_projeto):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        
        # Título Principal
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, "Plano Estruturado de Monografia", ln=True, align='C')
        pdf.ln(10)
        
        for label, chave in ordem:
            conteudo = st.session_state.dados.get(chave, "Não informado")
            
            # Título da Seção
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(0, 10, label, ln=True)
            
            # Conteúdo da Seção (Tratando caracteres especiais comuns)
            pdf.set_font("Arial", size=11)
            # Encode/decode para evitar erros de caracteres latin-1 na biblioteca fpdf padrão
            texto_limpo = str(conteudo).encode('latin-1', 'replace').decode('latin-1')
            pdf.multi_cell(0, 8, texto_limpo)
            pdf.ln(5)
            
        return pdf.output()

    # Botão de Download
    try:
        pdf_bytes = gerar_pdf(st.session_state.dados)
        
        st.download_button(
            label="📥 Baixar Projeto em PDF",
            data=pdf_bytes,
            file_name="projeto_monografia.pdf",
            mime="application/pdf"
        )
    except Exception as e:
        st.error(f"Erro ao gerar PDF: {e}. Certifique-se de que não há caracteres incompatíveis.")

    if st.button("Reiniciar Sistema (Novo Tema)"):
        st.session_state.clear()
        st.rerun()