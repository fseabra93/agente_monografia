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
st.title("🎓 Sistema de IA para Monografia")
st.title("Parte 1 - Escolha do tema, estratégia de pesquisa e cronograma")

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
    st.header("Passo 1: Definição do Tema")
    st.subheader("Digite sua área e descreva uma ideia inicial para começarmos")
    
    st.markdown("---") # Uma linha horizontal para separar o cabeçalho do formulário
    
    # Interface de entrada dupla
    col1, col2 = st.columns(2)
    with col1:
        area = st.text_input("Área do Conhecimento", placeholder="Ex: Psicologia Organizacional")
    with col2:
        # Usamos o markdown para criar o rótulo com quebras de linha
        st.markdown("Descreva sua ideia<br>Lembre-se que eu sou uma IA, descreva o mais detalhado possível.", unsafe_allow_html=True)

        # Criamos o text_area com label_visibility="collapsed" para não repetir o título
        ideia_bruta = st.text_area(
            label="Descricao", 
            label_visibility="collapsed",
            placeholder="Ex: Quero falar sobre..."
        )
    if st.button("Gerar Sugestões"):
        with st.spinner("O orientador IA está redigindo os temas..."):
            # Lógica de prioridade e seleção de prompt
            if ideia_bruta.strip():
                # Prompt para quando o usuário já tem uma ideia
                prompt = f"""Você atua como orientador acadêmico experiente. 
                O usuário propôs a seguinte ideia: {ideia_bruta} na área de {area}.
                Refine esta ideia e gere 10 opções de temas de monografia para uma revisão integrativa da literatura.
                Output: Apresente exatamente 10 temas, em lista numerada (1 a 10), apenas os títulos, sem comentários."""
            else:
                # Prompt original baseado na área
                prompt = f"""Você atua como orientador acadêmico experiente. 
                Gere 10 opções de temas de monografia a partir da área {area} para uma revisão integrativa da literatura.
                Output: Apresente exatamente 10 temas, em lista numerada (1 a 10), apenas os títulos, sem comentários."""
            
            resposta = call_gpt(prompt)
            # Transformar a string da API em uma lista real de Python para o st.radio
            linhas = resposta.strip().split('\n')
            # Limpar números e pontos (ex: "1. Tema" -> "Tema")
            temas_limpos = [l.split('.', 1)[-1].strip() for l in linhas if l.strip()]
            st.session_state.lista_temas_sugeridos = temas_limpos
        st.rerun()

    # Se já houver temas gerados, exibe o rádio para seleção
    if "lista_temas_sugeridos" in st.session_state:
        st.info("Selecione o tema que mais lhe agrada:")
        
        tema_selecionado = st.radio(
            "Temas sugeridos:",
            st.session_state.lista_temas_sugeridos,
            index=None, # Inicia sem nada selecionado
            help="Escolha um dos temas gerados pela IA"
        )
        
        outra_opcao = st.text_input("Ou digite seu próprio tema caso queira ajustar algum detalhe:")
        
        if st.button("Avançar para Aprofundamento"):
            # Prioriza o texto manual se preenchido, senão usa o rádio
            escolha_final = outra_opcao if outra_opcao.strip() else tema_selecionado
            
            if escolha_final:
                st.session_state.dados['tema_base'] = escolha_final
                st.session_state.step = 2
                st.rerun()
            else:
                st.warning("Por favor, selecione um tema ou digite um antes de avançar.")

# --- AGENTE 2: APROFUNDAMENTO ---
elif st.session_state.step == 2:
    st.header("Agente 2: Aprofundamento do Tema")
    
    # Exibe o tema base para orientação
    st.info(f"**Tema Base Selecionado:** {st.session_state.dados['tema_base']}")
    st.divider()

    if "subtemas_lista" not in st.session_state:
        with st.spinner("O orientador está gerando subtemas específicos..."):
            prompt = f"""Você é um professor universitário. 
            Apresente 10 sugestões de subtemas específicos para uma revisão da literatura 
            baseada no tema: {st.session_state.dados['tema_base']}.
            
            Output:
            Apresente exatamente 10 itens em uma lista numerada (1 a 10).
            Cada item deve conter o título do tema seguido de uma breve explicação.
            Use linguagem acadêmica formal."""
            
            res = call_gpt(prompt)
            # Armazenamos a string bruta para exibição e processamos para a lógica
            st.session_state.subtemas_texto_bruto = res
            linhas = res.strip().split('\n')
            # Extraímos apenas o texto após o "1. " para facilitar o resgate depois
            st.session_state.subtemas_lista = [l.split('.', 1)[-1].strip() for l in linhas if l.strip() and l[0].isdigit()]

    # Exibe a lista numerada para o usuário ver os números
    st.markdown(st.session_state.subtemas_texto_bruto)
    
    st.divider()
    
    # Caixa de entrada única para número ou texto
    escolha_input = st.text_input(
        "Digite o NÚMERO do tema desejado OU escreva um NOVO tema do zero:",
        placeholder="Ex: 5 ou 'A influência da IA na educação básica'"
    )

    if st.button("Confirmar Escolha"):
        if escolha_input.strip():
            # Tenta verificar se o input é um número entre 1 e 10
            if escolha_input.isdigit():
                indice = int(escolha_input)
                if 1 <= indice <= len(st.session_state.subtemas_lista):
                    # Usuário escolheu pelo número
                    tema_escolhido = st.session_state.subtemas_lista[indice - 1]
                    st.session_state.dados['tema_escolhido'] = tema_escolhido
                else:
                    st.error("Número fora do intervalo! Digite um número de 1 a 10 ou um novo texto.")
                    st.stop()
            else:
                # Usuário digitou um texto (novo tema)
                st.session_state.dados['tema_escolhido'] = escolha_input
            
            # Avança para o próximo passo
            st.session_state.step = 3
            st.rerun()
        else:
            st.warning("Por favor, preencha o campo antes de confirmar.")

# --- AGENTE 3: PROBLEMA DE PESQUISA ---
elif st.session_state.step == 3:
    st.header("Agente 3: Problema de Pesquisa")
    
    # UX: Exibe as escolhas anteriores para manter o contexto
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        st.info(f"**Tema Base (Passo 1):**\n\n{st.session_state.dados.get('tema_base', '')}")
    with col_c2:
        st.success(f"**Subtema Escolhido (Passo 2):**\n\n{st.session_state.dados.get('tema_escolhido', '')}")
    
    st.divider()

    # Lógica de geração de problemas
    if "probs_texto_bruto" not in st.session_state:
        with st.spinner("Formulando problemas de pesquisa..."):
            prompt = f"""Para o tema específico '{st.session_state.dados['tema_escolhido']}', 
            crie 5 sugestões de 'Problema de pesquisa' em formato de pergunta.
            
            Output:
            Apresente exatamente 5 problemas, em lista numerada (1 a 5).
            Utilize linguagem acadêmica formal e rigorosa."""
            
            res_bruta = call_gpt(prompt)
            st.session_state.probs_texto_bruto = res_bruta
            
            # Processamento para extrair apenas o texto das perguntas
            linhas = res_bruta.strip().split('\n')
            st.session_state.probs_lista = [
                l.split('.', 1)[-1].strip() for l in linhas 
                if l.strip() and l[0].isdigit()
            ]

    # Exibe as sugestões da IA
    st.markdown("### Sugestões de Problemas de Pesquisa")
    st.markdown(st.session_state.probs_texto_bruto)
    st.divider()

    # Entrada Híbrida
    prob_input = st.text_area(
        "Escolha uma opção:", 
        placeholder="Digite o NÚMERO da pergunta desejada OU escreva seu próprio PROBLEMA DE PESQUISA completo aqui:"
    )

    if st.button("Confirmar Problema"):
        if prob_input.strip():
            # Verifica se é um número
            if prob_input.isdigit():
                indice = int(prob_input)
                if 1 <= indice <= len(st.session_state.probs_lista):
                    # Seleciona a pergunta correspondente
                    st.session_state.dados['problema_pesquisa'] = st.session_state.probs_lista[indice - 1]
                    st.session_state.step = 4
                    st.rerun()
                else:
                    st.error(f"Número inválido. Escolha entre 1 e {len(st.session_state.probs_lista)}.")
            else:
                # Trata como novo texto digitado
                st.session_state.dados['problema_pesquisa'] = prob_input
                st.session_state.step = 4
                st.rerun()
        else:
            st.warning("Por favor, selecione um número ou digite seu problema.")

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
            prompt = f"Para o tema {st.session_state.dados['tema_escolhido']} e problema {st.session_state.dados['problema_pesquisa']}, sugira 10 objetivos específicos."
            res = call_gpt(prompt)
            # Mantendo sua lógica de parsing original do arquivo app3.py
            st.session_state.lista_objs = [l.strip() for l in res.split('\n') if l.strip() and any(c.isdigit() for c in l[:3])]

    st.markdown("### Selecione os objetivos que farão parte do seu trabalho:")
    
    # Lógica Original de Seleção (Checkboxes)
    selecionados = []
    for i, obj in enumerate(st.session_state.lista_objs):
        if st.checkbox(obj, key=f"obj_{i}"):
            selecionados.append(obj)
            
    if st.button("Confirmar Objetivos"):
        if selecionados:
            st.session_state.dados['objetivos'] = "\n".join(selecionados)
            st.session_state.step = 5
            st.rerun()
        else:
            st.warning("Selecione ao menos um objetivo antes de avançar.")

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