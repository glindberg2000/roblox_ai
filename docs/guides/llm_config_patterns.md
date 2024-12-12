# LLM Configuration Patterns Guide

## Basic Configuration Structure

### LLM Configuration Template
```python
LLM_CONFIGS = {
    "provider-name": {
        "model": "model-id",
        "model_endpoint_type": "provider",
        "model_endpoint": "https://api.provider.com/v1",
        "context_window": 100000,
    }
}
```

### Embedding Configuration Template
```python
EMBEDDING_CONFIGS = {
    "provider-name": {
        "embedding_endpoint_type": "provider",
        "embedding_endpoint": "https://api.provider.com/v1",
        "embedding_model": "embedding-model-id",
        "embedding_dim": 1536,
        "embedding_chunk_size": 300  # Optional
    }
}
```

## Common Configurations

### OpenAI Configuration
```python
"gpt4": {
    "model": "gpt-4",
    "model_endpoint_type": "openai",
    "model_endpoint": "https://api.openai.com/v1",
    "context_window": 128000,
}
```

### Anthropic Configuration
```python
"claude": {
    "model": "claude-3-haiku-20240307",
    "model_endpoint_type": "anthropic",
    "model_endpoint": "https://api.anthropic.com/v1",
    "context_window": 200000,
}
```

## VSCode/Cursor Snippets

Add these to your snippets configuration:

```json
{
    "LLM Config": {
        "prefix": "llmconfig",
        "body": [
            "LLM_CONFIGS = {",
            "    \"${1:provider}\": {",
            "        \"model\": \"${2:model-id}\",",
            "        \"model_endpoint_type\": \"${3:endpoint-type}\",",
            "        \"model_endpoint\": \"${4:https://api.provider.com/v1}\",",
            "        \"context_window\": ${5:100000},",
            "    }",
            "}"
        ],
        "description": "Create LLM configuration dictionary"
    },
    "Embedding Config": {
        "prefix": "embedconfig",
        "body": [
            "EMBEDDING_CONFIGS = {",
            "    \"${1:provider}\": {",
            "        \"embedding_endpoint_type\": \"${2:endpoint-type}\",",
            "        \"embedding_endpoint\": \"${3:https://api.provider.com/v1}\",",
            "        \"embedding_model\": \"${4:model-id}\",",
            "        \"embedding_dim\": ${5:1536},",
            "        \"embedding_chunk_size\": ${6:300}",
            "    }",
            "}"
        ],
        "description": "Create embedding configuration dictionary"
    }
}
```

## How to Use Snippets

1. In VSCode/Cursor:
   - Windows/Linux: File > Preferences > User Snippets
   - Mac: Code > Preferences > User Snippets
2. Select Python
3. Add the above JSON
4. Use by typing:
   - `llmconfig` + Tab for LLM configuration
   - `embedconfig` + Tab for embedding configuration

## Best Practices

1. **Endpoint Management**
   - Keep base URLs consistent within providers
   - Don't include specific endpoints (like /messages) in base URLs

2. **Default Selection**
   ```python
   DEFAULT_LLM = "provider-name"
   DEFAULT_EMBEDDING = "provider-name"
   ```

3. **Configuration Validation**
   ```python
   def validate_config(config: dict) -> bool:
       required_fields = ["model", "model_endpoint_type", "model_endpoint"]
       return all(field in config for field in required_fields)
   ```

## Common Provider Settings

| Provider  | Context Window | Embedding Dim | Base URL |
|-----------|---------------|---------------|----------|
| OpenAI    | 128000        | 1536          | api.openai.com/v1 |
| Anthropic | 200000        | 1536          | api.anthropic.com/v1 |
| Mixtral   | 32000         | 4096          | localhost:11434 | 