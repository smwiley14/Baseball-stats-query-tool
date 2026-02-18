# LangSmith Tracing Setup

LangSmith provides observability and tracing for your LangGraph agent. All LangChain/LangGraph operations are automatically traced when enabled.

## Setup

### 1. Get Your LangSmith API Key

1. Sign up at [https://smith.langchain.com](https://smith.langchain.com)
2. Go to Settings → API Keys
3. Create a new API key

### 2. Add to Environment Variables

Add to your `.env` file:

```bash
LANGCHAIN_API_KEY=your_langsmith_api_key_here
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=Baseball-Stats-Agent
```

### 3. Optional: Custom Project Name

You can set different project names for different environments:

```bash
# Development
LANGCHAIN_PROJECT=Baseball-Stats-Agent-Dev

# Production
LANGCHAIN_PROJECT=Baseball-Stats-Agent-Prod

# Testing
LANGCHAIN_PROJECT=Baseball-Stats-Agent-Test
```

## What Gets Traced

When enabled, LangSmith automatically traces:

- ✅ All LLM calls (OpenAI, etc.)
- ✅ All tool/function calls
- ✅ Graph node executions
- ✅ State transitions
- ✅ SQL query generation
- ✅ SQL execution results
- ✅ Vector store retrievals
- ✅ Agent executor steps

## Viewing Traces

1. Go to [https://smith.langchain.com](https://smith.langchain.com)
2. Navigate to "Traces" or "Projects"
3. Select your project name
4. View detailed execution traces with:
   - Inputs/outputs
   - Token usage
   - Latency
   - Errors
   - Full execution graph

## Disabling Tracing

To disable tracing temporarily:

```python
os.environ["LANGCHAIN_TRACING_V2"] = "false"
```

Or remove from `.env` file.

## Advanced: Custom Metadata

You can add custom metadata to traces:

```python
from langsmith import traceable

@traceable(name="custom_operation", tags=["custom"])
def my_function():
    # This will appear in LangSmith with custom tags
    pass
```

## Benefits

- **Debugging**: See exactly what your agent is doing at each step
- **Performance**: Identify bottlenecks and slow operations
- **Cost Tracking**: Monitor token usage and costs
- **Error Analysis**: Quickly find and fix issues
- **Iteration**: Compare different prompt versions and configurations
