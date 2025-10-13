import logging
import traceback

logger = logging.getLogger(__name__)


def exe_sql_query(state):
    """
    执行sql语句
    :param state:
    :return:
    """
    try:
        pass
    except Exception as e:
        traceback.print_exception(e)
        logging.error(f"Error in executing SQL query: {e}")
