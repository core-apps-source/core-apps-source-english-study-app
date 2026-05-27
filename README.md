# 🇬🇧 English Practice App (Streamlit & Gemini API)

Este é um aplicativo moderno e interativo desenvolvido em **Python** e **Streamlit**, projetado para ajudar estudantes brasileiros a praticarem a escrita de frases em inglês em contexto. O sistema é integrado com a inteligência artificial do Google através da API do Gemini (usando o modelo `gemini-1.5-flash-latest`), garantindo feedback gramatical instantâneo e sugestões enriquecedoras.

---

## ✨ Funcionalidades

*   **Avaliação Gramatical em Tempo Real**: O Gemini avalia a frase digitada e aponta se há erros de gramática, concordância ou concordância de tempo verbal.
*   **Correção Visual Atraente**: Se houver erros, a frase é reescrita de forma correta em destaque com um painel explicativo em português.
*   **Trabalho com Palavra-Chave (Keyword)**: Opcionalmente, adicione uma palavra ou expressão que deseja praticar (ex: *always*, *look forward to*). O sistema valida se você a empregou de forma natural e correta e fornece mais **3 frases práticas de exemplo** com aquela palavra para fixação.
*   **Sugestões Alternativas**: Receba formas diferentes e idiomáticas de expressar a mesma ideia em inglês.
*   **Tradução Oculta por Padrão**: A tradução para o português fica embutida em um painel expansível `st.expander` para não prejudicar seu aprendizado ativo.

---

## 🛠️ Pré-requisitos & Instalação

### Passo 1: Entrar no Diretório
Abra o seu terminal (CMD ou PowerShell) na pasta atual (`C:\Users\PICHAU\Desktop\Foco`):
```bash
cd "C:\Users\PICHAU\Desktop\Foco"
```

### Passo 2: Instalar as Dependências
Instale os pacotes requeridos usando o pip:
```bash
pip install -r requirements.txt
```

---

## 🔑 Configurando sua Gemini API Key

O aplicativo lê a sua chave de API do Gemini a partir da variável de ambiente padrão do sistema (`GEMINI_API_KEY`). Defina-a no seu terminal antes de rodar o app:

*   **Windows (PowerShell)**:
    ```powershell
    $env:GEMINI_API_KEY="sua_api_key_aqui"
    ```
*   **Windows (CMD)**:
    ```cmd
    set GEMINI_API_KEY=sua_api_key_aqui
    ```
*   **Linux/macOS**:
    ```bash
    export GEMINI_API_KEY="sua_api_key_aqui"
    ```

---

## 🚀 Como Executar o Projeto

Com as dependências instaladas e a chave de ambiente configurada, execute:

```bash
streamlit run app.py
```

O aplicativo abrirá automaticamente em seu navegador padrão no endereço `http://localhost:8501`.
