# Testing Your LangGraph Agent

## Quick Start

### 1. Simple Test (Single Query)

```bash
cd backend/agent
python test_agent.py --query "How many players are in the database?"
```

### 2. Interactive Mode

Run the agent in interactive mode to test multiple queries:

```bash
python test_agent.py --interactive
# or
python test_agent.py -i
```

### 3. Run Test Suite

Test multiple queries at once:

```bash
python test_agent.py --suite
```

### 4. Default Test

If no arguments provided, runs a default test:

```bash
python test_agent.py
```

## Prerequisites

Make sure you have:

1. **Environment variables set** in `.env`:
   - `POSTGRES_HOST`
   - `POSTGRES_PORT`
   - `POSTGRES_USER`
   - `POSTGRES_PASSWORD`
   - `POSTGRES_DB`
   - `OPENAI_API_KEY`

2. **Database running**:
   ```bash
   docker-compose up -d
   ```

3. **Dependencies installed**:
   ```bash
   pip install -r requirements.txt
   ```

## Understanding the Output

The test script will show:
- Initialization status (database, vector store, graph)
- Initial state (user query, messages)
- Final state (results, messages)
- Any errors with full traceback

## Debugging Tips

1. **Check database connection**: Make sure PostgreSQL is running and accessible
2. **Check vector store**: Ensure vector store is initialized (may need to populate it first)
3. **Check imports**: Make sure all paths are correct relative to your project structure
4. **Verbose mode**: Use `--verbose` or `-v` for detailed output

## Example Queries to Test

- "How many players are in the database?"
- "How many games were played in 2020?"
- "Who are the top 5 home run hitters in 2020?"
- "What is the batting average for Aaron Judge in 2020?"
