import random
import uuid as uuid_module
import sqlalchemy
from sqlalchemy import create_engine, select, Column, String, Integer, MetaData, Table, inspect
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from .utils import str_hash

Base = declarative_base()

class CacheEntry(Base):
    __tablename__ = 'prompt_cache2'
    index = Column(String, primary_key=True)
    key = Column(String)
    value = Column(String)

class Project_Task(Base):
    __tablename__ = 'project_task'
    id = Column(Integer, autoincrement=True, primary_key=True)
    uuid = Column(String, unique=True, index=True)  # UUID列
    project_id = Column(String, index=True)
    name = Column(String)  # root_function的name（合约名+函数名用点连接）
    content = Column(String)  # root function的内容
    rule = Column(String)  # all_checklists定义的每一个rule，原始的list
    rule_key = Column(String)  # 规则key，用于标识不同类型的检查规则
    result = Column(String)
    contract_code = Column(String)
    start_line = Column(String)
    end_line = Column(String)
    relative_file_path = Column(String)
    absolute_file_path = Column(String)
    recommendation = Column(String)
    business_flow_code = Column(String)  # root func的内容加上所有downstream的内容
    scan_record = Column(String)  # 扫描记录
    short_result = Column(String)  # 简短结果，保存yes/no

    fieldNames = ['id', 'uuid', 'project_id', 'name', 'content', 'rule', 'rule_key', 'result', 'contract_code', 'start_line', 'end_line', 'relative_file_path', 'absolute_file_path', 'recommendation', 'business_flow_code', 'scan_record', 'short_result']

    def __init__(self, project_id, name, content, rule, rule_key='', result='', contract_code='', start_line='', end_line='', relative_file_path='', absolute_file_path='', recommendation='', business_flow_code='', scan_record='', short_result=''):
        self.uuid = str(uuid_module.uuid4())  # 生成UUID
        self.project_id = project_id
        self.name = name  # root_function的name（合约名+函数名用点连接）
        self.content = content  # root function的内容
        self.rule = rule  # all_checklists定义的每一个rule
        self.rule_key = rule_key  # 规则key
        self.result = result
        self.contract_code = contract_code
        self.start_line = start_line
        self.end_line = end_line
        self.relative_file_path = relative_file_path
        self.absolute_file_path = absolute_file_path
        self.recommendation = recommendation
        self.business_flow_code = business_flow_code  # root func的内容加上所有downstream的内容
        self.scan_record = scan_record  # 扫描记录
        self.short_result = short_result  # 简短结果，保存yes/no



    def as_dict(self):
        return {
            'id': getattr(self, 'id', None),
            'uuid': self.uuid,
            'project_id': self.project_id,
            'name': self.name,
            'content': self.content,
            'rule': self.rule,
            'rule_key': self.rule_key,
            'result': self.result,
            'contract_code': self.contract_code,
            'start_line': self.start_line,
            'end_line': self.end_line,
            'relative_file_path': self.relative_file_path,
            'absolute_file_path': self.absolute_file_path,
            'recommendation': self.recommendation,
            'business_flow_code': self.business_flow_code,
            'scan_record': self.scan_record,
            'short_result': self.short_result
        }
    
    def set_result(self, result):
        self.result = result

    def get_result(self):
        result = self.result
        return None if result == '' else result
    
    def set_short_result(self, short_result):
        self.short_result = short_result
    
    def get_short_result(self):
        short_result = self.short_result
        return None if short_result == '' else short_result
    
    def get_key(self):
        # 使用UUID作为key
        return self.uuid


