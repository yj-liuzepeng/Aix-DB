import logging
import traceback

from agent.excel.excel_agent_state import ExcelAgentState
from agent.excel.excel_graph import create_excel_graph
from langgraph.graph.state import CompiledStateGraph

from services.user_service import decode_jwt_token

logger = logging.getLogger(__name__)


class ExcelAgent:
    """
    表格问答智能体
    """

    async def run_excel_agent(
        self,
        query: str,
        response=None,
        chat_id: str = None,
        uuid_str: str = None,
        user_token=None,
        file_list: list = None,
    ) -> None:
        """
        运行表格智能体
        :param query:
        :param response:
        :param chat_id:
        :param uuid_str:
        :param user_token:
        :param file_list
        :return:
        """
        try:
            initial_state = ExcelAgentState(
                user_query=query,
                file_list=file_list,
                db_schema="",
                generated_sql="",
                chart_url="",
                chart_type="",
                apache_chart_data={},
                execution_result=[],
                report_summary="",
            )
            graph: CompiledStateGraph = create_excel_graph()

            # 获取用户信息 标识对话状态
            user_dict = await decode_jwt_token(user_token)
            task_id = user_dict["id"]

            async for chunk_dict in graph.astream(initial_state, stream_mode="messages"):
                logger.info(f"Processing chunk: {chunk_dict}")

        except Exception as e:
            traceback.print_exception(e)
            logger.error(f"表格问答智能体运行异常: {e}")
