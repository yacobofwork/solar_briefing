import os
from dotenv import load_dotenv

print("当前工作目录：", os.getcwd())

load_dotenv(dotenv_path=".env")

print("DEEPSEEK_API_KEY =", os.getenv("DEEPSEEK_API_KEY"))