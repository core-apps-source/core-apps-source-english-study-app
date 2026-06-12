# Auditoria de consumo Gemini API

Projeto analisado: `C:\Users\PICHAU\Desktop\Projetos\Inglês`

Arquivo principal alterado: `app.py`

## Pontos de consumo encontrados no código original

Foram encontrados 6 pontos diretos de consumo Gemini:

1. `generate_multiple_conjugations_api(...)`
   - Uso original: `model.generate_content(user_prompt)`.
   - Finalidade: conjugações em lote.
   - Status: cacheado e monitorado via `gemini_generate(...)`.

2. `generate_conjugations_api(...)`
   - Uso original: `model.generate_content(user_prompt)`.
   - Finalidade: conjugações para uma pessoa gramatical.
   - Status: cacheado e monitorado via `gemini_generate(...)`.

3. `analyze_sentence(...)`
   - Uso original: `model.generate_content(user_prompt)`.
   - Finalidade: correção gramatical, tradução e dúvidas.
   - Status: cacheado e monitorado via `gemini_generate(...)`.

4. `generate_phrases_api(...)`
   - Uso original: `model.generate_content(user_prompt)`.
   - Finalidade: geração de frases.
   - Status: cacheado e monitorado via `gemini_generate(...)`.

5. `callback_translate_word()`
   - Uso original: import/configuração inline de `google.generativeai` + `generate_content(prompt)`.
   - Finalidade: tradução PT -> EN e classificação gramatical.
   - Status: cacheado e monitorado via `gemini_generate(...)`.

6. Busca de sugestões por IA
   - Uso original: import/configuração inline de `google.generativeai` + `generate_content(prompt)`.
   - Finalidade: sugestões de palavras.
   - Status: cacheado e monitorado via `gemini_generate(...)`.

## Implementado

- Wrapper central `gemini_generate(...)`.
- `DEV_MODE` por variável de ambiente `DEV_MODE=True` e por checkbox na sidebar.
- Bloqueio total de chamadas reais quando `DEV_MODE` está ativo.
- Respostas simuladas para testes ilimitados.
- Cache SQLite em `gemini_cache`.
- Histórico/logs em `gemini_call_logs`.
- Erros em `gemini_error_logs`.
- Contador de chamadas por sessão.
- Contador diário.
- Histórico de chamadas.
- Painel administrativo na sidebar.
- Retry automático para erro 429 com backoff.
- Registro de tempo de resposta e tokens quando `usage_metadata` estiver disponível.

## `st.rerun()` e risco de chamadas duplicadas

Os `st.rerun()` continuam existindo, mas os pontos que poderiam chamar Gemini passam agora por cache e/ou por flags consumidas.

Pontos de atenção:

- Histórico de verbos: define `should_generate=True`, depois faz rerun. A flag é consumida antes da geração.
- Conjugações: após salvar no banco, faz rerun para renderizar a UI. Como os dados ficam em `active_conjugations`, não há nova chamada sem clique/flag.
- Gerador de frases: rerun após regenerar. Agora a resposta entra no cache pelo prompt.
- Reveal/ocultar, quiz e limpeza: não chamam Gemini.

## Estimativa de redução

- DEV_MODE: 100% de redução de consumo real.
- Traduções repetidas: 70% a 95%.
- Sugestões repetidas: 50% a 90%.
- Correções iguais: 40% a 80%.
- Geração de frases com mesmo input: 60% a 95%.
- Conjugações: 80% a 98%.

Estimativa global em uso normal: 60% a 90% menos chamadas reais ao Gemini.

## Validação

- `python -m py_compile app.py`: OK.
- Streamlit iniciado em `http://localhost:8501`: OK.
- Varredura final: apenas um `generate_content(...)` permanece, dentro do wrapper central `gemini_generate(...)`.

## Diferença entre localhost e Streamlit Cloud

No `localhost`, normalmente só você usa a app e a cota da Gemini API é consumida pelo seu uso local.

No Streamlit Cloud, se a app estiver publicada com `GEMINI_API_KEY` em `st.secrets`, todos os visitantes usam a mesma chave da aplicação. Isso pode gerar erro 429/rate limit muito mais rápido.

Foi adicionado suporte a chave pessoal por sessão:

- A sidebar agora mostra "Usar minha própria API Key" mesmo quando existe uma chave global.
- A chave pessoal fica em `st.session_state.api_key_override` e tem prioridade sobre a chave da aplicação.
- Para app pública, configure no Streamlit Cloud Secrets:

```toml
REQUIRE_USER_API_KEY = true
```

Com isso, a app não usa a chave global e cada usuário precisa informar sua própria Gemini API Key na sidebar.

## Fallback Groq

Foi adicionada integração com Groq como fallback externo quando o Gemini estiver indisponível ou bloqueado por 429.

Configuração local no `.env`:

```env
GROQ_API_KEY=sua_groq_key
```

Configuração no Streamlit Cloud Secrets:

```toml
GROQ_API_KEY = "sua_groq_key"
GROQ_MODEL = "llama-3.1-8b-instant"
```

Também é possível configurar múltiplas chaves:

```toml
GROQ_API_KEYS = "groq_key_1,groq_key_2"
```

Fluxo atual:

1. Tenta cache local.
2. Se `DEV_MODE=True`, usa resposta simulada.
3. Tenta Gemini com uma ou mais chaves.
4. Se Gemini não tiver chave ou continuar em 429, tenta Groq.
5. Respostas reais do Groq também entram no cache.

O painel administrativo mostra `groq` no histórico da sessão quando a chamada vier do fallback.
