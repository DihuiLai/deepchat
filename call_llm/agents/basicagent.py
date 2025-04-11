import openai
import os
from typing import Union, Generator, List, Dict
import sys
from agents.completion import Completion
from dotenv import load_dotenv
load_dotenv(os.path.join("/Users/dlai/Projects/deepchat/", ".env"))
# Set up OpenAI API key

client = openai.OpenAI(api_key=os.getenv("AliLLM"), base_url="https://dashscope.aliyuncs.com/compatible-mode/v1")

if not client.api_key:
    raise ValueError("Please set the OPENAI_API_KEY environment variable.")

class BasicAgent:
    def __init__(self, model: str = "deepseek-r1", temperature: float = 0.7):
        """
        Initialize the AI Agent with conversation history.
        
        Args:
            model (str): The OpenAI model to use (e.g., 'gpt-4o-mini', 'gpt-4o').
            temperature (float): Controls randomness in responses (0.0 to 1.0).
        """
        self.model = model
        self.temperature = temperature
        self.history: List[Dict[str, str]] = []

    def get_response(self, prompt: str, stream: bool = False) -> Union[str, Generator[str, None, None]]:
        """
        Get a response from the OpenAI API in stream or non-stream mode, using conversation history.
        
        Args:
            prompt (str): The user's input prompt.
            stream (bool): Whether to stream the response (True) or return it all at once (False).
        
        Returns:
            str or Generator: The complete response text (non-stream) or a generator yielding chunks (stream).
        """
        # Append user prompt to history
        self.history.append({"role": "user", "content": prompt})

        try:
            if stream:
                return self._stream_response()
            else:
                return self._non_stream_response()
        except openai.OpenAIError as e:
            print(f"Error communicating with OpenAI API: {e}")
            self.history.pop()  # Remove the failed prompt from history
            return "" if not stream else iter([])

    def _non_stream_response(self) -> str:
        """
        Get a complete response from the OpenAI API (non-streaming) with conversation history.
        
        Returns:
            str: The complete response text.
        """
        # Prepare messages: system prompt + history
        messages = [
            {"role": "system", "content": "You are a helpful AI assistant."}
        ] + self.history

        response = client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature
        )
        response_text = response.choices[0].message.content.strip()
        completion = Completion.from_non_stream(response, response_text)        # Append assistant response to history
        self.history.append({"role": "assistant", "content": response_text})
        return completion

    def _stream_response(self) -> Generator[str, None, None]:
        """
        Stream the response from the OpenAI API, yielding chunks of content with conversation history.
        
        Returns:
            Generator: Yields response chunks as they arrive.
        """
        # Prepare messages: system prompt + history
        messages = [
            {"role": "system", "content": "You are a helpful AI assistant."}
        ] + self.history

        stream = client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            stream=True
        )
        
        full_response = ""
        chunks = []
        for chunk in stream:
            content = chunk.choices[0].delta.content
            if content:
                full_response += content
                yield content
            chunks.append(chunk)
        # Append the complete assistant response to history
        self.history.append({"role": "assistant", "content": full_response})
        completion = Completion.from_stream(chunks, full_response, self.model)
        yield completion

    def clear_history(self):
        """
        Clear the conversation history.
        """
        self.history = []


if __name__ == "__main__":
# Initialize the AI agent
    agent = BasicAgent(model="qwen-plus")
    prompt='法国首都在哪里？'
    # Get and display the response
    stream=True
    response = agent.get_response(prompt, stream=stream)


if stream:
    print("AI (streaming): ", end="", flush=True)
    full_response = ""
    for chunk in response:
        print(chunk, end="", flush=True)
        if isinstance(chunk, str):
            print(chunk)
        else:
            res=chunk
    print()  # Newline after streaming
else:
    print("\nAI:")
    print(response)