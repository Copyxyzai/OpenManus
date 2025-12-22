"""
Validation Agent - Specializes in quality checks and validation
"""

import logging
from typing import Any, Dict, List

from app.agents.base_agent import AgentConfig, BaseAgent, TaskRequest, TaskResult
from app.agents.communication.message import ValidationRequest, ValidationResult
from app.agents.communication.message_bus import MessageBus
from app.tools import PythonExecute
from app.tools.collection import ToolCollection

logger = logging.getLogger(__name__)


class ValidationAgent(BaseAgent):
    """
    Validation Agent - Validates results and ensures quality.

    Specializes in:
    - Code validation
    - Data validation
    - Quality checks
    - Testing
    - Error detection
    """

    def __init__(self, message_bus: MessageBus, llm=None):
        config = AgentConfig(
            agent_id="validation_agent",
            agent_type="validation",
            description="Specializes in quality checks and validation",
            max_concurrent_tasks=3,
        )

        # Initialize with validation tools
        tools = ToolCollection(PythonExecute())

        super().__init__(config, message_bus, tools=tools, llm=llm)

    async def execute_task(self, task: TaskRequest) -> TaskResult:
        """
        Execute validation task.

        Validates provided content and returns assessment.
        """
        try:
            logger.info(f"✅ Validating: {task.description}")

            parameters = task.parameters or {}

            # Perform validation
            validation = await self._validate(task.description, parameters)

            logger.info(
                f"{'✅' if validation['is_valid'] else '❌'} "
                f"Validation complete (confidence: {validation['confidence']:.0%})"
            )

            return TaskResult(
                task_id=task.task_type,
                success=True,
                result=validation,
                metadata={
                    "agent_type": "validation",
                    "is_valid": validation["is_valid"],
                    "confidence": validation["confidence"],
                },
            )

        except Exception as e:
            logger.error(f"❌ Validation failed: {e}")
            return TaskResult(task_id=task.task_type, success=False, error=str(e))

    async def _validate(self, description: str, parameters: Dict) -> Dict[str, Any]:
        """Perform validation"""

        target_type = parameters.get("target_type", "general")
        target = parameters.get("target")
        criteria = parameters.get("criteria", {})

        # Route to appropriate validation method
        if target_type == "code":
            result = await self._validate_code(target, criteria)
        elif target_type == "data":
            result = self._validate_data(target, criteria)
        elif target_type == "result":
            result = self._validate_result(target, criteria)
        else:
            result = self._validate_general(target, criteria)

        return result

    async def _validate_code(self, code: str, criteria: Dict) -> Dict[str, Any]:
        """Validate Python code"""

        if not code:
            return {
                "is_valid": False,
                "confidence": 1.0,
                "issues": ["No code provided"],
                "suggestions": ["Provide code to validate"],
            }

        issues = []
        suggestions = []

        # Check syntax
        try:
            compile(code, "<string>", "exec")
            syntax_valid = True
        except SyntaxError as e:
            syntax_valid = False
            issues.append(f"Syntax error: {e}")
            suggestions.append("Fix syntax errors")

        # Check for common issues
        if "import os" in code and "os.system" in code:
            issues.append("Security: os.system() detected")
            suggestions.append("Use subprocess instead of os.system")

        if len(code.split("\n")) > 100:
            issues.append("Code is very long (>100 lines)")
            suggestions.append("Consider breaking into functions")

        # Try to execute (if syntax is valid)
        execution_result = None
        if syntax_valid and criteria.get("test_execution", False):
            python_tool = next(
                (t for t in self.tools if t.name == "python_execute"), None
            )
            if python_tool:
                try:
                    exec_result = await python_tool.execute(code=code)
                    if hasattr(exec_result, "success") and not exec_result.success:
                        issues.append(
                            f"Execution error: {getattr(exec_result, 'error', 'Unknown')}"
                        )
                except Exception as e:
                    issues.append(f"Execution failed: {e}")

        # Calculate confidence
        if not issues:
            confidence = 0.95
            is_valid = True
        elif len(issues) == 1 and "very long" in issues[0]:
            confidence = 0.75
            is_valid = True
        else:
            confidence = 0.3
            is_valid = False

        return {
            "is_valid": is_valid,
            "confidence": confidence,
            "issues": issues,
            "suggestions": suggestions,
            "target_type": "code",
        }

    def _validate_data(self, data: Any, criteria: Dict) -> Dict[str, Any]:
        """Validate data"""

        issues = []
        suggestions = []

        required_type = criteria.get("type")
        min_length = criteria.get("min_length")
        max_length = criteria.get("max_length")

        # Check type
        if required_type and type(data).__name__ != required_type:
            issues.append(f"Expected {required_type}, got {type(data).__name__}")
            suggestions.append(f"Convert data to {required_type}")

        # Check length
        if hasattr(data, "__len__"):
            length = len(data)
            if min_length and length < min_length:
                issues.append(f"Data too short: {length} < {min_length}")
            if max_length and length > max_length:
                issues.append(f"Data too long: {length} > {max_length}")

        # Check for None/empty
        if data is None:
            issues.append("Data is None")
            suggestions.append("Provide valid data")
        elif hasattr(data, "__len__") and len(data) == 0:
            issues.append("Data is empty")
            suggestions.append("Add data elements")

        is_valid = len(issues) == 0
        confidence = 0.9 if is_valid else 0.4

        return {
            "is_valid": is_valid,
            "confidence": confidence,
            "issues": issues,
            "suggestions": suggestions,
            "target_type": "data",
        }

    def _validate_result(self, result: Any, criteria: Dict) -> Dict[str, Any]:
        """Validate a result/output"""

        issues = []
        suggestions = []

        # Check if result exists
        if result is None:
            issues.append("Result is None")
            suggestions.append("Ensure task produced a result")

        # Check expected keys (if dict)
        if isinstance(result, dict):
            required_keys = criteria.get("required_keys", [])
            missing_keys = [k for k in required_keys if k not in result]
            if missing_keys:
                issues.append(f"Missing required keys: {missing_keys}")
                suggestions.append(f"Add keys: {missing_keys}")

        # Check for errors
        if isinstance(result, dict) and "error" in result:
            issues.append(f"Result contains error: {result['error']}")
            suggestions.append("Fix the error before proceeding")

        is_valid = len(issues) == 0
        confidence = 0.85 if is_valid else 0.5

        return {
            "is_valid": is_valid,
            "confidence": confidence,
            "issues": issues,
            "suggestions": suggestions,
            "target_type": "result",
        }

    def _validate_general(self, target: Any, criteria: Dict) -> Dict[str, Any]:
        """General validation"""

        is_valid = target is not None and target != ""
        confidence = 0.7 if is_valid else 0.3

        issues = [] if is_valid else ["Target is None or empty"]
        suggestions = [] if is_valid else ["Provide valid target for validation"]

        return {
            "is_valid": is_valid,
            "confidence": confidence,
            "issues": issues,
            "suggestions": suggestions,
            "target_type": "general",
        }
