# Travel Agent AI - Application Flow

## Architecture Overview

```mermaid
flowchart TB
    subgraph Frontend["Frontend (React + TypeScript)"]
        UI[Chat Interface]
        MS[Model Selector]
        API_Client[API Client]
    end

    subgraph Backend["Backend (FastAPI)"]
        API[REST API Endpoints]
        SM[Session Manager]

        subgraph Session["Travel Agent Session"]
            CH[Conversation History]
            State[Session State]
            Itinerary[Current Itinerary]
        end
    end

    subgraph Agents["AI Agents"]
        CA[Communication Agent]
        SA[Search Agent]
        PA[Planner Agent]
    end

    subgraph External["External Services"]
        MP[Model Provider]
        OpenAI[OpenAI API]
        Gemini[Gemini API]
        Serper[Serper Web Search]
    end

    UI --> API_Client
    MS --> API_Client
    API_Client <--> API
    API <--> SM
    SM <--> Session

    Session --> CA
    Session --> SA
    Session --> PA

    CA --> MP
    SA --> MP
    SA --> Serper
    PA --> MP

    MP --> OpenAI
    MP --> Gemini
```

## Message Processing Flow

```mermaid
flowchart TD
    Start([User Sends Message]) --> Store[Store in Conversation History]
    Store --> Analyze[Communication Agent: Analyze Intent]

    Analyze --> Intent{Intent Type?}

    Intent -->|new_trip| NewTrip[Handle New Trip]
    Intent -->|modify_trip| Modify[Handle Modification]
    Intent -->|ask_question| Question[Handle Question]
    Intent -->|confirm| Confirm[Handle Confirmation]
    Intent -->|reject| Reject[Handle Rejection]
    Intent -->|unclear| Check{Has Itinerary?}

    Check -->|Yes, in review| Modify
    Check -->|No| General[Handle General]

    NewTrip --> Search[Search Agent: Web Search]
    Search --> Plan[Planner Agent: Create Itinerary]
    Plan --> Format[Communication Agent: Format Response]

    Modify --> Optimize[Planner Agent: Optimize with History]
    Optimize --> Format

    Question --> Answer[Communication Agent: Answer with Context]
    Answer --> Response

    Confirm --> Summary[Communication Agent: Summarize Trip]
    Summary --> Response

    Reject --> Response[Return Response to User]
    General --> Response
    Format --> Response

    Response --> Display([Display in Chat])
```

## Agent Responsibilities

```mermaid
flowchart LR
    subgraph Communication["Communication Agent"]
        C1[Analyze User Intent]
        C2[Generate Clarifying Questions]
        C3[Format Responses]
        C4[Summarize Trips]
        C5[Answer Questions]
    end

    subgraph Search["Search Agent"]
        S1[Search Flights]
        S2[Search Hotels]
        S3[Search Attractions]
        S4[Search Restaurants]
    end

    subgraph Planner["Planner Agent"]
        P1[Create Itinerary]
        P2[Optimize Itinerary]
        P3[Suggest Alternatives]
    end
```

## Session State Machine

```mermaid
stateDiagram-v2
    [*] --> greeting: Session Created

    greeting --> searching: New Trip Request
    greeting --> gathering_info: Missing Info

    gathering_info --> searching: Info Provided

    searching --> planning: Search Complete

    planning --> reviewing: Itinerary Created

    reviewing --> modifying: User Feedback
    reviewing --> [*]: User Confirms

    modifying --> reviewing: Update Complete
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

## Data Flow Example

```
User: "Plan a 5-day trip to Paris in April"
         │
         ▼
┌─────────────────────────────────────────┐
│  Communication Agent: Analyze Intent     │
│  → intent: "new_trip"                    │
│  → destination: "Paris"                  │
│  → dates: "April, 5 days"               │
└─────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│  Search Agent: Web Search                │
│  → Flights to Paris                      │
│  → Hotels in Paris                       │
│  → Attractions in Paris                  │
│  → Restaurants in Paris                  │
└─────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│  Planner Agent: Create Itinerary         │
│  → Day-by-day schedule                   │
│  → Hotel recommendations                 │
│  → Activity planning                     │
│  → Budget estimates                      │
└─────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│  Communication Agent: Format Response    │
│  → Friendly, readable format             │
│  → Invitation for feedback               │
└─────────────────────────────────────────┘
         │
         ▼
    Response to User
```

## Technology Stack

```
┌────────────────────────────────────────────────────────┐
│                    FRONTEND                             │
│  React + TypeScript + Vite                             │
│  • Chat Interface                                       │
│  • Model Selection                                      │
│  • Markdown Rendering                                   │
└────────────────────────────────────────────────────────┘
                          │
                          │ HTTP/REST
                          ▼
┌────────────────────────────────────────────────────────┐
│                    BACKEND                              │
│  FastAPI + Python                                       │
│  • Session Management                                   │
│  • Agent Orchestration                                  │
│  • OpenAI Agents SDK Tracing                           │
└────────────────────────────────────────────────────────┘
                          │
              ┌───────────┼───────────┐
              ▼           ▼           ▼
        ┌─────────┐ ┌─────────┐ ┌─────────┐
        │ OpenAI  │ │ Gemini  │ │ Serper  │
        │   API   │ │   API   │ │   API   │
        └─────────┘ └─────────┘ └─────────┘
```
