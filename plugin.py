from typing import List, Tuple, Type, Any
from src.plugin_system import (
    BasePlugin,
    register_plugin,
    BaseTool,
    ComponentInfo,
    ConfigField,
    ToolParamType,
)
from tavily import AsyncTavilyClient
from src.common.logger import get_logger


class TavilyTool(BaseTool):
    """使用Tavily进行网络搜索的工具"""

    name = "tavily"
    description = "使用Tavily进行网络搜索"
    parameters = [
        ("query", ToolParamType.STRING, "需要搜索查询的问题/关键词", True, None),
        (
            "max_results",
            ToolParamType.INTEGER,
            "返回的搜索结果数量，默认5条",
            False,
            None,
        ),
    ]
    _client = None
    logger = get_logger("tavily")

    def __init__(self):
        proxies = {
            "http": self.get_config("tavily.proxy", None),
            "https": self.get_config("tavily.proxy", None),
        }
        api_key: str = self.get_config("tavily.api_key", "")
        self._client = AsyncTavilyClient(api_key=api_key, proxies=proxies)

    async def execute(self, function_args: dict[str, Any]) -> dict[str, Any]:
        """执行Tavily搜索"""
        query: str = function_args.get("query")
        max_results: int = function_args.get("max_results", 5)
        if self._client is None:
            self.logger.error("Tavily客户端未初始化")
            return {"name": self.name, "content": "检索失败, 错误: 客户端未初始化"}
        try:
            result = await self._client.search(
                query,
                max_results=max_results,
                auto_parameters=True,
                include_answer="advanced",
            )
            if self.get_config("tavily.debug", False):
                self.logger.debug(f"查询: {query}, 结果: {result}")
            return {"name": self.name, "content": result["answer"]}
        except Exception as e:
            return {"name": self.name, "content": f"检索失败, 错误: {str(e)}"}


@register_plugin
class SearchPlugin(BasePlugin):
    """搜索插件"""

    plugin_name: str = "search_plugin"
    enable_plugin: bool = True
    dependencies: List[str] = []
    python_dependencies: List[str] = ["tavily-python"]
    config_file_name: str = "config.toml"

    config_section_descriptions = {"plugin": "插件基本信息", "tavily": "Tavily配置"}

    config_schema: dict = {
        "plugin": {
            "name": ConfigField(
                type=str, default="search_plugin", description="插件名称"
            ),
            "version": ConfigField(type=str, default="1.0.0", description="插件版本"),
            "enabled": ConfigField(type=bool, default=True, description="是否启用插件"),
        },
        "tavily": {
            "api_key": ConfigField(type=str, default="", description="Tavily API密钥"),
            "proxy": ConfigField(type=str, default=None, description="Tavily代理配置"),
            "debug": ConfigField(
                type=bool, default=False, description="是否启用调试模式"
            ),
        },
    }

    def get_plugin_components(self) -> List[Tuple[ComponentInfo, Type]]:
        return [
            (TavilyTool.get_tool_info(), TavilyTool),
        ]
