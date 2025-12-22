"""
Orchestrator Agent - Coordinates all specialized agents
"""

import asyncio
import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from app.agents.base_agent import AgentConfig, BaseAgent, TaskRequest, TaskResult
from app.agents.communication.message_bus import MessageBus
from app.agents.specialized import (
    ActionPlan,
    AnalysisAgent,
    CodeAgent,
    PlanningAgent,
    ResearchAgent,
    ValidationAgent,
)

logger = logging.getLogger(__name__)


@dataclass
class WorkflowResult:
    """Result of a complete workflow execution"""

    success: bool
    plan: Optional[ActionPlan]
    step_results: Dict[int, TaskResult]
    final_result: Any
    execution_time: float
    error: Optional[str] = None


class OrchestratorAgent:
    """
    Orchestrator Agent - Coordinates all specialized agents.

    Responsibilities:
    - Analyze user requests
    - Decompose into subtasks
    - Create execution plans
    - Route tasks to appropriate agents
    - Execute workflows
    - Validate and aggregate results
    """

    def __init__(self, message_bus: MessageBus, llm=None):
        self.message_bus = message_bus
        self.llm = llm

        # Initialize all specialized agents
        self.agents = {
            "planning": PlanningAgent(message_bus, llm),
            "research": ResearchAgent(message_bus, llm),
            "code": CodeAgent(message_bus, llm),
            "analysis": AnalysisAgent(message_bus, llm),
            "validation": ValidationAgent(message_bus, llm),
        }

        # Start all agents
        self.agent_tasks = {}

        # Metrics
        self.metrics = {
            "workflows_executed": 0,
            "workflows_succeeded": 0,
            "workflows_failed": 0,
            "total_steps_executed": 0,
            "avg_workflow_time": 0.0,
        }

        logger.info("🎯 Orchestrator initialized with 5 specialized agents")

    async def start_agents(self):
        """Start all specialized agents"""
        logger.info("▶️  Starting all specialized agents...")

        for agent_id, agent in self.agents.items():
            task = asyncio.create_task(agent.run())
            self.agent_tasks[agent_id] = task
            logger.info(f"   ✅ {agent_id} agent started")

        # Wait for agents to initialize
        await asyncio.sleep(0.5)

        logger.info("✅ All agents running")

    async def execute(
        self, user_request: str, parameters: Optional[Dict] = None
    ) -> WorkflowResult:
        """
        Execute a complete workflow for a user request.

        Args:
            user_request: User's natural language request
            parameters: Optional additional parameters

        Returns:
            WorkflowResult with complete execution details
        """
        import time

        start_time = time.time()

        logger.info(f"🎯 Orchestrator executing: {user_request}")

        try:
            # 1. Create execution plan
            logger.info("📋 Step 1: Creating execution plan...")
            plan = await self._create_plan(user_request, parameters or {})

            if not plan:
                return WorkflowResult(
                    success=False,
                    plan=None,
                    step_results={},
                    final_result=None,
                    execution_time=time.time() - start_time,
                    error="Failed to create execution plan",
                )

            logger.info(f"   ✅ Plan created with {len(plan.steps)} steps")

            # 2. Execute workflow
            logger.info("⚙️  Step 2: Executing workflow...")
            step_results = await self._execute_workflow(plan)

            # 3. Validate results
            logger.info("✅ Step 3: Validating results...")
            validation = await self._validate_results(step_results)

            # 4. Aggregate final result
            logger.info("📦 Step 4: Aggregating results...")
            final_result = self._aggregate_results(plan, step_results, validation)

            # Calculate metrics
            execution_time = time.time() - start_time

            # Determine success: all steps that ran must have succeeded
            # (don't fail if a step returned None result, check success flag)
            success = len(step_results) > 0 and all(
                r and r.success for r in step_results.values()
            )

            # Update metrics
            self.metrics["workflows_executed"] += 1
            if success:
                self.metrics["workflows_succeeded"] += 1
            else:
                self.metrics["workflows_failed"] += 1
            self.metrics["total_steps_executed"] += len(step_results)
            self._update_avg_time(execution_time)

            logger.info(
                f"{'✅' if success else '❌'} Workflow complete in {execution_time:.2f}s"
            )

            return WorkflowResult(
                success=success,
                plan=plan,
                step_results=step_results,
                final_result=final_result,
                execution_time=execution_time,
            )

        except Exception as e:
            logger.error(f"❌ Workflow execution failed: {e}")
            self.metrics["workflows_failed"] += 1

            return WorkflowResult(
                success=False,
                plan=None,
                step_results={},
                final_result=None,
                execution_time=time.time() - start_time,
                error=str(e),
            )

    async def _create_plan(
        self, request: str, parameters: Dict
    ) -> Optional[ActionPlan]:
        """Create execution plan using Planning Agent"""

        planning_agent = self.agents["planning"]

        task = TaskRequest(
            task_type="planning", description=request, parameters=parameters
        )

        result = await planning_agent.request_agent(
            "planning_agent", task, timeout=30.0
        )

        if result and result.success:
            plan_data = result.result.get("plan", {})

            # Reconstruct ActionPlan from dict
            from app.agents.specialized.planning_agent import ActionPlan, PlanStep

            steps = [
                PlanStep(
                    step_number=s["step"],
                    description=s["description"],
                    agent_type=s["agent"],
                    dependencies=s["dependencies"],
                    estimated_time=s["estimated_time"],
                )
                for s in plan_data.get("steps", [])
            ]

            return ActionPlan(
                goal=plan_data.get("goal", request),
                steps=steps,
                total_estimated_time=plan_data.get("total_estimated_time", 0),
                parallel_opportunities=plan_data.get("parallel_opportunities", []),
            )

        return None

    async def _execute_workflow(self, plan: ActionPlan) -> Dict[int, TaskResult]:
        """Execute the workflow according to the plan"""

        results = {}

        # Group steps by dependency level for parallel execution
        levels = self._group_by_dependency_level(plan.steps)

        logger.info(f"   Executing {len(levels)} levels of dependencies")

        for level_num, level_steps in sorted(levels.items()):
            logger.info(f"   Level {level_num}: {len(level_steps)} step(s)")

            # Execute all steps in this level in parallel
            tasks = []
            for step in level_steps:
                task = self._execute_step(step, results)
                tasks.append(task)

            # Wait for all steps in this level to complete
            level_results = await asyncio.gather(*tasks, return_exceptions=True)

            # Store results
            for step, result in zip(level_steps, level_results):
                if isinstance(result, Exception):
                    logger.error(f"      ❌ Step {step.step_number} failed: {result}")
                    results[step.step_number] = TaskResult(
                        task_id=f"step_{step.step_number}",
                        success=False,
                        error=str(result),
                    )
                else:
                    results[step.step_number] = result
                    status = "✅" if result.success else "❌"
                    logger.info(f"      {status} Step {step.step_number} complete")

        return results

    def _group_by_dependency_level(self, steps: List) -> Dict[int, List]:
        """Group steps by dependency level for parallel execution"""

        levels = {}

        for step in steps:
            # Calculate level based on dependencies
            if not step.dependencies:
                level = 0
            else:
                # Level is 1 + max level of dependencies
                max_dep_level = max(
                    self._get_step_level(dep_num, steps, levels)
                    for dep_num in step.dependencies
                )
                level = max_dep_level + 1

            if level not in levels:
                levels[level] = []
            levels[level].append(step)

        return levels

    def _get_step_level(self, step_num: int, all_steps: List, levels: Dict) -> int:
        """Get the level of a step"""
        for level, steps in levels.items():
            if any(s.step_number == step_num for s in steps):
                return level

        # Find step and calculate its level
        step = next((s for s in all_steps if s.step_number == step_num), None)
        if not step or not step.dependencies:
            return 0

        return (
            max(
                self._get_step_level(dep, all_steps, levels)
                for dep in step.dependencies
            )
            + 1
        )

    async def _execute_step(self, step, previous_results: Dict) -> TaskResult:
        """Execute a single step"""

        # Route to appropriate agent
        agent_type = step.agent_type
        agent = self.agents.get(agent_type)

        if not agent:
            return TaskResult(
                task_id=f"step_{step.step_number}",
                success=False,
                error=f"Unknown agent type: {agent_type}",
            )

        # Prepare task
        # Include results from dependencies
        dep_results = {
            dep_num: previous_results.get(dep_num)
            for dep_num in step.dependencies
            if dep_num in previous_results
        }

        task = TaskRequest(
            task_type=agent_type,
            description=step.description,
            parameters={"dependencies": dep_results, "step_number": step.step_number},
        )

        # Execute on agent
        result = await agent.request_agent(
            f"{agent_type}_agent",
            task,
            timeout=step.estimated_time * 2,  # 2x estimated time as timeout
        )

        if not result:
            return TaskResult(
                task_id=f"step_{step.step_number}",
                success=False,
                error="Agent did not respond",
            )

        return result

    async def _validate_results(self, results: Dict[int, TaskResult]) -> TaskResult:
        """Validate all results"""

        validation_agent = self.agents["validation"]

        task = TaskRequest(
            task_type="validation",
            description="Validate workflow results",
            parameters={
                "target_type": "result",
                "target": {
                    k: v.result if v.success else v.error for k, v in results.items()
                },
                "criteria": {"required_keys": list(results.keys())},
            },
        )

        result = await validation_agent.request_agent(
            "validation_agent", task, timeout=10.0
        )

        return (
            result
            if result
            else TaskResult(
                task_id="validation", success=False, error="Validation failed"
            )
        )

    def _aggregate_results(
        self,
        plan: ActionPlan,
        step_results: Dict[int, TaskResult],
        validation: TaskResult,
    ) -> Dict[str, Any]:
        """Aggregate all results into final output"""

        # Combine all successful results
        successful_steps = {
            step_num: result.result
            for step_num, result in step_results.items()
            if result.success
        }

        failed_steps = {
            step_num: result.error
            for step_num, result in step_results.items()
            if not result.success
        }

        return {
            "goal": plan.goal,
            "total_steps": len(plan.steps),
            "successful_steps": len(successful_steps),
            "failed_steps": len(failed_steps),
            "results": successful_steps,
            "errors": failed_steps if failed_steps else None,
            "validation": {
                "is_valid": (
                    validation.result.get("is_valid") if validation.success else False
                ),
                "confidence": (
                    validation.result.get("confidence") if validation.success else 0.0
                ),
            },
            "summary": self._create_summary(plan, step_results, validation),
        }

    def _create_summary(
        self, plan: ActionPlan, results: Dict[int, TaskResult], validation: TaskResult
    ) -> str:
        """Create human-readable summary"""

        lines = [
            f"Workflow: {plan.goal}",
            f"Steps executed: {len(results)}/{len(plan.steps)}",
            "",
        ]

        for step in plan.steps:
            result = results.get(step.step_number)
            if result:
                status = "✅" if result.success else "❌"
                lines.append(
                    f"{status} Step {step.step_number}: [{step.agent_type}] {step.description}"
                )
            else:
                lines.append(f"⚠️  Step {step.step_number}: Not executed")

        if validation.success:
            val_result = validation.result
            is_valid = val_result.get("is_valid", False)
            confidence = val_result.get("confidence", 0)
            lines.append("")
            lines.append(
                f"Validation: {'✅ Valid' if is_valid else '❌ Invalid'} "
                f"(confidence: {confidence:.0%})"
            )

        return "\n".join(lines)

    def _update_avg_time(self, new_time: float):
        """Update average workflow time"""
        total = self.metrics["workflows_executed"]
        if total > 0:
            current_avg = self.metrics["avg_workflow_time"]
            self.metrics["avg_workflow_time"] = (
                current_avg * (total - 1) + new_time
            ) / total

    def get_metrics(self) -> Dict[str, Any]:
        """Get orchestrator metrics"""
        return {
            **self.metrics,
            "success_rate": (
                self.metrics["workflows_succeeded"]
                / self.metrics["workflows_executed"]
                * 100
                if self.metrics["workflows_executed"] > 0
                else 0
            ),
            "active_agents": len(self.agents),
        }

    async def shutdown(self):
        """Graceful shutdown"""
        logger.info("🛑 Shutting down orchestrator...")

        # Cancel all agent tasks
        for agent_id, task in self.agent_tasks.items():
            logger.info(f"   Stopping {agent_id} agent...")
            task.cancel()

            try:
                await task
            except asyncio.CancelledError:
                pass

        logger.info("✅ Orchestrator shut down")
