"""AI helpers for generating responses and classifying emotions."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Callable, Dict, Iterable, List, Optional

try:
    import nltk
except ModuleNotFoundError:  # pragma: no cover - optional dependency
    nltk = None  # type: ignore[assignment]

from .database import ConversationHistory
from .ollama import chat as ollama_chat

ChatCallable = Callable[..., object]

REQUIRED_NLTK_PACKAGES = ["stopwords", "punkt", "wordnet"]

logger = logging.getLogger(__name__)


def ensure_nltk_data(packages: Iterable[str] = REQUIRED_NLTK_PACKAGES) -> None:
    """Ensure that the NLTK tokenizers required by the bot are available."""

    if nltk is None:
        raise ModuleNotFoundError("nltk is required to download data")
    for package in packages:
        logger.debug("Ensuring NLTK package '%s' is available", package)
        nltk.download(package)


class EmotionClassifier:
    """Wrap the Transformers pipeline used for emotion detection."""

    def __init__(
        self,
        pipeline_factory: Optional[Callable[[], Callable[..., List[Dict[str, float]]]]] = None,
        model: str = "bhadresh-savani/distilbert-base-uncased-finetuned-emotion",
    ) -> None:
        self.model = model
        self._pipeline_factory = pipeline_factory or self._default_pipeline_factory
        self._pipeline: Optional[Callable[..., List[Dict[str, float]]]] = None
        logger.debug("EmotionClassifier initialised with model '%s'", self.model)

    def _default_pipeline_factory(self) -> Callable[..., List[Dict[str, float]]]:
        from transformers import pipeline

        logger.debug("Creating default transformers pipeline for model '%s'", self.model)
        return pipeline(
            "text-classification",
            model=self.model,
            top_k=1,
        )

    def _get_pipeline(self) -> Callable[..., List[Dict[str, float]]]:
        if self._pipeline is None:
            logger.debug("Initialising emotion classification pipeline")
            self._pipeline = self._pipeline_factory()
        return self._pipeline

    def predict(self, text: str) -> Dict[str, float | str]:
        """Return the most likely emotion for *text*."""

        pipeline = self._get_pipeline()
        logger.debug("Running emotion prediction for text length %d", len(text))
        predictions = pipeline(text, truncation=True, max_length=512)
        if not predictions:
            raise ValueError("The classifier returned no predictions")
        result = predictions[0]
        if isinstance(result, list):
            result = result[0]
        if not isinstance(result, dict):
            raise TypeError("Unexpected classifier result format")
        return {"label": result["label"], "score": float(result["score"])}


@dataclass
class AiResponder:
    """Generate responses for the bot using the Ollama chat API."""

    history: ConversationHistory
    model: str = "llama3.2"
    chat_callable: Optional[ChatCallable] = None

    def __post_init__(self) -> None:
        if self.chat_callable is None:
            logger.debug("No chat callable supplied; using Ollama default implementation")
            self.chat_callable = ollama_chat

    def query(self, prompt: str, user_id: str, user_name: str, config: Dict[str, str]) -> str:
        """Send *prompt* to the chat model and persist the conversation."""

        user_key = str(user_id)
        logger.info("Querying AI responder for user %s", user_key)
        conversation = self.history.get_conversation(user_key)
        if not conversation:
            system_prompt = config.get(
                "SYSTEM_PROMPT",
                "You are an anime waifu named Gwen.",
            )
            logger.debug("Initialising conversation history with system prompt for user %s", user_key)
            self.history.add_message(user_key, "system", system_prompt)
            conversation = self.history.get_conversation(user_key)

        self.history.add_message(user_key, "user", prompt)
        self.history.prune_conversation(user_key)
        conversation = self.history.get_conversation(user_key)

        logger.debug("Sending chat request to model '%s' with %d messages", self.model, len(conversation))
        chat_response = self.chat_callable(model=self.model, messages=[msg.__dict__ for msg in conversation])
        response_text = self._extract_content(chat_response)

        self.history.add_message(user_key, "assistant", response_text)
        self.history.prune_conversation(user_key)
        logger.debug("Stored assistant response for user %s", user_key)
        return response_text

    @staticmethod
    def _extract_content(chat_response: object) -> str:
        """Extract the assistant text content from *chat_response*."""

        if isinstance(chat_response, str):
            logger.debug("Chat response received as raw string")
            return chat_response
        if hasattr(chat_response, "message") and hasattr(chat_response.message, "content"):
            logger.debug("Chat response received as object with message.content")
            return chat_response.message.content
        if isinstance(chat_response, dict) and "message" in chat_response:
            message = chat_response["message"]
            if isinstance(message, dict) and "content" in message:
                logger.debug("Chat response received as dictionary with nested content")
                return message["content"]
        raise TypeError("Unable to extract assistant response from chat response")
