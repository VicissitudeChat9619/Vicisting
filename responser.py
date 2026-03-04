from ollama import chat
from ollama import ChatResponse


# 或者直接访问响应对象的字段
# print(response.message.content)
def ai_response(question: str):
    response: ChatResponse = chat(
        model="deepseek-v3.1:671b-cloud",
        messages=[
            {
                "role": "user",
                "content": question,
            },
        ],
    )
    return response["message"]["content"]
