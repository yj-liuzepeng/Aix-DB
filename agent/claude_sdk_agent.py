import asyncio
import json
import logging
import os
import traceback
from typing import Optional

from claude_agent_sdk import query, ClaudeAgentOptions
from claude_agent_sdk.types import SystemMessage, AssistantMessage, ResultMessage

from common.minio_util import MinioUtils
from constants.code_enum import DataTypeEnum, IntentEnum
from services.user_service import add_user_record, decode_jwt_token
from model.db_connection_pool import get_db_pool
from model.db_models import TAiModel

logger = logging.getLogger(__name__)

minio_utils = MinioUtils()
pool = get_db_pool()


def _get_model_config_from_db():
    """
    从数据库获取模型配置
    :return: 模型配置字典，包含 api_domain, api_key, base_model
    """
    with pool.get_session() as session:
        model = session.query(TAiModel).filter(
            TAiModel.default_model == True,
            TAiModel.model_type == 1
        ).first()
        if not model:
            raise ValueError("No default AI model configured in database.")
        
        return {
            "api_domain": model.api_domain,
            "api_key": model.api_key or "",
            "base_model": model.base_model
        }


class ClaudeSDKAgent:
    """
    Claude Agent SDK 驱动的通用问答智能体
    """

    def __init__(self):
        # 从数据库获取模型配置并设置环境变量
        try:
            model_config = _get_model_config_from_db()
            
            # 设置环境变量
            os.environ["ANTHROPIC_BASE_URL"] = model_config["api_domain"]
            os.environ["ANTHROPIC_AUTH_TOKEN"] = model_config["api_key"]
            os.environ["ANTHROPIC_MODEL"] = model_config["base_model"]
            os.environ["ANTHROPIC_SMALL_FAST_MODEL"] = model_config["base_model"]
            os.environ["API_TIMEOUT_MS"] = "600000"
            os.environ["CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC"] = "1"
            
            logger.info(f"ClaudeSDKAgent 已从数据库加载配置: base_url={model_config['api_domain']}, model={model_config['base_model']}")
        except Exception as e:
            logger.error(f"从数据库加载模型配置失败: {e}")
            # 如果从数据库加载失败，使用环境变量中的默认值（如果存在）
            if not os.getenv("ANTHROPIC_BASE_URL"):
                logger.warning("使用默认环境变量配置，如果未设置可能导致错误")
        
        allowed_tools_env = os.getenv("CLAUDE_AGENT_ALLOWED_TOOLS")
        allowed_tools = (
            [t.strip() for t in allowed_tools_env.split(",") if t.strip()]
            if allowed_tools_env
            else ["Skill", "Read", "Write", "Bash"]
        )

        self.options = ClaudeAgentOptions(
            cwd=os.getenv("CLAUDE_AGENT_CWD", "./"),
            setting_sources=["user", "project"],
            system_prompt="You are a helpful assistant.",
            allowed_tools=allowed_tools,
        )

        # 存储运行中的任务
        self.running_tasks = {}

    @staticmethod
    def _create_response(
        content: str,
        message_type: str = "continue",
        data_type: str = DataTypeEnum.ANSWER.value[0],
    ) -> str:
        """封装响应结构为SSE格式"""
        res = {
            "data": {"messageType": message_type, "content": content},
            "dataType": data_type,
        }
        return "data:" + json.dumps(res, ensure_ascii=False) + "\n\n"

    async def run_agent(
        self,
        query_text: str,
        response,
        session_id: Optional[str] = None,
        uuid_str: str = None,
        user_token=None,
        file_list: dict = None,
    ):
        """
        运行 Claude SDK 智能体，支持流式响应与任务取消
        """
        # 验证查询文本不为空
        if not query_text or not query_text.strip():
            error_msg = "查询内容不能为空，请输入您的问题。"
            await response.write(self._create_response(error_msg, "error", DataTypeEnum.ANSWER.value[0]))
            await response.write(self._create_response("", "end", DataTypeEnum.STREAM_END.value[0]))
            return

        file_as_markdown = ""
        if file_list:
            file_as_markdown = minio_utils.get_files_content_as_markdown(file_list)

        user_dict = await decode_jwt_token(user_token)
        task_id = user_dict["id"]
        task_context = {"cancelled": False}
        self.running_tasks[task_id] = task_context

        try:
            t02_answer_data = []
            formatted_query = query_text.strip()
            if file_as_markdown:
                formatted_query = f"{formatted_query}\n\n参考资料内容如下：\n{file_as_markdown}"

            # 使用 session_id 作为线程标识，便于上层对话隔离
            chat_id = session_id if session_id else "default_thread"
            query_params = {"prompt": formatted_query, "options": self.options}

            async for message in query(**query_params):
                if self.running_tasks[task_id]["cancelled"]:
                    await response.write(
                        self._create_response(
                            "\n> 这条消息已停止",
                            "info",
                            DataTypeEnum.ANSWER.value[0],
                        )
                    )
                    await response.write(self._create_response("", "end", DataTypeEnum.STREAM_END.value[0]))
                    break

                content_parts = []
                logger.info("ClaudeSDKAgent 运行结果：%s", message)

                # 处理不同类型的message
                if isinstance(message, SystemMessage):
                    # 系统消息处理 - 提供初始化和配置信息
                    system_info = {
                        "subtype": message.subtype,
                        "cwd": message.data.get("cwd", ""),
                        "session_id": message.data.get("session_id", ""),
                        "model": message.data.get("model", ""),
                    }
                    logger.info("ClaudeSDKAgent 运行结果：%s", system_info)
                    # 系统消息不输出到前端，只记录日志

                elif isinstance(message, AssistantMessage):
                    if hasattr(message, "content") and message.content:
                        for block in message.content:
                            block_type = type(block).__name__
                            if block_type == "TextBlock":
                                if hasattr(block, "text") and block.text:
                                    content_parts.append(block.text)
                            elif block_type == "ResultMessage":
                                if hasattr(block, "result") and block.result:
                                    content_parts.append(block.result)
                            # ToolUseBlock 和 ToolResultBlock 暂不输出到前端
                            # elif block_type == "ToolUseBlock":
                            #     if hasattr(block, "name") and block.name:
                            #         content_parts.append(f"> 调用工具: {block.name}\n")
                            # elif block_type == "ToolResultBlock":
                            #     if hasattr(block, "content") and block.content:
                            #         content_parts.append(block.content)

                elif isinstance(message, ResultMessage):
                    # 直接处理 ResultMessage 类型
                    if hasattr(message, "result") and message.result:
                        content_parts.append(message.result)

                # 合并所有内容部分
                content = "\n\n".join(content_parts) if content_parts else ""

                # 只有非空内容才发送到前端
                if content:
                    t02_answer_data.append(content)
                    await response.write(self._create_response(content))
                    if hasattr(response, "flush"):
                        await response.flush()
                    await asyncio.sleep(0)

            # 发送结束消息
            if not self.running_tasks[task_id]["cancelled"]:
                await response.write(self._create_response("", "end", DataTypeEnum.STREAM_END.value[0]))
            
            # 未取消则记录
            if not self.running_tasks[task_id]["cancelled"]:
                await add_user_record(
                    uuid_str,
                    session_id,
                    query_text,
                    t02_answer_data,
                    {},
                    IntentEnum.COMMON_QA.value[0],
                    user_token,
                    file_list,
                )

        except asyncio.CancelledError:
            await response.write(self._create_response("\n> 这条消息已停止", "info", DataTypeEnum.ANSWER.value[0]))
            await response.write(self._create_response("", "end", DataTypeEnum.STREAM_END.value[0]))
        except Exception as e:
            logger.error("[ERROR] ClaudeSDKAgent 运行异常: %s", e)
            traceback.print_exception(e)
            await response.write(
                self._create_response("[ERROR] 智能体运行异常:", "error", DataTypeEnum.ANSWER.value[0])
            )
        finally:
            if task_id in self.running_tasks:
                del self.running_tasks[task_id]

    async def cancel_task(self, task_id: str) -> bool:
        """取消指定任务"""
        if task_id in self.running_tasks:
            self.running_tasks[task_id]["cancelled"] = True
            return True
        return False

    def get_running_tasks(self):
        """获取当前运行中的任务列表"""
        return list(self.running_tasks.keys())
