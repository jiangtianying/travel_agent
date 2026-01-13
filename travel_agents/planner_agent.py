from model_provider import get_provider


class PlannerAgent:
    """Agent for creating and optimizing travel itineraries based on search results."""

    def run(self, user_request: str, search_results: str) -> str:
        """Create an optimized travel itinerary based on search results."""
        provider = get_provider()

        prompt = f"""You are an expert travel planner. Based on the user's request and the search results provided, create a detailed and optimized travel itinerary.

## User Request:
{user_request}

## Search Results:
{search_results}

## Instructions:
1. Create a day-by-day itinerary that is practical and well-organized
2. Include recommended flights and hotels based on the search results
3. Suggest the best attractions to visit each day with timing recommendations
4. Include restaurant recommendations for meals
5. Consider travel time between locations
6. Provide estimated costs where possible
7. Add practical tips for each destination

Format the itinerary in a clear, readable format with:
- Overview of the trip
- Day-by-day schedule
- Accommodation recommendations
- Transportation suggestions
- Budget estimate
- Important tips and notes

Be specific and actionable in your recommendations."""

        try:
            response = provider.generate(prompt, "PlannerAgent", "create_itinerary")
            return response.content
        except Exception as e:
            return f"Error generating itinerary: {str(e)}"

    def optimize_itinerary(self, current_itinerary: str, feedback: str, conversation_history: list = None) -> str:
        """Optimize an existing itinerary based on user feedback."""
        provider = get_provider()

        # Build conversation context
        history_context = ""
        if conversation_history:
            recent_history = conversation_history[-10:]  # Last 10 messages
            history_context = "\n".join([
                f"{msg['role'].upper()}: {msg['content'][:500]}"
                for msg in recent_history
            ])

        prompt = f"""You are an expert travel planner. The user has provided feedback on their current itinerary. Please optimize and update the itinerary based on their feedback.

## Conversation History:
{history_context if history_context else "No previous conversation"}

## Current Itinerary:
{current_itinerary}

## User Feedback:
{feedback}

## Instructions:
1. Address all points mentioned in the user's feedback
2. Consider the context from the conversation history
3. Maintain the overall structure while incorporating changes
4. Ensure the updated itinerary is still practical and well-organized
5. Explain what changes you made and why

Provide the updated itinerary in the same format as before."""

        try:
            response = provider.generate(prompt, "PlannerAgent", "optimize_itinerary")
            return response.content
        except Exception as e:
            return f"Error optimizing itinerary: {str(e)}"

    def suggest_alternatives(self, itinerary: str, constraints: str) -> str:
        """Suggest alternatives based on constraints like budget, time, or preferences."""
        provider = get_provider()

        prompt = f"""You are an expert travel planner. Based on the current itinerary and the user's constraints, suggest alternative options.

## Current Itinerary:
{itinerary}

## User Constraints:
{constraints}

## Instructions:
1. Identify areas where alternatives could better meet the constraints
2. Provide 2-3 alternative options for each suggestion
3. Explain the trade-offs of each alternative
4. Provide a revised itinerary incorporating the best alternatives

Be practical and consider the user's constraints carefully."""

        try:
            response = provider.generate(prompt, "PlannerAgent", "suggest_alternatives")
            return response.content
        except Exception as e:
            return f"Error suggesting alternatives: {str(e)}"
