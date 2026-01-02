"""Gemini API client wrapper using the new google.genai SDK."""

from typing import Optional, Generator, Any
from google import genai
from google.genai import types
from pathlib import Path


class GeminiClient:
    """Gemini API client with support for text, vision, and long context."""

    def __init__(
        self,
        api_key: str,
        model: str = "gemini-2.0-flash-exp",
    ):
        """
        Initialize Gemini client.

        Args:
            api_key: Gemini API key
            model: Model name (gemini-2.0-flash-exp, gemini-1.5-pro, etc.)
        """
        self.api_key = api_key
        self.model_name = model
        
        self.client = genai.Client(api_key=api_key)
        self._chat_session = None
        self._system_instruction = None

    def generate(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 8192,
    ) -> str:
        """
        Generate text response.

        Args:
            prompt: User prompt
            system_instruction: Optional system instruction
            temperature: Sampling temperature
            max_tokens: Maximum output tokens

        Returns:
            Generated text response
        """
        config = types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
            system_instruction=system_instruction,
        )

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=config,
        )
        return response.text

    def generate_stream(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 8192,
    ) -> Generator[str, None, None]:
        """
        Generate text response with streaming.

        Args:
            prompt: User prompt
            system_instruction: Optional system instruction
            temperature: Sampling temperature
            max_tokens: Maximum output tokens

        Yields:
            Text chunks as they are generated
        """
        config = types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
            system_instruction=system_instruction,
        )

        for chunk in self.client.models.generate_content_stream(
            model=self.model_name,
            contents=prompt,
            config=config,
        ):
            if chunk.text:
                yield chunk.text

    def analyze_image(
        self,
        image_path: str,
        prompt: str,
        temperature: float = 0.7,
    ) -> str:
        """
        Analyze an image with Gemini Vision.

        Args:
            image_path: Path to the image file
            prompt: Analysis prompt
            temperature: Sampling temperature

        Returns:
            Analysis result text
        """
        from pathlib import Path
        
        image_path = Path(image_path)
        with open(image_path, "rb") as f:
            image_bytes = f.read()
        
        # Determine mime type
        suffix = image_path.suffix.lower()
        mime_types = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".gif": "image/gif",
            ".webp": "image/webp",
        }
        mime_type = mime_types.get(suffix, "image/png")
        
        return self.analyze_image_bytes(image_bytes, mime_type, prompt, temperature)

    def analyze_image_bytes(
        self,
        image_bytes: bytes,
        mime_type: str,
        prompt: str,
        temperature: float = 0.7,
    ) -> str:
        """
        Analyze image from bytes with Gemini Vision.

        Args:
            image_bytes: Image data as bytes
            mime_type: MIME type (e.g., "image/png")
            prompt: Analysis prompt
            temperature: Sampling temperature

        Returns:
            Analysis result text
        """
        import base64
        
        config = types.GenerateContentConfig(
            temperature=temperature,
        )
        
        # Create image part
        image_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
        
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=[prompt, image_part],
            config=config,
        )
        return response.text

    def start_chat(
        self,
        system_instruction: Optional[str] = None,
        history: Optional[list] = None,
    ) -> None:
        """
        Start a chat session.

        Args:
            system_instruction: Optional system instruction
            history: Optional chat history
        """
        self._system_instruction = system_instruction
        
        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
        )
        
        self._chat_session = self.client.chats.create(
            model=self.model_name,
            config=config,
            history=history or [],
        )

    def chat(
        self,
        message: str,
        stream: bool = False,
    ) -> str | Generator[str, None, None]:
        """
        Send a chat message.

        Args:
            message: User message
            stream: Whether to stream the response

        Returns:
            Response text or generator for streaming
        """
        if self._chat_session is None:
            self.start_chat()

        if stream:
            def stream_gen():
                for chunk in self._chat_session.send_message_stream(message):
                    if chunk.text:
                        yield chunk.text
            return stream_gen()
        else:
            response = self._chat_session.send_message(message)
            return response.text

    def get_chat_history(self) -> list:
        """Get the current chat history."""
        if self._chat_session is None:
            return []
        return self._chat_session.get_history()

    def generate_json(
        self,
        prompt: str,
        schema: dict,
        system_instruction: Optional[str] = None,
    ) -> dict:
        """
        Generate structured JSON output.

        Args:
            prompt: User prompt
            schema: JSON schema for the output
            system_instruction: Optional system instruction

        Returns:
            Parsed JSON response
        """
        import json

        json_instruction = f"""
You must respond with valid JSON that matches this schema:
{json.dumps(schema, indent=2)}

Only output the JSON, no other text.
"""

        full_instruction = system_instruction or ""
        full_instruction += "\n\n" + json_instruction

        response = self.generate(
            prompt,
            system_instruction=full_instruction,
            temperature=0.3,
        )

        # Clean up response and parse JSON
        response = response.strip()
        if response.startswith("```json"):
            response = response[7:]
        if response.startswith("```"):
            response = response[3:]
        if response.endswith("```"):
            response = response[:-3]

        return json.loads(response.strip())

    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text.

        Args:
            text: Text to count tokens for

        Returns:
            Token count
        """
        response = self.client.models.count_tokens(
            model=self.model_name,
            contents=text,
        )
        return response.total_tokens
