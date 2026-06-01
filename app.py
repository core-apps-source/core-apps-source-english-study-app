import os
import json
import streamlit as st
import google.generativeai as genai

# Configurações iniciais da página
st.set_page_config(
    page_title="English Practice & Word Mixer | Auxílio Gemini",
    page_icon="🇬🇧",
    layout="centered",
    initial_sidebar_state="expanded"
)

# Estilização CSS personalizada para um design moderno, premium e coeso
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
        padding: 1.5rem 0 1rem 0;
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
    
    /* Card elegante roxo para sentenças misturadas */
    .card-sentence {
        background-color: #faf5ff;
        border: 1px solid #e9d5ff;
        border-left: 5px solid #a855f7;
        border-radius: 12px;
        padding: 1.25rem;
        margin-bottom: 0.5rem;
        color: #581c87;
        font-size: 1.1rem;
        font-weight: 500;
        box-shadow: 0 4px 6px -1px rgba(168, 85, 247, 0.05);
    }
    
    /* Destaques de Frases */
    .corrected-text {
        font-family: 'Outfit', monospace;
        font-size: 1.2rem;
        font-weight: 600;
        padding: 0.5rem 0;
    }
    
    /* Animações e transições suaves nos botões */
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
api_key = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=api_key)

# ------------------------------------------------------------------------------
# EXCEÇÕES PERSONALIZADAS E TRATAMENTO DE ERROS (RATE LIMIT 429)
# ------------------------------------------------------------------------------
def handle_api_error(e):
    """
    Formata e exibe erros da API do Gemini de maneira amigável e profissional.
    """
    error_msg = str(e)
    if "429" in error_msg or "quota" in error_msg.lower() or "limit" in error_msg.lower():
        st.markdown("""
        <div class="card-incorrect" style="background-color: #fffbeb; border-color: #fef3c7; border-left-color: #d97706; color: #b45309;">
            <h4 style="margin:0; font-family:'Outfit';">⚠️ Limite de Requisições da API Excedido</h4>
            <p style="margin-top:0.5rem; margin-bottom:0.5rem;">
                Você atingiu o limite de cota da versão gratuita do Gemini (geralmente limitado a 15 requisições por minuto).
            </p>
            <p style="margin:0; font-size: 0.9rem; font-weight: 600;">
                ⏱️ Por favor, aguarde cerca de 30 a 60 segundos antes de tentar novamente para que o Google libere seu acesso!
            </p>
        </div>
        """, unsafe_allow_html=True)
    elif "404" in error_msg:
        st.error("💥 Erro 404: O modelo especificado não foi encontrado nos servidores da API do Gemini.")
    else:
        st.error(f"💥 Ocorreu um erro inesperado na requisição: {error_msg}")

# ------------------------------------------------------------------------------
# SIDEBAR - MENU DE NAVEGAÇÃO E GUIA
# ------------------------------------------------------------------------------
st.sidebar.markdown("""
<div style="text-align: center; padding-top: 1rem;">
    <h2 style="font-family: 'Outfit', sans-serif; color: #4f46e5; margin-bottom: 0.5rem;">Navegação</h2>
</div>
""", unsafe_allow_html=True)

# Seletor de página no Sidebar
active_page = st.sidebar.radio(
    "Escolha a ferramenta:",
    ["📝 Praticar Escrita & Dúvidas", "⚡ Gerador de Frases Rígido"]
)

st.sidebar.markdown("---")

if active_page == "📝 Praticar Escrita & Dúvidas":
    st.sidebar.markdown("""
    ### 💡 Como Usar:
    1. Digite uma frase em **inglês** no campo principal.
    2. (Opcional) Digite sua dúvida teórica ou gramatical em português no campo **"Pesquisa de dúvidas"**.
    3. Clique em **Verificar Frase**!
    4. O Gemini analisará sua escrita e responderá à sua dúvida.
    """)
else:
    st.sidebar.markdown("""
    ### 💡 Como Usar:
    1. Digite suas palavras em **inglês** (substantivos, adjetivos, verbos) separadas por espaço ou vírgula.
    2. Clique em **⚡ Gerar Frases**.
    3. O Gemini criará de 3 a 5 frases em inglês utilizando estritamente os seus termos.
    4. Clique no botão de revelação para ver a tradução em português de cada frase!
    """)

st.sidebar.markdown("""
---
⚠️ **Nota de Cota:** A API gratuita do Gemini possui um limite de requisições por minuto. Caso receba um alerta de limite, apenas aguarde 1 minuto para continuar praticando!
""")

# ------------------------------------------------------------------------------
# SISTEMA DE ESTADO DA SESSÃO (SESSION STATE)
# ------------------------------------------------------------------------------
if 'generated_sentences' not in st.session_state:
    st.session_state.generated_sentences = None
if 'last_words' not in st.session_state:
    st.session_state.last_words = ""

# ------------------------------------------------------------------------------
# FUNÇÕES DA API DO GEMINI
# ------------------------------------------------------------------------------
def analyze_sentence(user_sentence, user_doubt):
    """
    Chama a API do Gemini para analisar a frase e responder à dúvida.
    """
    system_prompt = """
    Você é um professor de inglês nativo e experiente. Seu papel é analisar criticamente e corrigir frases em inglês enviadas por estudantes brasileiros.
    
    Você deve avaliar a frase de acordo com:
    1. Correção gramatical geral.
    2. Fluidez, naturalidade e escolha de palavras (lexicologia).
    
    INSTRUÇÃO CENTRAL PARA O CAMPO DE DÚVIDA:
    Se o usuário preencher o campo "Pesquisa de dúvidas" com uma dúvida contextual, gramatical ou teórica (em português), você deve atuar como um suporte explicativo dedicado. Responda diretamente e de forma extremamente didática a essa dúvida no campo "doubt_explanation" do JSON, baseando sua explicação diretamente no contexto da frase informada (se houver). Quando este campo contiver texto, NÃO use a informação para fazer um teste de palavras-chave, mas sim para responder teoricamente à dúvida dele. Se não houver nenhuma dúvida informada, retorne null em "doubt_explanation".
    
    CASO DE AUSÊNCIA DE FRASE:
    Se o usuário não fornecer uma frase em inglês (ou seja, enviar uma string vazia ou sem valor), foque inteiramente em responder à dúvida teórica/gramatical enviada no campo "doubt_explanation" de forma completa, didática e clara. Nesse caso, preencha os outros campos da seguinte forma:
    - "is_correct": true
    - "translation": null
    - "corrected_sentence": null
    - "explanation": "Nenhuma frase foi enviada para análise."
    - "alternative_suggestions": []
    
    Você DEVE retornar a resposta estritamente no seguinte formato JSON, sem qualquer outro texto adicional antes ou depois. Não utilize blocos de código markdown adicionais como ```json se possível, ou retorne apenas o JSON bruto válido.
    
    Estrutura JSON esperada:
    {
      "is_correct": boolean, // true se a frase estiver 100% correta gramatical e contextualmente, false caso contrário
      "translation": "tradução exata da frase fornecida pelo usuário para o português brasileiro",
      "corrected_sentence": "a frase corrigida se houver qualquer erro (gramatical, ortográfico ou de pontuação), ou null se a frase estiver 100% correta",
      "explanation": "explicação curta e pedagógica (em português) sobre os erros cometidos, ou elogios e observações didáticas caso a frase esteja correta",
      "doubt_explanation": "resposta detalhada e didática em português para a dúvida informada no campo de 'Pesquisa de dúvidas'. Se não houver dúvida, retorne null",
      "alternative_suggestions": ["sugestão alternativa 1", "sugestão alternativa 2"] // 2 a 3 formas naturais e comuns de expressar a mesma ideia em inglês
    }
    """
    
    user_prompt = f"Frase do Usuário: '{user_sentence}'"
    if user_doubt and user_doubt.strip() != "":
        user_prompt += f"\nDúvida/Pesquisa enviada pelo usuário (em português): '{user_doubt.strip()}'"
        
    model = genai.GenerativeModel(
        model_name='gemini-2.5-flash',
        system_instruction=system_prompt,
        generation_config={
            "response_mime_type": "application/json",
            "temperature": 0.2,
        }
    )
    
    response = model.generate_content(user_prompt)
    return response.text


def generate_phrases_api(words_list):
    """
    Chama a API do Gemini para misturar as palavras em sentenças em inglês sob restrição estrita,
    retornando também as traduções correspondentes.
    """
    system_prompt = """
    Você é um gerador linguístico estrito e preciso de sentenças em inglês.
    Sua tarefa é ler uma lista de palavras fornecidas e gerar aleatoriamente entre 3 e 5 frases naturais em inglês misturando e usando essas palavras.
    
    RESTRIÇÃO GRAMATICAL ESTRITA E CRÍTICA:
    Você SÓ pode utilizar as palavras em inglês que o usuário enviou. A única exceção permitida para ligar ou dar sentido à frase é a adição de complementos gramaticais curtos em inglês (como artigos, preposições, conjunções, pronomes, verbos de ligação clássicos e verbos de ação simples). 
    NENHUM outro substantivo, adjetivo ou advérbio adicional pode ser incluído de forma alguma! Todas as palavras conceituais principais das frases devem vir exclusivamente da lista do usuário.
    
    Exemplo de entrada: "sun, beach, walk, happy"
    Exemplo de frase correta: "I can walk happy on the beach under the sun."
    Exemplo incorreto: "My friend walks happy on the beach." (ERRADO: "friend" não estava na entrada)
    
    Você DEVE retornar a resposta estritamente no seguinte formato JSON, sem qualquer outro texto adicional antes ou depois. Não utilize blocos de código markdown adicionais como ```json se possível, ou retorne apenas o JSON bruto válido.
    
    Estrutura JSON esperada:
    {
      "results": [
        {
          "sentence": "Frase em inglês gerada",
          "translation": "Tradução correspondente em português brasileiro"
        }
      ]
    }
    """
    
    user_prompt = f"Gere frases em inglês misturando as seguintes palavras do usuário: '{words_list}'"
    
    model = genai.GenerativeModel(
        model_name='gemini-2.5-flash',
        system_instruction=system_prompt,
        generation_config={
            "response_mime_type": "application/json",
            "temperature": 0.85,
        }
    )
    
    response = model.generate_content(user_prompt)
    return response.text

# ------------------------------------------------------------------------------
# INTERFACE PRINCIPAL - PÁGINA 1: PRÁTICA DE ESCRITA & DÚVIDAS
# ------------------------------------------------------------------------------
if active_page == "📝 Praticar Escrita & Dúvidas":
    st.markdown('<div class="header-container"><h1>English Practice App</h1></div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Pratique a escrita de frases em inglês no contexto certo com auxílio do Gemini</div>', unsafe_allow_html=True)
    
    with st.container():
        sentence = st.text_input(
            "✍️ Escreva sua frase em inglês:",
            placeholder="Digite sua frase aqui (ex: I always eats breakfast at 7 AM.)",
            help="Escreva qualquer frase que queira avaliar gramaticalmente"
        )
        
        doubt = st.text_input(
            "🔍 Pesquisa de dúvidas (Opcional):",
            placeholder="Ex: Por que não posso usar a palavra X aqui? / Qual a diferença entre X e Y nesse contexto?",
            help="Digite sua dúvida teórica ou gramatical em português sobre o contexto da frase ou regras gerais."
        )

        submit_button = st.button("🔍 Verificar Frase", use_container_width=True)

    if submit_button:
        has_sentence = sentence and sentence.strip() != ""
        has_doubt = doubt and doubt.strip() != ""
        
        if not has_sentence and not has_doubt:
            st.warning("⚠️ Por favor, digite uma frase em inglês ou uma dúvida antes de clicar em verificar.")
        else:
            with st.spinner("🧠 O Gemini está analisando sua solicitação... Aguarde um momento!"):
                try:
                    raw_response = analyze_sentence(sentence, doubt)
                    response_data = json.loads(raw_response)
                    
                    st.markdown("---")
                    st.markdown("### 📊 Resultado da Análise")
                    
                    # 1. AVALIAÇÃO GRAMATICAL (Apenas se tiver enviado uma frase)
                    if has_sentence:
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
                    
                    # Resposta à Dúvida do Usuário (Se houver)
                    doubt_explanation = response_data.get("doubt_explanation")
                    if has_doubt and doubt_explanation:
                        st.markdown("#### 💡 Resposta à sua Dúvida")
                        st.markdown(f"""
                        <div class="card-info" style="border-left-color: #6366f1; background-color: #f5f3ff; border-color: #ddd6fe; color: #4338ca;">
                            <h4 style="margin:0; font-family:'Outfit';">🧠 Explicação Teórica & Contextual:</h4>
                            <p style="margin-top:0.5rem; margin-bottom:0;">{doubt_explanation}</p>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # 2. SUGESTÕES ALTERNATIVAS (Apenas se tiver enviado uma frase)
                    if has_sentence:
                        st.markdown("#### 💡 Sugestões Alternativas")
                        alternatives = response_data.get("alternative_suggestions", [])
                        
                        if alternatives:
                            cols = st.columns(len(alternatives))
                            for i, alt in enumerate(alternatives):
                                with cols[i]:
                                    st.info(f"💡 **Forma {i+1}:**\n\n_{alt}_")
                        else:
                            st.write("Sem sugestões alternativas para esta frase.")
                        
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
                        
                except Exception as e:
                    handle_api_error(e)

# ------------------------------------------------------------------------------
# INTERFACE PRINCIPAL - PÁGINA 2: GERADOR DE FRASES RÍGIDO (MIXER)
# ------------------------------------------------------------------------------
else:
    st.markdown('<div class="header-container"><h1>Gerador de Frases Rígido</h1></div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Misture suas próprias palavras em inglês e veja a tradução correspondente com auxílio da IA</div>', unsafe_allow_html=True)
    
    with st.container():
        words_input = st.text_area(
            "✍️ Digite suas palavras em inglês (separadas por espaço ou vírgula):",
            placeholder="Ex: sun, beach, warm, walk, happy, today",
            help="Digite as palavras conceituais principais em inglês. O Gemini criará as sentenças misturando elas."
        )
        
        col_gen, col_clear = st.columns(2)
        with col_gen:
            generate_button = st.button("⚡ Gerar Frases", use_container_width=True)
        with col_clear:
            clear_button = st.button("🗑️ Limpar Tudo", use_container_width=True)

    if clear_button:
        st.session_state.generated_sentences = None
        st.session_state.last_words = ""
        st.rerun()

    # Fluxo de Geração
    if generate_button:
        # Separa termos por vírgula e espaço
        words_list = [w.strip() for w in words_input.split(",") if w.strip() != ""]
        if len(words_list) <= 1:
            words_list = [w.strip() for w in words_input.split(" ") if w.strip() != ""]
            
        if len(words_list) < 3:
            st.warning("⚠️ Por favor, digite pelo menos 3 palavras em inglês para gerar as sentenças de forma criativa.")
        else:
            with st.spinner("🧠 O Gemini está analisando seus termos e construindo as frases..."):
                try:
                    raw_response = generate_phrases_api(", ".join(words_list))
                    response_data = json.loads(raw_response)
                    st.session_state.generated_sentences = response_data.get("results", [])
                    st.session_state.last_words = words_input
                except Exception as e:
                    handle_api_error(e)

    # Exibição de Resultados
    if st.session_state.generated_sentences:
        st.markdown("---")
        st.markdown("### 📊 Frases Geradas em Inglês")
        
        for idx, item in enumerate(st.session_state.generated_sentences):
            english_sentence = item.get("sentence", "")
            portuguese_translation = item.get("translation", "")
            
            st.markdown(f"""
            <div class="card-sentence">
                <span style="font-size:0.85rem; font-weight:700; color:#a855f7; display:block; margin-bottom:0.25rem;">FRASE {idx+1}</span>
                "{english_sentence}"
            </div>
            """, unsafe_allow_html=True)
            
            # Botão de revelação da tradução via expander
            with st.expander(f"👁️ Revelar Tradução da Frase {idx+1}"):
                st.markdown(f"""
                <div style="background-color: #fafafa; border: 1px dashed #d1d5db; border-radius: 8px; padding: 0.85rem; text-align: center;">
                    <p style="margin: 0; font-size: 1.05rem; font-weight: 500; color: #1f2937;">"{portuguese_translation}"</p>
                </div>
                """, unsafe_allow_html=True)
            
        st.markdown("---")
        # Botão secundário de Regerar / Embaralhar
        if st.button("🔄 Gerar Novas Frases (Embaralhar)", use_container_width=True):
            with st.spinner("🧠 O Gemini está criando novas combinações de frases em inglês..."):
                try:
                    raw_response = generate_phrases_api(st.session_state.last_words)
                    response_data = json.loads(raw_response)
                    st.session_state.generated_sentences = response_data.get("results", [])
                    st.rerun()
                except Exception as e:
                    handle_api_error(e)
