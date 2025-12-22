"""
Test for Orchestrator Agent
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.agents.communication import MessageBus
from app.agents.orchestrator import OrchestratorAgent


async def test_simple_orchestration():
    """Test simple orchestration"""
    print("\n" + "=" * 60)
    print("🧪 Test 1: Simple Orchestration")
    print("=" * 60)

    bus = MessageBus()
    orchestrator = OrchestratorAgent(bus)

    # Start agents
    await orchestrator.start_agents()

    # Execute simple request
    print("\n📝 Request: Create a hello world program")
    result = await orchestrator.execute("Create a hello world program")

    if result.success:
        print(f"\n✅ Workflow succeeded!")
        print(f"   Steps executed: {len(result.step_results)}")
        print(f"   Execution time: {result.execution_time:.2f}s")
        print(f"\n{result.final_result.get('summary', '')}")
    else:
        print(f"\n❌ Workflow failed: {result.error}")

    # Shutdown
    await orchestrator.shutdown()

    return result.success


async def test_complex_orchestration():
    """Test complex multi-step orchestration"""
    print("\n" + "=" * 60)
    print("🧪 Test 2: Complex Multi-Step Orchestration")
    print("=" * 60)

    bus = MessageBus()
    orchestrator = OrchestratorAgent(bus)

    # Start agents
    await orchestrator.start_agents()

    # Execute complex request (code generation instead of web search to avoid rate limits)
    print("\n📝 Request: Create a Python function to calculate fibonacci")
    result = await orchestrator.execute(
        "Create a Python function to calculate fibonacci"
    )

    if result.success:
        print(f"\n✅ Workflow succeeded!")
        print(f"   Total steps: {len(result.plan.steps) if result.plan else 0}")
        print(f"   Successful: {result.final_result.get('successful_steps', 0)}")
        print(f"   Failed: {result.final_result.get('failed_steps', 0)}")
        print(f"   Execution time: {result.execution_time:.2f}s")

        # Show validation
        validation = result.final_result.get("validation", {})
        print(
            f"   Validation: {'✅' if validation.get('is_valid') else '❌'} "
            f"(confidence: {validation.get('confidence', 0):.0%})"
        )

        print(f"\n📊 Summary:")
        print(result.final_result.get("summary", ""))
    else:
        print(f"\n❌ Workflow failed: {result.error}")

    # Show metrics
    print(f"\n📈 Orchestrator Metrics:")
    metrics = orchestrator.get_metrics()
    print(f"   Workflows executed: {metrics['workflows_executed']}")
    print(f"   Success rate: {metrics['success_rate']:.0f}%")
    print(f"   Avg time: {metrics['avg_workflow_time']:.2f}s")

    # Shutdown
    await orchestrator.shutdown()

    return result.success


async def test_with_data_analysis():
    """Test orchestration with data analysis"""
    print("\n" + "=" * 60)
    print("🧪 Test 3: Orchestration with Data Analysis")
    print("=" * 60)

    bus = MessageBus()
    orchestrator = OrchestratorAgent(bus)

    # Start agents
    await orchestrator.start_agents()

    # Execute request with analysis
    print("\n📝 Request: Analyze the numbers 10, 20, 30, 40, 50")
    result = await orchestrator.execute(
        "Analyze the numbers 10, 20, 30, 40, 50",
        parameters={"data": [10, 20, 30, 40, 50]},
    )

    if result.success:
        print(f"\n✅ Workflow succeeded!")
        print(f"   Steps executed: {len(result.step_results)}")
        print(f"\n{result.final_result.get('summary', '')}")

        # Show analysis results
        results = result.final_result.get("results", {})
        for step_num, step_result in results.items():
            if isinstance(step_result, dict) and "mean" in step_result:
                print(f"\n📊 Analysis Results:")
                print(f"   Mean: {step_result.get('mean')}")
                print(
                    f"   Min: {step_result.get('min')}, Max: {step_result.get('max')}"
                )
                break
    else:
        print(f"\n❌ Workflow failed: {result.error}")

    # Shutdown
    await orchestrator.shutdown()

    return result.success


async def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("🚀 Orchestrator Tests")
    print("=" * 60)

    results = {
        "Simple Orchestration": await test_simple_orchestration(),
        "Complex Multi-Step": await test_complex_orchestration(),
        "With Data Analysis": await test_with_data_analysis(),
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
        print("\n🎉 All tests passed! Orchestrator working!\n")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed\n")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
