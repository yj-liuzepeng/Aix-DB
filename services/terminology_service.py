import json
import logging
from datetime import datetime
from typing import List, Optional

from sqlalchemy import or_, text, desc
from sqlalchemy.orm import Session
from langchain_core.messages import HumanMessage

from common.exception import MyException
from constants.code_enum import SysCodeEnum
from common.llm_util import get_llm
from model import Datasource
from model.db_connection_pool import get_db_pool
from model.db_models import TTerminology
from model.serializers import model_to_dict
from model.schemas import PaginatedResponse

logger = logging.getLogger(__name__)
pool = get_db_pool()


async def query_terminology_list(page: int, size: int, word: Optional[str] = None, dslist: Optional[List[int]] = None):
    """
    分页查询术语
    """
    with pool.get_session() as session:
        query = session.query(TTerminology)
        
        # 筛选条件
        filters = [TTerminology.pid.is_(None)] # 只查询父节点
        
        if word:
            # 搜索：匹配父节点名称或子节点(同义词)名称
            # 先找到匹配的ID
            matched_ids_query = session.query(TTerminology.id).filter(TTerminology.word.ilike(f"%{word}%"))
            matched_ids = [row[0] for row in matched_ids_query.all()]
            
            if matched_ids:
                # 查找这些ID及其父ID
                parent_ids_query = session.query(TTerminology.pid).filter(TTerminology.id.in_(matched_ids), TTerminology.pid.isnot(None))
                parent_ids = [row[0] for row in parent_ids_query.all()]
                
                # 合并ID：直接匹配的ID（如果是父节点） + 子节点对应的父ID
                all_candidate_ids = set(matched_ids) | set(parent_ids)
                filters.append(TTerminology.id.in_(all_candidate_ids))
            else:
                return PaginatedResponse(records=[], current_page=page, total_count=0, total_pages=0)

        if dslist:
             # 数据源筛选
             ds_conditions = [TTerminology.specific_ds == False]
             
             ds_str_list = [str(d) for d in dslist]
             ds_vals = ", ".join([f"'{d}'" for d in ds_str_list])
             if ds_vals:
                 ds_check = text(f"""
                    specific_ds = true AND datasource_ids IS NOT NULL AND EXISTS (
                        SELECT 1 FROM json_array_elements_text(datasource_ids::json) WHERE value IN ({ds_vals})
                    )
                 """)
                 ds_conditions.append(ds_check)
             
             filters.append(or_(*ds_conditions))

        query = query.filter(*filters)
        
        total_count = query.count()
        total_pages = (total_count + size - 1) // size
        
        records = query.order_by(desc(TTerminology.create_time)).offset((page - 1) * size).limit(size).all()
        
        result_list = []
        for record in records:
            item = model_to_dict(record)
            
            # 查询子节点（同义词）
            children = session.query(TTerminology).filter(TTerminology.pid == record.id).all()
            item['other_words'] = [c.word for c in children]
            
            # 解析 datasource_ids 获取名称
            item['datasource_names'] = []
            item['datasource_ids'] = []
            if record.specific_ds and record.datasource_ids:
                try:
                    ds_ids = json.loads(record.datasource_ids)
                    item['datasource_ids'] = ds_ids
                    if ds_ids:
                        ds_names = session.query(Datasource.name).filter(Datasource.id.in_(ds_ids)).all()
                        item['datasource_names'] = [r[0] for r in ds_names]
                except:
                    pass
            
            result_list.append(item)
            
        return PaginatedResponse(
            records=result_list,
            current_page=page,
            total_count=total_count,
            total_pages=total_pages,
        )

async def create_terminology(word: str, description: str, other_words: List[str], specific_ds: bool, datasource_ids: List[int], oid: int = 1):
    with pool.get_session() as session:
        # 检查重复
        all_words = [word] + other_words
        # 检查数据库中是否已存在这些词（作为父节点或子节点）
        existing = session.query(TTerminology).filter(TTerminology.word.in_(all_words)).first()
        if existing:
            raise MyException(SysCodeEnum.PARAM_ERROR, f"术语或同义词 '{existing.word}' 已存在")
            
        # 创建父节点
        parent = TTerminology(
            word=word,
            description=description,
            specific_ds=specific_ds,
            datasource_ids=json.dumps(datasource_ids) if datasource_ids else '[]',
            oid=oid,
            enabled=True,
            create_time=datetime.now()
        )
        session.add(parent)
        session.flush() # 获取ID
        
        # 创建子节点
        for ow in other_words:
            if not ow.strip():
                continue
            child = TTerminology(
                pid=parent.id,
                word=ow,
                specific_ds=specific_ds,
                datasource_ids=json.dumps(datasource_ids) if datasource_ids else '[]',
                oid=oid,
                enabled=True,
                create_time=datetime.now()
            )
            session.add(child)
            
        session.commit()
        return True

async def update_terminology(id: int, word: str, description: str, other_words: List[str], specific_ds: bool, datasource_ids: List[int], oid: int = 1):
    with pool.get_session() as session:
        parent = session.query(TTerminology).filter(TTerminology.id == id).first()
        if not parent:
            raise MyException(SysCodeEnum.PARAM_ERROR, "术语不存在")
            
        # 检查重复 (排除自己和自己的子节点)
        all_words = [word] + other_words
        existing = session.query(TTerminology).filter(
            TTerminology.word.in_(all_words),
            TTerminology.id != id,
            or_(TTerminology.pid != id, TTerminology.pid.is_(None)) 
        ).first()
        
        if existing:
             raise MyException(SysCodeEnum.PARAM_ERROR, f"术语或同义词 '{existing.word}' 已存在")

        # 更新父节点
        parent.word = word
        parent.description = description
        parent.specific_ds = specific_ds
        parent.datasource_ids = json.dumps(datasource_ids) if datasource_ids else '[]'
        
        # 删除旧子节点
        session.query(TTerminology).filter(TTerminology.pid == id).delete()
        
        # 添加新子节点
        for ow in other_words:
            if not ow.strip():
                continue
            child = TTerminology(
                pid=parent.id,
                word=ow,
                specific_ds=specific_ds,
                datasource_ids=json.dumps(datasource_ids) if datasource_ids else '[]',
                oid=oid,
                enabled=parent.enabled,
                create_time=datetime.now()
            )
            session.add(child)
            
        session.commit()
        return True

async def delete_terminology(ids: List[int]):
    with pool.get_session() as session:
        # 删除父节点和子节点
        session.query(TTerminology).filter(or_(TTerminology.id.in_(ids), TTerminology.pid.in_(ids))).delete(synchronize_session=False)
        session.commit()
        return True

async def enable_terminology(id: int, enabled: bool):
    with pool.get_session() as session:
        # 更新父节点和子节点
        session.query(TTerminology).filter(or_(TTerminology.id == id, TTerminology.pid == id)).update({TTerminology.enabled: enabled}, synchronize_session=False)
        session.commit()
        return True

async def get_terminology_detail(id: int):
    with pool.get_session() as session:
        record = session.query(TTerminology).filter(TTerminology.id == id).first()
        if not record:
            return None
            
        item = model_to_dict(record)
        
        # 查询子节点
        children = session.query(TTerminology).filter(TTerminology.pid == record.id).all()
        item['other_words'] = [c.word for c in children]
        
        # 解析 datasource_ids
        item['datasource_ids'] = []
        item['datasource_names'] = []
        if record.datasource_ids:
            try:
                ds_ids = json.loads(record.datasource_ids)
                item['datasource_ids'] = ds_ids
                if ds_ids:
                    ds_names = session.query(Datasource.name).filter(Datasource.id.in_(ds_ids)).all()
                    item['datasource_names'] = [r[0] for r in ds_names]
            except:
                pass
                
        return item

async def generate_synonyms_by_llm(word: str) -> List[str]:
    """
    使用LLM生成同义词
    """
    try:
        llm = get_llm()
        prompt = f"""
        请为术语 "{word}" 生成5个同义词，用于数据分析和商业智能场景。
        请直接返回JSON数组格式的字符串，例如 ["词1", "词2"]。
        不要包含Markdown标记或其他文本。
        """
        response = await llm.ainvoke([HumanMessage(content=prompt)])
        content = response.content.strip()
        
        # 清理可能存在的markdown代码块标记
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()
            
        try:
            result = json.loads(content)
            if isinstance(result, list):
                return [str(w) for w in result]
            else:
                return []
        except json.JSONDecodeError:
            # 如果解析失败，尝试按逗号分割
            return [w.strip() for w in content.split(",") if w.strip()]
            
    except Exception as e:
        logger.error(f"Error generating synonyms: {e}")
        # 如果是因为没有配置模型，抛出特定错误
        if "No default AI model" in str(e):
             raise MyException(SysCodeEnum.PARAM_ERROR, "未配置默认AI模型，请先在模型管理中配置")
        raise MyException(SysCodeEnum.c_9999, f"AI生成失败: {str(e)}")
