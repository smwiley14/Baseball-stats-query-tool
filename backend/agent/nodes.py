from pathlib import Path
import json
import re
from agent.state import State
from knowledge.vector_store import VectorStore
from agent.tools import Tools
from knowledge.few_shot_examples import SQLExample
from knowledge.data_dictionary import DataDictionary
from langchain_core.tools import StructuredTool
from langchain.agents import create_agent
# from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.types import interrupt
from langchain.chat_models import init_chat_model
from config import load_chat_prompt_template, load_config
from database.db_connect import DBConnector
from agent import util
from agent.cancellation import QueryCancelledError, is_cancelled
# from config.stat_config import StatConfig

db_connector = DBConnector()
# intent_classifier_prompt = load_chat_prompt_template(target_prompt="intent_classifier")
sql_generator_prompt = load_chat_prompt_template(target_prompt="sql_generator")

# llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
sql_examples_path = Path("configs/sql_examples.yml")

# Create data dictionary from DBConnector (automatically extracts schema)
data_dictionary = DataDictionary.load(Path("configs/db_dict.yml"))
sql_examples = SQLExample.from_yaml(sql_examples_path) if sql_examples_path.exists() else {}
stat_config = load_config(Path("configs/stat_config.yml"))
SCHEMA_RETRIEVAL_K = int(stat_config.get("schema_retrieval_k", 30))
# vector_store = VectorStore()


def _format_query_type_guidance(query_type: str) -> str:
    """Render query type config into concise prompt guidance."""
    query_definitions = stat_config.get("query_type_definitions", {})
    query_definition = query_definitions.get(query_type, {})

    if not query_definition:
        return "No specific query-type guidance found. Use general SQL best practices."

    return json.dumps(query_definition, indent=2)


def _classify_stat_profile(state: State) -> dict:
    """Select stat profile so hitter queries use batting config and pitcher queries use pitching config."""
    query = (state.user_query or "").lower()
    query_type = (state.query_type or "").lower()

    batting_keywords = [
        "hitter", "batter", "batting", "home run", "hr", "hits", "rbi", "rbis", "at bat",
        "avg", "obp", "slg", "ops", "stolen base", "walks", "strike out", "strikeout"
    ]
    pitching_keywords = [
        "pitcher", "pitching", "era", "whip", "innings", "ip", "earned run", "wins", "losses",
        "saves", "holds", "hits allowed", "walks allowed", "k/9", "fip"
    ]

    batting_hit = any(keyword in query for keyword in batting_keywords)
    pitching_hit = any(keyword in query for keyword in pitching_keywords)

    if query_type in {"player_matchup", "player_matchups"}:
        profile = "mixed"
    elif pitching_hit and not batting_hit:
        profile = "traditional_pitching"
    elif batting_hit and not pitching_hit:
        profile = "traditional_batting"
    elif "pitcher" in query:
        profile = "traditional_pitching"
    else:
        profile = "traditional_batting"

    if profile == "mixed":
        guidance_payload = {
            "selected_stat_profile": "mixed",
            "profiles": {
                "traditional_batting": stat_config.get("traditional_batting", {}).get("columns", []),
                "traditional_pitching": stat_config.get("traditional_pitching", {}).get("columns", []),
            },
            "rule": "Use traditional_batting for hitter metrics and traditional_pitching for pitcher metrics in the same query when needed.",
        }
        return {
            "selected_stat_profile": "mixed",
            "selected_stat_columns": None,
            "selected_stat_profile_guidance": json.dumps(guidance_payload, indent=2),
        }

    selected_columns = stat_config.get(profile, {}).get("columns", [])
    guidance_payload = {
        "selected_stat_profile": profile,
        "columns": selected_columns,
        "rule": "When returning hitter stats use traditional_batting columns. When returning pitcher stats use traditional_pitching columns.",
    }
    return {
        "selected_stat_profile": profile,
        "selected_stat_columns": selected_columns,
        "selected_stat_profile_guidance": json.dumps(guidance_payload, indent=2),
    }


def _extract_json_object(text: str) -> dict:
    """Best-effort JSON extraction for model outputs."""
    try:
        return json.loads(text)
    except Exception:
        pass

    match = re.search(r"\{[\s\S]*\}", text or "")
    if not match:
        return {}

    try:
        return json.loads(match.group(0))
    except Exception:
        return {}


def _normalize_tokens(text: str) -> set[str]:
    """Lowercase tokenization for lightweight lexical matching."""
    stopwords = {
        "the", "a", "an", "in", "of", "for", "by", "to", "and", "with",
        "what", "who", "is", "are", "show", "me",
    }
    tokens = re.findall(r"[a-z0-9_]+", (text or "").lower())
    return {t for t in tokens if t not in stopwords and len(t) > 1}


def _get_sql_examples_context(state: State, vector_store: VectorStore, k: int = 10) -> tuple[str, int]:
    """
    Build examples context by combining vector search with lexical backfill.
    This helps exact/near-exact questions pull intended curated examples.
    """
    vector_docs = vector_store.vectorstore.similarity_search(
        state.user_query,
        k=k,
        filter={"type": "example"},
    )

    query_tokens = _normalize_tokens(state.user_query or "")
    lexical_matches: list[tuple[float, SQLExample]] = []
    if query_tokens:
        for example in sql_examples.values():
            example_tokens = _normalize_tokens(example.question)
            if not example_tokens:
                continue
            overlap = len(query_tokens & example_tokens)
            if overlap == 0:
                continue
            score = overlap / max(len(query_tokens), 1)
            if score >= 0.45:
                lexical_matches.append((score, example))

    lexical_matches.sort(key=lambda x: x[0], reverse=True)

    combined_contents: list[str] = []
    seen = set()

    for doc in vector_docs:
        content = doc.page_content
        if content not in seen:
            seen.add(content)
            combined_contents.append(content)

    for _, example in lexical_matches[:3]:
        content = example.format_context()
        if content not in seen:
            seen.add(content)
            combined_contents.append(content)

    context = "\n\n".join(combined_contents)
    return context, len(combined_contents)


def _raise_if_cancelled(state: State) -> None:
    if is_cancelled(state.session_id):
        raise QueryCancelledError(f"Query cancelled for session {state.session_id}")


def normalize_input(state: State):
    """Ensure user_query is populated from the latest human message when omitted."""
    if state.user_query:
        return {}

    if not state.messages:
        return {"user_query": ""}

    for msg in reversed(state.messages):
        msg_type = getattr(msg, "type", "")
        if msg_type == "human":
            return {"user_query": getattr(msg, "content", "") or ""}

    return {"user_query": ""}


def _repair_sql_division_by_zero(original_sql: str, user_query: str) -> str | None:
    """Repair SQL to avoid division by zero by guarding every denominator."""
    llm = init_chat_model(model="gpt-4o-mini", temperature=0)
    prompt = f"""You are repairing PostgreSQL SQL that failed with division-by-zero.

User query:
{user_query}

Original SQL:
{original_sql}

Return ONLY valid JSON with a single key: sql_query.

Repair rules:
- Keep business logic unchanged.
- Guard every division denominator with NULLIF(denominator, 0).
- If denominator is an aggregate expression, wrap that expression in NULLIF(..., 0).
- Do not add markdown or commentary.
"""
    result = llm.invoke(prompt)
    content = result.content if hasattr(result, "content") else str(result)
    parsed = _extract_json_object(content)
    repaired_sql = (parsed.get("sql_query") or "").strip()
    return repaired_sql or None


def _repair_sql_syntax(original_sql: str, user_query: str, error_message: str) -> str | None:
    """Repair SQL syntax issues while preserving query intent."""
    llm = init_chat_model(model="gpt-4o-mini", temperature=0)
    prompt = f"""You are repairing PostgreSQL SQL that failed with a syntax error.

User query:
{user_query}

Database error:
{error_message}

Original SQL:
{original_sql}

Return ONLY valid JSON with a single key: sql_query.

Repair rules:
- Keep business logic unchanged.
- Fix only syntax issues (e.g., unbalanced parentheses, misplaced commas, invalid alias references).
- Do not add markdown or commentary.
"""
    result = llm.invoke(prompt)
    content = result.content if hasattr(result, "content") else str(result)
    parsed = _extract_json_object(content)
    repaired_sql = (parsed.get("sql_query") or "").strip()
    return repaired_sql or None


def _select_supplemental_dataset_type(state: State) -> str | None:
    """Decide whether to generate a supplemental detail dataset."""
    query = (state.user_query or "").lower()
    query_type = (state.query_type or "").lower()

    if query_type in {"player_matchup", "player_matchups"} or any(k in query for k in [" vs ", " versus ", " against ", "matchup", "head-to-head"]):
        return "matchup_events"

    is_career_query = any(keyword in query for keyword in ["career", "all time", "all-time"])
    if is_career_query and query_type not in {"top_players", "top_teams", "team_stats", "single_team"}:
        return "career_season_stats"

    is_player_season_or_stretch = any(
        keyword in query for keyword in ["season", "last ", "stretch", "between ", "from "]
    )
    is_non_team_context = query_type not in {"single_team", "top_teams", "team_stats", "top_players"}
    if query_type in {"player_season_stat", "individual_player_stretch", "player_date_range"} or (is_player_season_or_stretch and is_non_team_context):
        return "game_logs"

    return None


def _build_supplemental_schema_context(state: State, vector_store: VectorStore) -> str:
    """Retrieve schema context for supplemental query generation."""
    schema_docs = vector_store.vectorstore.similarity_search(
        f"{state.user_query} supplemental {state.query_type}",
        k=20,
        filter={"type": "schema"}
    )
    if schema_docs:
        return "\n\n".join([doc.page_content for doc in schema_docs])
    return data_dictionary.format_context()


def _generate_supplemental_sql(state: State, vector_store: VectorStore, detail_type: str) -> dict:
    """Generate SQL for supplemental detail dataset."""
    _raise_if_cancelled(state)
    schema_context = _build_supplemental_schema_context(state, vector_store)
    llm = init_chat_model(model="gpt-4o-mini", temperature=0)

    prompt = f"""You generate a SECONDARY SQL query for baseball analytics.

User question:
{state.user_query}

Primary query type:
{state.query_type}

Primary SQL query:
{state.sql_query}

Detail dataset requested:
{detail_type}

Schema context:
{schema_context}

Rules:
- Return ONLY valid JSON with keys: sql_query, description
- Prefer regular-season data where available by joining games and filtering LOWER(game_type) = 'regular'
- Use only tables/columns that exist in schema context
- Keep output granular for detail views (not summary-only)

Detail requirements by type:
- game_logs: return game-level logs for the player in this query. Include game_id, game_date, season, team and key per-game stats. Order by game_date.
- matchup_events: return event-level rows from events for this matchup. Include game_id, inning, batter_id, pitcher_id, event_text, event_code, rbi, outs, home_score, away_score. Order by game_id then inning.
- career_season_stats: return one row per season for the player in this query with aggregated seasonal stats and games played. Order by season.

If impossible, return {{"sql_query":"", "description":"reason"}}.
"""

    result = llm.invoke(prompt)
    _raise_if_cancelled(state)
    response_content = result.content if hasattr(result, "content") else str(result)
    parsed = _extract_json_object(response_content)
    sql_query = (parsed.get("sql_query") or "").strip()
    description = (parsed.get("description") or "").strip()
    return {
        "sql_query": sql_query,
        "description": description,
    }


def _build_supplemental_data(state: State, vector_store: VectorStore) -> dict | None:
    """Build supplemental dataset based on query intent."""
    _raise_if_cancelled(state)
    detail_type = _select_supplemental_dataset_type(state)
    if not detail_type:
        return None

    detail_spec = _generate_supplemental_sql(state, vector_store, detail_type)
    detail_sql = detail_spec.get("sql_query", "")
    if not detail_sql:
        return {
            "status": "skipped",
            "type": detail_type,
            "description": detail_spec.get("description") or "No supplemental SQL generated."
        }

    detail_result = util.execute_sql(detail_sql, db_connector)
    _raise_if_cancelled(state)
    if detail_result.get("status") != "success":
        return {
            "status": "failure",
            "type": detail_type,
            "description": detail_spec.get("description"),
            "sql_query": detail_sql,
            "error": detail_result.get("error"),
        }

    detail_rows = detail_result.get("data") or []
    return {
        "status": "success",
        "type": detail_type,
        "description": detail_spec.get("description"),
        "sql_query": detail_sql,
        "row_count": detail_result.get("row_count", len(detail_rows)),
        "data": format_table_data(detail_rows),
    }

def chat_agent(state:State, vector_store:VectorStore):
    messages = state.messages
    last_user_message = messages[-1]
    # chat_history = messages[-1:]
    tools_obj = Tools(vector_store)
    tools = [
        StructuredTool.from_function(
            func=tools_obj.get_similar_queries,
            name="get_similar_queries",
            description="Get similar queries from the vector store"
        ),
        StructuredTool.from_function(
            func=tools_obj.explain_query,
            name="explain_query",
            description="Explain the query"
        ),
        StructuredTool.from_function(
            func=tools_obj.get_table_info,
            name="get_table_info",
            description="Get information about the table"
        )
    ]
    # prompt = ChatPromptTemplate.from_messages([
    #     MessagesPlaceholder(variable_name="chat_history"),
    #     HumanMessage(content=last_user_message.content)
    # ])
        # Get the system prompt
    chat_system_prompt = """You are a NL2SQL assistant that can turn natural language queries into SQL queries and return the results in a readable table format with a small summary.

You have access to tools that can:
1. Find similar SQL query examples from the knowledge base
2. Explain SQL queries in simple terms and provide a small summary of the results
3. Provide database schema information

If the number of rows requested is not specified, return the top 20 rows.
"""
# IMPORTANT: You have access to the full conversation history. Use it to understand 
# context and follow-up questions. For example, if a user asks "what were his numbers the next year?"
# after asking about Cody Bellingers 2020 season, you should understand they are asking about Cody Bellingers 2021 season.
    agent = create_agent(
        model="gpt-4o-mini",
        # temperature=0,
        tools=tools,
        system_prompt=chat_system_prompt
    )
    # agent_executor = AgentExecutor(agent=agent, tools=tools)
    try:
        response = agent.invoke(
            {"input": state.user_query, "chat_history": state.messages}
        )
        # print("hello")
        response_content = response["messages"][-1].content
        # print("response", response)
    except Exception as e:
        # logger.error(f"Chat agent error: {e}")
        response_content = (
            "I'm here to help you with database queries and data analysis. "
            "What would you like to explore in your database?"
        )
        print("error", e)

    # logger.debug(f"✅ Chat Agent response: {response_content[:50]}...")
    # return {"messages": [AIMessage(content=response)]}
    return {"messages": [AIMessage(content=response_content)]}


def determine_query_type(state:State):
    """Determine the query type based on the user query"""
    query = state.user_query or ""
    
    # Create a system prompt that instructs the agent to look at query_types from config
    query_types = stat_config.get("query_types", [])
    query_type_definitions = stat_config.get("query_type_definitions", {})
    query_types_list = ", ".join(query_types)
    query_type_definition_text = json.dumps(query_type_definitions, indent=2)

    system_prompt = f"""
        You are a query classifier for baseball statistics queries. 
        Your task is to analyze the user's query and determine which query type it matches.

        Available query types from the configuration:
        {query_types_list}

        Query type definitions:
        {query_type_definition_text}

        Analyze the user query and respond with ONLY the exact query type name that matches (one of: {query_types_list}).
        If uncertain, respond with "other".
        Do not include explanation or extra text.
    """
    
    agent = create_agent(
        model="gpt-4o-mini",
        tools=[],
        system_prompt=system_prompt
    )
    
    try:
        response = agent.invoke({"input": query})
        _raise_if_cancelled(state)
        raw_content = response["messages"][-1].content
        response_content = raw_content if isinstance(raw_content, str) else str(raw_content)
        response_lower = response_content.strip().lower()

        # Exact match first.
        if response_lower in query_types:
            return response_lower

        # Extract first valid query type mentioned anywhere in output.
        for query_type in query_types:
            if re.search(rf"\b{re.escape(query_type)}\b", response_lower):
                return query_type

        # Config-driven intent fallback using intent_signals.
        query_lower = query.lower()
        best_type = "other"
        best_score = 0
        for query_type, definition in query_type_definitions.items():
            intent_signals = definition.get("intent_signals", [])
            score = sum(1 for signal in intent_signals if signal.lower() in query_lower)
            if score > best_score:
                best_score = score
                best_type = query_type
        if best_score > 0 and best_type in query_types:
            return best_type

        return "other"
    except Exception as e:
        print(f"Error in determine_query_type agent: {e}")
        query_lower = query.lower()
        # for query_type, definition in query_type_definitions.items():
        #     for signal in definition.get("intent_signals", []):
        #         if signal.lower() in query_lower and query_type in query_types:
        #             return query_type
        return "other"


def classify_query_type(state: State):
    """Classify query and attach query-specific SQL guidance to state."""
    _raise_if_cancelled(state)
    query_type = determine_query_type(state)
    guidance = _format_query_type_guidance(query_type)
    return {
        "query_type": query_type,
        "query_type_guidance": guidance,
    }


def classify_stat_profile(state: State):
    """Attach traditional stat profile guidance for SQL generation."""
    _raise_if_cancelled(state)
    return _classify_stat_profile(state)


# def determine_relevance(state:State):
#     pass



def sql_generator(state:State, vector_store:VectorStore):
    """Generate SQL query from natural language using knowledge base context"""
    _raise_if_cancelled(state)
    # For search-engine mode, we don't use chat history
    chat_history = ""

    # Use RAG to retrieve relevant schema parts based on the query
    # This is more efficient than sending the entire schema
    schema_docs = vector_store.vectorstore.similarity_search(
        state.user_query,
        k=SCHEMA_RETRIEVAL_K,
        filter={"type": "schema"}
    )
    
    # If we found relevant schema docs, use them; otherwise fall back to full schema
    if schema_docs:
        schema_context = "\n\n".join([doc.page_content for doc in schema_docs])
        print(f"Retrieved {len(schema_docs)} relevant schema documents via RAG")
    else:
        # Fallback to full schema if RAG doesn't find anything
        schema_context = data_dictionary.format_context()
        print("WARNING: No relevant schema found via RAG, using full schema")

    print(f"Schema context length: {len(schema_context)} characters")
    print(f"User query: {state.user_query}")
    
    sql_examples_context, examples_found = _get_sql_examples_context(state, vector_store, k=10)

    print(f"SQL examples found: {examples_found}")
    if examples_found == 0:
        print("WARNING: No SQL examples found in vector store. Proceeding without examples.")

    llm = init_chat_model(model="gpt-4o-mini", temperature=0)
    
    chain = sql_generator_prompt | llm

    result = chain.invoke({
        "user_query": state.user_query,
        "chat_history": chat_history,
        "schema_context": schema_context,
        "sql_examples": sql_examples_context,
        "query_type": state.query_type or "other",
        "query_type_guidance": state.query_type_guidance or "No specific query-type guidance provided.",
        "selected_stat_profile": state.selected_stat_profile or "traditional_batting",
        "selected_stat_profile_guidance": state.selected_stat_profile_guidance or "No explicit stat profile guidance provided.",
    })
    _raise_if_cancelled(state)
    # print(result)
    response_content = result.content if hasattr(result, 'content') else str(result)
    print(response_content)
    try:
        parsed = json.loads(response_content)
        print(parsed)
        sql_query = parsed.get("sql_query", "").strip()

        if sql_query:  
            return {
                "sql_query": sql_query,
                "sql_generation_status": "success"
            }
        else: 
            explanation = parsed.get("sql_explanation", "No SQL query could be generated.")
            return {
                "sql_query": None,
                "sql_generation_status": "failure",
                "messages": [AIMessage(content=f"I couldn't generate a SQL query for your question. {explanation}")]
            }
    except (json.JSONDecodeError, AttributeError, KeyError) as e:
        print(f"Error parsing SQL generator response: {e}")
        explanation = f"Error parsing JSON: {str(e)}"
        return {
            "sql_query": None,
            "sql_generation_status": "failure",
            "messages": [AIMessage(content=f"I couldn't generate a SQL query for your question. {explanation}")]
        }
    
def sql_executor(state:State, db_connector: DBConnector):
    _raise_if_cancelled(state)
    if not state.sql_query:
        return {
            "sql_execution_status": "failure",
            "sql_execution_result": {
                "status": "failure",
                "error": "No SQL query generated or query is empty"
            }
        }
    
    initial_sql = state.sql_query

    current_sql = initial_sql
    res = util.execute_sql(current_sql, db_connector)
    _raise_if_cancelled(state)
    print(res)

    error_text = (res.get("error") or "").lower() if isinstance(res, dict) else ""
    is_syntax_error = (
        res.get("status") == "failure"
        and ("syntax error" in error_text or "syntaxerror" in error_text)
    )
    is_division_error = (
        res.get("status") == "failure"
        and ("division by zero" in error_text or "divisionbyzero" in error_text)
    )

    if is_syntax_error:
        syntax_fixed_sql = _repair_sql_syntax(
            current_sql,
            state.user_query or "",
            res.get("error", ""),
        )
        if syntax_fixed_sql:
            current_sql = syntax_fixed_sql
            res = util.execute_sql(current_sql, db_connector)
            _raise_if_cancelled(state)
            print(res)
            error_text = (res.get("error") or "").lower() if isinstance(res, dict) else ""
            is_division_error = (
                res.get("status") == "failure"
                and ("division by zero" in error_text or "divisionbyzero" in error_text)
            )
            if res.get("status") == "success":
                res["repair_applied"] = True
                res["repair_reason"] = "syntax_error"
                return {
                    "sql_query": current_sql,
                    "sql_execution_status": "success",
                    "sql_execution_result": res
                }

    if not is_division_error:
        return {
            "sql_query": current_sql,
            "sql_execution_status": res["status"],
            "sql_execution_result": res
        }

    repaired_sql = _repair_sql_division_by_zero(current_sql, state.user_query or "")
    if not repaired_sql:
        return {
            "sql_query": initial_sql,
            "sql_execution_status": "failure",
            "sql_execution_result": res
        }

    repaired_res = util.execute_sql(repaired_sql, db_connector)
    _raise_if_cancelled(state)
    print(repaired_res)
    if repaired_res.get("status") == "success":
        repaired_res["repair_applied"] = True
        repaired_res["repair_reason"] = "division_by_zero"
        return {
            "sql_query": repaired_sql,
            "sql_execution_status": "success",
            "sql_execution_result": repaired_res
        }

    return {
        "sql_query": repaired_sql,
        "sql_execution_status": repaired_res.get("status", "failure"),
        "sql_execution_result": repaired_res
    }

def check_sql_execution(state: State) -> str:
    if state.sql_execution_status == "success":
        return "success"
    else:
        return "failure"

def check_sql_generation(state: State) -> str:
    if state.sql_generation_status == "success":
        return "success"
    else:
        return "failure"

def check_relevance_decision(state: State) -> bool:
    return state.relevance

    
def check_relevance(state:State, vector_store:VectorStore):
    """Check if the query is relevant and answerable using the knowledge base"""
    _raise_if_cancelled(state)
    query = state.user_query

    # NOTE: PGVector similarity_search returns k docs even for low similarity.
    # Use scores and a threshold to avoid marking unrelated queries as relevant.
    RELEVANCE_DISTANCE_THRESHOLD = 0.4
    RELEVANCE_SCORE_THRESHOLD = 0.45
    
    # Search for relevant schema and examples in knowledge base
    if hasattr(vector_store.vectorstore, "similarity_search_with_relevance_scores"):
        schema_results = vector_store.vectorstore.similarity_search_with_relevance_scores(
            query,
            k=5,
            filter={"type": "schema"}
        )
        example_results = vector_store.vectorstore.similarity_search_with_relevance_scores(
            query,
            k=5,
            filter={"type": "example"}
        )
        score_is_similarity = True
    elif hasattr(vector_store.vectorstore, "similarity_search_with_score"):
        schema_results = vector_store.vectorstore.similarity_search_with_score(
            query,
            k=5,
            filter={"type": "schema"}
        )
        example_results = vector_store.vectorstore.similarity_search_with_score(
            query,
            k=5,
            filter={"type": "example"}
        )
        score_is_similarity = False
    else:
        schema_docs = vector_store.vectorstore.similarity_search(
            query,
            k=5,
            filter={"type": "schema"}
        )
        example_docs = vector_store.vectorstore.similarity_search(
            query,
            k=5,
            filter={"type": "example"}
        )
        score_is_similarity = None
        schema_results = []
        example_results = []

    if schema_results or example_results:
        schema_docs = [doc for doc, _score in schema_results]
        example_docs = [doc for doc, _score in example_results]
    else:
        schema_docs = schema_docs if "schema_docs" in locals() else []
        example_docs = example_docs if "example_docs" in locals() else []

    if score_is_similarity is True:
        best_schema_score = max((score for _doc, score in schema_results), default=None)
        best_example_score = max((score for _doc, score in example_results), default=None)
        best_score = max(
            (score for score in [best_schema_score, best_example_score] if score is not None),
            default=None,
        )
        is_relevant = best_score is not None and best_score >= RELEVANCE_SCORE_THRESHOLD
    elif score_is_similarity is False:
        best_schema_score = min((score for _doc, score in schema_results), default=None)
        best_example_score = min((score for _doc, score in example_results), default=None)
        best_score = min(
            (score for score in [best_schema_score, best_example_score] if score is not None),
            default=None,
        )
        is_relevant = best_score is not None and best_score <= RELEVANCE_DISTANCE_THRESHOLD
    else:
        best_score = None
        is_relevant = bool(schema_docs or example_docs)
    
    # If we find relevant context, the query is likely answerable
    if is_relevant:
        return {
            "relevance": True,
            "relevance_status": "relevant",
        }
    else:
        if best_score is None and score_is_similarity is None:
            summary = "No relevance scores available; no relevant context found."
        elif best_score is None:
            summary = "No schema or example matches found."
        elif score_is_similarity is True:
            summary = (
                "No sufficiently relevant schema or examples found "
                f"(best score {best_score:.3f} < {RELEVANCE_SCORE_THRESHOLD})."
            )
        else:
            summary = (
                "No sufficiently relevant schema or examples found "
                f"(best distance {best_score:.3f} > {RELEVANCE_DISTANCE_THRESHOLD})."
            )
        return {
            "relevance": False,
            "relevance_status": "not_relevant",
            "table_data": None,
            "summary": summary,
            "messages": [AIMessage(content=summary)]
        }


def sql_return_message(state:State, vector_store:VectorStore):
    """Format SQL results as structured data (table with human-readable columns + summary)"""
    _raise_if_cancelled(state)
    print(state.sql_execution_result)
    vector_store.add_generated_query(state.user_query, state.sql_query)
    supplemental_data = _build_supplemental_data(state, vector_store)
    print(supplemental_data)
    if not state.sql_execution_result:
        return {
            "messages": [AIMessage(content="No execution result available.")],
            "table_data": None,
            "supplemental_data": supplemental_data,
            "summary": "No execution result available."
        }
    
    if state.sql_execution_status == "success":
        data = state.sql_execution_result.get("data")
        if data and isinstance(data, list) and len(data) > 0:
            # Format column names to be human-readable
            formatted_data = format_table_data(data)
            
            # Generate a brief summary using LLM
            summary = generate_result_summary(state.user_query, data, state.session_id)
            
            return {
                "table_data": formatted_data,
                "supplemental_data": supplemental_data,
                "summary": summary,
                "messages": [AIMessage(content=summary)]
            }
        elif data and isinstance(data, list) and len(data) == 0:
            # No results found
            summary = f"No results found for your query: \"{state.user_query}\". Please try rephrasing your question or check if the data exists in the database."
            return {
                "table_data": [],
                "supplemental_data": supplemental_data,
                "summary": summary,
                "messages": [AIMessage(content=summary)]
            }
        else:
            summary = state.sql_execution_result.get("message", "Query executed successfully.")
            return {
                "table_data": None,
                "supplemental_data": supplemental_data,
                "summary": summary,
                "messages": [AIMessage(content=summary)]
            }
    else:
        # Handle error case — log the full error server-side, return a safe message to the user.
        import logging as _logging
        _logger = _logging.getLogger(__name__)
        raw_error = state.sql_execution_result.get("error", "Unknown error occurred")
        _logger.error("SQL execution failed: %s", raw_error)
        summary = (
            "I was unable to retrieve results for your query. "
            "Please try rephrasing your question or simplifying the request."
        )
        return {
            "table_data": None,
            "supplemental_data": supplemental_data,
            "summary": summary,
            "messages": [AIMessage(content=summary)]
        }


def format_table_data(data: list[dict]) -> list[dict]:
    """Format query results with human-readable column names"""
    if not data or len(data) == 0:
        return []
    
    formatted_data = []
    for row in data:
        formatted_row = {}
        for key, value in row.items():
            # Convert column names to human-readable format
            readable_key = format_column_name(key)
            formatted_row[readable_key] = value
        formatted_data.append(formatted_row)
    
    return formatted_data


def format_column_name(column_name: str) -> str:
    """Convert database column names to human-readable format"""
    # Replace underscores with spaces and title case
    readable = column_name.replace("_", " ").title()
    
    # Common abbreviations to keep uppercase
    abbreviations = {
        "Id": "ID",
        "Rbi": "RBI",
        "Hr": "HR",
        "Ab": "AB",
        "Ip": "IP",
        "Era": "ERA",
        "Whip": "WHIP",
        "Ops": "OPS",
        "Obp": "OBP",
        "Slg": "SLG",
        "Avg": "AVG",
    }
    
    # Apply abbreviations
    for abbrev, replacement in abbreviations.items():
        readable = readable.replace(abbrev, replacement)
    
    return readable


def generate_result_summary(query: str, data: list[dict], session_id: str | None = None) -> str:
    """Generate a brief summary of the results using LLM"""
    try:
        if is_cancelled(session_id):
            raise QueryCancelledError(f"Query cancelled for session {session_id}")
        llm = init_chat_model(model="gpt-4o-mini", temperature=0)
        
        # Create a concise summary prompt
        summary_prompt = f"""Based on the following query and results, provide a brief 1-2 sentence summary of what the data shows.

Query: {query}

Results (first 3 rows as example):
{str(data[:3])}

Provide a concise summary focusing on the key findings. Do not include markdown formatting."""
        
        response = llm.invoke(summary_prompt)
        if is_cancelled(session_id):
            raise QueryCancelledError(f"Query cancelled for session {session_id}")
        summary = response.content if hasattr(response, 'content') else str(response)
        return summary.strip()
    except Exception as e:
        print(f"Error generating summary: {e}")
        # Fallback summary
        if data:
            return f"Found {len(data)} result(s) matching your query."
        return "Results retrieved successfully."
    
    
