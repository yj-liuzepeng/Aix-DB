import logging
import traceback

import pandas as pd
from sqlalchemy.inspection import inspect
from sqlalchemy.sql.expression import text

from agent.text2sql.state.agent_state import AgentState, ExecutionResult
from model.db_connection_pool import get_db_pool

db_pool = get_db_pool()
logger = logging.getLogger(__name__)


class DatabaseService:
    """
    数据库服务类
    """

    def __init__(self):
        pass
        # self.engine = db_pool.get_engine()

    @staticmethod
    def get_table_schema(state: AgentState):
        """
        @:param state
        :param state:
        :return:
        获取数据中所有表schema信息
        :return: 表schema信息
        """
        try:
            logger.info("获取数据库表schema信息")
            inspector = inspect(db_pool.get_engine())
            table_info = {}

            for table_name in inspector.get_table_names():
                columns = {
                    col["name"]: {"type": str(col["type"]), "comment": str(col["comment"])}
                    for col in inspector.get_columns(table_name)
                }
                foreign_keys = [
                    f"{fk['constrained_columns'][0]} -> {fk['referred_table']}.{fk['referred_columns'][0]}"
                    for fk in inspector.get_foreign_keys(table_name)
                ]

                table_info[table_name] = {"columns": columns, "foreign_keys": foreign_keys}
            state["db_info"] = table_info
        except Exception as e:
            logger.error(f"获取数据库表信息失败: {e}")
            state["db_info"] = {}

        return state

    @staticmethod
    def execute_sql(state: AgentState):
        """
        执行SQL
        :param state
        :return: 查询结果
        """
        logger.info("执行SQL语句")
        try:
            with db_pool.get_session() as connection:
                result = connection.execute(text(state["generated_sql"]))
                result_data = result.fetchall()
                column_key = result.keys()
                frame = pd.DataFrame(result_data, columns=column_key)
                state["execution_result"] = ExecutionResult(success=True, data=frame.to_dict(orient="records"))
        except Exception as e:
            traceback.print_exception(e)
            logger.error(f"执行SQL语句失败: {e}")
            state["execution_result"] = ExecutionResult(success=False, error=str(e))
        return state

    def execute_correction_sql(self, state: AgentState):
        """
        执行修正后的SQL
        :param state
        :return: 查询结果
        """
        logger.info("执行修正后的SQL")
        try:
            with self.engine.connect() as connection:
                result = connection.execute(state["correction_result"].corrected_sql_query)
                result_data = result.fetchall()
                column_key = result.keys()
                frame = pd.DataFrame(result_data, columns=column_key)
                state["execution_result"] = ExecutionResult(success=True, data=frame.to_dict(orient="records"))
        except Exception as e:
            logger.error(f"执行修正后的SQL语句失败: {e}")
            state["execution_result"] = ExecutionResult(success=False, error=str(e))
        return state
