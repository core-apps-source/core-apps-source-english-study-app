# English Study App

Streamlit app for English practice with AI support.

Current provider order:

1. Local cache
2. DEV_MODE mocks, when enabled
3. Groq as the primary AI provider
4. Gemini as fallback

## Local Setup

Install dependencies:

```bash
pip install -r requirements.txt
```

Create a local `.env` file from the example:

```bash
copy .env.example .env
```

Fill in your local keys:

```env
GEMINI_API_KEY=your_gemini_key
GROQ_API_KEY=your_groq_key
GROQ_MODEL=llama-3.1-8b-instant
REQUIRE_USER_API_KEY=false
DEV_MODE=false
```

Run:

```bash
streamlit run app.py
```

Open:

```text
http://localhost:8501
```

## Streamlit Cloud Secrets

Do not upload `.env` to GitHub. Configure secrets in Streamlit Cloud:

```toml
GEMINI_API_KEY = "your_gemini_key"
GROQ_API_KEY = "your_groq_key"
GROQ_MODEL = "llama-3.1-8b-instant"
REQUIRE_USER_API_KEY = false
DEV_MODE = false
```

Multiple keys are also supported:

```toml
GEMINI_API_KEYS = "gemini_key_1,gemini_key_2"
GROQ_API_KEYS = "groq_key_1,groq_key_2"
```

## Security Note

Even free API keys should not be committed to GitHub.

If a key is public, other people or automated bots can use it until the provider blocks it, exhausts the free quota, creates billing risk, or causes your account/project to be flagged. Keep real keys in `.env` locally and in Streamlit Secrets in production.

## Monitoring

The sidebar includes an administrative panel showing:

- real API calls in the current session;
- daily registered calls;
- cache hits;
- DEV_MODE responses;
- recent calls and errors.

## Rate Limits

Groq is configured as the primary provider because it is very fast for this use case. Gemini remains available as fallback when configured.

For best results:

- keep cache enabled;
- use DEV_MODE for UI tests;
- avoid regenerating large conjugation tables unnecessarily;
- keep Streamlit Cloud secrets updated after changing keys.
