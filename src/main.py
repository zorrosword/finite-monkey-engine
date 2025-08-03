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

def _perform_post_reasoning_deduplication(project_id, db_engine, logger):
    """在reasoning完成后，validation开始前进行去重处理"""
    log_step(logger, "开始获取reasoning后的漏洞数据")
    
    try:
        # 获取reasoning后的所有漏洞数据
        project_taskmgr = ProjectTaskMgr(project_id, db_engine)
        entities = project_taskmgr.query_task_by_project_id(project_id)
        
        # 调试信息：统计所有实体
        total_entities = len(entities)
        log_data_info(logger, "总任务实体数量", total_entities)
        print(f"🔍 调试信息 - 总任务实体数量: {total_entities}")
        
        # 详细分析每个筛选条件
        entities_with_result = 0
        entities_with_yes = 0
        entities_with_business_code = 0
        
        for entity in entities:
            if entity.result:
                entities_with_result += 1
                if "yes" in str(entity.result).lower():
                    entities_with_yes += 1
                if hasattr(entity, 'business_flow_code') and entity.business_flow_code and len(entity.business_flow_code) > 0:
                    entities_with_business_code += 1
        
        print(f"🔍 调试信息 - 有result的实体: {entities_with_result}")
        print(f"🔍 调试信息 - result包含'yes'的实体: {entities_with_yes}")
        print(f"🔍 调试信息 - 有business_flow_code的实体: {entities_with_business_code}")
        
        # 筛选有漏洞结果的数据
        vulnerability_data = []
        for entity in entities:
            # 调试每个实体的详细信息
            has_result = bool(entity.result)
            has_yes = has_result and ("yes" in str(entity.result).lower())
            has_business_code = hasattr(entity, 'business_flow_code') and entity.business_flow_code and len(entity.business_flow_code) > 0
            
            if has_result and has_yes and has_business_code:
                vulnerability_data.append({
                    '漏洞结果': entity.result,
                    'ID': entity.id,
                    '项目名称': entity.project_id,
                    '合同编号': entity.contract_code,
                    'UUID': entity.uuid,
                    '函数名称': entity.name,
                    '函数代码': entity.content,
                    '规则类型': entity.rule_key,
                    '开始行': entity.start_line,
                    '结束行': entity.end_line,
                    '相对路径': entity.relative_file_path,
                    '绝对路径': entity.absolute_file_path,
                    '业务流程代码': entity.business_flow_code,
                    '扫描记录': entity.scan_record,
                    '推荐': entity.recommendation
                })
        
        filtered_count = len(vulnerability_data)
        print(f"🔍 调试信息 - 通过筛选条件的实体: {filtered_count}")
        
        if not vulnerability_data:
            print(f"⚠️  严格筛选条件未找到数据，尝试宽松筛选条件...")
            print(f"   - 总实体数: {total_entities}")
            print(f"   - 有result的: {entities_with_result}")
            print(f"   - result包含'yes'的: {entities_with_yes}")
            print(f"   - 有business_flow_code的: {entities_with_business_code}")
            print(f"   - 通过所有筛选条件的: {filtered_count}")
            
            # 尝试宽松筛选条件：只要有result就进行去重
            print(f"🔄 尝试宽松筛选条件（只要有result）...")
            for entity in entities:
                if entity.result and entity.result.strip():  # 只要有非空result
                    vulnerability_data.append({
                        '漏洞结果': entity.result,
                        'ID': entity.id,
                        '项目名称': entity.project_id,
                        '合同编号': getattr(entity, 'contract_code', ''),
                        'UUID': getattr(entity, 'uuid', ''),
                        '函数名称': entity.name,
                        '函数代码': getattr(entity, 'content', ''),
                        '规则类型': getattr(entity, 'rule_key', ''),
                        '开始行': getattr(entity, 'start_line', ''),
                        '结束行': getattr(entity, 'end_line', ''),
                        '相对路径': getattr(entity, 'relative_file_path', ''),
                        '绝对路径': getattr(entity, 'absolute_file_path', ''),
                        '业务流程代码': getattr(entity, 'business_flow_code', ''),
                        '扫描记录': getattr(entity, 'scan_record', ''),
                        '推荐': getattr(entity, 'recommendation', '')
                    })
            
            fallback_count = len(vulnerability_data)
            print(f"🔍 宽松筛选条件找到: {fallback_count} 个实体")
            
            if not vulnerability_data:
                print(f"❌ 即使使用宽松筛选条件也未找到数据，跳过去重处理")
                log_warning(logger, f"严格和宽松筛选条件都未找到数据 - 总实体:{total_entities}, 有result:{entities_with_result}")
                return
            else:
                print(f"✅ 使用宽松筛选条件进行去重处理")
                log_warning(logger, f"使用宽松筛选条件进行去重 - 原始条件筛选出:{filtered_count}, 宽松条件筛选出:{fallback_count}")
        
        original_df = pd.DataFrame(vulnerability_data)
        original_count = len(original_df)
        original_ids = set(original_df['ID'].astype(str))
        
        log_data_info(logger, "去重前漏洞数量", original_count)
        log_data_info(logger, "去重前漏洞ID", f"{', '.join(sorted(original_ids))}")
        
        # 使用ResProcessor进行去重
        log_step(logger, "开始ResProcessor去重处理")
        res_processor = ResProcessor(original_df, max_group_size=5, iteration_rounds=4, enable_chinese_translation=False)
        processed_df = res_processor.process()
        
        deduplicated_count = len(processed_df)
        deduplicated_ids = set(processed_df['ID'].astype(str))
        
        log_data_info(logger, "去重后漏洞数量", deduplicated_count)
        log_data_info(logger, "去重后漏洞ID", f"{', '.join(sorted(deduplicated_ids))}")
        
        # 计算被去重的ID
        removed_ids = original_ids - deduplicated_ids
        removed_count = len(removed_ids)
        
        # 打印去重结果
        print(f"\n{'='*60}")
        print(f"🔄 Reasoning后去重处理结果")
        print(f"{'='*60}")
        print(f"去重前漏洞数量: {original_count}")
        print(f"去重后漏洞数量: {deduplicated_count}")
        print(f"被去重的漏洞数量: {removed_count}")
        
        if removed_ids:
            print(f"\n🗑️  被去重的漏洞ID列表:")
            for i, removed_id in enumerate(sorted(removed_ids), 1):
                print(f"  {i:2d}. ID: {removed_id}")
            
            # 逻辑删除被去重的记录 - 将short_result设置为"delete"
            print(f"\n🗑️  开始逻辑删除被去重的记录(设置short_result='delete')...")
            marked_count = 0
            failed_marks = []
            
            for removed_id in removed_ids:
                try:
                    # 转换为整数类型的ID
                    id_int = int(removed_id)
                    project_taskmgr.update_short_result(id_int, "delete")
                    marked_count += 1
                    print(f"    ✅ 标记成功: ID {removed_id} -> short_result='delete'")
                except Exception as e:
                    failed_marks.append(removed_id)
                    print(f"    ❌ 标记出错: ID {removed_id}, 错误: {str(e)}")
                    logger.error(f"标记删除ID {removed_id} 时出错: {str(e)}")
            
            print(f"\n📊 逻辑删除结果:")
            print(f"    成功标记: {marked_count} 条记录")
            if failed_marks:
                print(f"    标记失败: {len(failed_marks)} 条记录 - IDs: {', '.join(failed_marks)}")
                logger.warning(f"标记失败的IDs: {', '.join(failed_marks)}")
            
            log_success(logger, "逻辑删除操作完成", f"成功标记: {marked_count}/{removed_count}")
        else:
            print("✅ 没有漏洞被去重")
        
        print(f"{'='*60}\n")
        
        # 记录到日志
        log_success(logger, "去重处理完成", f"原始: {original_count} -> 去重后: {deduplicated_count}, 逻辑删除: {removed_count}")
        if removed_ids:
            logger.info(f"被去重的漏洞ID: {', '.join(sorted(removed_ids))}")
            logger.info(f"逻辑删除了 {marked_count} 条被去重的记录(设置short_result='delete')")
        
    except Exception as e:
        log_error(logger, "去重处理失败", e)
        import traceback
        logger.error(f"详细错误信息: {traceback.format_exc()}")

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
    
    log_step(logger, "执行漏洞扫描(Reasoning)")
    scan_start = time.time()
    engine.do_scan()
    scan_duration = time.time() - scan_start
    log_success(logger, "漏洞扫描(Reasoning)完成", f"耗时: {scan_duration:.2f}秒")
    
    # 在reasoning完成后，validation开始前进行去重
    log_step(logger, "Reasoning后去重处理")
    dedup_start = time.time()
    _perform_post_reasoning_deduplication(project.id, db_engine, logger)
    dedup_duration = time.time() - dedup_start
    log_success(logger, "Reasoning后去重处理完成", f"耗时: {dedup_duration:.2f}秒")
    
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
    total_entities = len(entities)
    deleted_entities = 0
    
    for entity in entities:
        # 跳过已逻辑删除的记录
        if getattr(entity, 'short_result', '') == 'delete':
            deleted_entities += 1
            continue
            
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
    
    # 打印数据统计信息
    print(f"\n📊 Excel报告数据统计:")
    print(f"   总记录数: {total_entities}")
    print(f"   逻辑删除的记录数: {deleted_entities}")
    print(f"   有效记录数: {total_entities - deleted_entities}")
    print(f"   符合条件的漏洞记录数: {len(data)}")
    
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
        project_id = 'fishcake0803021'  # 使用存在的项目ID
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