"""
术语检索器
基于关键词匹配检索术语，格式化为模板所需的 XML 格式
注意：当前项目的 TTerminology 表没有 embedding 字段，暂时只支持关键词匹配
"""

import json
import logging
from typing import List, Optional, Dict, Any
from sqlalchemy import or_, and_, text
from sqlalchemy.orm import Session

from model.db_connection_pool import get_db_pool
from model.db_models import TTerminology
from model.datasource_models import Datasource

logger = logging.getLogger(__name__)
pool = get_db_pool()


def retrieve_terminologies(
    question: str,
    datasource_id: Optional[int] = None,
    oid: int = 1,
    top_k: int = 10,
) -> str:
    """
    检索术语并格式化为模板所需的 XML 格式
    
    Args:
        question: 用户问题
        datasource_id: 数据源ID（可选）
        oid: 组织ID（默认：1）
        top_k: 返回的最大术语数量（默认：10）
    
    Returns:
        格式化的术语 XML 字符串，如果没有找到则返回空字符串
    """
    if not question or not question.strip():
        return ""
    
    try:
        with pool.get_session() as session:
            # 查询匹配的术语
            results = _select_terminology_by_word(
                session=session,
                word=question,
                oid=oid,
                datasource_id=datasource_id,
                top_k=top_k,
            )
            
            if not results or len(results) == 0:
                return ""
            
            # 格式化为 XML
            xml_str = _format_terminologies_to_xml(results)
            
            # 使用模板格式化
            from agent.text2sql.template.template_loader import TemplateLoader
            base_template = TemplateLoader.load_base_template()
            terminology_template = base_template['template']['terminology']
            
            return terminology_template.format(terminologies=xml_str)
            
    except Exception as e:
        logger.error(f"检索术语失败: {e}", exc_info=True)
        return ""


def _select_terminology_by_word(
    session: Session,
    word: str,
    oid: int,
    datasource_id: Optional[int] = None,
    top_k: int = 10,
) -> List[Dict[str, Any]]:
    """
    通过关键词匹配检索术语
    
    Args:
        session: 数据库会话
        word: 搜索关键词
        oid: 组织ID
        datasource_id: 数据源ID（可选）
        top_k: 返回的最大数量
    
    Returns:
        术语列表，格式为 [{"words": [...], "description": "..."}, ...]
    """
    # 查询匹配的术语（关键词匹配）
    stmt = session.query(TTerminology).filter(
        and_(
            text(":sentence ILIKE '%' || word || '%'"),
            TTerminology.oid == oid,
            TTerminology.enabled == True,
        )
    )
    
    if datasource_id is not None:
        # 数据源筛选：通用术语或指定数据源的术语
        stmt = stmt.filter(
            or_(
                or_(TTerminology.specific_ds == False, TTerminology.specific_ds.is_(None)),
                and_(
                    TTerminology.specific_ds == True,
                    TTerminology.datasource_ids.isnot(None),
                    text(f"datasource_ids::jsonb @> jsonb_build_array({datasource_id})")
                )
            )
        )
    else:
        stmt = stmt.filter(
            or_(TTerminology.specific_ds == False, TTerminology.specific_ds.is_(None))
        )
    
    # 执行查询
    results = stmt.params(sentence=word).limit(top_k * 2).all()  # 多查一些，因为要去重
    
    # 收集术语ID（包含父节点和子节点）
    terminology_ids = set()
    for term in results:
        if term.pid is not None:
            terminology_ids.add(term.pid)
        else:
            terminology_ids.add(term.id)
    
    if len(terminology_ids) == 0:
        return []
    
    # 查询完整的术语信息（包含父节点和子节点）
    all_terms = session.query(TTerminology).filter(
        or_(TTerminology.id.in_(list(terminology_ids)), TTerminology.pid.in_(list(terminology_ids)))
    ).all()
    
    # 组织为字典格式
    term_dict = {}
    for term in all_terms:
        pid = term.pid if term.pid is not None else term.id
        if pid not in term_dict:
            term_dict[pid] = {
                "words": [],
                "description": term.description or "",
            }
        term_dict[pid]["words"].append(term.word or "")
    
    # 转换为列表，限制数量
    result_list = []
    for pid, term_data in list(term_dict.items())[:top_k]:
        result_list.append(term_data)
    
    return result_list


def _format_terminologies_to_xml(terminologies: List[Dict[str, Any]]) -> str:
    """
    将术语列表格式化为 XML 字符串
    
    Args:
        terminologies: 术语列表，格式为 [{"words": [...], "description": "..."}, ...]
    
    Returns:
        XML 字符串
    """
    if not terminologies:
        return ""
    
    # 构建 XML
    xml_parts = ["<terminologies>"]
    
    for term in terminologies:
        words = term.get("words", [])
        description = term.get("description", "")
        
        xml_parts.append("  <terminology>")
        xml_parts.append("    <words>")
        for word in words:
            if word:
                xml_parts.append(f'      <word><![CDATA[{word}]]></word>')
        xml_parts.append("    </words>")
        if description:
            xml_parts.append(f'    <description><![CDATA[{description}]]></description>')
        xml_parts.append("  </terminology>")
    
    xml_parts.append("</terminologies>")
    
    return "\n".join(xml_parts)

