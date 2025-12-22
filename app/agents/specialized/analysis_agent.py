"""
Analysis Agent - Specializes in data analysis
"""

import logging
from typing import Any, Dict, List

from app.agents.base_agent import AgentConfig, BaseAgent, TaskRequest, TaskResult
from app.agents.communication.message_bus import MessageBus
from app.tools import PythonExecute
from app.tools.collection import ToolCollection

logger = logging.getLogger(__name__)


class AnalysisAgent(BaseAgent):
    """
    Analysis Agent - Analyzes data and generates insights.

    Specializes in:
    - Data analysis
    - Statistical computations
    - Pattern recognition
    - Generating insights
    - Creating summaries
    """

    def __init__(self, message_bus: MessageBus, llm=None):
        config = AgentConfig(
            agent_id="analysis_agent",
            agent_type="analysis",
            description="Specializes in data analysis and insights",
            max_concurrent_tasks=2,
        )

        # Initialize with analysis tools
        tools = ToolCollection(PythonExecute())

        super().__init__(config, message_bus, tools=tools, llm=llm)

    async def execute_task(self, task: TaskRequest) -> TaskResult:
        """
        Execute analysis task.

        Analyzes data and generates insights.
        """
        try:
            logger.info(f"📊 Analyzing: {task.description}")

            objective = task.description
            parameters = task.parameters or {}

            # Perform analysis
            analysis = await self._analyze(objective, parameters)

            logger.info(f"✅ Analysis complete")

            return TaskResult(
                task_id=task.task_type,
                success=True,
                result=analysis,
                metadata={"agent_type": "analysis", "objective": objective},
            )

        except Exception as e:
            logger.error(f"❌ Analysis failed: {e}")
            return TaskResult(task_id=task.task_type, success=False, error=str(e))

    async def _analyze(self, objective: str, parameters: Dict) -> Dict[str, Any]:
        """Perform data analysis"""

        data = parameters.get("data", [])
        analysis_type = parameters.get("type", "general")

        if not data:
            # No data provided, create sample analysis
            return {
                "type": "no_data",
                "message": "No data provided for analysis",
                "recommendation": "Provide data in parameters['data']",
            }

        # Perform analysis based on type
        if analysis_type == "statistics":
            result = self._statistical_analysis(data)
        elif analysis_type == "trends":
            result = self._trend_analysis(data)
        else:
            result = self._general_analysis(data)

        # Add insights using LLM if available
        if self.llm:
            insights = await self._generate_insights(objective, result)
            result["ai_insights"] = insights

        return result

    def _statistical_analysis(self, data: List) -> Dict[str, Any]:
        """Perform statistical analysis"""

        if not data:
            return {"error": "No data"}

        # Convert to numbers if possible
        try:
            numbers = [float(x) for x in data]
        except (ValueError, TypeError):
            return {"error": "Data must be numeric for statistics"}

        # Calculate basic statistics
        count = len(numbers)
        total = sum(numbers)
        mean = total / count if count > 0 else 0

        sorted_data = sorted(numbers)
        median = sorted_data[count // 2] if count > 0 else 0

        min_val = min(numbers) if numbers else 0
        max_val = max(numbers) if numbers else 0

        return {
            "type": "statistics",
            "count": count,
            "sum": total,
            "mean": mean,
            "median": median,
            "min": min_val,
            "max": max_val,
            "range": max_val - min_val,
        }

    def _trend_analysis(self, data: List) -> Dict[str, Any]:
        """Analyze trends in data"""

        if len(data) < 2:
            return {"error": "Need at least 2 data points for trend"}

        try:
            numbers = [float(x) for x in data]
        except (ValueError, TypeError):
            return {"error": "Data must be numeric for trend analysis"}

        # Simple trend detection
        increasing = sum(
            1 for i in range(1, len(numbers)) if numbers[i] > numbers[i - 1]
        )
        decreasing = sum(
            1 for i in range(1, len(numbers)) if numbers[i] < numbers[i - 1]
        )

        if increasing > decreasing:
            trend = "increasing"
        elif decreasing > increasing:
            trend = "decreasing"
        else:
            trend = "stable"

        # Calculate change
        change = numbers[-1] - numbers[0]
        change_percent = (change / numbers[0] * 100) if numbers[0] != 0 else 0

        return {
            "type": "trend",
            "trend": trend,
            "change": change,
            "change_percent": change_percent,
            "data_points": len(numbers),
        }

    def _general_analysis(self, data: Any) -> Dict[str, Any]:
        """General data analysis"""

        # Analyze data structure
        data_type = type(data).__name__

        if isinstance(data, (list, tuple)):
            length = len(data)
            item_types = set(type(x).__name__ for x in data)

            return {
                "type": "general",
                "data_type": data_type,
                "length": length,
                "item_types": list(item_types),
                "sample": data[:5] if len(data) > 5 else data,
            }

        elif isinstance(data, dict):
            return {
                "type": "general",
                "data_type": data_type,
                "keys": list(data.keys()),
                "num_keys": len(data),
            }

        else:
            return {"type": "general", "data_type": data_type, "value": str(data)[:200]}

    async def _generate_insights(self, objective: str, analysis: Dict) -> str:
        """Generate insights using LLM"""

        prompt = f"""
        Analyze this data and provide insights:

        Objective: {objective}
        Analysis: {analysis}

        Provide 2-3 key insights or recommendations.
        Be concise and actionable.
        """

        insights = await self.llm.agenerate(prompt)

        return insights
