# NL2SQL Agent Tuning Guide

This guide explains how to improve your LangChain SQL agent's performance for baseball statistics queries.

## Key Tuning Strategies

### 1. **Enhanced Database Configuration**

Use `sample_rows_in_table_info` to show example data:

```python
db = SQLDatabase(
    engine=engine,
    sample_rows_in_table_info=3,  # Shows 3 example rows per table
    custom_table_info={...}  # Domain-specific descriptions
)
```

**Benefits:**
- Agent sees actual data format
- Understands data types better
- Learns common values and patterns

### 2. **Custom Table Descriptions**

Provide domain-specific context:

```python
custom_table_info = {
    "batting_stats": """
    Batting statistics per game.
    - home_runs: Home runs hit in this game
    - rbis: Runs batted in
    - batting_average: hits / at_bats (calculated)
    """
}
```

### 3. **Comprehensive System Prompt**

Include:
- **Database schema knowledge**: Table relationships, key columns
- **Domain terminology**: Baseball-specific terms (HR, RBI, ERA, etc.)
- **Common query patterns**: Examples of window functions, aggregations
- **Response formatting**: How to present results

### 4. **Few-Shot Examples**

Provide examples of common query patterns:

```python
FEW_SHOT_EXAMPLES = [
    {
        "question": "Who hit the most home runs in 2020?",
        "sql": "SELECT p.first_name, p.last_name, SUM(bs.home_runs)...",
        "explanation": "..."
    }
]
```

### 5. **Model Selection**

- **GPT-4**: Better SQL generation, more accurate joins
- **GPT-3.5-turbo**: Faster, cheaper, but less accurate for complex queries
- **Temperature**: Keep at 0 for deterministic SQL

### 6. **Tool Configuration**

Limit tables to relevant ones:

```python
enhanced_db = SQLDatabase(
    engine=engine,
    include_tables=["players", "batting_stats", "pitching_stats", "games"],
    ignore_tables=["temp_tables", "staging_tables"]
)
```

## Implementation

### Basic Setup

```python
from create_agent_improved import create_improved_agent

# Create agent with enhancements
agent, db = create_improved_agent(
    model_name="gpt-4",  # Better for SQL
    temperature=0,
    use_enhanced_db=True
)

# Use the agent
result = agent.invoke({
    "messages": [{"role": "user", "content": "Who hit the most home runs in 2020?"}]
})
```

### Advanced: Custom Prompt with Few-Shot Examples

```python
from few_shot_examples import get_few_shot_prompt
from create_agent_improved import get_baseball_system_prompt, get_enhanced_db

db = get_enhanced_db()
few_shot = get_few_shot_prompt()
base_prompt = get_baseball_system_prompt(db)

# Combine prompts
full_prompt = f"{base_prompt}\n\n{few_shot}"

# Create agent with combined prompt
agent = create_agent(llm, tools, system_prompt=full_prompt)
```

## Testing & Evaluation

### Test Queries

Create a test suite:

```python
TEST_QUERIES = [
    "Who hit the most home runs in 2020?",
    "What was the highest batting average in a single season?",
    "Who had the most hits in a 10-game span?",
    "What was Mike Trout's batting average in 2020?",
]

for query in TEST_QUERIES:
    result = agent.invoke({"messages": [{"role": "user", "content": query}]})
    print(f"Q: {query}")
    print(f"A: {result['output']}\n")
```

### Metrics to Track

1. **Accuracy**: Does the SQL execute successfully?
2. **Correctness**: Does it return the right data?
3. **Efficiency**: Is the query optimized?
4. **Natural Language**: Is the response clear?

## Common Issues & Solutions

### Issue: Wrong Table Joins

**Solution**: Add explicit JOIN examples in system prompt:
```sql
-- Always join players for names
JOIN players p ON bs.player_id = p.player_id
```

### Issue: Incorrect Aggregations

**Solution**: Provide aggregation examples:
```sql
-- For season totals
GROUP BY player_id, season
-- For career totals
GROUP BY player_id
```

### Issue: Date Filtering Problems

**Solution**: Show date filtering patterns:
```sql
WHERE season = 2020
-- OR
WHERE game_date BETWEEN '2020-04-01' AND '2020-10-31'
```

### Issue: Window Function Errors

**Solution**: Include window function examples:
```sql
SUM(stat) OVER (
    PARTITION BY player_id 
    ORDER BY game_date 
    ROWS BETWEEN 9 PRECEDING AND CURRENT ROW
)
```

## Best Practices

1. **Start Simple**: Begin with basic queries, add complexity gradually
2. **Iterate**: Test with real questions, refine prompts based on failures
3. **Monitor**: Use LangSmith to track agent performance
4. **Document**: Keep examples of successful queries
5. **Version Control**: Track prompt changes and their impact

## Performance Tips

- **Cache table info**: Don't regenerate on every query
- **Limit table scope**: Only include relevant tables
- **Use views**: Pre-join common patterns in database views
- **Index properly**: Ensure foreign keys are indexed
- **Sample size**: 3-5 sample rows is usually sufficient

## Next Steps

1. Implement `create_agent_improved.py`
2. Test with your common queries
3. Refine prompts based on failures
4. Add domain-specific examples
5. Monitor performance with LangSmith
