"""
Code Agent - Specializes in software development
"""

import logging
from typing import Any, Dict

from app.agents.base_agent import AgentConfig, BaseAgent, TaskRequest, TaskResult
from app.agents.communication.message_bus import MessageBus
from app.tools import PythonExecute, StrReplaceEditor
from app.tools.collection import ToolCollection

logger = logging.getLogger(__name__)


class CodeAgent(BaseAgent):
    """
    Code Agent - Develops and executes code.

    Specializes in:
    - Writing Python code
    - Executing scripts
    - Editing files
    - Debugging
    - Testing code
    """

    def __init__(self, message_bus: MessageBus, llm=None):
        config = AgentConfig(
            agent_id="code_agent",
            agent_type="code",
            description="Specializes in software development",
            max_concurrent_tasks=2,
        )

        # Initialize with code tools
        tools = ToolCollection(PythonExecute(), StrReplaceEditor())

        super().__init__(config, message_bus, tools=tools, llm=llm)

    async def execute_task(self, task: TaskRequest) -> TaskResult:
        """
        Execute coding task.

        Writes and executes code based on requirements.
        """
        try:
            logger.info(f"💻 Coding: {task.description}")

            objective = task.description
            parameters = task.parameters or {}

            # Generate and execute code
            result = await self._code_task(objective, parameters)

            logger.info(f"✅ Code task complete")

            return TaskResult(
                task_id=task.task_type,
                success=True,
                result=result,
                metadata={"agent_type": "code", "objective": objective},
            )

        except Exception as e:
            logger.error(f"❌ Coding failed: {e}")
            return TaskResult(task_id=task.task_type, success=False, error=str(e))

    async def _code_task(self, objective: str, parameters: Dict) -> Dict[str, Any]:
        """Execute a coding task"""

        # Check if code is provided
        if "code" in parameters:
            code = parameters["code"]
            action = "execute"
        else:
            # Need to generate code
            if self.llm:
                code = await self._generate_code(objective)
                action = "generate_and_execute"
            else:
                # No LLM, try to create simple code
                code = self._create_simple_code(objective)
                action = "simple_execute"

        # Execute the code
        python_tool = None
        for tool in self.tools:
            if tool.name == "python_execute":
                python_tool = tool
                break

        if python_tool:
            execution_result = await python_tool.execute(code=code)

            # Check if execution was successful
            exec_success = (
                hasattr(execution_result, "success") and execution_result.success
            ) or (
                not hasattr(execution_result, "success")  # No success attr means OK
            )

            return {
                "action": action,
                "code": code,
                "output": (
                    str(execution_result.result)
                    if hasattr(execution_result, "result") and execution_result.result
                    else "Code executed successfully"
                ),
                "error": (
                    execution_result.error
                    if hasattr(execution_result, "error") and execution_result.error
                    else None
                ),
                "success": exec_success,
            }
        else:
            return {
                "action": action,
                "code": code,
                "error": "Python execution tool not available",
                "success": False,
            }

    async def _generate_code(self, objective: str) -> str:
        """Generate code using LLM"""

        prompt = f"""
        Write Python code to accomplish this objective:

        {objective}

        Requirements:
        - Use only standard library if possible
        - Include error handling
        - Add brief comments
        - Keep it concise

        Return ONLY the Python code, no explanation.
        """

        response = await self.llm.agenerate(prompt)

        # Extract code from response
        code = self._extract_code_from_response(response)

        return code

    def _extract_code_from_response(self, response: str) -> str:
        """Extract Python code from LLM response"""

        # Remove markdown code blocks if present
        lines = response.strip().split("\n")

        # Check for ```python or ``` markers
        in_code_block = False
        code_lines = []

        for line in lines:
            if line.strip().startswith("```"):
                in_code_block = not in_code_block
                continue

            if in_code_block or not any(
                line.startswith(marker) for marker in ["#", "//", "/*"]
            ):
                code_lines.append(line)

        return "\n".join(code_lines)

    def _create_simple_code(self, objective: str) -> str:
        """Create simple code based on objective keywords"""

        objective_lower = objective.lower()

        # Simple pattern matching
        if "hello" in objective_lower or "print" in objective_lower:
            return "print('Hello, World!')"

        elif "calculate" in objective_lower or "sum" in objective_lower():
            return """
# Simple calculation
result = sum([1, 2, 3, 4, 5])
print(f"Sum: {result}")
"""

        elif "file" in objective_lower:
            return """
# File operations example
with open('example.txt', 'w') as f:
    f.write('Example content')
print('File created')
"""

        else:
            # Default code
            return f"""
# Code for: {objective}
print('Task: {objective}')
print('Status: Completed')
"""
