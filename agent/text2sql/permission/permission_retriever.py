"""
权限检索器
获取用户的权限过滤条件
"""

import json
import logging
from typing import List, Dict, Any, Optional

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from model.db_connection_pool import get_db_pool
from model.db_models import TDsRules, TDsPermission
from model.datasource_models import DatasourceTable, Datasource
from agent.text2sql.permission.row_permission import trans_filter_tree

logger = logging.getLogger(__name__)
pool = get_db_pool()


def get_user_permission_filters(
    datasource_id: int,
    user_id: int,
    table_names: Optional[List[str]] = None,
) -> List[Dict[str, str]]:
    """
    获取用户的权限过滤条件（行级权限）
    
    Args:
        datasource_id: 数据源ID
        user_id: 用户ID（如果为1，表示管理员，不应用权限过滤）
        table_names: 表名列表（可选，如果为None则获取所有表的权限）
    
    Returns:
        权限过滤条件列表，格式为 [{"table": "表名", "filter": "SQL WHERE条件字符串"}, ...]
        如果用户是管理员或没有权限，返回空列表
    """
    # 管理员（user_id=1）不应用权限过滤
    if user_id == 1:
        return []
    
    try:
        with pool.get_session() as session:
            filters = []
            
            # 获取数据源信息（用于获取数据库类型）
            datasource = session.query(Datasource).filter(Datasource.id == datasource_id).first()
            if not datasource:
                logger.warning(f"数据源不存在: datasource_id={datasource_id}")
                return []
            
            db_type = datasource.type or "mysql"
            
            # 获取所有规则
            rules_stmt = select(TDsRules).where(TDsRules.enable == True)
            rules = session.execute(rules_stmt).scalars().all()
            
            if not rules:
                return []
            
            # 获取表信息
            if table_names:
                tables_stmt = select(DatasourceTable).where(
                    and_(
                        DatasourceTable.ds_id == datasource_id,
                        DatasourceTable.table_name.in_(table_names)
                    )
                )
            else:
                tables_stmt = select(DatasourceTable).where(
                    DatasourceTable.ds_id == datasource_id
                )
            
            tables = session.execute(tables_stmt).scalars().all()
            
            # 对每个表获取权限过滤条件
            for table in tables:
                # 查询该表的行权限
                permissions_stmt = select(TDsPermission).where(
                    and_(
                        TDsPermission.table_id == table.id,
                        TDsPermission.type == 'row',
                        TDsPermission.enable == True
                    )
                )
                row_permissions = session.execute(permissions_stmt).scalars().all()
                
                if not row_permissions:
                    continue
                
                # 检查权限是否与用户匹配（通过规则）
                matching_permissions = []
                for permission in row_permissions:
                    # 检查权限是否在某个规则中，且该规则包含当前用户
                    for rule in rules:
                        perm_ids = []
                        if rule.permission_list:
                            try:
                                perm_ids = json.loads(rule.permission_list)
                            except:
                                pass
                        
                        user_ids = []
                        if rule.user_list:
                            try:
                                user_ids = json.loads(rule.user_list)
                            except:
                                pass
                        
                        # 检查权限ID和用户ID是否匹配
                        if perm_ids and user_ids:
                            # 用户ID可能是整数或字符串
                            if permission.id in perm_ids and (
                                user_id in user_ids or str(user_id) in user_ids
                            ):
                                matching_permissions.append(permission)
                                break
                
                # 如果有匹配的权限，构建过滤条件
                if matching_permissions:
                    # 收集所有表达式树
                    expression_trees = []
                    for perm in matching_permissions:
                        if perm.expression_tree:
                            try:
                                expr_tree = json.loads(perm.expression_tree)
                                expression_trees.append(expr_tree)
                            except Exception as e:
                                logger.warning(f"解析表达式树失败: {e}, permission_id={perm.id}")
                                continue
                    
                    if expression_trees:
                        # 使用 trans_filter_tree 将表达式树转换为 SQL WHERE 条件
                        filter_str = trans_filter_tree(
                            session=session,
                            expression_trees=expression_trees,
                            db_type=db_type,
                            table_name=table.table_name,
                        )
                        
                        if filter_str:
                            filters.append({
                                "table": table.table_name,
                                "filter": filter_str  # SQL WHERE 条件字符串
                            })
            
            return filters
            
    except Exception as e:
        logger.error(f"获取用户权限过滤条件失败: {e}", exc_info=True)
        return []

