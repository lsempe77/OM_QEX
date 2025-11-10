# Config Setup Instructions

## 🔒 Security Note

**IMPORTANT**: Your API key should NEVER be committed to Git!

## ✅ Setup Steps

1. **Copy the template**:
   ```powershell
   cd om_qex_extraction/config
   Copy-Item config.yaml.template config.yaml
   ```

2. **Add your API key**:
   - Open `config.yaml` in a text editor
   - Replace `YOUR_OPENROUTER_API_KEY_HERE` with your actual OpenRouter API key
   - The key should start with `sk-or-v1-`

3. **Verify .gitignore**:
   - The `.gitignore` file already excludes `config.yaml`
   - Your API key will NOT be pushed to GitHub ✅

## 📁 Files

- `config.yaml.template` - Template (safe to commit, no secrets)
- `config.yaml` - Your actual config (ignored by Git, contains API key)

## 🔑 Get Your OpenRouter API Key

If you don't have one:
1. Go to https://openrouter.ai/keys
2. Sign in or create an account
3. Create a new API key
4. Copy it to `config.yaml`

## ✅ Current Status

Your config.yaml already exists with your API key and is working!
Just make sure it stays out of Git (already configured in .gitignore).
