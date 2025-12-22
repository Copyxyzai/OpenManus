"""
Planning Agent - Specializes in creating action plans and strategies
"""

import logging
from dataclasses import dataclass
from typing import Any, Dict, List

from app.agents.base_agent import AgentConfig, BaseAgent, TaskRequest, TaskResult
from app.agents.communication.message_bus import MessageBus

logger = logging.getLogger(__name__)


@dataclass
class PlanStep:
    """A step in an action plan"""

    step_number: int
    description: str
    agent_type: str  # Which agent should execute this
    dependencies: List[int]  # Which steps must complete first
    estimated_time: float  # Estimated time in seconds


@dataclass
class ActionPlan:
    """A complete action plan"""

    goal: str
    steps: List[PlanStep]
    total_estimated_time: float
    parallel_opportunities: List[List[int]]  # Steps that can run in parallel


class PlanningAgent(BaseAgent):
    """
    Planning Agent - Creates detailed action plans.

    Specializes in:
    - Analyzing complex requests
    - Breaking down into subtasks
    - Identifying dependencies
    - Creating execution strategies
    - Estimating resource requirements
    """

    def __init__(self, message_bus: MessageBus, llm=None):
        config = AgentConfig(
            agent_id="planning_agent",
            agent_type="planning",
            description="Specializes in creating action plans and strategies",
            max_concurrent_tasks=2,
        )
        super().__init__(config, message_bus, llm=llm)

    async def execute_task(self, task: TaskRequest) -> TaskResult:
        """
        Execute planning task.

        Analyzes the request and creates a detailed action plan.
        """
        try:
            logger.info(f"📋 Planning: {task.description}")

            # Extract the goal from task
            goal = task.description
            parameters = task.parameters or {}

            # Create action plan
            plan = await self._create_plan(goal, parameters)

            logger.info(
                f"✅ Created plan with {len(plan.steps)} steps "
                f"(est. {plan.total_estimated_time:.0f}s)"
            )

            return TaskResult(
                task_id=task.task_type,
                success=True,
                result={
                    "plan": self._plan_to_dict(plan),
                    "summary": self._create_summary(plan),
                },
                metadata={
                    "agent_type": "planning",
                    "steps_count": len(plan.steps),
                    "estimated_time": plan.total_estimated_time,
                },
            )

        except Exception as e:
            logger.error(f"❌ Planning failed: {e}")
            return TaskResult(task_id=task.task_type, success=False, error=str(e))

    async def _create_plan(self, goal: str, parameters: Dict) -> ActionPlan:
        """Create an action plan using LLM"""

        # If LLM is available, use it for intelligent planning
        if self.llm:
            plan = await self._create_plan_with_llm(goal, parameters)
        else:
            # Fallback to rule-based planning
            plan = self._create_simple_plan(goal, parameters)

        return plan

    async def _create_plan_with_llm(self, goal: str, parameters: Dict) -> ActionPlan:
        """Use LLM to create intelligent plan"""

        prompt = f"""
        Create a detailed action plan to accomplish this goal:

        Goal: {goal}
        Parameters: {parameters}

        Available agents:
        - Planning: Strategy and decomposition
        - Research: Web search and information gathering
        - Code: Software development and execution
        - Analysis: Data analysis and insights
        - Validation: Quality checks and testing

        Break this into concrete steps. For each step specify:
        1. Description
        2. Which agent should handle it
        3. Dependencies on other steps
        4. Estimated time

        Identify which steps can run in parallel.

        Format response as JSON.
        """

        # Use LLM to generate plan
        response = await self.llm.agenerate(prompt)

        # Parse LLM response into ActionPlan
        # (Simplified - in production, use proper JSON parsing)
        plan = self._parse_llm_plan(response, goal)

        return plan

    def _create_simple_plan(self, goal: str, parameters: Dict) -> ActionPlan:
        """Create simple rule-based plan"""

        steps = []

        # Detect keywords to determine plan
        goal_lower = goal.lower()

        # Research-related words
        if any(
            word in goal_lower for word in ["search", "find", "research", "look up"]
        ):
            steps.append(
                PlanStep(
                    step_number=1,
                    description=f"Research: {goal}",
                    agent_type="research",
                    dependencies=[],
                    estimated_time=10.0,
                )
            )

        # Code-related words
        if any(
            word in goal_lower
            for word in ["code", "implement", "write", "create", "develop"]
        ):
            research_step = len(steps) > 0
            steps.append(
                PlanStep(
                    step_number=len(steps) + 1,
                    description=f"Code: {goal}",
                    agent_type="code",
                    dependencies=[1] if research_step else [],
                    estimated_time=20.0,
                )
            )

        # Analysis-related words
        if any(
            word in goal_lower for word in ["analyze", "analyze", "metrics", "data"]
        ):
            steps.append(
                PlanStep(
                    step_number=len(steps) + 1,
                    description=f"Analyze: {goal}",
                    agent_type="analysis",
                    dependencies=list(range(1, len(steps) + 1)),
                    estimated_time=15.0,
                )
            )

        # Always add validation at the end
        if len(steps) > 0:
            steps.append(
                PlanStep(
                    step_number=len(steps) + 1,
                    description="Validate results",
                    agent_type="validation",
                    dependencies=list(range(1, len(steps) + 1)),
                    estimated_time=5.0,
                )
            )

        # If no specific plan, create generic research plan
        if len(steps) == 0:
            steps = [
                PlanStep(1, f"Research: {goal}", "research", [], 10.0),
                PlanStep(2, "Validate results", "validation", [1], 5.0),
            ]

        total_time = sum(step.estimated_time for step in steps)

        # Identify parallel opportunities
        parallel = self._find_parallel_steps(steps)

        return ActionPlan(
            goal=goal,
            steps=steps,
            total_estimated_time=total_time,
            parallel_opportunities=parallel,
        )

    def _find_parallel_steps(self, steps: List[PlanStep]) -> List[List[int]]:
        """Find which steps can run in parallel"""
        parallel = []

        # Group steps by dependency level
        levels = {}
        for step in steps:
            max_dep = max(step.dependencies) if step.dependencies else 0
            level = max_dep + 1
            if level not in levels:
                levels[level] = []
            levels[level].append(step.step_number)

        # Steps in same level can run in parallel
        for level_steps in levels.values():
            if len(level_steps) > 1:
                parallel.append(level_steps)

        return parallel

    def _parse_llm_plan(self, llm_response: str, goal: str) -> ActionPlan:
        """Parse LLM response into ActionPlan"""
        # Simplified parser - in production use proper JSON parsing
        # For now, return a simple plan
        return self._create_simple_plan(goal, {})

    def _plan_to_dict(self, plan: ActionPlan) -> Dict:
        """Convert plan to dictionary"""
        return {
            "goal": plan.goal,
            "steps": [
                {
                    "step": s.step_number,
                    "description": s.description,
                    "agent": s.agent_type,
                    "dependencies": s.dependencies,
                    "estimated_time": s.estimated_time,
                }
                for s in plan.steps
            ],
            "total_estimated_time": plan.total_estimated_time,
            "parallel_opportunities": plan.parallel_opportunities,
        }

    def _create_summary(self, plan: ActionPlan) -> str:
        """Create human-readable summary"""
        lines = [
            f"Plan for: {plan.goal}",
            f"Total steps: {len(plan.steps)}",
            f"Estimated time: {plan.total_estimated_time:.0f}s",
            "",
            "Steps:",
        ]

        for step in plan.steps:
            deps = f" (after step {step.dependencies})" if step.dependencies else ""
            lines.append(
                f"  {step.step_number}. [{step.agent_type}] "
                f"{step.description}{deps}"
            )

        if plan.parallel_opportunities:
            lines.append("\nParallel execution possible for:")
            for group in plan.parallel_opportunities:
                lines.append(f"  Steps {group}")

        return "\n".join(lines)
