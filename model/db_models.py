import datetime
from dataclasses import dataclass
from typing import Optional

from sqlalchemy import BigInteger, Column, DateTime, Float, Integer, String, TIMESTAMP, Table, text
from sqlalchemy.dialects.mysql import LONGTEXT, TEXT, VARCHAR
from sqlalchemy.orm import Mapped, mapped_column

from model.db_connection_pool import Base

"""
读取数据生成ORM数据库实体Bean
sqlacodegen mysql+pymysql://root:1@127.0.0.1:13006/chat_db --outfile=models.py
sqlacodegen mysql+pymysql://root:1@127.0.0.1:13006/chat_db --outfile=models.py --tables t_alarm_info --noviews
"""


@dataclass
class TAlarmInfo(Base):
    __tablename__ = "t_alarm_info"
    __table_args__ = {"comment": "诈骗数据"}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    Incident_addr: Mapped[Optional[str]] = mapped_column(VARCHAR(1000), comment="案发地点")
    division_name: Mapped[Optional[str]] = mapped_column(VARCHAR(100), comment="所属分局")
    call_in_type: Mapped[Optional[str]] = mapped_column(VARCHAR(100), comment="来电类别")
    caller_name: Mapped[Optional[str]] = mapped_column(VARCHAR(100), comment="报警人姓名")
    caller_sex: Mapped[Optional[str]] = mapped_column(VARCHAR(100), comment="性别")
    caller_age: Mapped[Optional[int]] = mapped_column(Integer, comment="性别")
    caller_education: Mapped[Optional[str]] = mapped_column(VARCHAR(100), comment="文化程度")
    caller_job: Mapped[Optional[str]] = mapped_column(VARCHAR(100), comment="受害人职业")
    caller_phone_type: Mapped[Optional[str]] = mapped_column(VARCHAR(100), comment="手机品牌")
    fraud_money: Mapped[Optional[float]] = mapped_column(Float, comment="涉案资金")
    is_fraud: Mapped[Optional[str]] = mapped_column(VARCHAR(100), comment="是否电诈(是，否）")
    fraud_general_class: Mapped[Optional[str]] = mapped_column(VARCHAR(100), comment="诈骗大类")
    drainage_type: Mapped[Optional[str]] = mapped_column(VARCHAR(100), comment="引流方式")
    drainage_addr_account: Mapped[Optional[str]] = mapped_column(VARCHAR(100), comment="引流地址、账号")
    drainage_time: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, comment="引流联系时间")
    fraud_publicity: Mapped[Optional[str]] = mapped_column(VARCHAR(100), comment="是否看（听）过反诈宣传(是，否）")
    registration_time: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, comment="登记时间")


class TDemandDocMeta(Base):
    __tablename__ = "t_demand_doc_meta"
    __table_args__ = {"comment": "需求文档元信息"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[Optional[int]] = mapped_column(Integer, comment="用户id")
    demand_id: Mapped[Optional[int]] = mapped_column(Integer, comment="项目id")
    page_title: Mapped[Optional[str]] = mapped_column(VARCHAR(100), comment="文档段落标题名称")
    page_content: Mapped[Optional[str]] = mapped_column(TEXT, comment="文档段落内容")
    create_time: Mapped[Optional[datetime.datetime]] = mapped_column(TIMESTAMP)
    update_time: Mapped[Optional[datetime.datetime]] = mapped_column(TIMESTAMP)


class TDemandManager(Base):
    __tablename__ = "t_demand_manager"
    __table_args__ = {"comment": "测试助手-需求文档管理"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    file_key: Mapped[str] = mapped_column(VARCHAR(100), nullable=False, comment="文件minio key")
    user_id: Mapped[Optional[int]] = mapped_column(Integer, comment="用户id")
    doc_name: Mapped[Optional[str]] = mapped_column(VARCHAR(100), comment="项目名称")
    doc_desc: Mapped[Optional[str]] = mapped_column(VARCHAR(200), comment="项目简介")
    fun_num: Mapped[Optional[int]] = mapped_column(Integer, server_default=text("'0'"), comment="功能数")
    create_time: Mapped[Optional[datetime.datetime]] = mapped_column(TIMESTAMP, comment="创建时间")
    update_time: Mapped[Optional[datetime.datetime]] = mapped_column(TIMESTAMP, comment="更新时间")


class TReportInfo(Base):
    __tablename__ = "t_report_info"
    __table_args__ = {"comment": "报告记录表"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[Optional[str]] = mapped_column(VARCHAR(100), comment="报告名称")
    markdown: Mapped[Optional[str]] = mapped_column(LONGTEXT, comment="报告内容")
    create_time: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, comment="创建时间")


class TUser(Base):
    __tablename__ = "t_user"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    userName: Mapped[Optional[str]] = mapped_column(VARCHAR(200), comment="用户名称")
    password: Mapped[Optional[str]] = mapped_column(VARCHAR(300), comment="密码")
    mobile: Mapped[Optional[str]] = mapped_column(VARCHAR(100), comment="手机号")
    createTime: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, comment="创建时间")
    updateTime: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, comment="修改时间")


class TUserQaRecord(Base):
    __tablename__ = "t_user_qa_record"
    __table_args__ = {"comment": "问答记录表"}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[Optional[int]] = mapped_column(Integer, comment="用户id")
    uuid: Mapped[Optional[str]] = mapped_column(VARCHAR(200), comment="自定义id")
    conversation_id: Mapped[Optional[str]] = mapped_column(String(100), comment="diy/对话id")
    message_id: Mapped[Optional[str]] = mapped_column(String(100), comment="dify/消息id")
    task_id: Mapped[Optional[str]] = mapped_column(String(100), comment="dify/任务id")
    chat_id: Mapped[Optional[str]] = mapped_column(String(100), comment="对话id")
    question: Mapped[Optional[str]] = mapped_column(TEXT, comment="用户问题")
    to2_answer: Mapped[Optional[str]] = mapped_column(LONGTEXT, comment="大模型答案")
    to4_answer: Mapped[Optional[str]] = mapped_column(LONGTEXT, comment="业务数据")
    qa_type: Mapped[Optional[str]] = mapped_column(String(100), comment="问答类型")
    file_key: Mapped[Optional[str]] = mapped_column(String(100), comment="文件minio/key")
    create_time: Mapped[Optional[datetime.datetime]] = mapped_column(
        TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"), comment="创建时间"
    )


t_view_alarm_detail = Table(
    "view_alarm_detail",
    Base.metadata,
    Column("案发地点", String(1000)),
    Column("所属分局", String(100)),
    Column("来电类别", String(100)),
    Column("报警人姓名", String(100)),
    Column("性别", String(100)),
    Column("年龄", Integer),
    Column("文化程度", String(100)),
    Column("受害人职业", String(100)),
    Column("手机品牌", String(100)),
    Column("涉案资金", Float),
    Column("是否电诈", String(100)),
    Column("诈骗类型", String(100)),
    Column("引流方式", String(100)),
    Column("引流地址", String(100)),
    Column("引流联系时间", DateTime),
    Column("是否看过反诈宣传", String(100)),
    Column("登记时间", DateTime),
)
