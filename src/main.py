import argparse
import ast
import os
import sys
import time
from ai_engine import *
from tree_sitter_parsing import TreeSitterProjectAudit as ProjectAudit
from dataset_manager import load_dataset, Project
from planning.planning import Planning
from sqlalchemy import create_engine
from dao import CacheManager, ProjectTaskMgr
import os
import pandas as pd
from openpyxl import Workbook,load_workbook
from openpyxl.utils.dataframe import dataframe_to_rows
from res_processor.res_processor import ResProcessor

import dotenv
dotenv.load_dotenv()

# 添加日志系统
from logging_config import setup_logging, get_logger, log_section_start, log_section_end, log_step, log_error, log_warning, log_success, log_data_info

def scan_project(project, db_engine):
    logger = get_logger("scan_project")
    scan_start_time = time.time()
    
    log_section_start(logger, "项目扫描", f"项目ID: {project.id}, 路径: {project.path}")
    
    # 1. parsing projects  
    log_step(logger, "Tree-sitter解析项目", f"项目路径: {project.path}")
    parsing_start = time.time()
    
    project_audit = ProjectAudit(project.id, project.path, db_engine)
    project_audit.parse()
    
    parsing_duration = time.time() - parsing_start
    log_success(logger, "项目解析完成", f"耗时: {parsing_duration:.2f}秒")
    log_data_info(logger, "解析的函数", len(project_audit.functions_to_check))
    log_data_info(logger, "调用树", len(project_audit.call_trees))
    log_data_info(logger, "调用图", len(project_audit.call_graphs))
    
    # 1.5 初始化RAG处理器（可选）
    log_step(logger, "初始化RAG处理器")
    rag_processor = None
    try:
        from context.rag_processor import RAGProcessor
        rag_start = time.time()
        
        # 传递project_audit对象，包含functions, functions_to_check, chunks
        rag_processor = RAGProcessor(
            project_audit, 
            "./src/codebaseQA/lancedb", 
            project.id
        )
        
        rag_duration = time.time() - rag_start
        log_success(logger, "RAG处理器初始化完成", f"耗时: {rag_duration:.2f}秒")
        log_data_info(logger, "基于tree-sitter解析的函数构建RAG", len(project_audit.functions_to_check))
        log_data_info(logger, "基于文档分块构建RAG", len(project_audit.chunks))
        log_data_info(logger, "使用调用树构建关系型RAG", len(project_audit.call_trees))
        log_data_info(logger, "集成调用图(Call Graph)", len(project_audit.call_graphs))
        
        # 显示 call graph 统计信息
        if project_audit.call_graphs:
            call_graph_stats = project_audit.get_call_graph_statistics()
            log_data_info(logger, "Call Graph统计", call_graph_stats)
        
    except ImportError as e:
        log_warning(logger, "RAG处理器不可用，将使用简化功能")
        logger.debug(f"ImportError详情: {e}")
    except Exception as e:
        log_error(logger, "RAG处理器初始化失败", e)
        rag_processor = None
    
    # 1.6 检查业务流模式配置
    log_step(logger, "检查业务流模式配置")
    switch_business_code = eval(os.environ.get('SWITCH_BUSINESS_CODE', 'True'))
    logger.info(f"SWITCH_BUSINESS_CODE: {switch_business_code}")
    
    if switch_business_code:
        log_step(logger, "启用业务代码扫描模式")
    else:
        log_step(logger, "使用传统扫描模式", "SWITCH_BUSINESS_CODE=False")
    
    # 2. planning & scanning - 直接使用project_audit
    log_step(logger, "创建任务管理器")
    project_taskmgr = ProjectTaskMgr(project.id, db_engine) 
    log_success(logger, "任务管理器创建完成")
    
    # 创建规划处理器，直接传递project_audit
    log_step(logger, "创建规划处理器")
    planning = Planning(project_audit, project_taskmgr)
    log_success(logger, "规划处理器创建完成")
    
    # 如果有RAG处理器，初始化planning的RAG功能
    if rag_processor:
        log_step(logger, "初始化规划器的RAG功能")
        planning.initialize_rag_processor("./src/codebaseQA/lancedb", project.id)
        log_success(logger, "规划器RAG功能初始化完成")
    
    # 创建AI引擎
    log_step(logger, "创建AI引擎")
    lancedb_table = rag_processor.db if rag_processor else None
    lancedb_table_name = rag_processor.table_name if rag_processor else f"lancedb_{project.id}"
    logger.info(f"LanceDB表名: {lancedb_table_name}")
    
    engine = AiEngine(planning, project_taskmgr, lancedb_table, lancedb_table_name, project_audit)
    log_success(logger, "AI引擎创建完成")
    
    # 执行规划和扫描
    log_step(logger, "执行项目规划")
    planning_start = time.time()
    engine.do_planning()
    planning_duration = time.time() - planning_start
    log_success(logger, "项目规划完成", f"耗时: {planning_duration:.2f}秒")
    
    log_step(logger, "执行漏洞扫描")
    scan_start = time.time()
    engine.do_scan()
    scan_duration = time.time() - scan_start
    log_success(logger, "漏洞扫描完成", f"耗时: {scan_duration:.2f}秒")
    
    total_scan_duration = time.time() - scan_start_time
    log_section_end(logger, "项目扫描", total_scan_duration)

    return lancedb_table, lancedb_table_name, project_audit

def check_function_vul(engine, lancedb, lance_table_name, project_audit):
    """执行漏洞检查，直接使用project_audit数据"""
    logger = get_logger("check_function_vul")
    check_start_time = time.time()
    
    log_section_start(logger, "漏洞验证", f"项目ID: {project_audit.project_id}")
    
    log_step(logger, "创建项目任务管理器")
    project_taskmgr = ProjectTaskMgr(project_audit.project_id, engine)
    log_success(logger, "项目任务管理器创建完成")
    
    # 直接使用project_audit创建漏洞检查器
    log_step(logger, "初始化漏洞检查器")
    from validating import VulnerabilityChecker
    checker = VulnerabilityChecker(project_audit, lancedb, lance_table_name)
    log_success(logger, "漏洞检查器初始化完成")
    
    # 执行漏洞检查
    log_step(logger, "执行漏洞验证")
    validation_start = time.time()
    checker.check_function_vul(project_taskmgr)
    validation_duration = time.time() - validation_start
    log_success(logger, "漏洞验证完成", f"耗时: {validation_duration:.2f}秒")
    
    total_check_duration = time.time() - check_start_time
    log_section_end(logger, "漏洞验证", total_check_duration)

def generate_excel(output_path, project_id):
    project_taskmgr = ProjectTaskMgr(project_id, engine)
    entities = project_taskmgr.query_task_by_project_id(project.id)
    
    # 创建一个空的DataFrame来存储所有实体的数据
    data = []
    for entity in entities:
        # 使用result字段和business_flow_code进行筛选
        if entity.result and ("yes" in str(entity.result).lower()) and len(entity.business_flow_code)>0:
            data.append({
                '漏洞结果': entity.result,
                'ID': entity.id,
                '项目名称': entity.project_id,
                '合同编号': entity.contract_code,
                'UUID': entity.uuid,  # 使用uuid而不是key
                '函数名称': entity.name,
                '函数代码': entity.content,
                '规则类型': entity.rule_key,  # 新增rule_key
                '开始行': entity.start_line,
                '结束行': entity.end_line,
                '相对路径': entity.relative_file_path,
                '绝对路径': entity.absolute_file_path,
                '业务流程代码': entity.business_flow_code,
                '扫描记录': entity.scan_record,  # 使用新的scan_record字段
                '推荐': entity.recommendation
            })
    
    # 将数据转换为DataFrame
    if not data:  # 检查是否有数据
        print("No data to process")
        return
        
    df = pd.DataFrame(data)
    
    try:
        # 对df进行漏洞归集处理
        res_processor = ResProcessor(df,max_group_size=10,iteration_rounds=5,enable_chinese_translation=True)
        processed_df = res_processor.process()
        
        # 确保所有必需的列都存在
        required_columns = df.columns
        for col in required_columns:
            if col not in processed_df.columns:
                processed_df[col] = ''
                
        # 重新排列列顺序以匹配原始DataFrame
        processed_df = processed_df[df.columns]
    except Exception as e:
        print(f"Error processing data: {e}")
        processed_df = df  # 如果处理失败，使用原始DataFrame
    
    # 确保输出目录存在
    output_dir = os.path.dirname(output_path)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # 检查文件是否存在，如果不存在则创建新文件
    if not os.path.exists(output_path):
        wb = Workbook()
        ws = wb.active
        ws.title = "项目数据"
    else:
        wb = load_workbook(output_path)
        if "项目数据" in wb.sheetnames:
            ws = wb["项目数据"]
        else:
            ws = wb.create_sheet("项目数据")
    
    # 如果工作表是空的，添加表头
    if ws.max_row == 1:
        for col, header in enumerate(processed_df.columns, start=1):
            ws.cell(row=1, column=col, value=header)
    
    # 将DataFrame数据写入工作表
    for row in dataframe_to_rows(processed_df, index=False, header=False):
        ws.append(row)
    
    # 保存Excel文件
    wb.save(output_path)
    
    print(f"Excel文件已保存到: {output_path}")
if __name__ == '__main__':
    # 初始化日志系统
    log_file_path = setup_logging()
    main_logger = get_logger("main")
    main_start_time = time.time()
    
    main_logger.info("🎯 程序启动参数:")
    main_logger.info(f"   Python版本: {sys.version}")
    main_logger.info(f"   工作目录: {os.getcwd()}")
    main_logger.info(f"   环境变量已加载")

    switch_production_or_test = 'test' # prod / test
    main_logger.info(f"运行模式: {switch_production_or_test}")

    if switch_production_or_test == 'test':
        log_section_start(main_logger, "测试模式执行")
        
        start_time=time.time()
        
        # 初始化数据库
        log_step(main_logger, "初始化数据库连接")
        db_url_from = os.environ.get("DATABASE_URL")
        main_logger.info(f"数据库URL: {db_url_from}")
        engine = create_engine(db_url_from)
        log_success(main_logger, "数据库连接创建完成")
        
        # 加载数据集
        log_step(main_logger, "加载数据集")
        dataset_base = "./src/dataset/agent-v1-c4"
        main_logger.info(f"数据集路径: {dataset_base}")
        projects = load_dataset(dataset_base)
        log_success(main_logger, "数据集加载完成", f"找到 {len(projects)} 个项目")
 
        # 设置项目参数
        project_id = 'fishcake0803'  # 使用存在的项目ID
        project_path = ''
        main_logger.info(f"目标项目ID: {project_id}")
        project = Project(project_id, projects[project_id])
        log_success(main_logger, "项目对象创建完成")
        
        # 检查扫描模式
        scan_mode = os.getenv("SCAN_MODE","SPECIFIC_PROJECT")
        main_logger.info(f"扫描模式: {scan_mode}")
        
        cmd = 'detect_vul'
        main_logger.info(f"执行命令: {cmd}")
        
        if cmd == 'detect_vul':
            # 执行项目扫描
            lancedb,lance_table_name,project_audit=scan_project(project, engine) # scan
            
            # 根据扫描模式决定是否执行漏洞验证
            if scan_mode in ["COMMON_PROJECT", "PURE_SCAN", "CHECKLIST", "COMMON_PROJECT_FINE_GRAINED"]:
                main_logger.info(f"扫描模式 '{scan_mode}' 需要执行漏洞验证")
                check_function_vul(engine,lancedb,lance_table_name,project_audit) # confirm
            else:
                main_logger.info(f"扫描模式 '{scan_mode}' 跳过漏洞验证步骤")

        # 统计总执行时间
        end_time=time.time()
        total_duration = end_time-start_time
        log_success(main_logger, "所有扫描任务完成", f"总耗时: {total_duration:.2f}秒")
        
        # 生成Excel报告
        log_step(main_logger, "生成Excel报告")
        excel_start = time.time()
        generate_excel("./output.xlsx",project_id)
        excel_duration = time.time() - excel_start
        log_success(main_logger, "Excel报告生成完成", f"耗时: {excel_duration:.2f}秒, 文件: ./output.xlsx")
        
        log_section_end(main_logger, "测试模式执行", time.time() - main_start_time)
        
        
    if switch_production_or_test == 'prod':
        # Set up command line argument parsing
        parser = argparse.ArgumentParser(description='Process input parameters for vulnerability scanning.')
        parser.add_argument('-fpath', type=str, required=True, help='Combined base path for the dataset and folder')
        parser.add_argument('-id', type=str, required=True, help='Project ID')
        # parser.add_argument('-cmd', type=str, choices=['detect', 'confirm','all'], required=True, help='Command to execute')
        parser.add_argument('-o', type=str, required=True, help='Output file path')
        # usage:
        # python main.py 
        # --fpath ../../dataset/agent-v1-c4/Archive 
        # --id Archive_aaa 
        # --cmd detect

        # Parse arguments
        args = parser.parse_args()
        print("fpath:",args.fpath)
        print("id:",args.id)
        print("cmd:",args.cmd)
        print("o:",args.o)
        # Split dataset_folder into dataset and folder
        dataset_base, folder_name = os.path.split(args.fpath)
        print("dataset_base:",dataset_base)
        print("folder_name:",folder_name)
        # Start time
        start_time = time.time()

        # Database setup
        db_url_from = os.environ.get("DATABASE_URL")
        engine = create_engine(db_url_from)

        # Load projects
        projects = load_dataset(dataset_base, args.id, folder_name)
        project = Project(args.id, projects[args.id])

        # Execute command
        # if args.cmd == 'detect':
        #     scan_project(project, engine)  # scan            
        # elif args.cmd == 'confirm':
        #     check_function_vul(engine)  # confirm
        # elif args.cmd == 'all':
        lancedb=scan_project(project, engine)  # scan
        check_function_vul(engine,lancedb)  # confirm

        end_time = time.time()
        print("Total time:", end_time -start_time)
        generate_excel(args.o,args.id)