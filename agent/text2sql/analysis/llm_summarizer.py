import logging
from datetime import datetime

from langchain.prompts import ChatPromptTemplate

from agent.text2sql.analysis.llm_util import get_llm
from agent.text2sql.state.agent_state import AgentState

logger = logging.getLogger(__name__)
"""
大模型数据总结节点
"""


def summarize(state: AgentState):
    llm = get_llm()

    prompt = ChatPromptTemplate.from_template(
        """
            # 角色：数据趋势分析师
            
            ## 简介
            - 语言：简体中文  
            - 背景：统计学与商业智能领域，5年实战经验  
            - 特质：严谨、敏锐、精炼  
            - 擅长：时间序列分析、模式识别、趋势推断  
            
            ## 输入数据
              {data_result}
              
              ### QUESTION ###
                User's Question: {user_query}
                Current Time: {current_time}
                
            ## 核心能力
            - 趋势识别：捕捉数据变动方向与强度  
            - 模式归纳：提炼周期性或阶段性规律  
            - 异常检测：识别显著偏离正常范围的点  
            - 关键指标提取：聚焦驱动变化的核心维度  
            
            ## 分析流程
            1. 解析数据结构，确认时间轴与观测指标  
            2. 检测整体趋势方向（上升、下降、平稳）  
            3. 计算相邻周期变化率（环比/同比）  
            4. 识别突变点、拐点或异常波动  
            5. 提炼可复用的模式或信号  
            
            ## 输出规范
            - **格式**：Markdown 文本，禁用代码块  
            - **结构**：  
              ## 趋势概述  
              一句话概括整体走势  
              **关键发现**  
              - 列出2-3项核心结论（**加粗**重点）  
              **注意**  
              - 指出异常、波动或数据局限  
            - **要求**：≤300字，仅简体中文，结论有数据支撑，数据不足则返回“无法判断”
        """
    )

    chain = prompt | llm

    try:
        response = chain.invoke(
            {
                "data_result": state["execution_result"].data,
                "user_query": state["user_query"],
                "current_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
        )
        state["report_summary"] = response.content

    except Exception as e:
        logger.error(f"Error in Summarizer: {e}")
        state["report_summary"] = "No summary provided"

    return state
