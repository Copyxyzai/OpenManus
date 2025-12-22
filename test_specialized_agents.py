"""
Test for specialized agents
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.agents.communication import MessageBus, TaskRequest
from app.agents.specialized import (
    AnalysisAgent,
    CodeAgent,
    PlanningAgent,
    ResearchAgent,
    ValidationAgent,
)


async def test_planning_agent():
    """Test Planning Agent"""
    print("\n" + "=" * 60)
    print("🧪 Test 1: Planning Agent")
    print("=" * 60)

    bus = MessageBus()
    agent = PlanningAgent(bus)

    # Start agent
    agent_task = asyncio.create_task(agent.run())
    await asyncio.sleep(0.5)

    # Request planning
    task = TaskRequest(
        task_type="planning",
        description="Research Python async and create examples",
        parameters={},
    )

    result = await agent.request_agent("planning_agent", task)

    if result and result.success:
        plan = result.result.get("plan", {})
        print(f"✅ Plan created with {len(plan.get('steps', []))} steps")
        print(result.result.get("summary", ""))
    else:
        print("❌ Planning failed")

    # Cleanup
    agent_task.cancel()
    try:
        await agent_task
    except asyncio.CancelledError:
        pass

    return result and result.success


async def test_code_agent():
    """Test Code Agent"""
    print("\n" + "=" * 60)
    print("🧪 Test 2: Code Agent")
    print("=" * 60)

    bus = MessageBus()
    agent = CodeAgent(bus)

    # Start agent
    agent_task = asyncio.create_task(agent.run())
    await asyncio.sleep(0.5)

    # Request code execution
    task = TaskRequest(
        task_type="code",
        description="Print hello world",
        parameters={"code": 'print("Hello from Code Agent!")'},
    )

    result = await agent.request_agent("code_agent", task)

    if result and result.success:
        output = result.result.get("output", "")
        print(f"✅ Code executed:")
        print(f"   Output: {output}")
    else:
        print("❌ Code execution failed")

    # Cleanup
    agent_task.cancel()
    try:
        await agent_task
    except asyncio.CancelledError:
        pass

    return result and result.success


async def test_analysis_agent():
    """Test Analysis Agent"""
    print("\n" + "=" * 60)
    print("🧪 Test 3: Analysis Agent")
    print("=" * 60)

    bus = MessageBus()
    agent = AnalysisAgent(bus)

    # Start agent
    agent_task = asyncio.create_task(agent.run())
    await asyncio.sleep(0.5)

    # Request analysis
    task = TaskRequest(
        task_type="analysis",
        description="Analyze sample data",
        parameters={"data": [10, 20, 30, 40, 50], "type": "statistics"},
    )

    result = await agent.request_agent("analysis_agent", task)

    if result and result.success:
        analysis = result.result
        print(f"✅ Analysis complete:")
        print(f"   Mean: {analysis.get('mean')}")
        print(f"   Min: {analysis.get('min')}, Max: {analysis.get('max')}")
    else:
        print("❌ Analysis failed")

    # Cleanup
    agent_task.cancel()
    try:
        await agent_task
    except asyncio.CancelledError:
        pass

    return result and result.success


async def test_validation_agent():
    """Test Validation Agent"""
    print("\n" + "=" * 60)
    print("🧪 Test 4: Validation Agent")
    print("=" * 60)

    bus = MessageBus()
    agent = ValidationAgent(bus)

    # Start agent
    agent_task = asyncio.create_task(agent.run())
    await asyncio.sleep(0.5)

    # Request validation
    task = TaskRequest(
        task_type="validation",
        description="Validate Python code",
        parameters={
            "target_type": "code",
            "target": 'print("Valid code!")',
            "criteria": {},
        },
    )

    result = await agent.request_agent("validation_agent", task)

    if result and result.success:
        validation = result.result
        is_valid = validation.get("is_valid")
        confidence = validation.get("confidence", 0)
        print(f"{'✅' if is_valid else '❌'} Validation: {is_valid}")
        print(f"   Confidence: {confidence:.0%}")
        if validation.get("issues"):
            print(f"   Issues: {validation['issues']}")
    else:
        print("❌ Validation failed")

    # Cleanup
    agent_task.cancel()
    try:
        await agent_task
    except asyncio.CancelledError:
        pass

    return result and result.success


async def test_multi_agent_collaboration():
    """Test agents working together"""
    print("\n" + "=" * 60)
    print("🧪 Test 5: Multi-Agent Collaboration")
    print("=" * 60)

    bus = MessageBus()

    # Create all agents
    planner = PlanningAgent(bus)
    coder = CodeAgent(bus)
    validator = ValidationAgent(bus)

    # Start agents
    tasks = [
        asyncio.create_task(planner.run()),
        asyncio.create_task(coder.run()),
        asyncio.create_task(validator.run()),
    ]

    await asyncio.sleep(0.5)

    # 1. Planner creates a plan
    print("\n1️⃣ Planning phase...")
    plan_task = TaskRequest(
        task_type="planning", description="Create a hello world program", parameters={}
    )

    plan_result = await planner.request_agent("planning_agent", plan_task)

    if plan_result and plan_result.success:
        print("   ✅ Plan created")

    # 2. Code Agent executes
    print("\n2️⃣ Coding phase...")
    code_task = TaskRequest(
        task_type="code",
        description="Write hello world",
        parameters={"code": 'print("Hello, Multi-Agent World!")'},
    )

    code_result = await coder.request_agent("code_agent", code_task)

    if code_result and code_result.success:
        print(f"   ✅ Code executed: {code_result.result.get('output', '')}")

    # 3. Validator checks
    print("\n3️⃣ Validation phase...")
    val_task = TaskRequest(
        task_type="validation",
        description="Validate code",
        parameters={
            "target_type": "code",
            "target": 'print("Hello, Multi-Agent World!")',
            "criteria": {},
        },
    )

    val_result = await validator.request_agent("validation_agent", val_task)

    if val_result and val_result.success:
        is_valid = val_result.result.get("is_valid")
        print(f"   {'✅' if is_valid else '❌'} Validation: {is_valid}")

    # Cleanup
    for task in tasks:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

    return all(
        [
            plan_result and plan_result.success,
            code_result and code_result.success,
            val_result and val_result.success,
        ]
    )


async def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("🚀 Specialized Agents Tests")
    print("=" * 60)

    results = {
        "Planning Agent": await test_planning_agent(),
        "Code Agent": await test_code_agent(),
        "Analysis Agent": await test_analysis_agent(),
        "Validation Agent": await test_validation_agent(),
        "Multi-Agent Collaboration": await test_multi_agent_collaboration(),
    }

    print("\n" + "=" * 60)
    print("📊 Test Results")
    print("=" * 60)

    passed = sum(1 for result in results.values() if result)
    total = len(results)

    for test_name, success in results.items():
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{test_name:.<40} {status}")

    print("=" * 60)
    print(f"Total: {passed}/{total} tests passed ({passed/total*100:.0f}%)")
    print("=" * 60)

    if passed == total:
        print("\n🎉 All tests passed! Specialized agents working!\n")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed\n")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
