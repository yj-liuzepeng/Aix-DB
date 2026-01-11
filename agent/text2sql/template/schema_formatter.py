"""
Schema 格式化工具
将当前项目的 db_info 字典格式转换为 SQLBot 需要的 M-Schema 字符串格式
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


def format_schema_to_m_schema(
    db_info: Dict[str, Dict[str, Any]],
    db_name: str = "database",
    db_type: str = "mysql",
) -> str:
    """
    将 db_info 字典格式转换为 M-Schema 字符串格式
    
    Args:
        db_info: 数据库信息字典，格式为：
            {
                "table_name": {
                    "columns": {
                        "column_name": {
                            "type": "VARCHAR(255)",
                            "comment": "列注释"
                        }
                    },
                    "table_comment": "表注释",
                    "foreign_keys": ["column -> table.column"]
                }
            }
        db_name: 数据库名称（默认：database）
        db_type: 数据库类型（默认：mysql）
    
    Returns:
        M-Schema 格式的字符串
    """
    if not db_info:
        return ""
    
    schema_str = f"【DB_ID】 {db_name}\n【Schema】\n"
    
    for table_name, table_info in db_info.items():
        # 构建表定义行
        if db_type in ["mysql", "es"]:
            # MySQL 和 Elasticsearch 不使用 schema 前缀
            schema_table = f"# Table: {table_name}"
        else:
            # 其他数据库使用 schema.table 格式
            schema_table = f"# Table: {db_name}.{table_name}"
        
        # 添加表注释
        table_comment = table_info.get("table_comment", "").strip()
        if table_comment:
            schema_table += f", {table_comment}"
        
        schema_table += "\n[\n"
        
        # 添加字段定义
        columns = table_info.get("columns", {})
        if columns:
            field_list = []
            for column_name, column_info in columns.items():
                column_type = column_info.get("type", "VARCHAR")
                column_comment = column_info.get("comment", "").strip()
                
                if column_comment:
                    field_list.append(f"({column_name}:{column_type}, {column_comment})")
                else:
                    field_list.append(f"({column_name}:{column_type})")
            
            schema_table += ",\n".join(field_list)
        
        schema_table += "\n]\n"
        schema_str += schema_table
    
    # 添加外键关系信息（如果存在）
    # 当前项目中，表关系信息通过 Neo4j 获取，格式为：
    # [{"from_table": "table1", "relationship": "relation", "to_table": "table2"}, ...]
    # SQLBot 的格式为：table1.column=table2.column
    # 由于当前项目的表关系信息不包含具体的列信息，暂时不添加外键部分
    # TODO: 阶段二可以增强，从 Neo4j 或数据库 metadata 中获取完整的外键信息
    
    return schema_str


def get_database_engine_info(
    db_type: str,
    db_version: Optional[str] = None,
) -> str:
    """
    获取数据库引擎信息字符串
    
    Args:
        db_type: 数据库类型（如 'mysql', 'pg', 'oracle' 等）
        db_version: 数据库版本（可选）
    
    Returns:
        引擎信息字符串，格式如 "MySQL 8.0" 或 "PostgreSQL 17.6"
    """
    db_type_map = {
        "mysql": "MySQL",
        "pg": "PostgreSQL",
        "postgresql": "PostgreSQL",
        "oracle": "Oracle",
        "sqlserver": "Microsoft SQL Server",
        "mssql": "Microsoft SQL Server",
        "ck": "ClickHouse",
        "clickhouse": "ClickHouse",
        "redshift": "AWS Redshift",
        "elasticsearch": "Elasticsearch",
        "es": "Elasticsearch",
        "starrocks": "StarRocks",
        "doris": "Apache Doris",
        "dm": "DM",
        "kingbase": "Kingbase",
    }
    
    engine_name = db_type_map.get(db_type.lower(), "MySQL")
    
    if db_version:
        return f"{engine_name} {db_version}"
    else:
        # 如果没有提供版本，使用默认版本
        default_versions = {
            "MySQL": "8.0",
            "PostgreSQL": "17.6",
            "Oracle": "19c",
            "Microsoft SQL Server": "2019",
            "ClickHouse": "24.0",
        }
        version = default_versions.get(engine_name, "")
        return f"{engine_name} {version}" if version else engine_name

