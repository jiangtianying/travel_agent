import os
from dotenv import load_dotenv
from agents import trace
from travel_agents import SearchAgent, PlannerAgent, CommunicationAgent
from model_provider import get_current_model, set_current_model, get_model_key_from_display

load_dotenv()


class TravelAgentOrchestrator:
    """Orchestrates the three AI agents to create travel plans."""

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
        """Process user message and return appropriate response."""
        # Use OpenAI Agents SDK trace for workflow tracking
        with trace("travel_agent"):
            self.conversation_history.append({"role": "user", "content": user_message})

            intent = self.communication_agent.analyze_user_intent(user_message)
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
                return self._handle_general(user_message)

    def _handle_new_trip(self, user_message: str, intent: dict) -> str:
        """Handle new trip planning request."""
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

        final_response += "\n\nWould you like me to modify anything in this plan? Feel free to share your feedback!"

        self.conversation_history.append({"role": "assistant", "content": final_response})
        return final_response

    def _handle_modification(self, user_message: str, intent: dict) -> str:
        """Handle modification requests."""
        if not self.current_itinerary:
            return self._handle_new_trip(user_message, intent)

        self.current_state = "modifying"
        feedback = intent.get("feedback") or user_message

        self.current_itinerary = self.planner_agent.optimize_itinerary(
            self.current_itinerary, feedback
        )
        self.current_state = "reviewing"

        response = self.communication_agent.format_response(
            self.current_itinerary, "itinerary"
        )
        response += "\n\nI've updated the itinerary based on your feedback. What do you think?"

        self.conversation_history.append({"role": "assistant", "content": response})
        return response

    def _handle_question(self, user_message: str, intent: dict) -> str:
        """Handle user questions."""
        context = f"""
Current itinerary: {self.current_itinerary if self.current_itinerary else 'No itinerary created yet'}
Search results: {self.search_results if self.search_results else 'No searches performed yet'}
"""
        response = self.communication_agent.run(user_message, context)
        self.conversation_history.append({"role": "assistant", "content": response})
        return response

    def _handle_confirmation(self) -> str:
        """Handle user confirmation."""
        if self.current_itinerary:
            summary = self.communication_agent.summarize_trip(self.current_itinerary)
            response = f"Excellent! Your trip is all set!\n\n{summary}\n\n"
            response += "Have a wonderful trip! Feel free to come back if you need any changes or want to plan another adventure."
        else:
            response = "Great! What trip would you like to plan?"

        self.conversation_history.append({"role": "assistant", "content": response})
        return response

    def _handle_rejection(self, user_message: str) -> str:
        """Handle user rejection or dissatisfaction."""
        response = "I understand. Let me know what specific changes you'd like to make, or if you'd prefer to start fresh with different options."
        self.conversation_history.append({"role": "assistant", "content": response})
        return response

    def _handle_general(self, user_message: str) -> str:
        """Handle general messages."""
        context = f"""
Current state: {self.current_state}
Current itinerary: {self.current_itinerary[:500] if self.current_itinerary else 'None'}
"""
        response = self.communication_agent.run(user_message, context)
        self.conversation_history.append({"role": "assistant", "content": response})
        return response

    def reset(self):
        """Reset the orchestrator state."""
        self.current_state = "greeting"
        self.user_request = ""
        self.search_results = ""
        self.current_itinerary = ""
        self.conversation_history = []
        self.communication_agent.reset_conversation()


orchestrator = TravelAgentOrchestrator()


def chat(message: str, history: list) -> str:
    """Chat function for Gradio interface."""
    return orchestrator.process_message(message)


def reset_chat():
    """Reset the chat state."""
    orchestrator.reset()
    return []


def change_model(model_display_name: str) -> str:
    """Change the current model."""
    model_key = get_model_key_from_display(model_display_name)
    set_current_model(model_key)
    return f"Model changed to: {model_display_name}"
