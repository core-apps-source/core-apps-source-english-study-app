# -*- coding: utf-8 -*-
import os
import json
import sqlite3
import random
import re
import streamlit as st
import google.generativeai as genai

# Configurações iniciais da página
st.set_page_config(
    page_title="English Practice, Word Mixer & Verb Study | Auxílio Gemini",
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
    
    /* Card elegante azul/indigo para conjugação verbal */
    .card-conjugation {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        border-left: 5px solid #6366f1;
        border-radius: 10px;
        padding: 0.75rem 1rem;
        margin-bottom: 0.75rem;
        color: #1e293b;
        font-size: 1.05rem;
        font-weight: 500;
        box-shadow: 0 2px 4px rgba(99, 102, 241, 0.03);
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
def get_api_key():
    # 1. Verifica no session_state (inserida manualmente pelo usuário)
    if "api_key_override" in st.session_state and st.session_state.api_key_override:
        return st.session_state.api_key_override

    # 2. Verifica variáveis de ambiente convencionais
    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if key:
        return key
        
    # 3. Verifica segredos internos do Streamlit (.streamlit/secrets.toml)
    try:
        if "GEMINI_API_KEY" in st.secrets:
            return st.secrets["GEMINI_API_KEY"]
        if "GOOGLE_API_KEY" in st.secrets:
            return st.secrets["GOOGLE_API_KEY"]
    except Exception:
        pass
        
    # 4. Verifica arquivo .env local manualmente se existir
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if os.path.exists(env_path):
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip() and not line.strip().startswith("#"):
                        parts = line.strip().split("=", 1)
                        if len(parts) == 2:
                            name, val = parts[0].strip(), parts[1].strip()
                            if name in ["GEMINI_API_KEY", "GOOGLE_API_KEY"]:
                                return val.strip("'\"")
        except Exception:
            pass
            
    return None

api_key = get_api_key()
if api_key:
    genai.configure(api_key=api_key)

# ------------------------------------------------------------------------------
# BANCO DE DADOS E HISTÓRICO DE VERBOS (SQLite)
# ------------------------------------------------------------------------------
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "verbs.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conjugations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            verb TEXT,
            person TEXT,
            tense TEXT,
            affirmative_text TEXT,
            affirmative_translation TEXT,
            question_text TEXT,
            question_translation TEXT,
            negative_text TEXT,
            negative_translation TEXT,
            example_text TEXT,
            example_translation TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS study_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            verb TEXT UNIQUE,
            last_studied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_verb_person_tense 
        ON conjugations (verb, person, tense)
    """)
    conn.commit()
    conn.close()

# Inicializa o banco de dados
init_db()

def get_cached_conjugations(verb, person):
    verb = verb.lower().strip()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT tense, affirmative_text, affirmative_translation, 
               question_text, question_translation, 
               negative_text, negative_translation, 
               example_text, example_translation 
        FROM conjugations 
        WHERE LOWER(verb) = ? AND person = ?
    """, (verb, person))
    rows = cursor.fetchall()
    conn.close()
    
    if len(rows) == 12:
        return [dict(row) for row in rows]
    return None

def get_cached_conjugations_for_tenses(verb, person, target_tenses):
    verb = verb.lower().strip()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    placeholders = ",".join(["?"] * len(target_tenses))
    cursor.execute(f"""
        SELECT tense, affirmative_text, affirmative_translation, 
               question_text, question_translation, 
               negative_text, negative_translation, 
               example_text, example_translation 
        FROM conjugations 
        WHERE LOWER(verb) = ? AND person = ? AND tense IN ({placeholders})
    """, (verb, person, *target_tenses))
    rows = cursor.fetchall()
    conn.close()
    
    if len(rows) == len(target_tenses):
        return [dict(row) for row in rows]
    return None

def resolve_cached_verb(verb_clean, study_type):
    verb_clean = verb_clean.lower().strip()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    if study_type == "Verbo":
        cursor.execute("SELECT DISTINCT verb FROM conjugations WHERE LOWER(verb) = ?", (verb_clean,))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else None
        
    elif study_type == "Adjetivo (com 'to be')":
        target = verb_clean if verb_clean.startswith("be ") else f"be {verb_clean}"
        cursor.execute("SELECT DISTINCT verb FROM conjugations WHERE LOWER(verb) = ?", (target,))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else None
        
    elif study_type == "Verbo + Adjetivo":
        cursor.execute("SELECT DISTINCT verb FROM conjugations WHERE LOWER(verb) = ?", (verb_clean,))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else None
        
    elif study_type == "Substantivo":
        cursor.execute("SELECT DISTINCT verb FROM conjugations WHERE LOWER(verb) LIKE ?", (f"%{verb_clean}%",))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else None
        
    conn.close()
    return None

def save_conjugations(verb, person, tenses_list):
    verb = verb.lower().strip()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    for tense_data in tenses_list:
        cursor.execute("""
            INSERT OR REPLACE INTO conjugations (
                verb, person, tense, 
                affirmative_text, affirmative_translation, 
                question_text, question_translation, 
                negative_text, negative_translation, 
                example_text, example_translation
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            verb, person, tense_data["tense"],
            tense_data["affirmative_text"], tense_data["affirmative_translation"],
            tense_data["question_text"], tense_data["question_translation"],
            tense_data["negative_text"], tense_data["negative_translation"],
            tense_data["example_text"], tense_data["example_translation"]
        ))
    conn.commit()
    conn.close()

def save_to_history(verb):
    verb = verb.lower().strip()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO study_history (verb, last_studied_at) 
        VALUES (?, CURRENT_TIMESTAMP)
        ON CONFLICT(verb) DO UPDATE SET last_studied_at = CURRENT_TIMESTAMP
    """, (verb,))
    conn.commit()
    conn.close()

def get_history(search_query=None, sort_by="recent"):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    query = "SELECT verb FROM study_history"
    params = []
    if search_query:
        query += " WHERE verb LIKE ?"
        params.append(f"%{search_query.lower().strip()}%")
        
    if sort_by == "alphabetical":
        query += " ORDER BY verb ASC"
    else:
        query += " ORDER BY last_studied_at DESC"
        
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [row[0] for row in rows]

def normalize_string(s):
    if not s:
        return ""
    s = s.lower().strip()
    contractions = {
        "don't": "do not",
        "doesn't": "does not",
        "didn't": "did not",
        "won't": "will not",
        "haven't": "have not",
        "hasn't": "has not",
        "hadn't": "had not",
        "isn't": "is not",
        "aren't": "are not",
        "wasn't": "was not",
        "weren't": "were not",
        "i'm": "i am",
        "he's": "he is",
        "she's": "she is",
        "it's": "it is",
        "we're": "we are",
        "they're": "they are",
        "you're": "you are",
        "i've": "i have",
        "you've": "you have",
        "we've": "we have",
        "they've": "they have",
        "he'll": "he will",
        "she'll": "she will",
        "i'll": "i will",
        "we'll": "we will",
        "they'll": "they will",
        "you'll": "you will"
    }
    for contract, expand in contractions.items():
        s = s.replace(contract, expand)
    s = re.sub(r"[.?!,;:'`’]", "", s)
    return " ".join(s.split())

def select_random_quiz_question():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT verb, person, tense, affirmative_text, question_text, negative_text FROM conjugations")
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        return None
        
    row = random.choice(rows)
    verb, person, tense, aff, quest, neg = row
    
    form = random.choice(["Affirmative", "Question", "Negative"])
    if form == "Affirmative":
        expected_full = aff
    elif form == "Question":
        expected_full = quest
    else:
        expected_full = neg
        
    subj_clean = person.replace(" (plural)", "").lower()
    normalized_full = normalize_string(expected_full)
    
    expected_verb = ""
    if form != "Question" and normalized_full.startswith(subj_clean):
        expected_verb = normalized_full[len(subj_clean):].strip()
        
    return {
        "verb": verb,
        "person": person,
        "tense": tense,
        "form": form,
        "expected_full": expected_full,
        "expected_verb": expected_verb
    }

def validate_conjugation_json(data, expected_tenses=None):
    if not isinstance(data, dict):
        return False
    if "tenses" not in data or not isinstance(data["tenses"], list):
        return False
    req_len = len(expected_tenses) if expected_tenses else 12
    if len(data["tenses"]) < req_len:
        return False
    required_fields = [
        "tense", 
        "affirmative_text", "affirmative_translation", 
        "question_text", "question_translation", 
        "negative_text", "negative_translation", 
        "example_text", "example_translation"
    ]
    for tense_data in data["tenses"]:
        for field in required_fields:
            if field not in tense_data or not tense_data[field]:
                return False
    return True

def validate_multiple_conjugations_json(data, persons, expected_tenses=None):
    if not isinstance(data, dict):
        return False
    if "results" not in data or not isinstance(data["results"], dict):
        return False
    for p in persons:
        if p not in data["results"]:
            return False
        single_person_data = {"tenses": data["results"][p]}
        if not validate_conjugation_json(single_person_data, expected_tenses):
            return False
    return True

def generate_multiple_conjugations_api(word, persons, study_type, target_tenses):
    current_key = get_api_key()
    if not current_key:
        raise ValueError("API_KEY_MISSING")
    genai.configure(api_key=current_key)
    
    tenses_str = ", ".join(target_tenses)
    
    # Customizar instruções com base no tipo de estudo
    if study_type == "Adjetivo (com 'to be')":
        adj = word.lower().replace("be ", "").strip()
        instruction = f"Sua tarefa é gerar a conjugação completa do adjetivo '{adj}' associado ao verbo 'to be' (expressão 'be {adj}') para as seguintes pessoas gramaticais: {', '.join(persons)} para os seguintes tempos verbais: {tenses_str}."
    elif study_type == "Verbo + Adjetivo":
        instruction = f"Sua tarefa é gerar a conjugação completa da expressão '{word}' para as seguintes pessoas gramaticais: {', '.join(persons)} para os seguintes tempos verbais: {tenses_str}."
    elif study_type == "Substantivo":
        instruction = f"Sua tarefa é escolher um verbo de ação muito comum e natural que combine com o substantivo '{word}' (ex: se for 'car', use 'drive a car') e gerar a conjugação completa dessa expressão para as seguintes pessoas gramaticais: {', '.join(persons)} para os seguintes tempos verbais: {tenses_str}."
    else:
        instruction = f"Sua tarefa é gerar a conjugação completa do verbo '{word}' para as seguintes pessoas gramaticais: {', '.join(persons)} para os seguintes tempos verbais: {tenses_str}."

    system_prompt = f"""
    Você é um especialista em gramática da língua inglesa.
    {instruction}
    
    Os tempos verbais obrigatórios a serem gerados são exatamente: {tenses_str}.
    
    Para cada pessoa listada e cada tempo verbal especificado, forneça:
    - Affirmative: Frase afirmativa
    - Affirmative Translation: Tradução da frase afirmativa
    - Question: Frase interrogativa
    - Question Translation: Tradução da pergunta
    - Negative: Frase negativa
    - Negative Translation: Tradução da negação
    - Example: Frase de exemplo curta
    - Example Translation: Tradução do exemplo
    
    INSTRUÇÕES IMPORTANTES:
    1. Use contrações naturais nas formas negativas (ex: "doesn't", "didn't").
    2. Traduções naturais em português do Brasil.
    3. Retorne a resposta ESTREITAMENTE no formato JSON estruturado a seguir, sem markdown ou explicações.
    4. No campo 'verb', indique a expressão verbal/conjugada completa utilizada (ex: 'be {word}', 'get {word}', 'drive a car', '{word}').
    
    Estrutura JSON esperada:
    {{
      "verb": "Expressão verbal completa utilizada",
      "results": {{
        "Pessoa1": [
          {{
            "tense": "Nome do tempo verbal (ex: Present Simple)",
            "affirmative_text": "...",
            "affirmative_translation": "...",
            "question_text": "...",
            "question_translation": "...",
            "negative_text": "...",
            "negative_translation": "...",
            "example_text": "...",
            "example_translation": "..."
          }},
          ...
        ]
      }}
    }}
    """
    
    user_prompt = f"Gere conjugações de '{word}' para as pessoas: {', '.join(persons)} usando o tipo '{study_type}' para os tempos verbais: {tenses_str}."
    
    model = genai.GenerativeModel(
        model_name='gemini-2.5-flash',
        system_instruction=system_prompt,
        generation_config={
            "response_mime_type": "application/json",
            "temperature": 0.15,
        }
    )
    
    response = model.generate_content(user_prompt)
    return response.text

def generate_conjugations_api(word, person, study_type, target_tenses):
    current_key = get_api_key()
    if not current_key:
        raise ValueError("API_KEY_MISSING")
    genai.configure(api_key=current_key)
    
    tenses_str = ", ".join(target_tenses)
    
    # Customizar instruções com base no tipo de estudo
    if study_type == "Adjetivo (com 'to be')":
        adj = word.lower().replace("be ", "").strip()
        instruction = f"Sua tarefa é gerar a conjugação completa do adjetivo '{adj}' associado ao verbo 'to be' (ou seja, a expressão 'be {adj}') para a pessoa gramatical '{person}' nos seguintes tempos verbais em inglês: {tenses_str}."
    elif study_type == "Verbo + Adjetivo":
        instruction = f"Sua tarefa é gerar a conjugação completa da expressão de verbo + adjetivo '{word}' para a pessoa gramatical '{person}' nos seguintes tempos verbais em inglês: {tenses_str}."
    elif study_type == "Substantivo":
        instruction = f"Sua tarefa é escolher um verbo de ação muito comum e natural que combine com o substantivo '{word}' (ex: se for 'car', use 'drive a car') e gerar a conjugação completa dessa expressão para a pessoa gramatical '{person}' nos seguintes tempos verbais em inglês: {tenses_str}."
    else:  # Verbo
        instruction = f"Sua tarefa é gerar a conjugação completa do verbo '{word}' para a pessoa gramatical '{person}' nos seguintes tempos verbais em inglês: {tenses_str}."

    system_prompt = f"""
    Você é um especialista em gramática da língua inglesa.
    {instruction}
    
    Os tempos verbais obrigatórios a serem gerados são exatamente: {tenses_str}.
    
    Para cada um dos tempos verbais fornecidos, você deve fornecer as seguintes 4 formas:
    - Affirmative: A frase afirmativa conjugada usando a pessoa "{person}".
    - Affirmative Translation: A tradução correspondente da frase afirmativa para o português.
    - Question: A frase na forma interrogativa correspondente.
    - Question Translation: A tradução correspondente da pergunta para o português.
    - Negative: A frase na forma negativa correspondente.
    - Negative Translation: A tradução correspondente da negação para o português.
    - Example: Uma frase de exemplo curta e natural em inglês usando essa conjugação.
    - Example Translation: A tradução correspondente do exemplo para o português.
    
    INSTRUÇÕES IMPORTANTES:
    1. A pessoa gramatical "{person}" deve ser o sujeito das conjugações.
    2. Use contrações naturais onde apropriado nas formas negativas (ex: "doesn't" em vez de "does not", "didn't" em vez de "did not"), mas mantenha a clareza.
    3. As traduções devem ser naturais em português do Brasil.
    4. Retorne a resposta ESTREITAMENTE no formato JSON estruturado a seguir, sem explicações extras, comentários ou tags markdown (como ```json).
    5. No campo 'verb' do JSON de retorno, indique a expressão verbal/conjugada completa que você utilizou (ex: 'be {word}', 'get {word}', 'drive a car', '{word}').
    
    Estrutura JSON esperada:
    {{
      "verb": "Expressão verbal completa utilizada (ex: se o tipo for adjetivo, retorne 'be happy')",
      "person": "{person}",
      "tenses": [
        {{
          "tense": "Nome do tempo verbal (ex: Present Simple)",
          "affirmative_text": "Frase afirmativa em inglês",
          "affirmative_translation": "Tradução da frase afirmativa em português",
          "question_text": "Frase interrogativa em inglês",
          "question_translation": "Tradução da frase interrogativa em português",
          "negative_text": "Frase negativa em inglês",
          "negative_translation": "Tradução da frase negativa em português",
          "example_text": "Frase de exemplo em inglês",
          "example_translation": "Tradução da frase de exemplo em português"
        }}
      ]
    }}
    """
    user_prompt = f"Gere a tabela de conjugação para '{word}' e a pessoa '{person}' usando o tipo '{study_type}' para os tempos verbais: {tenses_str}."
    
    model = genai.GenerativeModel(
        model_name='gemini-2.5-flash',
        system_instruction=system_prompt,
        generation_config={
            "response_mime_type": "application/json",
            "temperature": 0.15,
        }
    )
    
    response = model.generate_content(user_prompt)
    return response.text

# ------------------------------------------------------------------------------
# EXCEÇÕES PERSONALIZADAS E TRATAMENTO DE ERROS (RATE LIMIT 429)
# ------------------------------------------------------------------------------
def handle_api_error(e):
    """
    Formata e exibe erros da API do Gemini de maneira amigável e profissional.
    """
    error_msg = str(e)
    if "API_KEY_MISSING" in error_msg:
        st.markdown("""
        <div class="card-incorrect" style="background-color: #fffbeb; border-color: #fef3c7; border-left-color: #d97706; color: #b45309;">
            <h4 style="margin:0; font-family:'Outfit';">\U0001f511 API Key do Gemini Não Detectada</h4>
            <p style="margin-top:0.5rem; margin-bottom:0.5rem;">
                Não conseguimos detectar nenhuma chave de API válida nas configurações do seu sistema ou do seu projeto.
            </p>
            <p style="margin:0; font-size: 0.9rem; font-weight: 600;">
                \U0001f449 Por favor, insira sua API Key no campo "API Key do Gemini" no menu lateral para liberar as consultas!
            </p>
        </div>
        """, unsafe_allow_html=True)
    elif "429" in error_msg or "quota" in error_msg.lower() or "limit" in error_msg.lower():
        st.markdown("""
        <div class="card-incorrect" style="background-color: #fffbeb; border-color: #fef3c7; border-left-color: #d97706; color: #b45309;">
            <h4 style="margin:0; font-family:'Outfit';">\u26a0\ufe0f Limite de Requisições da API Excedido</h4>
            <p style="margin-top:0.5rem; margin-bottom:0.5rem;">
                Você atingiu o limite de cota da versão gratuita do Gemini (geralmente limitado a 15 requisições por minuto).
            </p>
            <p style="margin:0; font-size: 0.9rem; font-weight: 600;">
                \u23f1\ufe0f Por favor, aguarde cerca de 30 a 60 segundos antes de tentar novamente para que o Google libere seu acesso!
            </p>
        </div>
        """, unsafe_allow_html=True)
    elif "404" in error_msg:
        st.error("\U0001f4a5 Erro 404: O modelo especificado não foi encontrado nos servidores da API do Gemini.")
    else:
        st.error(f"\U0001f4a5 Ocorreu um erro inesperado na requisição: {error_msg}")

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
    ["📝 Praticar Escrita & Dúvidas", "⚡ Gerador de Frases Rígido", "📊 Estudo de Verbos"]
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
elif active_page == "⚡ Gerador de Frases Rígido":
    st.sidebar.markdown("""
    ### 💡 Como Usar:
    1. Digite suas palavras em **inglês** (substantivos, adjetivos, verbos) separadas por espaço ou vírgula.
    2. Clique em **⚡ Gerar Frases**.
    3. O Gemini criará de 3 a 5 frases em inglês utilizando estritamente os seus termos.
    4. Clique no botão de revelação para ver a tradução em português de cada frase!
    """)
else:
    st.sidebar.markdown("""
    ### 💡 Como Usar:
    1. Digite o verbo em **inglês** no campo principal (ex: *speak*, *run*, *write*).
    2. Selecione a **pessoa gramatical** (sujeito) na lista suspensa.
    3. Clique em **Gerar / Buscar Conjugações** para ver os 12 tempos verbais estruturados.
    4. Use o **Modo Estudo** para ocultar as conjugações e testar sua memória.
    5. Jogue no **Quiz de Conjugação** para exercitar o preenchimento de lacunas e ver sua pontuação!
    """)
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📊 Histórico de Verbos")
    search_query = st.sidebar.text_input("Buscar no histórico:", key="history_search_query")
    sort_option = st.sidebar.selectbox("Ordenar por:", ["Mais recentes", "Ordem alfabética"], key="history_sort_option")
    
    sort_by = "recent" if sort_option == "Mais recentes" else "alphabetical"
    history_verbs = get_history(search_query=search_query, sort_by=sort_by)
    
    if history_verbs:
        st.sidebar.markdown("<div style='margin-bottom: 0.5rem; font-size: 0.9rem; color: #6b7280;'>Clique em um verbo para carregar:</div>", unsafe_allow_html=True)
        for v in history_verbs:
            if st.sidebar.button(v.capitalize(), key=f"hist_btn_{v}", use_container_width=True):
                st.session_state.selected_verb = v
                st.session_state.verb_input_widget = v
                st.session_state.should_generate = True
                st.rerun()
    else:
        st.sidebar.info("Nenhum verbo estudado ainda.")

    # Controle da API Key no menu lateral
    api_key_detected = get_api_key()
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🔑 API Key do Gemini")
    
    if not api_key_detected:
        st.sidebar.warning("⚠️ Nenhuma chave detectada!")
        user_key = st.sidebar.text_input("Insira sua Gemini API Key:", type="password", key="sidebar_key_input")
        if user_key:
            st.session_state.api_key_override = user_key
            st.rerun()
    else:
        if "api_key_override" in st.session_state and st.session_state.api_key_override:
            st.sidebar.success("🔑 Chave inserida manualmente")
            if st.sidebar.button("🗑️ Remover chave manual"):
                st.session_state.api_key_override = ""
                st.rerun()
        else:
            st.sidebar.success("🔑 Chave detectada automaticamente")

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
    current_key = get_api_key()
    if not current_key:
        raise ValueError("API_KEY_MISSING")
    genai.configure(api_key=current_key)
    
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
    current_key = get_api_key()
    if not current_key:
        raise ValueError("API_KEY_MISSING")
    genai.configure(api_key=current_key)
    
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
elif active_page == "⚡ Gerador de Frases Rígido":
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

# ------------------------------------------------------------------------------
# INTERFACE PRINCIPAL - PÁGINA 3: ESTUDO DE VERBOS
# ------------------------------------------------------------------------------
else:
    st.markdown('<div class="header-container"><h1>Estudo de Verbos</h1></div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Estude e pratique a conjugação de verbos em inglês em todos os 12 tempos verbais com auxílio do Gemini</div>', unsafe_allow_html=True)
    
    # Inicialização de variáveis de sessão
    if 'selected_verb' not in st.session_state:
        st.session_state.selected_verb = ""
    if 'should_generate' not in st.session_state:
        st.session_state.should_generate = False
    if 'active_conjugations' not in st.session_state:
        st.session_state.active_conjugations = None
    if 'active_verb' not in st.session_state:
        st.session_state.active_verb = ""
    if 'active_person' not in st.session_state:
        st.session_state.active_person = ""
    if 'study_type' not in st.session_state:
        st.session_state.study_type = "Verbo"
    if 'ai_word_suggestions' not in st.session_state:
        st.session_state.ai_word_suggestions = None
        
    # Inicialização do Quiz no session_state
    if 'quiz_score' not in st.session_state:
        st.session_state.quiz_score = 0
    if 'quiz_total' not in st.session_state:
        st.session_state.quiz_total = 0
    if 'quiz_current' not in st.session_state:
        st.session_state.quiz_current = select_random_quiz_question()
    if 'quiz_answered' not in st.session_state:
        st.session_state.quiz_answered = False
    if 'quiz_feedback' not in st.session_state:
        st.session_state.quiz_feedback = None
    if 'quiz_user_input' not in st.session_state:
        st.session_state.quiz_user_input = ""

    # Abas principais
    tab_tables, tab_quiz = st.tabs(["📚 Tabelas de Conjugação", "🎮 Quiz de Conjugação"])
    
    with tab_tables:
        # 1. Definição dos callbacks que rodam ANTES da renderização
        def callback_translate_word():
            pt_val = st.session_state.get("pt_word_input", "").strip()
            if pt_val:
                try:
                    current_key = get_api_key()
                    if not current_key:
                        st.session_state.translate_error = "⚠️ Insira sua Gemini API Key na barra lateral primeiro para habilitar a tradução!"
                    else:
                        import google.generativeai as genai
                        genai.configure(api_key=current_key)
                        
                        prompt = f"""
                        Analise a palavra ou expressão em português '{pt_val}'.
                        1. Traduza-a para o inglês.
                        2. Identifique o tipo gramatical correspondente:
                           - Se for um verbo, use 'Verbo'.
                           - Se for um adjetivo, use 'Adjetivo (com 'to be')'.
                           - Se for um substantivo, use 'Substantivo'.
                        3. Se for um adjetivo ou substantivo, forneça uma tradução direta no infinitivo/singular (ex: 'feliz' -> 'happy', 'carro' -> 'car').
                        
                        Retorne a resposta ESTREITAMENTE no formato JSON a seguir, sem explicações extras ou markdown:
                        {{
                          "translation": "Tradução em inglês (minúscula, ex: 'run', 'happy' ou 'car')",
                          "type": "Um dos valores: 'Verbo', 'Adjetivo (com 'to be')', ou 'Substantivo'",
                          "explanation": "Explicação curta em português (ex: 'correr é um verbo que se traduz como run')"
                        }}
                        """
                        
                        model = genai.GenerativeModel('gemini-2.5-flash', generation_config={"response_mime_type": "application/json"})
                        response = model.generate_content(prompt)
                        res_data = json.loads(response.text.strip())
                        
                        en_word = res_data["translation"].strip().lower()
                        word_type = res_data["type"]
                        explanation = res_data.get("explanation", "")
                        
                        st.session_state.selected_verb = en_word
                        st.session_state.verb_input_widget = en_word
                        st.session_state.study_type = word_type
                        st.session_state.study_type_select = word_type
                        st.session_state.translate_success = f"🎉 Traduzido! '{pt_val}' em inglês é '{en_word}' ({word_type}). {explanation}"
                except Exception as e:
                    st.session_state.translate_error = f"Erro na tradução: {e}"

        def callback_select_common_verb():
            val = st.session_state.get("common_verbs_select", "-- Selecione --")
            if val and val != "-- Selecione --":
                st.session_state.selected_verb = val
                st.session_state.verb_input_widget = val
                st.session_state.study_type = "Verbo"
                st.session_state.study_type_select = "Verbo"

        def callback_select_common_adjective():
            val = st.session_state.get("common_adjectives_select", "-- Selecione --")
            if val and val != "-- Selecione --":
                st.session_state.selected_verb = val
                st.session_state.verb_input_widget = val
                st.session_state.study_type = "Adjetivo (com 'to be')"
                st.session_state.study_type_select = "Adjetivo (com 'to be')"

        def callback_select_common_noun():
            val = st.session_state.get("common_nouns_select", "-- Selecione --")
            if val and val != "-- Selecione --":
                st.session_state.selected_verb = val
                st.session_state.verb_input_widget = val
                st.session_state.study_type = "Substantivo"
                st.session_state.study_type_select = "Substantivo"

        # 2. Exibição de alertas persistidos de reruns
        if "translate_success" in st.session_state and st.session_state.translate_success:
            st.success(st.session_state.translate_success)
            st.session_state.translate_success = None
        if "translate_error" in st.session_state and st.session_state.translate_error:
            st.error(st.session_state.translate_error)
            st.session_state.translate_error = None
            
        col_word, col_type, col_person = st.columns([2, 1, 1])
        
        with col_word:
            if "selected_verb" not in st.session_state:
                st.session_state.selected_verb = ""
                
            # Sincroniza o valor digitado de forma a evitar StreamlitStateError
            def sync_selected_verb():
                st.session_state.selected_verb = st.session_state.verb_input_widget
                
            verb = st.text_input(
                "Digite a palavra/frase em inglês:",
                value=st.session_state.selected_verb,
                placeholder="Ex: speak, happy, get tired, car",
                key="verb_input_widget",
                on_change=sync_selected_verb,
                help="Digite um verbo, adjetivo, expressão (verbo+adjetivo) ou substantivo em inglês."
            )

        with col_type:
            def sync_study_type():
                st.session_state.study_type = st.session_state.study_type_select

            study_types_list = ["Verbo", "Adjetivo (com 'to be')", "Verbo + Adjetivo", "Substantivo"]
            try:
                type_index = study_types_list.index(st.session_state.study_type)
            except ValueError:
                type_index = 0

            study_type = st.selectbox(
                "Tipo de Estudo:",
                study_types_list,
                index=type_index,
                key="study_type_select",
                on_change=sync_study_type,
                help="Escolha o tipo de treino desejado para o termo fornecido."
            )
            
        with col_person:
            person = st.selectbox(
                "Escolha a pessoa gramatical:",
                ["Todas as pessoas", "I", "You", "He", "She", "It", "We", "You (plural)", "They"],
                index=3, # Default para "He"
                key="person_select_field"
            )

        col_tense, col_forms = st.columns([1, 1])

        with col_tense:
            tense_types_list = [
                "Todos", "Present Simple", "Present Continuous", "Present Perfect", "Present Perfect Continuous",
                "Past Simple", "Past Continuous", "Past Perfect", "Past Perfect Continuous",
                "Future Simple", "Future Continuous", "Future Perfect", "Future Perfect Continuous"
            ]
            tense_selected = st.selectbox(
                "Tempo Verbal:",
                tense_types_list,
                index=0,
                key="tense_select_field",
                help="Escolha se deseja gerar/ver todos os tempos verbais ou apenas um tempo específico."
            )

        with col_forms:
            forms_selected = st.multiselect(
                "Formas a exibir:",
                options=["Afirmativa", "Negativa", "Pergunta", "Exemplo"],
                default=["Afirmativa", "Negativa", "Pergunta", "Exemplo"],
                key="forms_display_select",
                help="Selecione quais formas (afirmativa, negativa, pergunta, exemplo) deseja exibir."
            )
            
        study_mode = st.checkbox("📖 Modo Estudo (ocultar respostas para testes rápidos)", key="study_mode")
        
        # Auxiliares para ajudar o usuário a escolher/traduzir verbos
        col_help1, col_help2 = st.columns(2)
        with col_help1:
            with st.expander("🔍 Traduzir do Português"):
                st.text_input("Palavra em português (ex: falar, feliz, carro):", key="pt_word_input")
                # Botão usando callback on_click!
                st.button("Traduzir para Inglês 🔄", use_container_width=True, on_click=callback_translate_word)
                            
        with col_help2:
            tab_static, tab_ai = st.tabs(["📚 Listas Estáticas", "🧠 Buscar na IA"])
            with tab_static:
                word_category = st.radio("Categoria:", ["Verbos", "Adjetivos", "Substantivos"], horizontal=True, key="common_words_category")
                if word_category == "Verbos":
                    common_verbs = [
                        "be", "have", "do", "say", "go", "get", "make", "know", "think", "take",
                        "see", "come", "want", "use", "find", "give", "tell", "work", "call", "try",
                        "ask", "need", "feel", "leave", "put", "mean", "keep", "let", "begin", "seem",
                        "help", "talk", "turn", "start", "show", "hear", "play", "run", "move", "like"
                    ]
                    st.selectbox(
                        "Escolha um verbo comum:", 
                        ["-- Selecione --"] + common_verbs, 
                        key="common_verbs_select",
                        on_change=callback_select_common_verb
                    )
                elif word_category == "Adjetivos":
                    common_adjectives = [
                        "happy", "sad", "tired", "busy", "hungry", "angry", "excited", "bored",
                        "scared", "sick", "late", "ready", "smart", "strong", "weak", "cold",
                        "hot", "proud", "worried", "nervous"
                    ]
                    st.selectbox(
                        "Escolha um adjetivo comum:", 
                        ["-- Selecione --"] + common_adjectives, 
                        key="common_adjectives_select",
                        on_change=callback_select_common_adjective
                    )
                else:
                    common_nouns = [
                        "car", "book", "house", "friend", "job", "dog", "city", "money",
                        "time", "family", "class", "game", "song", "movie", "water", "food",
                        "computer", "phone", "coffee", "tea"
                    ]
                    st.selectbox(
                        "Escolha um substantivo comum:", 
                        ["-- Selecione --"] + common_nouns, 
                        key="common_nouns_select",
                        on_change=callback_select_common_noun
                    )
            with tab_ai:
                pt_search = st.text_input("Buscar exemplos na IA (ex: adjetivos de sentimentos, feliz, comer):", key="pt_word_finder_input")
                search_clicked = st.button("Buscar Exemplos 🧠🔍", use_container_width=True)
                
                if search_clicked and pt_search.strip():
                    with st.spinner("🧠 O Gemini está gerando sugestões de palavras..."):
                        try:
                            current_key = get_api_key()
                            if not current_key:
                                st.error("⚠️ Insira sua Gemini API Key na barra lateral primeiro!")
                            else:
                                import google.generativeai as genai
                                genai.configure(api_key=current_key)
                                prompt = f"""
                                Com base na busca em português '{pt_search}', sugira uma lista de até 10 palavras ou expressões curtas em inglês ideais para treino de vocabulário e gramática.
                                Identifique a categoria correta para cada uma: 'Verbo', 'Adjetivo (com 'to be')', ou 'Substantivo'.
                                
                                Retorne a resposta ESTREITAMENTE no formato JSON a seguir, sem markdown ou explicações:
                                {{
                                  "results": [
                                    {{
                                      "english": "palavra em inglês (ex: 'happy', 'run', 'car')",
                                      "portuguese": "tradução em português (ex: 'feliz', 'correr', 'carro')",
                                      "type": "Um dos valores exatos: 'Verbo', 'Adjetivo (com 'to be')', ou 'Substantivo'"
                                    }}
                                  ]
                                }}
                                """
                                model = genai.GenerativeModel('gemini-2.5-flash', generation_config={"response_mime_type": "application/json"})
                                response = model.generate_content(prompt)
                                suggestions_data = json.loads(response.text.strip())
                                st.session_state.ai_word_suggestions = suggestions_data.get("results", [])
                        except Exception as e:
                            st.error(f"Erro na busca: {e}")
                            
                if "ai_word_suggestions" in st.session_state and st.session_state.ai_word_suggestions:
                    st.markdown("<div style='font-size:0.85rem; color:#6b7280; margin-bottom:0.5rem;'>Clique em uma palavra para carregar no estudo:</div>", unsafe_allow_html=True)
                    for idx, item in enumerate(st.session_state.ai_word_suggestions):
                        en_word = item["english"]
                        pt_word = item["portuguese"]
                        w_type = item["type"]
                        btn_label = f"💡 {en_word} ({pt_word}) - {w_type}"
                        
                        def select_ai_word(word=en_word, study_type=w_type):
                            st.session_state.selected_verb = word
                            st.session_state.verb_input_widget = word
                            st.session_state.study_type = study_type
                            st.session_state.study_type_select = study_type
                            
                        st.button(btn_label, key=f"ai_sug_{idx}_{en_word}", use_container_width=True, on_click=select_ai_word)
                    
        generate_clicked = st.button("📊 Gerar / Buscar Conjugações", use_container_width=True)
        
        # Dispara busca/geração se clicou no botão ou no histórico da sidebar
        if generate_clicked or st.session_state.should_generate:
            st.session_state.should_generate = False # consome a flag
            
            if not verb or verb.strip() == "":
                st.warning("⚠️ Por favor, digite um termo válido.")
            else:
                verb_clean = verb.lower().strip()
                
                # Definir tempos verbais a buscar
                tenses_list_all = [
                    "Present Simple", "Present Continuous", "Present Perfect", "Present Perfect Continuous",
                    "Past Simple", "Past Continuous", "Past Perfect", "Past Perfect Continuous",
                    "Future Simple", "Future Continuous", "Future Perfect", "Future Perfect Continuous"
                ]
                if st.session_state.get("tense_select_field", "Todos") == "Todos":
                    target_tenses = tenses_list_all
                else:
                    target_tenses = [st.session_state.tense_select_field]
                
                with st.spinner(f"🧠 Buscando conjugações de '{verb_clean}' para '{person}'..."):
                    try:
                        # 1. Tentar resolver a palavra na chave de cache correspondente
                        resolved_verb = resolve_cached_verb(verb_clean, st.session_state.study_type)
                        tenses_data = {}
                        
                        # Definir lista de pessoas a buscar
                        if person == "Todas as pessoas":
                            target_persons = ["I", "You", "He", "She", "It", "We", "You (plural)", "They"]
                        else:
                            target_persons = [person]
                            
                        # Verificar cache para cada pessoa e cada tempo verbal
                        missing_persons = []
                        if resolved_verb:
                            for p in target_persons:
                                p_cached = get_cached_conjugations_for_tenses(resolved_verb, p, target_tenses)
                                if p_cached:
                                    tenses_data[p] = p_cached
                                else:
                                    missing_persons.append(p)
                            verb_clean = resolved_verb
                        else:
                            missing_persons = list(target_persons)
                            
                        # Se houver pessoas faltando no cache, buscar do Gemini
                        if missing_persons:
                            if len(missing_persons) == 1:
                                # Apenas 1 pessoa: usar API simples existente
                                single_p = missing_persons[0]
                                raw_response = generate_conjugations_api(verb_clean, single_p, st.session_state.study_type, target_tenses)
                                response_data = json.loads(raw_response)
                                
                                if validate_conjugation_json(response_data, target_tenses):
                                    resolved_verb_from_api = response_data.get("verb", verb_clean).lower().strip()
                                    save_conjugations(resolved_verb_from_api, single_p, response_data["tenses"])
                                    
                                    # Para preencher tenses_data, buscamos novamente do banco (para garantir que inclua tenses antigas que já estavam no cache)
                                    cached_all_target = get_cached_conjugations_for_tenses(resolved_verb_from_api, single_p, target_tenses)
                                    if cached_all_target:
                                        tenses_data[single_p] = cached_all_target
                                    else:
                                        tenses_data[single_p] = response_data["tenses"]
                                    verb_clean = resolved_verb_from_api
                                else:
                                    st.error(f"❌ O Gemini retornou uma resposta inválida para a pessoa '{single_p}'.")
                            else:
                                # Múltiplas pessoas: usar a nova API em lote
                                raw_response = generate_multiple_conjugations_api(verb_clean, missing_persons, st.session_state.study_type, target_tenses)
                                response_data = json.loads(raw_response)
                                
                                if validate_multiple_conjugations_json(response_data, missing_persons, target_tenses):
                                    resolved_verb_from_api = response_data.get("verb", verb_clean).lower().strip()
                                    for p in missing_persons:
                                        p_tenses = response_data["results"][p]
                                        save_conjugations(resolved_verb_from_api, p, p_tenses)
                                        
                                        cached_all_target = get_cached_conjugations_for_tenses(resolved_verb_from_api, p, target_tenses)
                                        if cached_all_target:
                                            tenses_data[p] = cached_all_target
                                        else:
                                            tenses_data[p] = p_tenses
                                    verb_clean = resolved_verb_from_api
                                else:
                                    st.error("❌ O Gemini retornou uma resposta inválida para o lote de pessoas.")
                                    
                        # Atualizar dados ativos na sessão se conseguimos carregar todas as pessoas requisitadas
                        if len(tenses_data) == len(target_persons):
                            # Salva o termo final no histórico
                            save_to_history(verb_clean)
                            
                            # Atualiza dados ativos na sessão
                            st.session_state.active_conjugations = tenses_data
                            st.session_state.active_verb = verb_clean
                            st.session_state.active_person = person
                            
                            # Atualiza o quiz caso estivesse sem perguntas
                            if st.session_state.quiz_current is None:
                                st.session_state.quiz_current = select_random_quiz_question()
                            
                    except Exception as e:
                        handle_api_error(e)
                        
        # Renderiza a tabela de conjugações se houver dados ativos
        if st.session_state.active_conjugations:
            active_v = st.session_state.active_verb
            active_p = st.session_state.active_person
            active_conjs = st.session_state.active_conjugations
            
            st.markdown("---")
            
            def render_conjugation_tenses(active_v, active_p, tenses, study_mode):
                # Obter formas selecionadas para exibição
                forms_sel = st.session_state.get("forms_display_select", ["Afirmativa", "Negativa", "Pergunta", "Exemplo"])
                if not forms_sel:
                    forms_sel = ["Afirmativa", "Negativa", "Pergunta", "Exemplo"]
                    
                show_aff = "Afirmativa" in forms_sel
                show_neg = "Negativa" in forms_sel
                show_ques = "Pergunta" in forms_sel
                show_ex = "Exemplo" in forms_sel

                for tense_data in tenses:
                    tense_name = tense_data["tense"]
                    reveal_key = f"reveal_{active_v}_{active_p}_{tense_name}"
                    if reveal_key not in st.session_state:
                        st.session_state[reveal_key] = False
                        
                    with st.expander(f"📌 {tense_name}"):
                        if study_mode and not st.session_state[reveal_key]:
                            st.markdown("<div style='text-align: center; padding: 0.5rem;'>", unsafe_allow_html=True)
                            st.write("🙈 *Conteúdo ocultado pelo Modo Estudo.*")
                            if st.button("👁️ Mostrar resposta", key=f"btn_reveal_{tense_name}_{active_v}_{active_p}", use_container_width=True):
                                st.session_state[reveal_key] = True
                                st.rerun()
                            st.markdown("</div>", unsafe_allow_html=True)
                        else:
                            if study_mode:
                                if st.button("🙈 Ocultar resposta", key=f"btn_hide_{tense_name}_{active_v}_{active_p}", use_container_width=True):
                                    st.session_state[reveal_key] = False
                                    st.rerun()
                                    
                            # Montar lista de cartões ativos a exibir
                            active_cards = []
                            if show_aff:
                                active_cards.append({
                                    "key": "affirmative",
                                    "title": "🟢 Afirmativa",
                                    "text": tense_data["affirmative_text"],
                                    "translation": tense_data["affirmative_translation"]
                                })
                            if show_neg:
                                active_cards.append({
                                    "key": "negative",
                                    "title": "🔴 Negativa",
                                    "text": tense_data["negative_text"],
                                    "translation": tense_data["negative_translation"]
                                })
                            if show_ques:
                                active_cards.append({
                                    "key": "question",
                                    "title": "❓ Pergunta",
                                    "text": tense_data["question_text"],
                                    "translation": tense_data["question_translation"]
                                })
                            if show_ex:
                                active_cards.append({
                                    "key": "example",
                                    "title": "💡 Exemplo",
                                    "text": tense_data["example_text"],
                                    "translation": tense_data["example_translation"]
                                })

                            if not active_cards:
                                st.warning("⚠️ Nenhuma forma selecionada para exibição.")
                            else:
                                if len(active_cards) == 1:
                                    cols = [st]
                                else:
                                    cols = st.columns(2)
                                
                                for idx, card in enumerate(active_cards):
                                    col_to_use = cols[idx % len(cols)]
                                    with col_to_use:
                                        st.markdown(f"##### {card['title']}")
                                        st.markdown(f'<div class="card-conjugation">{card["text"]}</div>', unsafe_allow_html=True)
                                        
                                        toggle_key = f"toggle_{active_v}_{active_p}_{tense_name}_{card['key']}"
                                        if toggle_key not in st.session_state:
                                            st.session_state[toggle_key] = False
                                            
                                        btn_label = "🙈 Ocultar tradução" if st.session_state[toggle_key] else "👁️ Traduzir"
                                        if st.button(btn_label, key=f"btn_{toggle_key}", use_container_width=True):
                                            st.session_state[toggle_key] = not st.session_state[toggle_key]
                                            st.rerun()
                                            
                                        if st.session_state[toggle_key]:
                                            st.markdown(f"""
                                            <div style="background-color: #faf5ff; border: 1px dashed #c084fc; border-radius: 8px; padding: 0.6rem; margin-bottom: 1rem; color: #581c87; font-size: 0.95rem; font-weight: 500;">
                                                {card["translation"]}
                                            </div>
                                            """, unsafe_allow_html=True)
                                        else:
                                            st.markdown("<div style='margin-bottom: 1rem;'></div>", unsafe_allow_html=True)

            if active_p == "Todas as pessoas" and isinstance(active_conjs, dict):
                first_person = list(active_conjs.keys())[0]
                available_tenses = [t["tense"] for t in active_conjs[first_person]]
                
                st.markdown(f"### 📋 Conjugações de **{active_v.capitalize()}** (Todas as Pessoas)")
                
                for tense_name in available_tenses:
                    reveal_key = f"reveal_{active_v}_all_{tense_name}"
                    if reveal_key not in st.session_state:
                        st.session_state[reveal_key] = False
                        
                    with st.expander(f"📌 {tense_name}"):
                        if study_mode and not st.session_state[reveal_key]:
                            st.markdown("<div style='text-align: center; padding: 0.5rem;'>", unsafe_allow_html=True)
                            st.write("🙈 *Conteúdo ocultado pelo Modo Estudo.*")
                            if st.button("👁️ Mostrar resposta", key=f"btn_reveal_all_{tense_name}_{active_v}", use_container_width=True):
                                st.session_state[reveal_key] = True
                                st.rerun()
                            st.markdown("</div>", unsafe_allow_html=True)
                        else:
                            if study_mode:
                                if st.button("🙈 Ocultar resposta", key=f"btn_hide_all_{tense_name}_{active_v}", use_container_width=True):
                                    st.session_state[reveal_key] = False
                                    st.rerun()
                                    
                            show_translations = st.checkbox("👁️ Mostrar Traduções na Tabela", key=f"trans_chk_{active_v}_{tense_name}", value=True)
                            
                            # Obter formas selecionadas para exibição na tabela
                            forms_sel = st.session_state.get("forms_display_select", ["Afirmativa", "Negativa", "Pergunta", "Exemplo"])
                            if not forms_sel:
                                forms_sel = ["Afirmativa", "Negativa", "Pergunta", "Exemplo"]
                                
                            show_aff = "Afirmativa" in forms_sel
                            show_neg = "Negativa" in forms_sel
                            show_ques = "Pergunta" in forms_sel
                            show_ex = "Exemplo" in forms_sel

                            # Cabeçalhos ativos
                            active_headers = ['<th style="padding: 10px; font-weight: 700; color: #475569;">Pessoa</th>']
                            if show_aff:
                                active_headers.append('<th style="padding: 10px; font-weight: 700; color: #15803d;">🟢 Afirmativa</th>')
                            if show_neg:
                                active_headers.append('<th style="padding: 10px; font-weight: 700; color: #b91c1c;">🔴 Negativa</th>')
                            if show_ques:
                                active_headers.append('<th style="padding: 10px; font-weight: 700; color: #1d4ed8;">❓ Pergunta</th>')
                            if show_ex:
                                active_headers.append('<th style="padding: 10px; font-weight: 700; color: #6d28d9;">💡 Exemplo</th>')

                            # Construir a tabela sem qualquer espaço ou tabulação no início das linhas
                            html_table = '<table style="width:100%; border-collapse: collapse; margin-top: 10px;">\n'
                            html_table += '<thead>\n'
                            html_table += '<tr style="background-color: #f1f5f9; border-bottom: 2px solid #e2e8f0; text-align: left;">\n'
                            for h in active_headers:
                                html_table += f'{h}\n'
                            html_table += '</tr>\n'
                            html_table += '</thead>\n'
                            html_table += '<tbody>\n'
                            
                            pronouns_list = ["I", "You", "He", "She", "It", "We", "You (plural)", "They"]
                            for p in pronouns_list:
                                if p in active_conjs:
                                    t_data = next((t for t in active_conjs[p] if t["tense"] == tense_name), None)
                                    if t_data:
                                        aff_txt = t_data["affirmative_text"]
                                        neg_txt = t_data["negative_text"]
                                        ques_txt = t_data["question_text"]
                                        ex_txt = t_data["example_text"]
                                        
                                        if show_translations:
                                            aff_txt += f'<br><span style="font-size:0.85rem; color:#64748b; font-style:italic;">{t_data["affirmative_translation"]}</span>'
                                            neg_txt += f'<br><span style="font-size:0.85rem; color:#64748b; font-style:italic;">{t_data["negative_translation"]}</span>'
                                            ques_txt += f'<br><span style="font-size:0.85rem; color:#64748b; font-style:italic;">{t_data["question_translation"]}</span>'
                                            ex_txt += f'<br><span style="font-size:0.85rem; color:#64748b; font-style:italic;">{t_data["example_translation"]}</span>'
                                            
                                        html_table += '<tr style="border-bottom: 1px solid #f1f5f9; vertical-align: top;">\n'
                                        html_table += f'<td style="padding: 10px; font-weight: 600; color: #475569;">{p}</td>\n'
                                        if show_aff:
                                            html_table += f'<td style="padding: 10px; color: #1e293b;">{aff_txt}</td>\n'
                                        if show_neg:
                                            html_table += f'<td style="padding: 10px; color: #1e293b;">{neg_txt}</td>\n'
                                        if show_ques:
                                            html_table += f'<td style="padding: 10px; color: #1e293b;">{ques_txt}</td>\n'
                                        if show_ex:
                                            html_table += f'<td style="padding: 10px; color: #1e293b;">{ex_txt}</td>\n'
                                        html_table += '</tr>\n'
                                        
                            html_table += '</tbody>\n'
                            html_table += '</table>\n'
                            st.markdown(html_table, unsafe_allow_html=True)
            else:
                st.markdown(f"### 📋 Conjugação de **{active_v.capitalize()}** para **{active_p}**")
                tenses = list(active_conjs.values())[0] if isinstance(active_conjs, dict) else active_conjs
                render_conjugation_tenses(active_v, active_p, tenses, study_mode)
                                
    with tab_quiz:
        if st.session_state.quiz_current is None:
            st.warning("⚠️ Histórico vazio. Por favor, gere pelo menos uma tabela de conjugação na aba ao lado para iniciar o Quiz.")
            if st.button("🔄 Tentar Carregar Quiz"):
                st.session_state.quiz_current = select_random_quiz_question()
                st.rerun()
        else:
            q = st.session_state.quiz_current
            
            st.markdown("### 🎮 Pratique no Quiz")
            st.write("Complete a conjugação com a forma correta do verbo de acordo com as especificações.")
            
            st.markdown(f"""
            <div style="background-color: #eff6ff; border: 1px solid #bfdbfe; border-radius: 10px; padding: 1rem; margin-bottom: 1.5rem;">
                <h4 style="margin: 0 0 0.5rem 0; font-family: 'Outfit'; color: #1e3a8a;">🎯 Desafio Atual:</h4>
                <p style="margin: 0; font-size: 1.05rem;">
                    <strong>Verbo:</strong> <span style="color: #3b82f6; font-weight: 700;">{q['verb'].upper()}</span> | 
                    <strong>Pessoa:</strong> <span style="font-weight: 600;">{q['person']}</span> | 
                    <strong>Tempo Verbal:</strong> <span style="font-weight: 600;">{q['tense']} ({q['form']})</span>
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            # Constrói o texto do prompt do input
            if q['form'] == 'Question':
                prompt_label = "Digite a pergunta completa em inglês:"
                placeholder = f"Ex: Does {q['person'].lower()}..."
            else:
                prompt_label = f"Complete a frase ({q['person']} ...):"
                placeholder = "Ex: speaks"
                
            with st.form(key="quiz_form"):
                user_input = st.text_input(
                    prompt_label, 
                    placeholder=placeholder, 
                    value=st.session_state.quiz_user_input, 
                    disabled=st.session_state.quiz_answered
                )
                submit_btn = st.form_submit_button(
                    "Confirmar Resposta" if not st.session_state.quiz_answered else "Respondido", 
                    disabled=st.session_state.quiz_answered
                )
                
            if submit_btn and not st.session_state.quiz_answered:
                if not user_input.strip():
                    st.warning("Por favor, digite uma resposta válida.")
                else:
                    st.session_state.quiz_user_input = user_input
                    
                    user_ans_norm = normalize_string(user_input)
                    expected_full_norm = normalize_string(q["expected_full"])
                    expected_verb_norm = normalize_string(q["expected_verb"]) if q["expected_verb"] else ""
                    
                    is_correct = (user_ans_norm == expected_full_norm) or (expected_verb_norm and user_ans_norm == expected_verb_norm)
                    
                    st.session_state.quiz_total += 1
                    if is_correct:
                        st.session_state.quiz_score += 1
                        st.session_state.quiz_feedback = {
                            "status": "correct",
                            "msg": f"🎉 **Parabéns! Resposta correta!**<br><br>Frase completa: <strong>\"{q['expected_full']}\"</strong>"
                        }
                    else:
                        st.session_state.quiz_feedback = {
                            "status": "incorrect",
                            "msg": f"❌ **Resposta incorreta.**<br><br>Sua resposta: <em>\"{user_input}\"</em><br><br>Resposta esperada: <strong>\"{q['expected_full']}\"</strong>" + (f" (ou apenas <strong>\"{q['expected_verb']}\"</strong>)" if q['expected_verb'] else "")
                        }
                    st.session_state.quiz_answered = True
                    st.rerun()
                    
            # Exibe o feedback após o usuário submeter a resposta
            if st.session_state.quiz_answered and st.session_state.quiz_feedback:
                fb = st.session_state.quiz_feedback
                if fb["status"] == "correct":
                    st.markdown(f'<div class="card-correct">{fb["msg"]}</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="card-incorrect">{fb["msg"]}</div>', unsafe_allow_html=True)
                    
                # Botão para avançar para a próxima pergunta
                if st.button("Próxima Pergunta ➡️", use_container_width=True):
                    st.session_state.quiz_current = select_random_quiz_question()
                    st.session_state.quiz_answered = False
                    st.session_state.quiz_feedback = None
                    st.session_state.quiz_user_input = ""
                    st.rerun()
                    
            # Exibe o placar do Quiz
            st.markdown(f"""
            <div style="background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px; padding: 0.75rem 1rem; margin-top: 1.5rem; display: flex; justify-content: space-between; align-items: center;">
                <span style="font-size: 1.1rem; font-weight: 600; color: #475569;">🏆 Placar Geral:</span>
                <span style="font-size: 1.25rem; font-weight: 700; color: #4f46e5;">{st.session_state.quiz_score} / {st.session_state.quiz_total}</span>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("Reiniciar Placar 🔄", use_container_width=True):
                st.session_state.quiz_score = 0
                st.session_state.quiz_total = 0
                st.session_state.quiz_current = select_random_quiz_question()
                st.session_state.quiz_answered = False
                st.session_state.quiz_feedback = None
                st.session_state.quiz_user_input = ""
                st.rerun()
