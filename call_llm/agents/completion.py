from dataclasses import dataclass
from typing import Union, List, Dict, Optional
import re
import openai

@dataclass
class Completion:
    """
    A class representing a combined OpenAI ChatCompletion response, for both stream and non-stream modes.
    """
    id: str
    object: str  # "chat.completion"
    created: int
    model: str
    choices: List[Dict]
    usage: Optional[Dict]
    reasoning: Optional[str]
    is_stream: bool

    @classmethod
    def from_non_stream(cls, response: openai.types.chat.ChatCompletion, full_content: str) -> 'Completion':
        """
        Create a Completion from a non-stream ChatCompletion response.
        
        Args:
            response: OpenAI ChatCompletion response object
            full_content: The full response text to parse for reasoning
        
        Returns:
            Completion: A Completion object with non-stream data
        """
        reasoning, final_answer = cls._parse_response(full_content)
        return cls(
            id=response.id,
            object="chat.completion",
            created=response.created,
            model=response.model,
            choices=[
                {
                    "index": choice.index,
                    "message": {
                        "role": choice.message.role,
                        "content": final_answer.strip()
                    },
                    "finish_reason": choice.finish_reason
                } for choice in response.choices
            ],
            usage={
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            },
            reasoning=reasoning,
            is_stream=False
        )

    @classmethod
    def from_stream(cls, chunks: List[openai.types.chat.ChatCompletionChunk], full_content: str, model: str) -> 'Completion':
        """
        Create a Completion from a list of stream ChatCompletionChunk objects.
        
        Args:
            chunks: List of OpenAI ChatCompletionChunk objects
            full_content: Combined content from all chunks
            model: Model name used for the request
        
        Returns:
            Completion: A Completion object with combined stream data
        """
        if not chunks:
            return cls(
                id="", object="chat.completion", created=int(time()), model=model,
                choices=[], usage=None, reasoning=None, is_stream=True
            )

        reasoning, final_answer = cls._parse_response(full_content)
        first_chunk = chunks[0]
        # Estimate usage (rough word-based counting)
        prompt_tokens = 0  # Could estimate from input, but not provided here
        completion_words = len(full_content.split())
        completion_tokens = int(completion_words * 1.3)  # Rough estimate: words to tokens
        total_tokens = prompt_tokens + completion_tokens

        return cls(
            id=first_chunk.id,
            object="chat.completion",
            created=first_chunk.created,
            model=first_chunk.model,
            choices=[
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": final_answer.strip()
                    },
                    "finish_reason": chunks[-1].choices[0].finish_reason or "stop"
                }
            ],
            usage={
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens
            },
            reasoning=reasoning,
            is_stream=True
        )

    @staticmethod
    def _parse_response(content: str) -> tuple[Optional[str], str]:
        """
        Parse the response to separate reasoning and final answer.
        
        Args:
            content: The full response text
        
        Returns:
            tuple: (reasoning, final_answer)
        """
        reasoning_match = re.search(r'\[Reasoning\](.*?)\[Final Answer\]', content, re.DOTALL)
        final_answer_match = re.search(r'\[Final Answer\](.*)', content, re.DOTALL)

        if reasoning_match and final_answer_match:
            reasoning = reasoning_match.group(1).strip()
            final_answer = final_answer_match.group(1).strip()
        else:
            reasoning = None
            final_answer = content.strip()

        return reasoning, final_answer