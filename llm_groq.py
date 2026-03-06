import json
import os
from typing import Any, Dict, List, Optional

from groq import Groq

DEFAULT_SYSTEM = "You are an expert technical recruiter and interviewer for IT roles. Be precise and structured."

class GroqLLM:
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or os.environ.get("GROQ_API_KEY")
        if not self.api_key:
            raise RuntimeError("GROQ_API_KEY is missing. Add it to your .env file or environment variables.")
        self.model = model or os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")
        self.client = Groq(api_key=self.api_key)

    def chat_text(self, messages: List[Dict[str, str]], temperature: float = 0.2, max_tokens: int = 1200) -> str:
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_completion_tokens=max_tokens,
        )
        return resp.choices[0].message.content or ""

    def chat_json(self, messages: List[Dict[str, str]], temperature: float = 0.1, max_tokens: int = 1600) -> Dict[str, Any]:
        # Use Groq "JSON mode" to get parseable JSON.
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_completion_tokens=max_tokens,
            response_format={"type": "json_object"},
        )
        content = resp.choices[0].message.content or "{}"
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            # fallback: try to salvage JSON if model included stray text
            start = content.find("{")
            end = content.rfind("}")
            if start != -1 and end != -1 and end > start:
                return json.loads(content[start : end + 1])
            raise
