import json
from typing import Optional
from model_provider import get_provider


class CommunicationAgent:
    """Agent for communicating with users and gathering feedback."""

    def __init__(self):
        self.conversation_history = []

    def analyze_user_intent(self, message: str) -> dict:
        """Analyze user message to determine intent and extract key information."""
        provider = get_provider()

        prompt = f"""Analyze the following user message in the context of travel planning and determine the user's intent.

User message: {message}

Return a JSON object with:
- intent: one of ["new_trip", "modify_trip", "ask_question", "provide_feedback", "confirm", "reject", "unclear"]
- destination: extracted destination if mentioned (null if not)
- dates: extracted travel dates if mentioned (null if not)
- preferences: list of extracted preferences (budget, activities, etc.)
- questions: any specific questions the user is asking
- feedback: specific feedback about a previous plan (null if not applicable)

Return only valid JSON without markdown formatting."""

        try:
            response = provider.generate(prompt, "CommunicationAgent", "analyze_intent")
            return json.loads(response.content.strip())
        except (json.JSONDecodeError, Exception):
            return {
                "intent": "unclear",
                "destination": None,
                "dates": None,
                "preferences": [],
                "questions": [],
                "feedback": None
            }

    def generate_clarifying_questions(self, user_request: str, missing_info: list[str]) -> str:
        """Generate clarifying questions for missing information."""
        provider = get_provider()

        prompt = f"""You are a friendly travel assistant. The user wants to plan a trip but some information is missing.

User request: {user_request}
Missing information: {', '.join(missing_info)}

Generate friendly, conversational questions to gather the missing information. Be concise and helpful.
Ask 2-3 questions maximum to avoid overwhelming the user."""

        try:
            response = provider.generate(prompt, "CommunicationAgent", "clarifying_questions")
            return response.content
        except Exception:
            return f"Could you please provide more details about your trip? Specifically: {', '.join(missing_info)}"

    def format_response(self, content: str, response_type: str = "general") -> str:
        """Format the response for user presentation."""
        provider = get_provider()

        prompt = f"""You are a friendly travel assistant. Format the following content for a chat conversation.
Make it conversational, engaging, and easy to read.

Content type: {response_type}
Content:
{content}

Guidelines:
- Use a warm, helpful tone
- Break up long text into readable paragraphs
- Highlight key information
- Keep it concise but informative
- If it's an itinerary, make sure it's well-structured
- End with an invitation for feedback or questions"""

        try:
            response = provider.generate(prompt, "CommunicationAgent", "format_response")
            return response.content
        except Exception:
            return content

    def summarize_trip(self, itinerary: str) -> str:
        """Create a brief summary of the trip plan."""
        provider = get_provider()

        prompt = f"""Create a brief, engaging summary of this travel itinerary in 3-4 sentences.
Highlight the destination, duration, and key highlights.

Itinerary:
{itinerary}"""

        try:
            response = provider.generate(prompt, "CommunicationAgent", "summarize_trip")
            return response.content
        except Exception:
            return itinerary[:500] + "..."

    def run(self, message: str, context: Optional[str] = None) -> str:
        """Process user message and generate appropriate response."""
        provider = get_provider()

        self.conversation_history.append({"role": "user", "content": message})

        history_text = "\n".join([
            f"{msg['role'].upper()}: {msg['content']}"
            for msg in self.conversation_history[-10:]
        ])

        prompt = f"""You are a friendly and knowledgeable travel assistant. Your role is to help users plan their perfect trip.

## Conversation History:
{history_text}

## Additional Context:
{context if context else "No additional context"}

## Instructions:
1. Respond naturally and helpfully to the user's message
2. If they're starting a new trip, gather necessary information (destination, dates, budget, preferences)
3. If they have questions, answer them based on the context provided
4. If they provide feedback, acknowledge it and explain how it will be incorporated
5. Always be encouraging and helpful
6. Keep responses concise but informative

Generate your response:"""

        try:
            response = provider.generate(prompt, "CommunicationAgent", "generate_response")
            assistant_response = response.content
            self.conversation_history.append({"role": "assistant", "content": assistant_response})
            return assistant_response
        except Exception as e:
            return f"I apologize, but I encountered an error. Please try again. Error: {str(e)}"

    def reset_conversation(self):
        """Reset the conversation history."""
        self.conversation_history = []
