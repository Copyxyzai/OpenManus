"""
Comprehensive Application Testing Script
Tests OpenManus with various task types
"""

import asyncio
from datetime import datetime

from app.agent.manus import Manus

# Test scenarios
TEST_SCENARIOS = [
    {
        "name": "Simple Code Generation",
        "prompt": "Create a Python function to calculate the sum of two numbers",
    },
    {
        "name": "File Listing",
        "prompt": "List all Python files in the current directory",
    },
    {
        "name": "Data Analysis",
        "prompt": "Calculate the average of these numbers: 10, 20, 30, 40, 50",
    },
    {"name": "Math Operations", "prompt": "Calculate 25 * 4 + 100"},
    {"name": "Code with Logic", "prompt": "Create a hello world function in Python"},
]


class TestRunner:
    """Run application tests"""

    def __init__(self):
        self.agent = None
        self.results = []

    async def setup(self):
        """Initialize agent"""
        print("🔧 Initializing OpenManus Agent...")
        try:
            self.agent = await Manus.create()
            print("✅ Agent initialized successfully\n")
            return True
        except Exception as e:
            print(f"❌ Failed to initialize agent: {e}")
            return False

    async def cleanup(self):
        """Cleanup agent resources"""
        if self.agent:
            await self.agent.cleanup()

    async def run_test(self, scenario):
        """Run a single test scenario"""
        print(f"\n{'='*60}")
        print(f"🧪 Test: {scenario['name']}")
        print(f"{'='*60}")
        print(f"📝 Prompt: {scenario['prompt']}")
        print(f"⏱️  Started at: {datetime.now().strftime('%H:%M:%S')}")

        start_time = datetime.now()

        try:
            # Run the task
            await self.agent.run(scenario["prompt"])

            # Calculate duration
            duration = (datetime.now() - start_time).total_seconds()

            # Store result
            test_result = {
                "name": scenario["name"],
                "success": True,
                "duration": duration,
            }

            print(f"\n✅ Test PASSED")
            print(f"⏱️  Duration: {duration:.2f}s")

        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            test_result = {
                "name": scenario["name"],
                "success": False,
                "duration": duration,
                "error": str(e),
            }

            print(f"\n❌ Test FAILED")
            print(f"⏱️  Duration: {duration:.2f}s")
            print(f"🔥 Error: {str(e)}")

        self.results.append(test_result)
        return test_result

    async def run_all_tests(self):
        """Run all test scenarios"""
        print("\n" + "=" * 60)
        print("🚀 OpenManus Application Testing Suite")
        print("=" * 60)
        print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🧪 Number of tests: {len(TEST_SCENARIOS)}")
        print("=" * 60)

        # Setup
        if not await self.setup():
            print("\n❌ Setup failed. Aborting tests.")
            return

        try:
            # Run each test
            for scenario in TEST_SCENARIOS:
                await self.run_test(scenario)
                # Small delay between tests
                await asyncio.sleep(2)

            # Print summary
            self.print_summary()
        finally:
            # Cleanup
            await self.cleanup()

    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)

        total = len(self.results)
        passed = sum(1 for r in self.results if r["success"])
        failed = total - passed

        print(f"\n📈 Results:")
        print(f"   Total tests: {total}")
        print(f"   ✅ Passed: {passed}")
        print(f"   ❌ Failed: {failed}")
        print(f"   📊 Success rate: {(passed/total*100):.1f}%")

        if self.results:
            avg_duration = sum(r["duration"] for r in self.results) / len(self.results)
            total_time = sum(r["duration"] for r in self.results)
            print(f"\n⏱️  Performance:")
            print(f"   Average duration: {avg_duration:.2f}s")
            print(f"   Total time: {total_time:.2f}s")

        # Print individual results
        print(f"\n📋 Individual Test Results:")
        for i, result in enumerate(self.results, 1):
            status = "✅ PASS" if result["success"] else "❌ FAIL"
            duration = f"{result['duration']:.2f}s"
            print(f"   {i}. {result['name']}... {status} ({duration})")
            if not result["success"]:
                print(f"      Error: {result.get('error', 'Unknown')}")

        print("\n" + "=" * 60)

        if failed == 0:
            print("🎉 All tests passed! Application is working correctly!")
        else:
            print(f"⚠️  {failed} test(s) failed. Review errors above.")

        print("=" * 60 + "\n")


async def main():
    """Main entry point"""
    runner = TestRunner()
    await runner.run_all_tests()


if __name__ == "__main__":
    print("\n🤖 OpenManus Application Test Suite\n")
    asyncio.run(main())
