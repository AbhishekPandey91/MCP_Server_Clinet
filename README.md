# MCP Servers Collection with Agent

A comprehensive collection of Model Context Protocol (MCP) servers with an intelligent LangChain-powered agent that seamlessly integrates multiple services and APIs for AI assistants and chatbots.

## 🚀 Overview

This repository contains multiple MCP server implementations and a sophisticated client agent that enables AI assistants to interact with external services, APIs, and tools. The agent uses LangChain and LangGraph to orchestrate complex workflows across different servers, powered by Groq's LLM API.

## 🎯 Key Features

- **Multi-Server Architecture**: 9 specialized MCP servers for different functionalities
- **Intelligent Agent**: LangGraph ReAct agent for autonomous task execution
- **Async Operations**: Full async/await support for efficient I/O operations
- **Groq LLM Integration**: Fast inference using Llama 3.1 8B Instant model
- **Interactive CLI**: User-friendly command-line interface
- **Robust Error Handling**: Comprehensive exception handling and logging

## 📦 Available Servers

### 1. Weather Server (`WEATHER.py`)
Provides real-time weather information using external APIs.

**Features:**
- Current weather conditions
- Weather forecasts
- Location-based weather data

### 2. Math Calculation Server (`calculation_server.py`)
Mathematical computation server supporting BODMAS/PEMDAS operations.

**Features:**
- Advanced mathematical calculations
- Expression evaluation
- BODMAS order of operations

### 3. Gmail Toolkit Server (`gmail_server.py`)
Comprehensive Gmail integration for email management.

**Tools:**
- `send` - Send emails
- `draft` - Save emails as drafts
- `get_latest_emails` - Fetch recent emails
- `search_gmail` - Search emails using Gmail search syntax
- `get_gmail_message` - Retrieve full email content by ID

**Use Cases:**
- Automated event detail notifications
- Important email management
- Basic email replies with feedback integration

### 4. Search Server (`search_server.py`)
Multi-source search capabilities for information retrieval.

**Tools:**
- **DuckDuckGo** - Web search for latest information
- **Wikipedia** - Knowledge base search

### 5. Google Workspace Server (`drive_calander_server.py`)
Google Drive & Calendar integration for file and schedule management.

**Tools:**
- `google_drive_search` - Search files in Google Drive
- `google_drive_get_file` - Retrieve detailed file information
- `google_calendar_view` - Read calendar events and schedules
- `google_calendar_create` - Create new calendar events
- `google_calendar_update` - Update existing events
- `google_calendar_delete` - Delete calendar events

**Note:** Google Forms API has limitations. The `create_simple_form` function only sets form titles. Additional items require the `batchUpdate` method.

### 6. OpenStreetMap Server (`map_server.py`)
Location and mapping services integration.

**Tools:**
- `maps_geocode` - Convert address to coordinates
- `maps_reverse_geocode` - Convert coordinates to address
- `maps_search_places` - Search for places by text query
- `maps_place_details` - Get detailed place information
- `maps_distance_matrix` - Calculate distances between points
- `maps_elevation` - Get elevation data
- `maps_directions` - Get directions between points

**Transport Modes:** driving, walking, bicycling, transit

### 7. GitHub Server (`github_server.py`)
Complete GitHub API integration for repository and code management.

**Features:**
- Automatic branch creation
- Comprehensive error handling
- Git history preservation
- Batch operations support
- Advanced search capabilities

**File Operations:**
- `create_or_update_file` - Create/update single files
- `push_files` - Push multiple files in one commit
- `get_file_contents` - Read file/directory contents

**Repository Management:**
- `create_repository` - Create new repositories
- `search_repositories` - Search GitHub repositories
- `fork_repository` - Fork repositories
- `create_branch` - Create new branches
- `list_commits` - Get branch commit history

**Issues & Pull Requests:**
- `create_issue`, `list_issues`, `update_issue`, `add_issue_comment`, `get_issue`
- `create_pull_request`, `list_pull_requests`, `get_pull_request`
- `get_pull_request_files`, `get_pull_request_status`
- `create_pull_request_review`, `merge_pull_request`
- `update_pull_request_branch`, `get_pull_request_comments`, `get_pull_request_reviews`

**Search Capabilities:**
- `search_code` - Search code across repositories
- `search_issues` - Search issues and PRs
- `search_users` - Search GitHub users

### 8. SQLite Server (`sql_server.py`)
Database interaction and business intelligence capabilities.

**Resources:**
- `memo://insights` - Auto-updating business insights memo

**Tools:**
- `read_query` - Execute SELECT queries
- `write_query` - Execute INSERT/UPDATE/DELETE queries
- `create_table` - Create new tables
- `list_tables` - List all database tables
- `describe_table` - View table schema
- `append_insight` - Add business insights to memo

### 9. Google Sheets Robotics Server (`robo_club_server.py`)
Custom integration for robotics club management.

**Features:**
- Robotics club data management
- Google Sheets integration
- Automated reporting and tracking

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    MCP Client Agent                      │
│              (LangChain + LangGraph + Groq)             │
└──────────────────────┬──────────────────────────────────┘
                       │
                       │ STDIO Transport
                       │
       ┌───────────────┴───────────────┐
       │                               │
       ▼                               ▼
┌─────────────┐                 ┌─────────────┐
│   Weather   │                 │    Math     │
│   Server    │                 │   Server    │
└─────────────┘                 └─────────────┘
       ▼                               ▼
┌─────────────┐                 ┌─────────────┐
│    Gmail    │                 │   Search    │
│   Server    │                 │   Server    │
└─────────────┘                 └─────────────┘
       ▼                               ▼
┌─────────────┐                 ┌─────────────┐
│   Google    │                 │  OpenStreet │
│  Workspace  │                 │     Map     │
└─────────────┘                 └─────────────┘
       ▼                               ▼
┌─────────────┐                 ┌─────────────┐
│   GitHub    │                 │   SQLite    │
│   Server    │                 │   Server    │
└─────────────┘                 └─────────────┘
       ▼
┌─────────────┐
│   Robotics  │
│   Server    │
└─────────────┘
```

## 🛠️ Installation

### Prerequisites

- Python 3.8+
- pip package manager
- API keys for various services (see Configuration)

### Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/mcp-servers.git
cd mcp-servers

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Dependencies

Create a `requirements.txt` file with:

```txt
langchain-mcp-adapters
langgraph
langchain-groq
python-dotenv
asyncio
requests
google-auth
google-auth-oauthlib
google-auth-httplib2
google-api-python-client
PyGithub
```

## ⚙️ Configuration

Create a `.env` file in the project root:

```env
# Groq API (Required)
GROQ_API_KEY=your_groq_api_key_here

# Weather API
WEATHER_API_KEY=your_weather_api_key

# Gmail API
GMAIL_CLIENT_ID=your_gmail_client_id
GMAIL_CLIENT_SECRET=your_gmail_client_secret

# Google Drive & Calendar
GOOGLE_DRIVE_CREDENTIALS=path_to_credentials.json

# Google Maps API
GOOGLE_MAPS_API_KEY=your_maps_api_key

# GitHub Token
GITHUB_TOKEN=your_github_personal_access_token

# SQLite Database
SQLITE_DB_PATH=./data/database.db
```

### Getting API Keys

1. **Groq API**: Sign up at [console.groq.com](https://console.groq.com)
2. **Google Services**: Create project at [console.cloud.google.com](https://console.cloud.google.com)
3. **GitHub**: Generate token at [github.com/settings/tokens](https://github.com/settings/tokens)
4. **Weather API**: Sign up at your preferred weather API provider

## 🚀 Usage

### Starting the Agent

```bash
python client.py
```

### Interactive Commands

The agent provides an interactive CLI where you can ask questions or give commands:

```
You: What's the weather in New York?
AI Response: The current temperature in New York is 72°F with partly cloudy skies...

You: Calculate 25 * 4 + 10
AI Response: The result is 110

You: Search for information about quantum computing
AI Response: Here's what I found about quantum computing...

You: Send an email to john@example.com with subject "Meeting Tomorrow"
AI Response: Email sent successfully to john@example.com

You: Create a calendar event for team meeting tomorrow at 2 PM
AI Response: Calendar event created successfully...

You: Search GitHub for React projects
AI Response: Here are the top React repositories...
```

### Exit Commands

Type any of these to exit:
- `bye`
- `exit`
- `quit`

Or press `Ctrl+C` for keyboard interrupt.

## 🔧 Client Configuration

The MCP client is configured in `client.py` with the following server mappings:

| Server Name | Script | Transport | Purpose |
|-------------|--------|-----------|---------|
| math | calculation_server.py | stdio | Mathematical calculations |
| Weather_server | WEATHER.py | stdio | Weather information |
| gmail-mcp-server | gmail_server.py | stdio | Gmail operations |
| search_tools | search_server.py | stdio | Web & knowledge search |
| google-workspace | drive_calander_server.py | stdio | Drive & Calendar |
| openstreetmap | map_server.py | stdio | Maps & location |
| github | github_server.py | stdio | GitHub operations |
| sqlite-db | sql_server.py | stdio | Database operations |
| google-sheets-robotics | robo_club_server.py | stdio | Robotics club data |

## 🤖 Agent Capabilities

The LangGraph ReAct agent can:

- **Understand Context**: Maintains conversation history
- **Tool Selection**: Automatically chooses appropriate tools
- **Multi-Step Reasoning**: Plans and executes complex workflows
- **Error Recovery**: Handles failures gracefully
- **Parallel Operations**: Executes multiple operations when possible

### Example Workflows

**Complex Task Example:**
```
You: Get the weather in San Francisco, search for Python tutorials, 
     and create a calendar event for studying tomorrow at 3 PM

Agent Process:
1. Calls weather server for San Francisco weather
2. Calls search server for Python tutorials
3. Calls calendar server to create event
4. Combines all results in coherent response
```

## 📚 Code Structure

```
mcp-servers/
├── client.py                    # Main agent client
├── calculation_server.py        # Math server
├── WEATHER.py                   # Weather server
├── gmail_server.py              # Gmail server
├── search_server.py             # Search server
├── drive_calander_server.py     # Google Workspace server
├── map_server.py                # OpenStreetMap server
├── github_server.py             # GitHub server
├── sql_server.py                # SQLite server
├── robo_club_server.py          # Robotics server
├── .env                         # Environment variables
├── requirements.txt             # Python dependencies
├── README.md                    # This file
└── docs/                        # Documentation
    ├── api/                     # API documentation
    └── examples/                # Usage examples
```

## 🔐 Authentication

### Google Services Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project
3. Enable APIs: Gmail, Drive, Calendar, Maps
4. Create OAuth 2.0 credentials
5. Download `credentials.json`
6. Place in project root

### GitHub Token Setup

1. Go to [GitHub Settings > Developer settings > Personal access tokens](https://github.com/settings/tokens)
2. Generate new token (classic)
3. Select scopes: `repo`, `user`, `workflow`
4. Copy token to `.env` file

## 🎨 Customization

### Adding New Servers

1. Create your server script (e.g., `my_server.py`)
2. Add to client configuration:

```python
"my-custom-server": {
    "command": "python",
    "args": ["my_server.py"],
    "transport": "stdio"
}
```

### Changing LLM Model

Modify in `client.py`:

```python
llm = ChatGroq(
    model="llama-3.1-70b-versatile",  # or other Groq models
    api_key=groq_api_key,
    temperature=0.7,  # adjust creativity
)
```

Available Groq models:
- `llama-3.1-8b-instant` (fast, default)
- `llama-3.1-70b-versatile` (more capable)
- `mixtral-8x7b-32768` (large context)

## 🐛 Troubleshooting

### Common Issues

**Server Connection Failed:**
```bash
# Check if server script exists
ls -la calculation_server.py

# Verify Python path
which python
```

**API Key Errors:**
```bash
# Verify .env file is loaded
python -c "from dotenv import load_dotenv; load_dotenv(); import os; print(os.getenv('GROQ_API_KEY'))"
```

**Import Errors:**
```bash
# Reinstall dependencies
pip install --upgrade -r requirements.txt
```

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Development Guidelines

- Follow PEP 8 style guide
- Add docstrings to all functions
- Include error handling
- Write tests for new features
- Update documentation

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔮 Roadmap

- [x] Multi-server MCP architecture
- [x] LangGraph ReAct agent
- [x] Google Workspace integration
- [x] GitHub operations
- [ ] Add Slack integration server
- [ ] Implement Discord bot server
- [ ] Add voice interface support
- [ ] Create web dashboard
- [ ] Add conversation memory persistence
- [ ] Implement multi-user support
- [ ] Add analytics and logging dashboard

## 📊 Performance

- **Average Response Time**: ~2-3 seconds (depending on LLM and tools)
- **Concurrent Server Support**: 9+ servers simultaneously
- **Token Efficiency**: Optimized prompts for minimal token usage

## 💬 Support

For issues, questions, or contributions:
- **GitHub Issues**: [Open an issue](https://github.com/yourusername/mcp-servers/issues)
- **Email**: your.email@example.com
- **Documentation**: [Wiki](https://github.com/yourusername/mcp-servers/wiki)

## 🙏 Acknowledgments

- [Anthropic](https://anthropic.com) - Model Context Protocol
- [LangChain](https://langchain.com) - LLM orchestration framework
- [Groq](https://groq.com) - Fast LLM inference
- Google API Python Client
- GitHub REST API
- DuckDuckGo Search API
- OpenWeather API

## 📖 Additional Resources

- [MCP Documentation](https://modelcontextprotocol.io)
- [LangChain Documentation](https://python.langchain.com)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [Groq API Documentation](https://console.groq.com/docs)

---

**Made with ❤️ for the MCP and LangChain community**

**⭐ Star this repo if you find it useful!**
