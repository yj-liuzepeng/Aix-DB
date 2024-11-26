import json
import logging
import os
import re
import traceback
import uuid
from typing import Dict

import aiohttp

from common.exception import MyException
from constants.code_enum import (
    DiFyAppEnum,
    DataTypeEnum,
    DiFyCodeEnum,
    SysCodeEnum,
***REMOVED***
from services.db_qadata_process import process
from services.user_service import add_question_record


class QaContext:
    """问答上下文信息"""

    def __init__(self, token, question, chat_id***REMOVED***:
        self.token = token
        self.question = question
        self.chat_id = chat_id


class DiFyRequest:
    """
    DiFy操作服务类
    """

    def __init__(self***REMOVED***:
        pass

    async def exec_query(self, res***REMOVED***:
        """

        :return:
        """
        try:
            # 获取请求体内容 从res流对象获取request-body
            req_body_content = res.request.body
            # 将字节流解码为字符串
            body_str = req_body_content.decode("utf-8"***REMOVED***

            req_obj = json.loads(body_str***REMOVED***
            logging.info(f"query param: {body_str***REMOVED***"***REMOVED***

            uuid_str = str(uuid.uuid4(***REMOVED******REMOVED***
            query = req_obj.get("query"***REMOVED***
            #  使用正则表达式移除所有空白字符（包括空格、制表符、换行符等）
            cleaned_query = re.sub(r"\s+", "", query***REMOVED***
            source_chat = {
                "chat_id": uuid_str,
                "query": cleaned_query,
                "qa_type": req_obj.get("qa_type"***REMOVED***,
            ***REMOVED***

            # 获取登录用户信息
            token = res.request.headers.get("Authorization"***REMOVED***
            if not token:
                raise MyException(SysCodeEnum.c_401***REMOVED***
            if token.startswith("Bearer "***REMOVED***:
                token = token.split(" "***REMOVED***[1]

            # 封装问答上下文信息
            qa_context = QaContext(token, query, uuid_str***REMOVED***

            # 判断请求类别
            app_key = self._get_authorization_token(source_chat***REMOVED***

            # 构建请求参数
            dify_service_url, body_params, headers = self._build_request(source_chat["query"], app_key***REMOVED***

            async with aiohttp.ClientSession(read_bufsize=1024 * 16***REMOVED*** as session:
                async with session.post(
                    dify_service_url,
                    headers=headers,
                    json=body_params,
                    timeout=aiohttp.ClientTimeout(total=60 * 2***REMOVED***,  # 等待2分钟超时
                ***REMOVED*** as response:
                    logging.info(f"dify response status: {response.status***REMOVED***"***REMOVED***
                    if response.status == 200:
                        await self.res_begin(res, uuid_str***REMOVED***
                        data_type = ""
                        bus_data = ""
                        while True:
                            reader = response.content
                            reader._high_water = 10 * 1024 * 1024  # 设置为10MB
                            chunk = await reader.readline(***REMOVED***
                            if not chunk:
                                break
                            str_chunk = chunk.decode("utf-8"***REMOVED***
                            if str_chunk.startswith("data"***REMOVED***:
                                str_data = str_chunk[5:]
                                data_json = json.loads(str_data***REMOVED***
                                event_name = data_json.get("event"***REMOVED***
                                if DiFyCodeEnum.MESSAGE.value[0] == event_name:
                                    answer = data_json.get("answer"***REMOVED***
                                    if answer and answer.startswith("dify_"***REMOVED***:
                                        event_list = answer.split("_"***REMOVED***
                                        if event_list[1] == "0":
                                            # 输出开始
                                            data_type = event_list[2]
                                            if data_type == DataTypeEnum.ANSWER.value[0]:
                                                await self.send_message(res, qa_context, {"data": {"messageType": "begin"***REMOVED***, "dataType": data_type***REMOVED******REMOVED***
                                        elif event_list[1] == "1":
                                            # 输出结束
                                            data_type = event_list[2]
                                            if data_type == DataTypeEnum.ANSWER.value[0]:
                                                await self.send_message(res, qa_context, {"data": {"messageType": "end"***REMOVED***, "dataType": data_type***REMOVED******REMOVED***

                                            # 输出业务数据
                                            elif bus_data and data_type == DataTypeEnum.BUS_DATA.value[0]:
                                                res_data = process(json.loads(bus_data***REMOVED***["data"]***REMOVED***
                                                # logging.info(f"chart_data: {res_data***REMOVED***"***REMOVED***
                                                await self.send_message(
                                                    res,
                                                    qa_context,
                                                  ***REMOVED***"data": res_data, "dataType": data_type***REMOVED***,
                                                ***REMOVED***

                                            data_type = ""

                                    elif len(data_type***REMOVED*** > 0:
                                        # 这里输出 t02之间的内容
                                        if data_type == DataTypeEnum.ANSWER.value[0]:
                                            await self.send_message(
                                                res,
                                                qa_context,
                                              ***REMOVED***"data": {"messageType": "continue", "content": answer***REMOVED***, "dataType": data_type***REMOVED***,
                                            ***REMOVED***

                                        # 这里设置业务数据
                                        if data_type == DataTypeEnum.BUS_DATA.value[0]:
                                            bus_data = answer
        except Exception as e:
            logging.error(f"Error during get_answer: {e***REMOVED***"***REMOVED***
            traceback.print_exception(e***REMOVED***
        ***REMOVED***"error": str(e***REMOVED******REMOVED***  # 返回错误信息作为字典
        finally:
            await self.res_end(res***REMOVED***

    @staticmethod
    async def send_message(response, qa_context, message***REMOVED***:
        """
            SSE 格式发送数据，每一行以 data: 开头
        :param response:
        :param qa_context
        :param message:
        :return:
        """
        await response.write("data:" + json.dumps(message, ensure_ascii=False***REMOVED*** + "\n\n"***REMOVED***

        # 保存用户问答记录 1.保存用户问题 2.保存用户答案 t02 和 t04
        if "content" in message["data"]:
            await add_question_record(qa_context.token, qa_context.chat_id, qa_context.question, message, ""***REMOVED***
        elif message["dataType"] == DataTypeEnum.BUS_DATA.value[0]:
            await add_question_record(qa_context.token, qa_context.chat_id, qa_context.question, "", message***REMOVED***

    @staticmethod
    async def res_begin(res, uuid_str***REMOVED***:
        """

        :param res:
        :param uuid_str:
        :return:
        """
        await res.write(
            "data:"
            + json.dumps(
              ***REMOVED***
                    "data": {"id": uuid_str***REMOVED***,
                    "dataType": DataTypeEnum.TASK_ID.value[0],
                ***REMOVED***
            ***REMOVED***
            + "\n\n"
        ***REMOVED***

    @staticmethod
    async def res_end(res***REMOVED***:
        """
        :param res:
        :return:
        """
        await res.write(
            "data:"
            + json.dumps(
              ***REMOVED***
                    "data": "DONE",
                    "dataType": DataTypeEnum.STREAM_END.value[0],
                ***REMOVED***
            ***REMOVED***
            + "\n\n"
        ***REMOVED***

    @staticmethod
    def _build_request(query, app_key***REMOVED***:
        """
        构建请求参数
        :param app_key:
        :param query:
        :return:
        """
        body_params = {
            "inputs": {***REMOVED***,
            "query": query,
            "response_mode": "streaming",
            "user": "abc-123",
        ***REMOVED***
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {app_key.value[1]***REMOVED***",
        ***REMOVED***

        if os.getenv("ENV"***REMOVED*** == "test":
            dify_service_url = os.getenv("DIFY_SERVICE_URL_TEST"***REMOVED***
        else:
            dify_service_url = os.getenv("DIFY_SERVICE_URL_DEV"***REMOVED***

        return dify_service_url, body_params, headers

    @staticmethod
    def _get_authorization_token(source_chat: Dict***REMOVED***:
        """
            根据请求类别获取api/token
            :param source_chat
        :return:
        """
        qa_type = source_chat["qa_type"]
        if qa_type == DiFyAppEnum.DATABASE_QA.value[0]:
            return DiFyAppEnum.DATABASE_QA
        if qa_type == DiFyAppEnum.FILEDATA_QA.value[0]:
            return DiFyAppEnum.FILEDATA_QA
        else:
            raise ValueError("问答类型不支持"***REMOVED***
