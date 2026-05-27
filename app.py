import os
import json
import streamlit as st
import google.generativeai as genai

# Configurações iniciais da página
st.set_page_config(
    page_title="English Practice | Prática de Escrita com Gemini",
    page_icon="🇬🇧",
    layout="centered",
    initial_sidebar_state="expanded"
)

# Estilização CSS personalizada para um design moderno e premium
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap');
    
    /* Configurações globais de fonte e estilo */
    html, body, [class*="css"], .stApp {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    h1, h2, h3 {
        font-family: 'Outfit', sans-serif;
        font-weight: 700;
        letter-spacing: -0.5px;
    }
    
    /* Header estilizado */
    .header-container {
        text-align: center;
        padding: 2rem 0 1.5rem 0;
        background: linear-gradient(135deg, #4f46e5 0%, #06b6d4 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    
    .subtitle {
        text-align: center;
        color: #6b7280;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }
    
    /* Cards personalizados para exibição de resultados */
    .card-correct {
        background-color: #f0fdf4;
        border: 1px solid #bbf7d0;
        border-left: 5px solid #22c55e;
        border-radius: 12px;
        padding: 1.25rem;
        margin-bottom: 1.5rem;
        color: #166534;
    }
    
    .card-incorrect {
        background-color: #fff1f2;
        border: 1px solid #fecdd3;
        border-left: 5px solid #f43f5e;
        border-radius: 12px;
        padding: 1.25rem;
        margin-bottom: 1.5rem;
        color: #9f1239;
    }
    
    .card-info {
        background-color: #eff6ff;
        border: 1px solid #bfdbfe;
        border-left: 5px solid #3b82f6;
        border-radius: 12px;
        padding: 1.25rem;
        margin-bottom: 1.5rem;
        color: #1e3a8a;
    }
    
    /* Destakes de Frases */
    .corrected-text {
        font-family: 'Outfit', monospace;
        font-size: 1.2rem;
        font-weight: 600;
        padding: 0.5rem 0;
    }
    
    /* Animações e transições suaves */
    .stButton>button {
        background: linear-gradient(135deg, #4f46e5 0%, #3730a3 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.6rem 2rem !important;
        font-weight: 600 !important;
        font-family: 'Outfit', sans-serif !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 6px -1px rgba(79, 70, 229, 0.2) !important;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 10px 15px -3px rgba(79, 70, 229, 0.3) !important;
    }
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# CONTROLE DE CREDENCIAIS (API KEY)
# ------------------------------------------------------------------------------
# Obtém a API Key diretamente da variável de ambiente padrão do sistema
api_key = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=api_key)

# Configuração da Sidebar
st.sidebar.markdown("""
<div style="text-align: center; padding-top: 1rem;">
    <h2 style="font-family: 'Outfit', sans-serif; color: #4f46e5; margin-bottom: 0.5rem;">Configurações</h2>
</div>
""", unsafe_allow_html=True)

st.sidebar.markdown("""
### 💡 Como Usar:
1. Digite uma frase em **inglês** no campo de texto principal.
2. (Opcional) Digite uma **Palavra-Chave** (ex: *always*, *although*, *break down*) que deseja praticar.
3. Clique em **Verificar Frase**!
4. O Gemini analisará sua escrita e fornecerá explicações e exemplos interativos.
""")

# ------------------------------------------------------------------------------
# INTERFACE PRINCIPAL
# ------------------------------------------------------------------------------

# Título Principal do App
st.markdown('<div class="header-container"><h1>English Practice App</h1></div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Pratique a escrita de frases em inglês no contexto certo com auxílio do Gemini 1.5 Flash</div>', unsafe_allow_html=True)

# Container para os inputs do usuário
with st.container():
    sentence = st.text_input(
        "✍️ Escreva sua frase em inglês:",
        placeholder="Digite sua frase aqui (ex: I always eats breakfast at 7 AM.)",
        help="Escreva qualquer frase que queira avaliar gramaticalmente"
    )
    
    keyword = st.text_input(
        "🔑 Palavra-Chave para praticar (Opcional):",
        placeholder="Ex: always, since, look forward to",
        help="Se informado, o Gemini avaliará se você usou esta palavra corretamente na frase acima."
    )

    submit_button = st.button("🔍 Verificar Frase", use_container_width=True)

# ------------------------------------------------------------------------------
# INTEGRAÇÃO COM A API DO GEMINI
# ------------------------------------------------------------------------------
def analyze_sentence(user_sentence, user_keyword):
    """
    Chama a API do Gemini 1.5 Flash passando a frase e palavra-chave.
    Retorna a resposta estruturada em JSON.
    """
    # Prompt do Sistema
    system_prompt = """
    Você é um professor de inglês nativo e experiente. Seu papel é analisar criticamente e corrigir frases em inglês enviadas por estudantes brasileiros.
    
    Você deve avaliar a frase de acordo com:
    1. Correção gramatical geral.
    2. Fluidez, naturalidade e escolha de palavras (lexicologia).
    3. Se uma palavra-chave for fornecida, valide detalhadamente se ela foi empregada de forma adequada, natural e correta.
    
    Você DEVE retornar a resposta estritamente no seguinte formato JSON, sem qualquer outro texto adicional antes ou depois. Não utilize blocos de código markdown adicionais como ```json se possível, ou retorne apenas o JSON bruto válido.
    
    Estrutura JSON esperada:
    {
      "is_correct": boolean, // true se a frase estiver 100% correta gramatical e contextualmente, false caso contrário
      "translation": "tradução exata da frase fornecida pelo usuário para o português brasileiro",
      "corrected_sentence": "a frase corrigida se houver qualquer erro (gramatical, ortográfico ou de pontuação), ou null se a frase estiver 100% correta",
      "explanation": "explicação curta e pedagógica (em português) sobre os erros cometidos, ou elogios e observações didáticas caso a frase esteja correta",
      "keyword_valid": boolean ou null, // se uma palavra-chave foi fornecida, true se foi usada corretamente, false se usada incorretamente. Se nenhuma palavra-chave foi fornecida, retorne null
      "keyword_explanation": "explicação (em português) do porquê a palavra-chave foi usada corretamente ou incorretamente na frase, ou null se não houver palavra-chave",
      "alternative_suggestions": ["sugestão alternativa 1", "sugestão alternativa 2"], // 2 a 3 formas naturais e comuns de expressar a mesma ideia em inglês
      "examples": ["exemplo 1", "exemplo 2", "exemplo 3"] // se uma palavra-chave foi fornecida, 3 frases curtas e práticas de exemplo em inglês usando essa mesma palavra-chave. Cada frase de exemplo DEVE ser acompanhada de sua tradução em português entre parênteses, no formato: 'Frase em Inglês (Frase em Português)'. Se não houver palavra-chave, forneça um array vazio []
    }
    """
    
    # Prompt do usuário
    user_prompt = f"Frase do Usuário: '{user_sentence}'"
    if user_keyword and user_keyword.strip() != "":
        user_prompt += f"\nPalavra-Chave desejada: '{user_keyword.strip()}'"
        
    model = genai.GenerativeModel(
        model_name='gemini-flash-latest',
        system_instruction=system_prompt,
        generation_config={
            "response_mime_type": "application/json",
            "temperature": 0.2,
        }
    )
    
    response = model.generate_content(user_prompt)
    return response.text

# ------------------------------------------------------------------------------
# FLUXO DE SUBMISSÃO E RESULTADO
# ------------------------------------------------------------------------------
if submit_button:
    if not sentence or sentence.strip() == "":
        st.warning("⚠️ Por favor, digite uma frase em inglês antes de clicar em verificar.")
    else:
        with st.spinner("🧠 O Gemini está analisando sua frase... Aguarde um momento!"):
            try:
                # Realiza a análise
                raw_response = analyze_sentence(sentence, keyword)
                
                # Faz o parse da resposta JSON
                response_data = json.loads(raw_response)
                
                st.markdown("---")
                st.markdown("### 📊 Resultado da Análise")
                
                # 1. AVALIAÇÃO GRAMATICAL
                st.markdown("#### 📝 Avaliação Gramatical")
                
                is_correct = response_data.get("is_correct", False)
                corrected = response_data.get("corrected_sentence")
                explanation = response_data.get("explanation", "")
                
                if is_correct:
                    st.markdown(f"""
                    <div class="card-correct">
                        <h4 style="margin:0; font-family:'Outfit';">🎉 Muito bem! Sua frase está gramaticalmente correta!</h4>
                        <p style="margin-top:0.5rem; margin-bottom:0;">{explanation}</p>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    corrected_html = f'<div class="corrected-text">👉 "{corrected}"</div>' if corrected else ""
                    st.markdown(f"""
                    <div class="card-incorrect">
                        <h4 style="margin:0; font-family:'Outfit';">⚠️ Encontramos pontos de melhoria na sua frase:</h4>
                        {corrected_html}
                        <p style="margin-top:0.5rem; margin-bottom:0;"><strong>Explicação:</strong> {explanation}</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Validação da Palavra-Chave (Se fornecida)
                keyword_valid = response_data.get("keyword_valid")
                keyword_explanation = response_data.get("keyword_explanation")
                
                if keyword and keyword.strip() != "" and keyword_valid is not None:
                    st.markdown("#### 🔑 Análise da Palavra-Chave")
                    if keyword_valid:
                        st.markdown(f"""
                        <div class="card-correct" style="border-left-color: #06b6d4;">
                            <h4 style="margin:0; font-family:'Outfit';">🎯 Palavra-chave '{keyword}' aplicada com sucesso!</h4>
                            <p style="margin-top:0.5rem; margin-bottom:0;">{keyword_explanation}</p>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                        <div class="card-incorrect" style="border-left-color: #f59e0b; background-color: #fffbeb; border-color: #fef3c7; color: #b45309;">
                            <h4 style="margin:0; font-family:'Outfit';">⚠️ Ajuste necessário para a palavra-chave '{keyword}':</h4>
                            <p style="margin-top:0.5rem; margin-bottom:0;">{keyword_explanation}</p>
                        </div>
                        """, unsafe_allow_html=True)
                
                # 2. SUGESTÕES ALTERNATIVAS & EXEMPLOS
                st.markdown("#### 💡 Sugestões Alternativas")
                alternatives = response_data.get("alternative_suggestions", [])
                
                if alternatives:
                    cols = st.columns(len(alternatives))
                    for i, alt in enumerate(alternatives):
                        with cols[i]:
                            st.info(f"💡 **Forma {i+1}:**\n\n_{alt}_")
                else:
                    st.write("Sem sugestões alternativas para esta frase.")
                
                # Exibição de frases de exemplo com a Palavra-Chave
                examples = response_data.get("examples", [])
                if keyword and keyword.strip() != "" and examples:
                    st.markdown(f"#### 📚 Pratique mais: Frases de Exemplo com '{keyword}'")
                    for ex in examples:
                        # Se contiver a tradução nos parênteses, estiliza ela
                        if "(" in ex and ex.endswith(")"):
                            parts = ex.split(" (", 1)
                            english_part = parts[0]
                            portuguese_part = parts[1].rstrip(")")
                            st.markdown(f"""
                            <div style="background-color: #f8fafc; border-left: 3px solid #6366f1; padding: 0.8rem 1.2rem; border-radius: 6px; margin-bottom: 0.5rem;">
                                <span style="font-weight: 600; color: #4f46e5;">{english_part}</span><br>
                                <span style="color: #64748b; font-size: 0.9rem; font-style: italic;">{portuguese_part}</span>
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.markdown(f"- {ex}")
                
                # 3. TRADUÇÃO (OCULTA POR PADRÃO)
                st.markdown("#### 🌐 Tradução da Frase")
                translation = response_data.get("translation", "")
                
                with st.expander("👁️ Revelar Tradução para o Português"):
                    st.markdown(f"""
                    <div style="background-color: #fafafa; border: 1px dashed #d1d5db; border-radius: 8px; padding: 1rem; text-align: center;">
                        <h4 style="margin: 0; font-family: 'Outfit', sans-serif; color: #374151;">Tradução aproximada:</h4>
                        <p style="margin-top: 0.5rem; font-size: 1.15rem; font-weight: 500; color: #111827;">"{translation}"</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
            except json.JSONDecodeError:
                st.error("💥 Erro ao processar a resposta do Gemini. O modelo não gerou um JSON válido.")
                with st.expander("Ver resposta bruta do modelo"):
                    st.code(raw_response)
            except Exception as e:
                st.error(f"💥 Ocorreu um erro na requisição: {str(e)}")
