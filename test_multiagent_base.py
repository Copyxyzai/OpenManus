"""
Test for multi-agent base communication system
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.agents import AgentConfig, BaseAgent, MessageBus, TaskRequest, TaskResult


class SimpleAgent(BaseAgent):
    """Simple test agent"""

    async def execute_task(self, task: TaskRequest) -> TaskResult:
        """Execute a simple task"""
        # Simulate work
        await asyncio.sleep(0.5)

        result = f"Completed: {task.description}"

        return TaskResult(task_id=task.task_type, success=True, result=result)


async def test_basic_communication():
    """Test basic agent-to-agent communication"""
    print("\n" + "=" * 60)
    print("🧪 Test 1: Basic Agent Communication")
    print("=" * 60)

    # Create message bus
    bus = MessageBus()

    # Create two agents
    agent_a = SimpleAgent(
        config=AgentConfig(
            agent_id="agent_a", agent_type="simple", description="Test Agent A"
        ),
        message_bus=bus,
    )

    agent_b = SimpleAgent(
        config=AgentConfig(
            agent_id="agent_b", agent_type="simple", description="Test Agent B"
        ),
        message_bus=bus,
    )

    # Start agents
    task_a = asyncio.create_task(agent_a.run())
    task_b = asyncio.create_task(agent_b.run())

    # Wait for initialization
    await asyncio.sleep(0.5)

    # Agent A requests Agent B to do something
    print("\n📤 Agent A requesting Agent B...")
    task_request = TaskRequest(
        task_type="test",
        description="Process some data",
        parameters={"data": [1, 2, 3]},
    )

    result = await agent_a.request_agent(
        target_agent="agent_b", task=task_request, timeout=5.0
    )

    if result and result.success:
        print(f"✅ Agent A received result: {result.result}")
    else:
        print("❌ Request failed or timed out")

    # Check metrics
    print("\n📊 Agent Metrics:")
    print(f"Agent A: {agent_a.get_metrics()}")
    print(f"Agent B: {agent_b.get_metrics()}")

    # Check bus metrics
    print(f"\nMessage Bus: {bus.get_metrics()}")

    # Cleanup
    task_a.cancel()
    task_b.cancel()

    try:
        await task_a
    except asyncio.CancelledError:
        pass

    try:
        await task_b
    except asyncio.CancelledError:
        pass

    return True


async def test_pub_sub():
    """Test publish-subscribe pattern"""
    print("\n" + "=" * 60)
    print("🧪 Test 2: Publish-Subscribe Pattern")
    print("=" * 60)

    bus = MessageBus()

    agent = SimpleAgent(
        config=AgentConfig(
            agent_id="subscriber", agent_type="simple", description="Subscriber Agent"
        ),
        message_bus=bus,
    )

    # Subscribe to event
    notifications_received = []

    def on_event(message):
        notifications_received.append(message.content)
        print(f"🔔 Received notification: {message.content}")

    agent.subscribe_to("task.completed", on_event)

    # Publish events
    print("\n📢 Publishing events...")
    await agent.notify("task.completed", {"task": "Task 1", "status": "done"})
    await agent.notify("task.completed", {"task": "Task 2", "status": "done"})

    # Wait for processing
    await asyncio.sleep(0.5)

    print(f"\n✅ Received {len(notifications_received)} notifications")

    return len(notifications_received) == 2


async def test_concurrent_requests():
    """Test multiple concurrent requests"""
    print("\n" + "=" * 60)
    print("🧪 Test 3: Concurrent Requests")
    print("=" * 60)

    bus = MessageBus()

    # Create worker agent
    worker = SimpleAgent(
        config=AgentConfig(
            agent_id="worker",
            agent_type="simple",
            description="Worker Agent",
            max_concurrent_tasks=3,
        ),
        message_bus=bus,
    )

    # Create coordinator agent
    coordinator = SimpleAgent(
        config=AgentConfig(
            agent_id="coordinator", agent_type="simple", description="Coordinator Agent"
        ),
        message_bus=bus,
    )

    # Start agents
    task_worker = asyncio.create_task(worker.run())
    task_coordinator = asyncio.create_task(coordinator.run())

    await asyncio.sleep(0.5)

    # Send multiple concurrent requests
    print("\n📤 Sending 5 concurrent requests...")

    requests = [
        coordinator.request_agent(
            target_agent="worker",
            task=TaskRequest(task_type=f"task_{i}", description=f"Process item {i}"),
        )
        for i in range(5)
    ]

    results = await asyncio.gather(*requests)

    successful = sum(1 for r in results if r and r.success)
    print(f"\n✅ {successful}/5 requests completed successfully")

    # Cleanup
    task_worker.cancel()
    task_coordinator.cancel()

    try:
        await task_worker
    except asyncio.CancelledError:
        pass

    try:
        await task_coordinator
    except asyncio.CancelledError:
        pass

    return successful == 5


async def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("🚀 Multi-Agent Base System Tests")
    print("=" * 60)

    results = {
        "Basic Communication": await test_basic_communication(),
        "Publish-Subscribe": await test_pub_sub(),
        "Concurrent Requests": await test_concurrent_requests(),
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
        print("\n🎉 All tests passed! Base system OK!\n")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed\n")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
