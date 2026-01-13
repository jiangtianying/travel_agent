# Travel Agent AI

An AI-powered travel planning assistant that helps you create personalized travel itineraries using multiple intelligent agents.

## Features

- **Production-Ready Architecture**: FastAPI backend with React frontend
- **Multi-Model Support**: Switch between OpenAI GPT-4o-mini and Gemini 2.0 Flash
- **OpenAI Agents SDK Tracing**: View agent traces in the OpenAI Traces Dashboard under workflow "travel_agent"
- **Multi-Agent Architecture**: Three specialized AI agents working together:
  - **Search Agent**: Searches for flights, hotels, attractions, and restaurants using Serper API
  - **Planner Agent**: Creates and optimizes detailed travel itineraries
  - **Communication Agent**: Handles user interaction and gathers feedback
- **Real-time Web Search**: Gets up-to-date travel information from the web
- **Iterative Planning**: Refine your itinerary based on feedback
- **Session Management**: Support for multiple concurrent users

## Prerequisites

- Python 3.12+
- Node.js 18+ (for frontend)
- [UV](https://github.com/astral-sh/uv) package manager
- OpenAI API key (from [OpenAI Platform](https://platform.openai.com/))
- Gemini API key (optional, from [Google AI Studio](https://aistudio.google.com/app/apikey))
- Serper API key (from [Serper.dev](https://serper.dev/))

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd travel_agent
   ```

2. Install Python dependencies using UV:
   ```bash
   uv sync
   ```

3. Install frontend dependencies:
   ```bash
   cd frontend
   npm install
   cd ..
   ```

4. Create your environment file:
   ```bash
   cp .env.example .env
   ```

5. Edit `.env` and add your API keys:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   GEMINI_API_KEY=your_gemini_api_key_here
   SERPER_API_KEY=your_serper_api_key_here
   ```

## Usage

### Running the Full Stack

1. Start the backend server:
   ```bash
   uv run python server/api.py
   ```
   The API will be available at `http://localhost:8000`

2. In a separate terminal, start the frontend:
   ```bash
   cd frontend
   npm run dev
   ```
   The app will be available at `http://localhost:5173`

### Running the Gradio Interface (Legacy)

For quick testing with the simpler Gradio interface:
```bash
uv run python main.py
```
The app will start at `http://localhost:7860`

### Example Prompts

- "I want to plan a 7-day trip to Paris in April with a budget of $2000"
- "Help me find the cheapest flights from New York to London for next month"
- "I'm looking for a romantic getaway in Italy for 5 days"
- "Plan a family vacation to Orlando, Florida with kids-friendly activities"

## Project Structure

```
travel_agent/
├── server/
│   └── api.py               # FastAPI REST API backend
├── frontend/
│   ├── src/
│   │   ├── App.tsx          # React chat interface
│   │   ├── api.ts           # API client
│   │   └── types.ts         # TypeScript interfaces
│   └── package.json
├── travel_agents/
│   ├── __init__.py
│   ├── search_agent.py      # Web search for travel info
│   ├── planner_agent.py     # Itinerary creation and optimization
│   └── communication_agent.py # User interaction handling
├── backend.py               # Agent orchestration (Gradio backend)
├── main.py                  # Gradio frontend (legacy)
├── model_provider.py        # Multi-model provider with tracing
├── .env.example             # Environment template
├── pyproject.toml           # Project dependencies
└── README.md
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | API info |
| `/health` | GET | Health check |
| `/api/chat` | POST | Send message to travel agent |
| `/api/reset` | POST | Reset chat session |
| `/api/models` | GET | Get available models |
| `/api/models` | POST | Change current model |

## How It Works

1. **User Input**: You describe your travel needs in natural language
2. **Intent Analysis**: The Communication Agent analyzes your request
3. **Web Search**: The Search Agent queries the web for flights, hotels, and attractions
4. **Itinerary Generation**: The Planner Agent creates a detailed day-by-day plan
5. **Feedback Loop**: You can request modifications, and the agents will refine the plan

## Tracing

Agent traces are sent to the OpenAI Traces Dashboard under the workflow "travel_agent". View your traces at:
https://platform.openai.com/traces

## Configuration

- **Default Model**: OpenAI GPT-4o-mini
- **Alternative Model**: Gemini 2.0 Flash (requires GEMINI_API_KEY)

You can switch models using the dropdown in the UI.

## License

MIT
