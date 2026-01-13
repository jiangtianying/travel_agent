import os
import sys
from typing import Optional
from contextlib import asynccontextmanager

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from agents import trace
from travel_agents import SearchAgent, PlannerAgent, CommunicationAgent
from model_provider import (
    get_current_model,
    set_current_model,
    get_available_models,
    get_model_key_from_display,
    AVAILABLE_MODELS,
)

load_dotenv()


# Request/Response models
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = "default"


class ChatResponse(BaseModel):
    response: str
    session_id: str


class ModelChangeRequest(BaseModel):
    model_display_name: str


class ModelChangeResponse(BaseModel):
    status: str
    current_model: str


class ModelsResponse(BaseModel):
    models: list[str]
    current_model: str


# Session storage for conversation state
class SessionManager:
    def __init__(self):
        self.sessions: dict[str, "TravelAgentSession"] = {}

    def get_session(self, session_id: str) -> "TravelAgentSession":
        if session_id not in self.sessions:
            self.sessions[session_id] = TravelAgentSession()
        return self.sessions[session_id]

    def reset_session(self, session_id: str):
        if session_id in self.sessions:
            del self.sessions[session_id]


class TravelAgentSession:
    """Per-session travel agent state."""

    def __init__(self):
        self.search_agent = SearchAgent()
        self.planner_agent = PlannerAgent()
        self.communication_agent = CommunicationAgent()
        self.current_state = "greeting"
        self.user_request = ""
        self.search_results = ""
        self.current_itinerary = ""
        self.conversation_history = []

    def process_message(self, user_message: str) -> str:
        """Process user message and return response."""
        with trace("travel_agent"):
            self.conversation_history.append({"role": "user", "content": user_message})

            # Pass conversation context to intent analysis
            context_for_intent = ""
            if self.current_itinerary:
                context_for_intent = f"User already has an itinerary being planned. Current state: {self.current_state}"

            intent = self.communication_agent.analyze_user_intent(
                f"{user_message}\n\n[Context: {context_for_intent}]" if context_for_intent else user_message
            )
            intent_type = intent.get("intent", "unclear")

            if intent_type == "new_trip" or self.current_state == "greeting":
                return self._handle_new_trip(user_message, intent)
            elif intent_type == "modify_trip" or intent_type == "provide_feedback":
                return self._handle_modification(user_message, intent)
            elif intent_type == "ask_question":
                return self._handle_question(user_message, intent)
            elif intent_type == "confirm":
                return self._handle_confirmation()
            elif intent_type == "reject":
                return self._handle_rejection(user_message)
            else:
                # If unclear but we have an existing itinerary in review, treat as modification
                if self.current_itinerary and self.current_state == "reviewing":
                    return self._handle_modification(user_message, {"feedback": user_message})
                return self._handle_general(user_message)

    def _handle_new_trip(self, user_message: str, intent: dict) -> str:
        self.user_request = user_message
        self.current_state = "searching"

        missing_info = []
        if not intent.get("destination"):
            missing_info.append("destination")
        if not intent.get("dates"):
            missing_info.append("travel dates")

        if missing_info and self.current_state == "greeting":
            self.current_state = "gathering_info"
            questions = self.communication_agent.generate_clarifying_questions(
                user_message, missing_info
            )
            response = f"I'd love to help you plan your trip! {questions}"
            self.conversation_history.append({"role": "assistant", "content": response})
            return response

        response = "Let me search for the best options for your trip...\n\n"
        self.search_results = self.search_agent.run(user_message)

        self.current_state = "planning"
        response += "Found some great options! Now creating your personalized itinerary...\n\n"

        self.current_itinerary = self.planner_agent.run(user_message, self.search_results)
        self.current_state = "reviewing"

        final_response = self.communication_agent.format_response(
            self.current_itinerary, "itinerary"
        )
        final_response += "\n\nWould you like me to modify anything in this plan?"

        self.conversation_history.append({"role": "assistant", "content": final_response})
        return final_response

    def _handle_modification(self, user_message: str, intent: dict) -> str:
        if not self.current_itinerary:
            return self._handle_new_trip(user_message, intent)

        self.current_state = "modifying"
        feedback = intent.get("feedback") or user_message

        self.current_itinerary = self.planner_agent.optimize_itinerary(
            self.current_itinerary, feedback, self.conversation_history
        )
        self.current_state = "reviewing"

        response = self.communication_agent.format_response(
            self.current_itinerary, "itinerary"
        )
        response += "\n\nI've updated the itinerary based on your feedback. What do you think?"

        self.conversation_history.append({"role": "assistant", "content": response})
        return response

    def _handle_question(self, user_message: str, intent: dict) -> str:
        context = f"""
Current itinerary: {self.current_itinerary if self.current_itinerary else 'No itinerary created yet'}
Search results: {self.search_results if self.search_results else 'No searches performed yet'}
"""
        response = self.communication_agent.run(user_message, context)
        self.conversation_history.append({"role": "assistant", "content": response})
        return response

    def _handle_confirmation(self) -> str:
        if self.current_itinerary:
            summary = self.communication_agent.summarize_trip(self.current_itinerary)
            response = f"Excellent! Your trip is all set!\n\n{summary}\n\n"
            response += "Have a wonderful trip!"
        else:
            response = "Great! What trip would you like to plan?"

        self.conversation_history.append({"role": "assistant", "content": response})
        return response

    def _handle_rejection(self, user_message: str) -> str:
        response = "I understand. Let me know what specific changes you'd like to make."
        self.conversation_history.append({"role": "assistant", "content": response})
        return response

    def _handle_general(self, user_message: str) -> str:
        # Build comprehensive context including conversation history
        history_summary = "\n".join([
            f"{msg['role'].upper()}: {msg['content'][:200]}..."
            for msg in self.conversation_history[-6:]
        ]) if self.conversation_history else "No previous messages"

        context = f"""
Current state: {self.current_state}
Current itinerary: {self.current_itinerary if self.current_itinerary else 'None'}
Recent conversation:
{history_summary}
"""
        response = self.communication_agent.run(user_message, context)
        self.conversation_history.append({"role": "assistant", "content": response})
        return response


# Initialize session manager
session_manager = SessionManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting Travel Agent API...")
    yield
    # Shutdown
    print("Shutting down Travel Agent API...")


# Create FastAPI app
app = FastAPI(
    title="Travel Agent API",
    description="AI-powered travel planning assistant",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "Travel Agent API", "version": "1.0.0"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Send a message to the travel agent."""
    try:
        session = session_manager.get_session(request.session_id)
        response = session.process_message(request.message)
        return ChatResponse(response=response, session_id=request.session_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/reset")
async def reset_session(session_id: str = "default"):
    """Reset a chat session."""
    session_manager.reset_session(session_id)
    return {"status": "success", "message": "Session reset"}


@app.get("/api/models", response_model=ModelsResponse)
async def get_models():
    """Get available models."""
    current = get_current_model()
    return ModelsResponse(
        models=get_available_models(),
        current_model=AVAILABLE_MODELS[current]["display_name"],
    )


@app.post("/api/models", response_model=ModelChangeResponse)
async def change_model(request: ModelChangeRequest):
    """Change the current model."""
    try:
        model_key = get_model_key_from_display(request.model_display_name)
        set_current_model(model_key)
        return ModelChangeResponse(
            status="success",
            current_model=request.model_display_name,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
