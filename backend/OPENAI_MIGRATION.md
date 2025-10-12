# OpenAI API Migration Guide

## ✅ Migration Complete

The Hospital BlockOps system has been successfully migrated from **Anthropic Claude** to **OpenAI GPT**.

---

## 🔄 Changes Made

### 1. **Environment Variables**
**Before:**
```bash
ANTHROPIC_API_KEY=your_anthropic_key
```

**After:**
```bash
OPENAI_API_KEY=your_openai_key
```

### 2. **Dependencies**
**Before:**
```txt
anthropic==0.7.8
```

**After:**
```txt
openai==1.3.0
```

### 3. **Default Model**
**Before:**
```python
model: str = "claude-3-5-sonnet-20241022"
```

**After:**
```python
model: str = "gpt-4-turbo-preview"
```

### 4. **API Call Structure**
**Before (Anthropic):**
```python
response = self.client.messages.create(
    model=self.model,
    max_tokens=max_tokens,
    temperature=temperature,
    messages=[{
        "role": "user",
        "content": prompt_template
    }]
)
response_text = response.content[0].text
```

**After (OpenAI):**
```python
response = self.client.chat.completions.create(
    model=self.model,
    max_tokens=max_tokens,
    temperature=temperature,
    messages=[{
        "role": "system",
        "content": "You are an AI agent in a hospital operations system. Respond with valid JSON only."
    }, {
        "role": "user",
        "content": prompt_template
    }],
    response_format={"type": "json_object"}
)
response_text = response.choices[0].message.content
```

---

## 🚀 Setup Instructions

### 1. **Get Your OpenAI API Key**
1. Go to https://platform.openai.com/api-keys
2. Sign in or create an account
3. Click "Create new secret key"
4. Copy the key (starts with `sk-`)

### 2. **Update Environment File**
```bash
cd hospital-blockops-demo/backend

# Copy example file if you haven't already
cp .env.example .env

# Edit .env and add your key
nano .env
```

Add this line:
```bash
OPENAI_API_KEY=sk-your-actual-key-here
```

### 3. **Reinstall Dependencies**
```bash
# If you have existing venv, remove it
rm -rf venv

# Create new virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate  # On macOS/Linux
# OR
venv\Scripts\activate     # On Windows

# Install dependencies
pip install -r requirements.txt
```

### 4. **Start the Server**
```bash
./start.sh
```

---

## 📊 Model Options

You can use any of these OpenAI models:

| Model | Description | Cost | Speed |
|-------|-------------|------|-------|
| `gpt-4-turbo-preview` | **Default** - Most capable, best for complex reasoning | $$$ | Medium |
| `gpt-4` | Stable GPT-4 version | $$$$ | Slower |
| `gpt-3.5-turbo` | Faster, cheaper, good for simple tasks | $ | Fast |
| `gpt-4o` | Multimodal, latest model | $$$ | Fast |

To change the model, edit each agent file or pass it during initialization:
```python
agent = SupplyChainAgent(model="gpt-3.5-turbo")
```

---

## 🔍 Key Differences

### Anthropic Claude vs OpenAI GPT

| Feature | Anthropic | OpenAI |
|---------|-----------|--------|
| **JSON Mode** | Manual parsing | Built-in `response_format={"type": "json_object"}` |
| **System Messages** | Not supported | Supported via `role: "system"` |
| **Temperature Range** | 0.0 - 1.0 | 0.0 - 2.0 |
| **Response Structure** | `response.content[0].text` | `response.choices[0].message.content` |
| **Error Handling** | Same (APIError, RateLimitError) | Same |

---

## ✅ Testing

Run the test suite to verify everything works:

```bash
cd backend
python3 test_agents.py
```

**Expected Output:**
```
✅ Test 1: Supply Chain Agent - PASSED
✅ Test 2: Financial Agent - PASSED
✅ Test 3: Facility Agent - PASSED
✅ All agent tests passed!
```

---

## 🧪 Testing Individual Agents

### Test Supply Chain Agent:
```python
from agents import SupplyChainAgent

agent = SupplyChainAgent(model="gpt-4-turbo-preview")
state = {"inventory_level": 150, "reorder_point": 200}
decision = agent.decide(state)
print(decision)
```

### Test with Different Models:
```python
# Fast and cheap
agent = SupplyChainAgent(model="gpt-3.5-turbo")

# Most capable
agent = SupplyChainAgent(model="gpt-4-turbo-preview")

# Latest
agent = SupplyChainAgent(model="gpt-4o")
```

---

## 💰 Cost Considerations

OpenAI pricing (as of 2024):

- **GPT-4 Turbo**: $0.01/1K input tokens, $0.03/1K output tokens
- **GPT-3.5 Turbo**: $0.0005/1K input tokens, $0.0015/1K output tokens

**Estimated cost per agent decision:**
- GPT-4 Turbo: ~$0.01 - $0.05 per decision
- GPT-3.5 Turbo: ~$0.001 - $0.005 per decision

For development/testing: Use GPT-3.5 Turbo
For production/demo: Use GPT-4 Turbo

---

## 🐛 Troubleshooting

### Error: "OPENAI_API_KEY not set"
**Solution:**
```bash
# Check if .env exists
cat backend/.env

# If missing, copy example and edit
cp backend/.env.example backend/.env
nano backend/.env
```

### Error: "Module 'openai' not found"
**Solution:**
```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
```

### Error: "Rate limit exceeded"
**Solution:**
- Wait a few seconds and retry
- The agent has automatic retry logic with exponential backoff
- Check your OpenAI account usage limits

### Error: "Invalid API key"
**Solution:**
- Verify your key starts with `sk-`
- Check for extra spaces in .env file
- Generate a new key at https://platform.openai.com/api-keys

---

## 📝 Files Modified

1. ✅ `backend/.env.example` - Updated environment variable name
2. ✅ `backend/requirements.txt` - Replaced anthropic with openai
3. ✅ `backend/agents/agent_base.py` - Updated API calls and imports

**No other files need modification** - all agents inherit from the base class!

---

## 🎯 Advantages of OpenAI Migration

1. **JSON Mode**: Native JSON response format (more reliable)
2. **System Messages**: Better instruction following
3. **Model Variety**: More model options (3.5, 4, 4-turbo, 4o)
4. **Cost Options**: Cheaper models available (GPT-3.5)
5. **Speed**: GPT-4 Turbo is faster than Claude Sonnet
6. **Multimodal**: GPT-4o supports images (future use)

---

## 📖 Additional Resources

- **OpenAI API Docs**: https://platform.openai.com/docs
- **Rate Limits**: https://platform.openai.com/account/rate-limits
- **Pricing**: https://openai.com/pricing
- **Best Practices**: https://platform.openai.com/docs/guides/production-best-practices

---

## ✨ What's Next?

Your system is now ready to use OpenAI! To start:

```bash
cd hospital-blockops-demo/backend
./start.sh
```

The agents will now use GPT-4 Turbo for all reasoning and decision-making! 🚀
