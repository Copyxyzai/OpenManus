"""
Research Agent - Specializes in web search and information gathering
"""

import logging
from typing import Any, Dict, List

from app.agents.base_agent import AgentConfig, BaseAgent, TaskRequest, TaskResult
from app.agents.communication.message_bus import MessageBus
from app.tools import BrowserUseTool, WebSearch
from app.tools.collection import ToolCollection

logger = logging.getLogger(__name__)


class ResearchAgent(BaseAgent):
    """
    Research Agent - Gathers information from the web.

    Specializes in:
    - Web searching
    - Browsing websites
    - Extracting information
    - Summarizing findings
    - Finding relevant sources
    """

    def __init__(self, message_bus: MessageBus, llm=None):
        config = AgentConfig(
            agent_id="research_agent",
            agent_type="research",
            description="Specializes in web search and information gathering",
            max_concurrent_tasks=3,
        )

        # Initialize with web search tools
        tools = ToolCollection(WebSearch(), BrowserUseTool())

        super().__init__(config, message_bus, tools=tools, llm=llm)

    async def execute_task(self, task: TaskRequest) -> TaskResult:
        """
        Execute research task.

        Searches the web and gathers relevant information.
        """
        try:
            logger.info(f"🔍 Researching: {task.description}")

            query = task.description
            parameters = task.parameters or {}

            # Perform research
            findings = await self._research(query, parameters)

            logger.info(
                f"✅ Research complete: found {len(findings.get('results', []))} results"
            )

            return TaskResult(
                task_id=task.task_type,
                success=True,
                result=findings,
                metadata={
                    "agent_type": "research",
                    "query": query,
                    "results_count": len(findings.get("results", [])),
                },
            )

        except Exception as e:
            logger.error(f"❌ Research failed: {e}")
            return TaskResult(task_id=task.task_type, success=False, error=str(e))

    async def _research(self, query: str, parameters: Dict) -> Dict[str, Any]:
        """Perform research using available tools"""

        num_results = parameters.get("num_results", 5)
        deep_search = parameters.get("deep_search", False)

        # Execute web search
        search_tool = None
        for tool in self.tools:
            if tool.name == "web_search":
                search_tool = tool
                break

        if search_tool:
            search_result = await search_tool.execute(
                query=query, num_results=num_results
            )

            # Extract results
            if hasattr(search_result, "result"):
                results = search_result.result
            else:
                results = []

            # If deep search, visit top results
            if deep_search and results:
                detailed_findings = await self._deep_research(results[:3])
            else:
                detailed_findings = []

            return {
                "query": query,
                "results": results,
                "detailed_findings": detailed_findings,
                "summary": self._create_summary(query, results),
            }
        else:
            # No search tool available
            return {
                "query": query,
                "results": [],
                "error": "Web search tool not available",
            }

    async def _deep_research(self, urls: List[str]) -> List[Dict]:
        """Visit URLs and extract detailed information"""

        browser_tool = None
        for tool in self.tools:
            if tool.name == "browser_use":
                browser_tool = tool
                break

        if not browser_tool:
            return []

        detailed = []
        for url in urls[:3]:  # Max 3 URLs
            try:
                result = await browser_tool.execute(
                    task=f"Visit {url} and extract key information"
                )

                detailed.append(
                    {"url": url, "content": str(result)[:500]}  # First 500 chars
                )
            except Exception as e:
                logger.warning(f"Failed to browse {url}: {e}")

        return detailed

    def _create_summary(self, query: str, results: List) -> str:
        """Create summary of research findings"""

        if not results:
            return f"No results found for: {query}"

        summary_lines = [
            f"Research query: {query}",
            f"Found {len(results)} results",
            "",
            "Top findings:",
        ]

        for i, result in enumerate(results[:5], 1):
            if isinstance(result, dict):
                title = result.get("title", "No title")
                summary_lines.append(f"  {i}. {title}")
            else:
                summary_lines.append(f"  {i}. {str(result)[:100]}")

        return "\n".join(summary_lines)
