"""
Baseball Stats Query Tool - Streamlit UI
A simple web interface for querying baseball statistics using LangChain SQL Agent
"""

import streamlit as st
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain.agents import create_agent
from langchain_community.utilities.sql_database import SQLDatabase


# Page configuration
st.set_page_config(
    page_title="Baseball Stats Query Tool",
    page_icon="⚾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load environment variables
load_dotenv(override=True)

# Initialize session state
if "agent" not in st.session_state:
    st.session_state.agent = None
if "db" not in st.session_state:
    st.session_state.db = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Sidebar configuration
with st.sidebar:
    st.title("⚾ Baseball Stats Query Tool")
    st.markdown("---")
    
    st.subheader("Configuration")
    
    # Database connection settings
    db_host = st.text_input("Database Host", value="localhost", key="db_host")
    db_port = st.text_input("Database Port", value="5433", key="db_port")
    db_name = st.text_input("Database Name", value="retrosheet", key="db_name")
    db_user = st.text_input("Database User", value="baseball", key="db_user")
    db_password = st.text_input("Database Password", value="baseball", type="password", key="db_password")
    
    # OpenAI settings
    openai_api_key = st.text_input(
        "OpenAI API Key", 
        value=os.getenv("OPENAI_API_KEY", ""),
        type="password",
        key="openai_key"
    )
    
    model_name = st.selectbox(
        "Model",
        ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo-preview"],
        index=0,
        key="model_name"
    )
    
    # Connect button
    if st.button("🔌 Connect to Database", type="primary", use_container_width=True):
        try:
            with st.spinner("Connecting to database and initializing agent..."):
                # Create database connection
                db_uri = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
                st.session_state.db = SQLDatabase.from_uri(db_uri)
                
                # Initialize LLM
                llm = ChatOpenAI(
                    model=model_name,
                    temperature=0,
                    openai_api_key=openai_api_key
                )
                
                # Create toolkit and tools
                toolkit = SQLDatabaseToolkit(db=st.session_state.db, llm=llm)
                tools = toolkit.get_tools()
                
                # Agent system prompt
                system_prompt = f"""
You are an expert baseball statistics assistant. You have access to a comprehensive baseball database with:
- Player statistics (batting, pitching, fielding)
- Game information
- Team data
- Historical records

Given an input question, create a syntactically correct {st.session_state.db.dialect} query to run,
then look at the results of the query and return the answer in a clear, natural language format.

Guidelines:
- Always provide context and explain what the numbers mean
- For player queries, include their full name when possible
- Format dates in a readable format
- Limit queries to top results (usually 5-10) unless specifically asked for more
- Never perform DML operations (INSERT, UPDATE, DELETE)
- If a query fails, explain why and suggest alternatives
"""
                
                # Create agent
                st.session_state.agent = create_agent(
                    llm, 
                    tools, 
                    system_prompt=system_prompt
                )
                
                st.success("✅ Connected successfully!")
                st.session_state.chat_history = []
        except Exception as e:
            st.error(f"❌ Connection failed: {str(e)}")
    
    st.markdown("---")
    
    # Example queries
    st.subheader("💡 Example Queries")
    example_queries = [
        "How many players are in the database?",
        "Who hit the most home runs in 2020?",
        "What was the highest batting average in a single season?",
        "Who had the most strikeouts as a pitcher in 2020?",
        "What team won the most games in 2020?",
        "Who had the most hits in a 10-game span?",
        "What was the average ERA for all pitchers in 2020?",
        "Which player had the most RBIs in a single game?"
    ]
    
    for query in example_queries:
        if st.button(query, key=f"example_{hash(query)}", use_container_width=True):
            st.session_state.current_query = query
    
    st.markdown("---")
    
    # Clear chat button
    if st.button("🗑️ Clear Chat History", use_container_width=True):
        st.session_state.chat_history = []
        st.rerun()

# Main content area
st.title("⚾ Baseball Statistics Query Assistant")
st.markdown("Ask questions about baseball statistics in natural language!")

# Check if agent is initialized
if st.session_state.agent is None:
    st.info("👈 Please configure your database connection in the sidebar and click 'Connect to Database' to get started.")
    
    # Show database schema info
    with st.expander("📊 Available Database Tables"):
        st.markdown("""
        **Main Tables:**
        - `players` - Player information
        - `teams` - Team information
        - `games` - Game information
        - `batting_stats` - Batting statistics per game
        - `pitching_stats` - Pitching statistics per game
        - `fielding_stats` - Fielding statistics per game
        - `rosters` - Player-team-season rosters
        - `events` - Play-by-play events
        
        **Views:**
        - `v_player_career_batting` - Career batting stats
        - `v_player_career_pitching` - Career pitching stats
        - `v_season_batting_leaders` - Season batting leaders
        - `v_season_pitching_leaders` - Season pitching leaders
        """)
else:
    # Display chat history
    for i, (query, response) in enumerate(st.session_state.chat_history):
        with st.chat_message("user"):
            st.write(query)
        
        with st.chat_message("assistant"):
            st.write(response)
    
    # Chat input
    query = st.chat_input("Ask a question about baseball statistics...")
    
    # Handle query from sidebar example buttons
    if "current_query" in st.session_state:
        query = st.session_state.current_query
        del st.session_state.current_query
    
    if query:
        # Add user query to chat
        st.session_state.chat_history.append((query, None))
        
        # Get response from agent
        with st.chat_message("user"):
            st.write(query)
        
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    result = st.session_state.agent.invoke({
                        "messages": [{"role": "user", "content": query}]
                    })
                    
                    # Extract the response
                    if isinstance(result, dict):
                        if "output" in result:
                            response = result["output"]
                        elif "messages" in result and len(result["messages"]) > 0:
                            # Get the last AI message
                            last_message = result["messages"][-1]
                            if hasattr(last_message, 'content'):
                                response = last_message.content
                            else:
                                response = str(last_message)
                        else:
                            response = str(result)
                    else:
                        response = str(result)
                    
                    st.write(response)
                    
                    # Update chat history
                    st.session_state.chat_history[-1] = (query, response)
                    
                except Exception as e:
                    error_msg = f"❌ Error: {str(e)}"
                    st.error(error_msg)
                    st.session_state.chat_history[-1] = (query, error_msg)
        
        st.rerun()

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #666;'>"
    "Baseball Stats Query Tool | Powered by LangChain & OpenAI"
    "</div>",
    unsafe_allow_html=True
)
