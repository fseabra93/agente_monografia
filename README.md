# 🎓 Agente Monografia

> **Sistema de Inteligência Artificial para Escolha de Tema, Problema e Estratégia de Pesquisa para Monografias e TCCs.**  
> *Idealizado por Flávio Seabra ([@fs_orientadoracademico](https://www.instagram.com/fs_orientadoracademico/))*

---

## 📖 Sobre o Projeto

O **Agente Monografia** é uma ferramenta desenvolvida para auxiliar estudantes, orientadores e pesquisadores nas etapas iniciais e cruciais de um Trabalho de Conclusão de Curso (TCC) ou Monografia, com foco especial no modelo de **Revisão Integrativa da Literatura**.

Por meio de agentes inteligentes e modelos de linguagem (OpenAI GPT / LangGraph), o sistema atua de maneira interativa e sequencial para transformar uma ideia inicial genérica em uma estrutura metodológica pronta para execução.

---

## 🚀 Etapas do Fluxo Metodológico

O assistente é organizado em etapas consecutivas e interativas:

1. **Passo 1 — Definição do Tema:** A partir da área do conhecimento e da ideia inicial do estudante, a IA sugere 10 temas viáveis e acadêmicos.
2. **Passo 2 — Delimitação em Subtemas:** O agente mapeia **6 subtemas abrangentes e distintos**, garantindo que nenhum se sobreponha e cobrindo os eixos teóricos, metodológicos, contextuais e de impacto.
3. **Passo 3 — Problema de Pesquisa:** Formula **6 problemas de pesquisa (perguntas norteadoras)** sem sobreposição conceitual, focados em revisão integrativa.
4. **Passo 4 — Objetivos da Pesquisa:** Sugere objetivos específicos com verbos no infinitivo e justificativas metodológicas.
5. **Passo 5 — Curadoria Teórica e Estratégia de Busca:**
   - **Referencial Teórico:** Mapa de autores clássicos e contemporâneos e correntes de pensamento.
   - **Estratégia DeCS/MeSH:** Descritores controlados e strings booleanas (`AND`/`OR`) para PubMed, SciELO, LILACS e Google Acadêmico.
6. **Passo 6 — Consolidação e Exportação:** Visualização unificada e download do Plano de Trabalho em formato Markdown (`.md`).

> [!TIP]
> **Navegação Flexível & Identidade Visual:**  
> A partir do Passo 2, todas as etapas possuem o botão **"Retornar ao passo anterior"**, permitindo revisar escolhas sem reiniciar o trabalho. Todos os botões de confirmação de avanço são destacados em **vermelho**.

---

## 🧠 Arquitetura e Fluxo do Agente

```mermaid
flowchart TD
    subgraph Entrada ["📥 Entrada de Dados"]
        In1["Área do Conhecimento"]
        In2["Ideia Inicial do Estudante"]
    end

    subgraph Passo1 ["🎯 Passo 1: Definição do Tema"]
        A1["Agente 1: Gerador de Temas (OpenAI GPT)"]
        T1["Lista de Temas Sugeridos (10 Opções)"]
        U1["Seleção ou Ajuste do Tema Base"]
        BtnConf1["Confirmar Tema (Botão Vermelho)"]
    end

    subgraph Passo2 ["🔍 Passo 2: Aprofundamento"]
        A2["Agente 2: Recorte Temático (Eixos Independentes)"]
        T2["6 Subtemas Abrangentes e Distintos"]
        U2["Seleção do Subtema ou Manter Original"]
        BtnVoltar2["Retornar ao Passo 1"]
        BtnConf2["Confirmar Subtema (Botão Vermelho)"]
    end

    subgraph Passo3 ["❓ Passo 3: Problema de Pesquisa"]
        A3["Agente 3: Perguntas Norteadoras"]
        T3["6 Problemas Sem Sobreposição"]
        U3["Seleção ou Edição da Pergunta"]
        BtnVoltar3["Retornar ao Passo 2"]
        BtnConf3["Confirmar Problema (Botão Vermelho)"]
    end

    subgraph Passo4 ["🎯 Passo 4: Objetivos Específicos"]
        A4["Agente 4: Objetivos Operacionais (Verbos Infinitivo)"]
        T4["Sugestões de Objetivos com Justificativas"]
        U4["Seleção Múltipla de Objetivos"]
        BtnVoltar4["Retornar ao Passo 3"]
        BtnConf4["Confirmar Objetivos (Botão Vermelho)"]
    end

    subgraph Passo5 ["📚 Passo 5: Curadoria e Metodologia"]
        A5["Agente 5: Referencial Teórico (Autores e Correntes)"]
        A6["Agente 6: Estratégia de Busca (DeCS/MeSH e Strings)"]
    end

    subgraph Passo6 ["📄 Passo 6: Consolidação e Exportação"]
        Relatorio["Plano de Trabalho Acadêmico Estruturado"]
        Download["Download do Arquivo Markdown (.md)"]
        BtnVoltar6["Retornar ao Passo 4"]
        BtnReset["Reiniciar Sistema"]
    end

    %% Fluxo Sequencial
    Entrada --> A1
    A1 --> T1
    T1 --> U1
    U1 --> BtnConf1
    BtnConf1 --> A2
    A2 --> T2
    T2 --> U2
    U2 --> BtnConf2
    BtnConf2 --> A3
    A3 --> T3
    T3 --> U3
    U3 --> BtnConf3
    BtnConf3 --> A4
    A4 --> T4
    T4 --> U4
    U4 --> BtnConf4
    BtnConf4 --> A5
    BtnConf4 --> A6
    A5 --> Relatorio
    A6 --> Relatorio
    Relatorio --> Download

    %% Ciclos de Retorno / Navegação Interativa
    BtnVoltar2 -. "Retornar" .-> U1
    BtnVoltar3 -. "Retornar" .-> U2
    BtnVoltar4 -. "Retornar" .-> U3
    BtnVoltar6 -. "Retornar" .-> U4
    BtnReset -. "Reiniciar" .-> In1
```

---

## 📁 Estrutura de Arquivos

```plaintext
agente_monografia/
├── app.py                # Interface web principal interativa em Streamlit
├── graph_logic.py        # Grafo de agentes e orquestração do LangGraph
├── requirements.txt      # Dependências do projeto
├── .env.example          # Modelo de variáveis de ambiente
└── .gitignore            # Arquivos ignorados pelo Git (.env, venvs, etc.)
```

---

## 🛠️ Pré-requisitos

- **Python:** Versão 3.10 ou superior instalada.
- **Chave de API da OpenAI:** Obtenha uma chave em [platform.openai.com](https://platform.openai.com/).

---

## ⚙️ Instalação e Configuração

Siga o passo a passo abaixo no terminal na raiz do projeto:

### 1. Criar o Ambiente Virtual (`venv`)

#### No Windows (PowerShell / Prompt de Comando):
```powershell
python -m venv my_env
```

#### No Linux / macOS:
```bash
python3 -m venv my_env
```

---

### 2. Ativar o Ambiente Virtual

#### No Windows (PowerShell):
```powershell
.\my_env\Scripts\Activate.ps1
```
> *Caso ocorra erro de execução de scripts no PowerShell, execute antes:*  
> `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process`

#### No Windows (Prompt de Comando - CMD):
```cmd
my_env\Scripts\activate.bat
```

#### No Linux / macOS:
```bash
source my_env/bin/activate
```

---

### 3. Atualizar o `pip` e Instalar as Dependências

Com o ambiente virtual ativado, execute:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

---

### 4. Configurar a Chave da OpenAI (`.env`)

Crie um arquivo chamado `.env` na raiz do diretório `agente_monografia` com a sua chave de API:

```env
OPENAI_API_KEY=sua-chave-api-aqui
```

---

## ▶️ Como Executar

Execute a aplicação interativa via **Streamlit**:

```bash
streamlit run app.py
```

O aplicativo abrirá automaticamente no navegador no endereço:  
👉 **`http://localhost:8501`**

---

## 📦 Dependências Principais

- **[Streamlit](https://streamlit.io/):** Criação rápida de interfaces web interativas.
- **[LangGraph](https://github.com/langchain-ai/langgraph) & [LangChain](https://www.langchain.com/):** Orquestração do estado e fluxo dos agentes de pesquisa.
- **[OpenAI API](https://platform.openai.com/docs):** Modelos de linguagem para geração e refinamento dos passos metodológicos.
- **[python-dotenv](https://github.com/theskumar/python-dotenv):** Gerenciamento seguro de variáveis de ambiente.

---

## 🔄 Como Atualizar o Projeto no GitHub

Para enviar suas alterações, novos arquivos ou arquivos removidos para o repositório remoto no GitHub, execute os seguintes comandos no terminal:

### 1. Entrar na pasta do projeto
Caso seu terminal esteja na pasta pai (`projetos`), entre na pasta do repositório:
```bash
cd agente_monografia
```

### 2. Verificar os arquivos modificados
```bash
git status
```

### 3. Adicionar todas as alterações (novos arquivos, modificações e exclusões)
```bash
git add .
```

### 4. Registrar o commit com uma mensagem descritiva
```bash
git commit -m "feat: atualizacoes no agente de monografia, navegacao e documentacao"
```

### 5. (Recomendado) Obter eventuais atualizações remotas
```bash
git pull origin main
```

### 6. Enviar as alterações para o GitHub
```bash
git push origin main
```

> [!IMPORTANT]
> **Segurança de Credenciais:** Certifique-se de que o arquivo `.env` (contendo sua `OPENAI_API_KEY`) **nunca** seja enviado ao GitHub. Ele já está configurado no arquivo `.gitignore` para sua segurança.

---

## 👨‍🏫 Autor & Créditos

Desenvolvido por **Flávio Seabra**  
- Orientação acadêmica, metodologia de pesquisa e inteligência artificial aplicada.  
- Instagram: [@fs_orientadoracademico](https://www.instagram.com/fs_orientadoracademico/)

