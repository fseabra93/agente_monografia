import streamlit as st
from openai import OpenAI
import os
from dotenv import load_dotenv
from fpdf import FPDF
from io import BytesIO
from datetime import datetime

# 1. Configurações Iniciais
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

st.set_page_config(page_title="Agente Monografia", layout="wide")
st.title("🎓 Sistema Agente Monografia")

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

area = ""

# --- AGENTE 1: ESCOLHA DO TEMA ---
if st.session_state.step == 1:
    st.header("Agente 1: Escolha do Tema")
    area = st.text_input("Qual sua área de interesse?")
    
    if st.button("Iniciar"):
        with st.spinner("Gerando sugestões de temas..."):
            #prompt = f"Faça uma análise dos títulos dos artigos dos últimos 5 anos dos 
            #3 periódicos científicos internacionais mais importantes atualmente na área 
            #{area} e identifique os 5 temas mais relevantes com base na quantidade de publicações."

            prompt = f"""Você atua como orientador acadêmico experiente, 
            com domínio de metodologia científica e elaboração de trabalhos de conclusão de curso, 
            capaz de propor temas viáveis, relevantes e academicamente bem delimitados.
            Gere 10 opções de temas de monografia a partir do assunto {area}, que sejam adequados a nível 
            de graduação ou pós-graduação, considerando:
                - relevância científica,
                - clareza conceitual,
                - adequação à escrita acadêmica formal,
                - que as sugestões sejam realmente diferentes umas das outras do ponto de vista conceitual,
                - que o trabalho deverá sempre ser do tipo revisão da literatura do tipo integrativa.
            Output
                Apresente exatamente 10 temas, em lista numerada (1 a 10). 
                Cada item deve conter somente o título do tema, sem comentários, explicações ou subtítulos.
                Utilize linguagem acadêmica formal.
                Garanta variação de enfoque entre os temas (teórico, empírico, aplicado, comparativo, metodológico).
            """
            st.session_state.temas_sugeridos = call_gpt(prompt)
        st.rerun()

    if "temas_sugeridos" in st.session_state:
        st.info("Sugestões encontradas:")
        st.markdown(st.session_state.temas_sugeridos)
        escolha = st.text_input("Copie o tema que deseje trabalhar e cole na caixa de texto abaixo. " \
        "\nCaso não tenha gostado de nenhuma das minhas sugestões, digite um novo tema:")
        if st.button("Enviar para Aprofundamento do Tema"):
            st.session_state.dados['tema_base'] = escolha  ##################################
            st.session_state.step = 2
            st.rerun()

# --- AGENTE 2: APROFUNDAMENTO ---
elif st.session_state.step == 2:
    st.header("Agente 2: Aprofundamento do Tema")
    if "subtemas_texto" not in st.session_state:
        with st.spinner("Gerando subtemas..."):
            prompt = f"""Você é um professor universitário na área de {area}. 
            Atue como orientador acadêmico experiente, com domínio de metodologia científica e 
            elaboração de trabalhos de conclusão de curso, capaz de propor temas viáveis, relevantes e 
            academicamente bem delimitados.
            Apresente 10 sugestões de subtemas específicos para revisão da literatura 
            no tema {st.session_state.dados['tema_base']}.
            Garanta variação de enfoque entre os temas sugeridos.
            Output
                Apresente exatamente 10 temas, em lista numerada (1 a 10).
                Cada item deve conter somente o título do tema seguido de um parágrafo com
                uma breve definição ou explicação do tema.
                Utilize linguagem acadêmica formal. """
            st.session_state.subtemas_texto = call_gpt(prompt)

    st.markdown(st.session_state.subtemas_texto)
    tema_final = st.text_input("Digite/Cole o tema específico escolhido:")
    if st.button("Confirmar Subtema"):
        st.session_state.dados['tema_escolhido'] = tema_final
        st.session_state.step = 3
        st.rerun()

# --- AGENTE 3: PROBLEMA DE PESQUISA ---
elif st.session_state.step == 3:
    st.header("Agente 3: Problema de Pesquisa")
    if "probs" not in st.session_state:
        prompt = f"Para o tema {st.session_state.dados['tema_escolhido']}, crie 5 sugestões de 'Problema de pesquisa'."
        st.session_state.probs = call_gpt(prompt)

    st.markdown(st.session_state.probs)
    prob_input = st.text_area("Escolha ou digite o Problema de Pesquisa:")
    if st.button("Confirmar Problema"):
        st.session_state.dados['problema_pesquisa'] = prob_input
        st.session_state.step = 4
        st.rerun()

# --- AGENTE 4: OBJETIVOS ---
elif st.session_state.step == 4:
    st.header("Agente 4: Objetivos Específicos")
    if "lista_objs" not in st.session_state:
        prompt = f"Para o tema {st.session_state.dados['tema_escolhido']} e problema {st.session_state.dados['problema_pesquisa']}, sugira 10 objetivos específicos."
        res = call_gpt(prompt)
        st.session_state.lista_objs = [l.strip() for l in res.split('\n') if l.strip() and any(c.isdigit() for c in l[:3])]

    selecionados = []
    for i, obj in enumerate(st.session_state.lista_objs):
        if st.checkbox(obj, key=f"obj_{i}"):
            selecionados.append(obj)
            
    if st.button("Confirmar Objetivos"):
        st.session_state.dados['objetivos'] = "\n".join(selecionados)
        st.session_state.step = 5
        st.rerun()

# --- AGENTE 5 & 6: REFERÊNCIAS ---
elif st.session_state.step == 5:
    st.header("Agentes 5 e 6: Levantamento Bibliográfico")
    
    with st.spinner("Buscando referências clássicas e gerando estratégia de busca..."):
        # Agente 5 (Referencial Clássico)
        p5 = f"""Quero escrever uma monografia que será uma revisão da literatura sobre o tema {st.session_state.dados['tema_escolhido']} 
        trabalhando o problema de pesquisa {st.session_state.dados['problema_pesquisa']} com os seguintes objetivos específicos: 
        {st.session_state.dados['objetivos']}. Quais os trabalhos mais clássicos sobre o tema, que eu não posso deixar de 
        referenciar, e os autores mais importantes na atualidade?"""
        st.session_state.dados['ref_classicas'] = call_gpt(p5)

        # Agente 6 (Estratégia Atualizada conforme seu novo prompt)
        ano_atual = datetime.now().year
        ano_inicial = ano_atual - 5
        
        p6 = f"""Atue como um especialista em metodologia de pesquisa acadêmica. Estou desenvolvendo uma revisão bibliográfica para minha monografia. Me ajude a construir uma estratégia de busca abrangente considerando os seguintes elementos:
            **Contexto da pesquisa:**
            - Tema principal: [{st.session_state.dados['tema_escolhido']}]
            - Problema de pesquisa: [{st.session_state.dados['problema_pesquisa']}]
            - Objetivos: [{st.session_state.dados['objetivos']}]

            **Parâmetros da busca:**
            1. Período temporal: Trabalhos publicados entre o ano {ano_atual} e o ano {ano_inicial}
            2. Idiomas prioritários: [Português, Inglês, Espanhol]
            3. Tipos de fontes: [Artigos científicos, teses, dissertações, livros]
            4. Bases de dados recomendadas: [SciELO, Scopus, Web of Science, PubMed]

            **Aspectos a serem cobertos:**
            - Conceitos-chave e definições atuais
            - Principais autores e referências seminais recentes
            - Metodologias predominantes na área
            - Resultados convergentes e divergentes na literatura
            - Lacunas identificadas nos estudos atuais
            - Tendências emergentes e direções futuras de pesquisa

            **Palavras-chave e estratégias booleanas:**
            Sugira um conjunto de palavras-chave em português e inglês, além de combinações booleanas eficientes (AND, OR, NOT) para refinar a busca.

            **Critérios de seleção:**
            Indique critérios para inclusão e exclusão de trabalhos na triagem inicial."""
        
        st.session_state.dados['ref_atuais'] = call_gpt(p6)
        
        st.session_state.step = 6
        st.rerun()

# --- AGENTE 7: CONSOLIDAÇÃO E PDF (CORRIGIDO) ---
elif st.session_state.step == 6:
    st.header("Agente 7: Consolidação e PDF")
    
    ordem = [
        ('Tema Final', 'tema_escolhido'),
        ('Problema de Pesquisa', 'problema_pesquisa'),
        ('Objetivos Específicos', 'objetivos'),
        ('Referências Clássicas', 'ref_classicas'),
        ('Referências Atuais', 'ref_atuais')
    ]

    for label, chave in ordem:
        st.subheader(label)
        conteudo = st.session_state.dados.get(chave, "")
        st.write(conteudo)
        st.divider()

    def criar_pdf():
        pdf = FPDF()
        pdf.add_page()
        # Usando 'helvetica' que é padrão e mais compatível que 'Arial' em algumas versões
        pdf.set_font("helvetica", 'B', 16)
        pdf.cell(0, 10, "Plano de Monografia", ln=True, align='C')
        pdf.ln(10)
        
        for label, chave in ordem:
            pdf.set_font("helvetica", 'B', 12)
            pdf.cell(0, 10, label.encode('latin-1', 'replace').decode('latin-1'), ln=True)
            pdf.set_font("helvetica", size=11)
            txt = str(st.session_state.dados.get(chave, "")).encode('latin-1', 'replace').decode('latin-1')
            pdf.multi_cell(0, 7, txt)
            pdf.ln(5)
            
        # O segredo está aqui: converter explicitamente para bytes
        return bytes(pdf.output())

    try:
        pdf_out = criar_pdf()
        st.download_button(
            label="📥 Baixar PDF", 
            data=pdf_out, 
            file_name="monografia.pdf", 
            mime="application/pdf"
        )
    except Exception as e:
        st.error(f"Erro ao processar o arquivo: {e}")
    
    if st.button("Reiniciar"):
        st.session_state.clear()
        st.rerun()