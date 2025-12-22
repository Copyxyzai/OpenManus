import os

from app.tools.ai.memory import MemoryTool

print("Instantiating MemoryTool...")
tool = MemoryTool()
print("MemoryTool instantiated.")
path = "workspace/memory/memory.json"
if os.path.exists(os.path.dirname(path)):
    print(f"Directory {os.path.dirname(path)} created successfully.")
else:
    print(f"Directory {os.path.dirname(path)} NOT found.")
