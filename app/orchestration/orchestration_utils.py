"""
Orchestration utilities module
"""

from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class TaskNode:
    """Represents a task in the dependency graph"""

    id: str
    description: str
    agent_type: str
    dependencies: List[str]
    estimated_time: float


class TaskDecomposer:
    """
    Decomposes complex tasks into subtasks.

    Analyzes natural language requests and breaks them down
    into actionable subtasks.
    """

    def decompose(self, request: str) -> List[Dict[str, Any]]:
        """
        Decompose a request into subtasks.

        Args:
            request: Natural language request

        Returns:
            List of subtask descriptions
        """
        # Simple keyword-based decomposition
        # In production, use LLM for intelligent decomposition

        subtasks = []
        request_lower = request.lower()

        # Check for research keywords
        if any(
            word in request_lower
            for word in ["search", "find", "research", "look up", "information about"]
        ):
            subtasks.append(
                {
                    "type": "research",
                    "description": f"Research: {request}",
                    "estimated_time": 15.0,
                }
            )

        # Check for code keywords
        if any(
            word in request_lower
            for word in ["code", "implement", "write", "create", "develop", "program"]
        ):
            subtasks.append(
                {
                    "type": "code",
                    "description": f"Implement: {request}",
                    "estimated_time": 30.0,
                }
            )

        # Check for analysis keywords
        if any(
            word in request_lower
            for word in [
                "analyze",
                "analyse",
                "analyze",
                "metrics",
                "statistics",
                "data",
            ]
        ):
            subtasks.append(
                {
                    "type": "analysis",
                    "description": f"Analyze: {request}",
                    "estimated_time": 20.0,
                }
            )

        # Always add validation
        if subtasks:
            subtasks.append(
                {
                    "type": "validation",
                    "description": "Validate results",
                    "estimated_time": 5.0,
                }
            )

        return (
            subtasks
            if subtasks
            else [{"type": "research", "description": request, "estimated_time": 10.0}]
        )


class TaskRouter:
    """
    Routes tasks to appropriate agents.

    Determines which agent is best suited for each task type.
    """

    AGENT_CAPABILITIES = {
        "planning": ["plan", "strategy", "organize", "decompose"],
        "research": ["search", "find", "lookup", "research", "web", "information"],
        "code": ["code", "implement", "write", "develop", "program", "execute"],
        "analysis": ["analyze", "analyse", "metrics", "statistics", "data", "insights"],
        "validation": ["validate", "check", "verify", "test", "quality"],
    }

    def route(self, task_description: str) -> str:
        """
        Determine which agent should handle a task.

        Args:
            task_description: Description of the task

        Returns:
            Agent type (e.g., "research", "code", etc.)
        """
        description_lower = task_description.lower()

        # Score each agent based on keyword matches
        scores = {}
        for agent, keywords in self.AGENT_CAPABILITIES.items():
            score = sum(1 for keyword in keywords if keyword in description_lower)
            if score > 0:
                scores[agent] = score

        if not scores:
            # Default to research
            return "research"

        # Return agent with highest score
        return max(scores.items(), key=lambda x: x[1])[0]

    def route_batch(self, tasks: List[str]) -> Dict[str, str]:
        """
        Route multiple tasks.

        Args:
            tasks: List of task descriptions

        Returns:
            Dict mapping task to agent type
        """
        return {task: self.route(task) for task in tasks}


class ResultAggregator:
    """
    Aggregates results from multiple agents.

    Combines and formats results into a cohesive final output.
    """

    def aggregate(
        self, results: Dict[str, Any], format_type: str = "summary"
    ) -> Dict[str, Any]:
        """
        Aggregate results.

        Args:
            results: Dict of agent results
            format_type: "summary", "detailed", or "raw"

        Returns:
            Aggregated result
        """
        if format_type == "summary":
            return self._create_summary(results)
        elif format_type == "detailed":
            return self._create_detailed(results)
        else:
            return results

    def _create_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Create summary of results"""
        summary = {
            "total_results": len(results),
            "successful": sum(1 for r in results.values() if r.get("success", False)),
            "failed": sum(1 for r in results.values() if not r.get("success", True)),
            "key_findings": [],
        }

        # Extract key findings from each result
        for agent_type, result in results.items():
            if result.get("success"):
                finding = {
                    "agent": agent_type,
                    "result": str(result.get("result", ""))[:200],  # First 200 chars
                }
                summary["key_findings"].append(finding)

        return summary

    def _create_detailed(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Create detailed results"""
        return {
            "results_by_agent": results,
            "summary": self._create_summary(results),
            "metadata": {
                "agents_used": list(results.keys()),
                "total_agents": len(results),
            },
        }
