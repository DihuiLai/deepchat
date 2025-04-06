from openai import OpenAI
from typing import List
import os
from dotenv import load_dotenv
load_dotenv(os.path.join(os.getcwd(), ".env"))

# Set your OpenAI API key (you'll need to get this from OpenAI)
client = OpenAI(
            # 若没有配置环境变量，请用百炼API Key将下行替换为：api_key="sk-xxx",
            api_key=os.environ.get('AliLLM'),  # 如何获取API Key：https://help.aliyun.com/zh/model-studio/developer-reference/get-api-key
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
        )


class ConversationAgent:
    def __init__(self, model="deepseek-r1"):
        """Initialize the conversation agent with a specified model"""
        self.model = model
        self.messages: List[dict] = [
            {"role": "system", "content": "You are a helpful AI assistant created by xAI. "
                                        "Maintain a friendly tone and provide useful responses."}
        ]

    def add_message(self, role: str, content: str):
        """Add a message to the conversation history"""
        self.messages.append({"role": role, "content": content})

    def get_response(self, user_input: str) -> str:
        """Get a response from the AI based on the conversation history"""
        # Add user's message to the conversation
        self.add_message("user", user_input)

        try:
            reasoning_content = ""  # 定义完整思考过程
            answer_content = ""     # 定义完整回复
            is_answering = False   # 判断是否结束思考过程并开始回复

            # 创建聊天完成请求
            stream = client.chat.completions.create(
                model="deepseek-r1",  # 此处以 deepseek-r1 为例，可按需更换模型名称
                messages=self.messages,
                stream=True,
                # 解除以下注释会在最后一个chunk返回Token使用量
                # stream_options={
                #     "include_usage": True
                # }
            )
            # Make API call to OpenAI

            for chunk in stream:
                # 如果chunk.choices为空，则打印usage
                if not chunk.choices:
                    print("\nUsage:")
                    print(chunk.usage)
                else:
                    delta = chunk.choices[0].delta
                    # 打印思考过程
                    if hasattr(delta, 'reasoning_content') and delta.reasoning_content != None:
                        #print(delta.reasoning_content, end='', flush=True)
                        reasoning_content += delta.reasoning_content
                        yield delta.reasoning_content
                    else:
                        # 开始回复
                        if delta.content != "" and is_answering == False:
                            is_answering = True
                        # 打印回复过程
                        #print(delta.content, end='', flush=True)
                        answer_content += delta.content
                        yield delta.content


            # Get the AI's response
            ai_response ={'final': {'answer': answer_content, 'reasoning':reasoning_content}}
            
            # Add AI's response to conversation history
            self.add_message("assistant", answer_content)
            
            yield ai_response

        except Exception as e:
            return f"Sorry, I encountered an error: {str(e)}"

    def clear_conversation(self):
        """Reset the conversation history, keeping only the system prompt"""
        self.messages = [self.messages[0]]


if __name__ == "__main__":
    # Make sure you have your OPENAI_API_KEY set in your environment
    # You can set it in terminal: export OPENAI_API_KEY='your-api-key-here'
    agent = ConversationAgent()
    stremresonse = agent.get_response("法国的首都是哪里？")
    for i in stremresonse:
        if isinstance(i, dict) and 'final' in i:
            print("\n" + "=" * 20 + "完整回复" + "=" * 20 + "\n")
            print('final answer:', i['final']['answer'])
        else:
            print(i)
    
    print("Welcome! I'm your AI assistant. Type 'quit' to exit or 'clear' to reset the conversation.")
    