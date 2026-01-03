import os

BASE_DIR = os.path.dirname(__file__)
prompt_path = os.path.join(BASE_DIR, "prompts", "analyze_price_impact.txt")

print("BASE_DIR =", BASE_DIR)
print("Prompt path =", prompt_path)
print("Exists? ", os.path.exists(prompt_path))

print("\nListing prompts directory:")
prompts_dir = os.path.join(BASE_DIR, "prompts")
if os.path.exists(prompts_dir):
    print(os.listdir(prompts_dir))
else:
    print("prompts directory does NOT exist")