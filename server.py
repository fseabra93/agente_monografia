import os
from flask import Flask, request, jsonify, render_template, send_from_directory
from openai import OpenAI
from dotenv import load_dotenv
from datetime import datetime

# Carregar variáveis de ambiente
load_dotenv()

app = Flask(__name__, static_folder='static', template_folder='templates')
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Determinar qual modelo usar (fallback para gpt-4o caso gpt-5.1 não esteja disponível)
DEFAULT_MODEL = "gpt-4o"

def call_gpt(prompt):
    try:
        # Tenta com gpt-4o primeiro, pois é o modelo disponível mais estável.
        # Se preferir gpt-5.1, tentará gpt-5.1 e depois gpt-4o.
        response = client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Erro ao chamar OpenAI com {DEFAULT_MODEL}: {e}")
        # Se falhar, tenta com gpt-4o-mini como último recurso
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content
        except Exception as err:
            return f"Erro na API da OpenAI: {err}"

# Rota para servir a página principal do frontend
@app.route('/')
def index():
    return render_template('index.html')

# Endpoint para o Passo 1: Geração de temas sugeridos
@app.route('/api/gerar-temas', methods=['POST'])
def gerar_temas():
    data = request.json or {}
    area = data.get('area', '').strip()
    ideia_bruta = data.get('ideia_bruta', '').strip()
    temas_existentes = data.get('temas_existentes', [])

    if not area or not ideia_bruta:
        return jsonify({"error": "Área e ideia bruta são obrigatórias"}), 400

    exclusao = "\n".join(temas_existentes)
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
    novos_temas = [l.split('.', 1)[-1].strip() for l in linhas if l.strip() and l[0].isdigit()]
    
    return jsonify({"temas": novos_temas})

# Endpoint para o Passo 2: Geração de subtemas
@app.route('/api/gerar-subtemas', methods=['POST'])
def gerar_subtemas():
    data = request.json or {}
    area = data.get('area', '').strip()
    tema_base = data.get('tema_base', '').strip()

    if not area or not tema_base:
        return jsonify({"error": "Área e tema base são obrigatórios"}), 400

    prompt = f"""
        Você é um especialista em metodologia de pesquisa científica com ampla experiência 
        em revisões integrativas da literatura na área de {area}.

        Sua tarefa é mapear os principais subtemas que compõem ou se relacionam diretamente 
        com o seguinte tema de pesquisa:

        Tema central: {tema_base}

        Entende-se por subtema um recorte temático específico que pode ser investigado 
        de forma independente dentro do tema central, com literatura científica própria 
        e relevância para uma revisão integrativa de TCC de graduação.

        Critérios para as sugestões:
        - Devem ser recortes diretos do tema central, não tópicos periféricos ou tangenciais
        - Devem ter literatura científica disponível suficiente para uma revisão integrativa
        - Devem variar entre recortes conceituais, populacionais, contextuais e aplicados,
        sempre que pertinente ao tema
        - Devem ser viáveis no escopo de um TCC de graduação
        
        Output:
        Gere exatamente 10 sugestões de subtemas em lista numerada de 1 a 10.
        Cada item deve conter o título do subtema escrito em negrito seguido de uma breve justificativa 
        acadêmica de sua relevância para o tema central, no seguinte formato:
        {{título do subtema}}: {{justificativa}};
        Use linguagem acadêmica formal.
        """

    resposta = call_gpt(prompt)
    subtemas = [l.split('.', 1)[-1].strip() if '.' in l[:3] else l.strip() 
                for l in resposta.strip().split('\n') if l.strip()]

    return jsonify({"subtemas": subtemas})

# Endpoint para o Passo 3: Geração de problemas de pesquisa
@app.route('/api/gerar-problemas', methods=['POST'])
def gerar_problemas():
    data = request.json or {}
    tema_escolhido = data.get('tema_escolhido', '').strip()

    if not tema_escolhido:
        return jsonify({"error": "Tema escolhido é obrigatório"}), 400

    prompt = f"""Você é um especialista em metodologia de pesquisa científica com ampla experiência 
        em revisões integrativas da literatura.

        Sua tarefa é formular problemas de pesquisa adequados para uma monografia no 
        formato de revisão integrativa da literatura, a partir do seguinte tema:

        Tema escolhido: {tema_escolhido}

        Entende-se por problema de pesquisa uma pergunta clara, delimitada e investigável 
        que orienta toda a revisão, cuja resposta pode ser construída a partir da análise 
        crítica da literatura científica existente — sem coleta de dados primários.

        Critérios para as sugestões:
        - Devem ser perguntas respondíveis por meio de revisão da literatura, 
        não por experimentos ou coleta de dados primários
        - Devem ter escopo adequado a um TCC de graduação: nem amplos demais 
        (impossíveis de responder) nem restritos demais (literatura insuficiente)
        - Devem variar em abordagem: algumas focando em relações entre variáveis, 
        outras em lacunas do conhecimento, outras em comparações ou tendências 
        identificadas na literatura
        - Devem ser formulados de forma clara, objetiva e em linguagem acadêmica formal

        Gere exatamente 10 sugestões de problema de pesquisa em lista numerada de 1 a 10,
        apresentando apenas as perguntas, sem comentários ou explicações adicionais."""

    resposta = call_gpt(prompt)
    probs = [l.split('.', 1)[-1].strip() if '.' in l[:3] else l.strip() 
             for l in resposta.strip().split('\n') if l.strip()]

    return jsonify({"problemas": probs})

# Endpoint para o Passo 4: Geração de objetivos específicos
@app.route('/api/gerar-objetivos', methods=['POST'])
def gerar_objetivos():
    data = request.json or {}
    tema_escolhido = data.get('tema_escolhido', '').strip()
    problema_pesquisa = data.get('problema_pesquisa', '').strip()

    if not tema_escolhido or not problema_pesquisa:
        return jsonify({"error": "Tema escolhido e problema de pesquisa são obrigatórios"}), 400

    prompt = f"""Você é um especialista em metodologia de pesquisa científica com ampla experiência 
        em revisões integrativas da literatura.

        Sua tarefa é sugerir objetivos específicos adequados para uma monografia no 
        formato de revisão integrativa da literatura, com base no seguinte contexto:

        Tema: {tema_escolhido}
        Problema de pesquisa: {problema_pesquisa}

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

    resposta = call_gpt(prompt)
    objs = [l.strip() for l in resposta.split('\n') if l.strip() and any(c.isdigit() for c in l[:3])]

    return jsonify({"objetivos": objs})

# Endpoint para o Passo 5: Geração de referencial e estratégia
@app.route('/api/gerar-estrategia', methods=['POST'])
def gerar_estrategia():
    data = request.json or {}
    area = data.get('area', '').strip()
    tema_escolhido = data.get('tema_escolhido', '').strip()

    if not area or not tema_escolhido:
        return jsonify({"error": "Área e tema escolhido são obrigatórios"}), 400

    # Chamada 1: Referencial Teórico (Agente 5)
    prompt_ref = f"""Você é um especialista em metodologia de pesquisa científica e revisão de literatura,
        com conhecimento aprofundado sobre o campo de {area}.

        Sua tarefa é mapear o panorama intelectual da literatura sobre o tema a seguir,
        auxiliando um estudante de graduação a compreender as bases teóricas antes de 
        iniciar sua revisão integrativa.

        Tema: {tema_escolhido}

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

    ref_classicas = call_gpt(prompt_ref)

    # Chamada 2: Estratégia de Busca (Agente 6)
    ano_atual = datetime.now().year
    ano_inicial = ano_atual - 5

    prompt_busca = f"""Você é um especialista em Biblioteconomia, Ciência da Informação e recuperação 
        de informação em bases de dados científicas, com amplo conhecimento sobre os 
        vocabulários controlados DeCS (Descritores em Ciências da Saúde) e MeSH 
        (Medical Subject Headings).

        Sua tarefa é construir uma estratégia de busca estruturada para uma revisão 
        integrativa da literatura sobre o tema a seguir:

        Tema: {tema_escolhido}
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

    ref_atuais = call_gpt(prompt_busca)

    return jsonify({
        "ref_classicas": ref_classicas,
        "ref_atuais": ref_atuais
    })

# Endpoint para o Passo 8: Redação da Monografia
@app.route('/api/gerar-monografia', methods=['POST'])
def gerar_monografia():
    data = request.json or {}
    area = data.get('area', '').strip()
    plano_final_texto = data.get('plano_final_texto', '').strip()

    if not area or not plano_final_texto:
        return jsonify({"error": "Área e plano final de texto são obrigatórios"}), 400

    prompt_agente8 = f"""Você é um orientador acadêmico sênior, doutor em {area} com expertise 
        em redação científica, estruturação de pesquisas e conformidade com normas ABNT 
        (NBR 14724 para trabalhos acadêmicos, NBR 6023 para referências e NBR 10520 para citações). 
        Sua abordagem é didática, rigorosa e criativa, garantindo originalidade, profundidade analítica e 
        relevância prática. Adote uma personalidade empática e encorajadora, com tom formal e respeitoso, 
        linguagem acadêmica precisa, estilo expositivo e narrativo, e propósito de ensinar e informar, 
        visando capacitar o aluno a defender o trabalho com confiança.
        
        Objetivo:
        Produzir um Trabalho de Conclusão de Curso (TCC) completo, coeso e de alta qualidade acadêmica, 
        com critérios de sucesso mensuráveis:
        (1) alinhamento total ao plano de trabalho abaixo;
        (2) estrutura lógica com todas as seções obrigatórias;
        (3) pelo menos 10 referências atualizadas e citadas corretamente;
        (4) análise crítica original sem plágio;
        (5) extensão entre 40-60 páginas sem anexos (gere o conteúdo mais denso e detalhado possível);
        (6) linguagem clara, objetiva e acessível, com vocabulário técnico apropriado;
        (7) inclusão de elementos visuais como figuras, tabelas e fluxogramas (descritos em texto/markdown) para ilustrar conceitos;
        (8) conclusão com recomendações práticas e sugestões para pesquisas futuras.

        Plano de Trabalho de Referência:
        {plano_final_texto}

        Tarefa:
        Realize uma revisão bibliográfica extensa, sintetizando pelo menos 15 fontes recentes (de 2018 em diante, priorizando artigos de revistas indexadas como Scopus ou Web of Science, livros e teses), destacando lacunas na literatura que o TCC preenche.
        Desenvolva a metodologia de forma detalhada: descreva o tipo de pesquisa (qualitativa, quantitativa ou mista), métodos de coleta de dados (ex.: surveys, experimentos, análise de casos), ferramentas utilizadas (ex.: Python para simulações, surveys via Google Forms) e procedimentos éticos (anonimato, consentimento).
        Apresente resultados e discussão: inclua dados simulados ou hipotéticos realistas baseados em referências, com análise crítica comparando com a literatura, identificando contribuições originais e limitações.
        Finalize com conclusões que respondam aos objetivos, recomendações aplicáveis e perspectivas futuras. 
        Limites: Foque exclusivamente no escopo do tema; evite generalizações amplas ou conteúdos off-topic; não inclua dados inventados sem base referencial – sinalize incertezas e sugira verificações; respeite normas éticas; proíba plágio; gere conteúdo 100% original.
        """

    monografia = call_gpt(prompt_agente8)
    return jsonify({"monografia": monografia})

if __name__ == '__main__':
    # Roda localmente na porta 5000
    app.run(host='0.0.0.0', port=5000, debug=True)
