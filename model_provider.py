import os
from typing import Optional
from dataclasses import dataclass
from agents.tracing import custom_span


@dataclass
class ModelResponse:
    """Unified response from any model provider."""
    content: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


# Global model setting
_current_model = "gpt-4o-mini"

AVAILABLE_MODELS = {
    "gpt-4o-mini": {
        "provider": "openai",
        "model_id": "gpt-4o-mini",
        "display_name": "OpenAI GPT-4o Mini"
    },
    "gemini-2.0-flash": {
        "provider": "gemini",
        "model_id": "gemini-2.0-flash",
        "display_name": "Google Gemini 2.0 Flash (Free)"
    }
}


def get_current_model() -> str:
    """Get the current model setting."""
    return _current_model


def set_current_model(model: str):
    """Set the current model to use."""
    global _current_model
    if model in AVAILABLE_MODELS:
        _current_model = model
    else:
        raise ValueError(f"Unknown model: {model}. Available: {list(AVAILABLE_MODELS.keys())}")


def get_available_models() -> list[str]:
    """Get list of available model display names."""
    return [info["display_name"] for info in AVAILABLE_MODELS.values()]


def get_model_key_from_display(display_name: str) -> str:
    """Get model key from display name."""
    for key, info in AVAILABLE_MODELS.items():
        if info["display_name"] == display_name:
            return key
    return "gpt-4o-mini"


class ModelProvider:
    """Unified interface for different LLM providers."""

    def __init__(self):
        self._openai_client = None
        self._gemini_client = None
        self._init_clients()

    def _init_clients(self):
        """Initialize available clients."""
        # OpenAI
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            from openai import OpenAI
            self._openai_client = OpenAI(api_key=openai_key)

        # Gemini
        gemini_key = os.getenv("GEMINI_API_KEY")
        if gemini_key:
            from google import genai
            self._gemini_client = genai.Client(api_key=gemini_key)

    def generate(
        self,
        prompt: str,
        agent_name: str = "unknown",
        action_name: str = "generate"
    ) -> ModelResponse:
        """Generate a response using the current model."""
        model_key = get_current_model()
        model_info = AVAILABLE_MODELS[model_key]

        # Use OpenAI Agents SDK custom_span for tracing
        with custom_span(name=f"{agent_name}.{action_name}"):
            if model_info["provider"] == "openai":
                return self._generate_openai(prompt, model_info["model_id"])
            elif model_info["provider"] == "gemini":
                return self._generate_gemini(prompt, model_info["model_id"])
            else:
                raise ValueError(f"Unknown provider: {model_info['provider']}")

    def _generate_openai(self, prompt: str, model_id: str) -> ModelResponse:
        """Generate using OpenAI."""
        if not self._openai_client:
            raise RuntimeError("OpenAI client not initialized. Check OPENAI_API_KEY.")

        response = self._openai_client.chat.completions.create(
            model=model_id,
            messages=[{"role": "user", "content": prompt}]
        )

        usage = response.usage
        return ModelResponse(
            content=response.choices[0].message.content,
            prompt_tokens=usage.prompt_tokens,
            completion_tokens=usage.completion_tokens,
            total_tokens=usage.total_tokens
        )

    def _generate_gemini(self, prompt: str, model_id: str) -> ModelResponse:
        """Generate using Gemini."""
        if not self._gemini_client:
            raise RuntimeError("Gemini client not initialized. Check GEMINI_API_KEY.")

        response = self._gemini_client.models.generate_content(
            model=model_id,
            contents=prompt
        )

        # Gemini usage metadata
        usage = response.usage_metadata
        prompt_tokens = usage.prompt_token_count if usage else 0
        completion_tokens = usage.candidates_token_count if usage else 0
        total_tokens = usage.total_token_count if usage else 0

        return ModelResponse(
            content=response.text,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens
        )

    def is_available(self, model_key: str) -> bool:
        """Check if a model is available."""
        if model_key not in AVAILABLE_MODELS:
            return False

        provider = AVAILABLE_MODELS[model_key]["provider"]
        if provider == "openai":
            return self._openai_client is not None
        elif provider == "gemini":
            return self._gemini_client is not None
        return False


# Global provider instance
_provider: Optional[ModelProvider] = None


def get_provider() -> ModelProvider:
    """Get the global model provider instance."""
    global _provider
    if _provider is None:
        _provider = ModelProvider()
    return _provider


def reinit_provider():
    """Reinitialize the provider (call after env changes)."""
    global _provider
    _provider = ModelProvider()
