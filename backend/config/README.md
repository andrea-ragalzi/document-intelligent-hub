# Prompt Configuration Files

🔒 **SECURITY CRITICAL**: This directory contains prompt configuration files that are **git-ignored** to protect proprietary prompt engineering and prevent jailbreaking attacks.

## Setup Instructions

1. **Copy example files** to create your production prompts:
   ```bash
   cp rag_system_prompt.txt.example rag_system_prompt.txt
   cp classification_prompt.txt.example classification_prompt.txt
   cp query_reformulation_prompt.txt.example query_reformulation_prompt.txt
   ```

2. **Customize prompts** for your specific use case
   - Edit the `.txt` files directly (multi-line, no escaping needed)
   - Files are automatically loaded at startup
   - Changes require application restart

3. **Environment-specific prompts** (optional):
   - Set `RAG_SYSTEM_PROMPT_PATH=/path/to/prod_prompt.txt` in `.env`
   - Useful for A/B testing or different environments

## Files in This Directory

- `*.txt.example` - Template files (safe to commit, tracked in git)
- `*.txt` - **Active prompts** (git-ignored, contain secrets)
- `README.md` - This documentation file

## Why Files Instead of Environment Variables?

✅ **Advantages:**
- Clean, readable multi-line prompts (no escaping)
- Easy editing without env var syntax issues
- Version control friendly (`.example` files show structure)
- Same security (git-ignored like `.env`)

❌ **Don't commit:**
- Never commit `*.txt` files to git
- They contain proprietary prompt engineering
- Exposure enables jailbreaking attacks

## Deployment

### Local Development
- Prompts automatically load from `./config/*.txt`

### Docker
```dockerfile
COPY config/rag_system_prompt.txt /app/config/
```

### Railway / Cloud
- Upload files via dashboard secrets manager
- Or set `RAG_SYSTEM_PROMPT_PATH` to mounted volume path
