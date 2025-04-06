import os
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from openai import OpenAI
from dotenv import load_dotenv
import asyncio
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

load_dotenv(os.path.join(os.getcwd(), ".env"))

class ChatRequest(BaseModel):
    message: str
    model: str = "gpt-3.5-turbo"  # default model
    temperature: float = 0.7

async def stream_openai_response(message: str, model: str, temperature: float):
    """
    Generator function to stream OpenAI chat completion responses
    """
    try:

        client = OpenAI(
            # 若没有配置环境变量，请用百炼API Key将下行替换为：api_key="sk-xxx",
            api_key=os.environ.get('AliLLM'),  # 如何获取API Key：https://help.aliyun.com/zh/model-studio/developer-reference/get-api-key
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
        )

        reasoning_content = ""  # 定义完整思考过程
        answer_content = ""     # 定义完整回复
        is_answering = False   # 判断是否结束思考过程并开始回复

        # 创建聊天完成请求
        stream = client.chat.completions.create(
            model="deepseek-r1",  # 此处以 deepseek-r1 为例，可按需更换模型名称
            messages=[
                {"role": "user", "content": "9.9和9.11谁大"}
            ],
            stream=True,
            # 解除以下注释会在最后一个chunk返回Token使用量
            # stream_options={
            #     "include_usage": True
            # }
        )


        for chunk in stream:
            # 如果chunk.choices为空，则打印usage
            if not chunk.choices:
                print("\nUsage:")
                print(chunk.usage)
            else:
                delta = chunk.choices[0].delta
                # 打印思考过程
                if hasattr(delta, 'reasoning_content') and delta.reasoning_content != None:
                    print(delta.reasoning_content, end='', flush=True)
                    yield delta.reasoning_content
                else:
                    # 开始回复
                    if delta.content != "" and is_answering == False:
                        print("\n" + "=" * 20 + "完整回复" + "=" * 20 + "\n")
                        is_answering = True
                    # 打印回复过程
                    print(delta.content, end='', flush=True)
                    yield delta.content


    except Exception as e:
        yield f"Error: {str(e)}"

@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    Endpoint that streams GPT responses
    """
    async def event_generator():
        async for chunk in stream_openai_response(
            request.message,
            request.model,
            request.temperature
        ):
            yield chunk

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )

# # Example regular endpoint for comparison
# @app.post("/chat")
# async def chat_regular(request: ChatRequest):
#     """
#     Regular non-streaming endpoint
#     """
#     response = openai.ChatCompletion.create(
#         model=request.model,
#         messages=[{"role": "user", "content": request.message}],
#         temperature=request.temperature
#     )
#     return {"response": response.choices[0].message.content}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)