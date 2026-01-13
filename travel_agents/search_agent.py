import os
import json
import requests
from typing import Optional
from model_provider import get_provider


class SearchAgent:
    """Agent for searching flight tickets, hotels, and travel information using Serper API."""

    def __init__(self):
        self.serper_api_key = os.getenv("SERPER_API_KEY")

    def search_web(self, query: str, num_results: int = 10) -> list[dict]:
        """Search the web using Serper API."""
        if not self.serper_api_key:
            return [{"error": "SERPER_API_KEY not configured"}]

        url = "https://google.serper.dev/search"
        headers = {
            "X-API-KEY": self.serper_api_key,
            "Content-Type": "application/json"
        }
        payload = {
            "q": query,
            "num": num_results
        }

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            data = response.json()

            results = []
            for item in data.get("organic", []):
                results.append({
                    "title": item.get("title", ""),
                    "link": item.get("link", ""),
                    "snippet": item.get("snippet", "")
                })
            return results
        except requests.RequestException as e:
            return [{"error": f"Search failed: {str(e)}"}]

    def search_flights(self, origin: str, destination: str, date: str, return_date: Optional[str] = None) -> dict:
        """Search for flight information."""
        query = f"cheapest flights from {origin} to {destination} on {date}"
        if return_date:
            query += f" return {return_date}"
        query += " prices booking"

        results = self.search_web(query)
        return {
            "type": "flights",
            "origin": origin,
            "destination": destination,
            "date": date,
            "return_date": return_date,
            "results": results
        }

    def search_hotels(self, destination: str, checkin: str, checkout: str) -> dict:
        """Search for hotel information."""
        query = f"best hotels in {destination} checkin {checkin} checkout {checkout} prices booking"

        results = self.search_web(query)
        return {
            "type": "hotels",
            "destination": destination,
            "checkin": checkin,
            "checkout": checkout,
            "results": results
        }

    def search_attractions(self, destination: str) -> dict:
        """Search for tourist attractions and activities."""
        query = f"top tourist attractions things to do in {destination}"

        results = self.search_web(query)
        return {
            "type": "attractions",
            "destination": destination,
            "results": results
        }

    def search_restaurants(self, destination: str) -> dict:
        """Search for restaurant recommendations."""
        query = f"best restaurants to eat in {destination} local food recommendations"

        results = self.search_web(query)
        return {
            "type": "restaurants",
            "destination": destination,
            "results": results
        }

    def run(self, user_request: str) -> str:
        """Process user request and perform relevant searches."""
        provider = get_provider()

        prompt = f"""You are a travel search assistant. Analyze the following user request and extract search parameters.

User request: {user_request}

Extract the following information in JSON format:
- origin: departure city/location (if mentioned)
- destination: destination city/location
- departure_date: travel start date (if mentioned)
- return_date: return date (if mentioned)
- checkin: hotel check-in date (if mentioned)
- checkout: hotel check-out date (if mentioned)
- search_types: list of what to search for (flights, hotels, attractions, restaurants)

If information is not provided, set it to null.
Return only valid JSON without markdown formatting."""

        try:
            response = provider.generate(prompt, "SearchAgent", "extract_search_params")
            params = json.loads(response.content.strip())
        except (json.JSONDecodeError, Exception):
            params = {
                "destination": user_request,
                "search_types": ["attractions", "restaurants"]
            }

        all_results = {}
        search_types = params.get("search_types", [])

        if "flights" in search_types and params.get("origin") and params.get("destination"):
            all_results["flights"] = self.search_flights(
                params["origin"],
                params["destination"],
                params.get("departure_date", "flexible"),
                params.get("return_date")
            )

        if "hotels" in search_types and params.get("destination"):
            all_results["hotels"] = self.search_hotels(
                params["destination"],
                params.get("checkin", "flexible"),
                params.get("checkout", "flexible")
            )

        if "attractions" in search_types and params.get("destination"):
            all_results["attractions"] = self.search_attractions(params["destination"])

        if "restaurants" in search_types and params.get("destination"):
            all_results["restaurants"] = self.search_restaurants(params["destination"])

        return json.dumps(all_results, indent=2)
