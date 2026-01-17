# test_direct_v2.py
from dashscope import Generation
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path("src/config/.env"))

response = Generation.call(
    model="qwen-plus",
    messages=[{"role": "user", "content": "你好"}],  # ← 关键改动
    enable_search=False,
    result_format="message",
    api_key=os.getenv("DASHSCOPE_API_KEY")
)

print("✅ code:", response.code)
print("✅ content:", response.output.choices[0].message.content)