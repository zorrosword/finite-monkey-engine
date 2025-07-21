# Token计算器 - 预估API调用的token使用量
# Token Calculator - Estimate token usage for API calls

import re
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class TokenUsage:
    """Token使用情况"""
    input_tokens: int           # 输入token数量
    estimated_output_tokens: int # 预估输出token数量
    total_tokens: int          # 总token数量
    is_within_limit: bool      # 是否在限制范围内
    model_limit: int           # 模型token限制
    recommendation: str        # 建议

class TokenCalculator:
    """Token计算器 - 估算API调用的token使用量"""
    
    # 不同模型的token限制
    MODEL_LIMITS = {
        'claude-3-5-sonnet-20241022': 200000,  # Claude 3.5 Sonnet (主要模型)
        'claude-sonnet-4-20250514': 200000,    # Claude 4 Sonnet (备用)
        'gpt-4.1': 128000,                     # GPT-4 Turbo
        'gpt-4o-mini': 128000,                 # GPT-4o mini
        'gpt-4o': 128000,                      # GPT-4o
        'deepseek-reasoner': 32000,            # DeepSeek
        'default': 8000                        # 默认保守值
    }
    
    # 输出token估算倍数（基于经验）
    OUTPUT_TOKEN_MULTIPLIERS = {
        'project_overview': 0.3,    # 概览分析输出相对较少
        'module_detail': 0.5,       # 模块详细分析输出中等
        'dependency_analysis': 0.2,  # 依赖分析输出较少
        'mermaid_generation': 0.4,  # Mermaid图生成中等输出
        'smart_query': 0.6,         # 智能查询可能输出较多
        'default': 0.3              # 默认倍数
    }
    
    def __init__(self):
        """初始化token计算器"""
        logger.info("初始化Token计算器")
    
    def estimate_tokens(self, text: str) -> int:
        """估算文本的token数量
        
        使用简化的token估算方法：
        - 英文：约4个字符 = 1个token
        - 中文：约1.5个字符 = 1个token
        - 代码：约3个字符 = 1个token
        
        Args:
            text: 要估算的文本
            
        Returns:
            预估的token数量
        """
        if not text:
            return 0
        
        # 统计不同类型的字符
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        english_chars = len(re.findall(r'[a-zA-Z]', text))
        code_chars = len(re.findall(r'[{}()[\];=+\-*/<>]', text))
        other_chars = len(text) - chinese_chars - english_chars - code_chars
        
        # 按不同规则计算token
        tokens = 0
        tokens += chinese_chars / 1.5      # 中文字符
        tokens += english_chars / 4        # 英文字符
        tokens += code_chars / 3           # 代码字符
        tokens += other_chars / 4          # 其他字符
        
        return int(tokens)
    
    def calculate_prompt_tokens(self, prompt: str, model: str = "default") -> TokenUsage:
        """计算prompt的token使用情况
        
        Args:
            prompt: 要分析的prompt
            model: 使用的模型名称
            
        Returns:
            Token使用情况
        """
        input_tokens = self.estimate_tokens(prompt)
        model_limit = self.MODEL_LIMITS.get(model, self.MODEL_LIMITS['default'])
        
        # 预估输出token（保守估算，留出足够空间）
        estimated_output = min(input_tokens * 0.3, 4000)  # 最多4000个输出token
        total_tokens = input_tokens + estimated_output
        
        # 判断是否在限制范围内（留20%的安全边距）
        safe_limit = int(model_limit * 0.8)
        is_within_limit = total_tokens <= safe_limit
        
        # 生成建议
        recommendation = self._generate_recommendation(
            input_tokens, total_tokens, model_limit, is_within_limit)
        
        return TokenUsage(
            input_tokens=input_tokens,
            estimated_output_tokens=int(estimated_output),
            total_tokens=total_tokens,
            is_within_limit=is_within_limit,
            model_limit=model_limit,
            recommendation=recommendation
        )
    
    def calculate_files_tokens(self, files_content: Dict[str, str], 
                             analysis_type: str = "default",
                             model: str = "default") -> TokenUsage:
        """计算文件内容的token使用情况
        
        Args:
            files_content: 文件内容映射
            analysis_type: 分析类型
            model: 使用的模型
            
        Returns:
            Token使用情况
        """
        # 计算所有文件的token总数
        total_content_tokens = 0
        for file_path, content in files_content.items():
            file_tokens = self.estimate_tokens(content)
            total_content_tokens += file_tokens
            logger.debug(f"文件 {file_path}: {file_tokens} tokens")
        
        # 添加prompt模板的token（估算）
        prompt_template_tokens = 1000  # 系统prompt和指令的估算token
        
        input_tokens = total_content_tokens + prompt_template_tokens
        
        # 根据分析类型估算输出token
        output_multiplier = self.OUTPUT_TOKEN_MULTIPLIERS.get(
            analysis_type, self.OUTPUT_TOKEN_MULTIPLIERS['default'])
        estimated_output = int(input_tokens * output_multiplier)
        
        # 限制最大输出token
        max_output = 6000  # 设置最大输出限制
        estimated_output = min(estimated_output, max_output)
        
        total_tokens = input_tokens + estimated_output
        
        model_limit = self.MODEL_LIMITS.get(model, self.MODEL_LIMITS['default'])
        safe_limit = int(model_limit * 0.8)
        is_within_limit = total_tokens <= safe_limit
        
        recommendation = self._generate_recommendation(
            input_tokens, total_tokens, model_limit, is_within_limit)
        
        return TokenUsage(
            input_tokens=input_tokens,
            estimated_output_tokens=estimated_output,
            total_tokens=total_tokens,
            is_within_limit=is_within_limit,
            model_limit=model_limit,
            recommendation=recommendation
        )
    
    def suggest_batch_size(self, files_content: Dict[str, str], 
                          model: str = "default",
                          analysis_type: str = "default") -> Tuple[int, List[List[str]]]:
        """建议批次大小和文件分组
        
        Args:
            files_content: 文件内容映射
            model: 使用的模型
            analysis_type: 分析类型
            
        Returns:
            建议的批次大小和文件分组
        """
        model_limit = self.MODEL_LIMITS.get(model, self.MODEL_LIMITS['default'])
        safe_limit = int(model_limit * 0.6)  # 使用60%的限制作为安全阈值
        
        # 计算每个文件的token数
        file_tokens = {}
        for file_path, content in files_content.items():
            file_tokens[file_path] = self.estimate_tokens(content)
        
        # 按token数量排序文件
        sorted_files = sorted(file_tokens.items(), key=lambda x: x[1])
        
        # 智能分组
        batches = []
        current_batch = []
        current_tokens = 1000  # 预留prompt token
        
        for file_path, tokens in sorted_files:
            # 检查添加这个文件是否会超限
            if current_tokens + tokens > safe_limit:
                # 如果当前批次不为空，保存它
                if current_batch:
                    batches.append(current_batch)
                    current_batch = []
                    current_tokens = 1000
                
                # 如果单个文件就超限，需要截断
                if tokens > safe_limit:
                    logger.warning(f"文件 {file_path} 单独就超过token限制，将被截断")
                    current_batch.append(file_path)
                    batches.append(current_batch)
                    current_batch = []
                    current_tokens = 1000
                else:
                    current_batch.append(file_path)
                    current_tokens += tokens
            else:
                current_batch.append(file_path)
                current_tokens += tokens
        
        # 添加最后一个批次
        if current_batch:
            batches.append(current_batch)
        
        optimal_batch_size = sum(len(batch) for batch in batches) // len(batches) if batches else 1
        
        logger.info(f"建议批次大小: {optimal_batch_size}, 总批次数: {len(batches)}")
        return optimal_batch_size, batches
    
    def truncate_content_by_tokens(self, content: str, max_tokens: int) -> str:
        """按token数量截断内容
        
        Args:
            content: 原始内容
            max_tokens: 最大token数量
            
        Returns:
            截断后的内容
        """
        current_tokens = self.estimate_tokens(content)
        
        if current_tokens <= max_tokens:
            return content
        
        # 计算需要保留的比例
        keep_ratio = max_tokens / current_tokens
        
        # 智能截断：保留开头和部分结尾
        lines = content.split('\n')
        total_lines = len(lines)
        
        # 保留70%给开头，30%给结尾
        head_lines = int(total_lines * keep_ratio * 0.7)
        tail_lines = int(total_lines * keep_ratio * 0.3)
        
        if head_lines + tail_lines >= total_lines:
            return content
        
        truncated_lines = []
        
        # 添加开头部分
        truncated_lines.extend(lines[:head_lines])
        
        # 添加截断标记
        truncated_lines.append("")
        truncated_lines.append("// ... [内容因token限制被截断] ...")
        truncated_lines.append("")
        
        # 添加结尾部分
        if tail_lines > 0:
            truncated_lines.extend(lines[-tail_lines:])
        
        truncated_content = '\n'.join(truncated_lines)
        
        # 验证截断后的token数量
        new_tokens = self.estimate_tokens(truncated_content)
        logger.info(f"内容截断: {current_tokens} -> {new_tokens} tokens (目标: {max_tokens})")
        
        return truncated_content
    
    def _generate_recommendation(self, input_tokens: int, total_tokens: int, 
                               model_limit: int, is_within_limit: bool) -> str:
        """生成token使用建议"""
        
        if is_within_limit:
            usage_percent = (total_tokens / model_limit) * 100
            if usage_percent < 50:
                return f"✅ Token使用良好 ({usage_percent:.1f}%)"
            else:
                return f"⚠️ Token使用较高 ({usage_percent:.1f}%)，建议优化"
        else:
            excess_tokens = total_tokens - model_limit
            return f"❌ Token超限 (超出 {excess_tokens} tokens)，需要分批处理或截断内容"
    
    def get_model_info(self, model: str = "default") -> Dict[str, Any]:
        """获取模型信息"""
        limit = self.MODEL_LIMITS.get(model, self.MODEL_LIMITS['default'])
        
        return {
            "model": model,
            "token_limit": limit,
            "safe_limit": int(limit * 0.8),
            "recommended_batch_limit": int(limit * 0.6),
            "description": f"模型 {model} 的token限制为 {limit:,}"
        }
    
    def print_token_analysis(self, usage: TokenUsage, title: str = "Token分析"):
        """打印token分析结果"""
        print(f"\n📊 {title}")
        print("-" * 40)
        print(f"   📥 输入Token: {usage.input_tokens:,}")
        print(f"   📤 预估输出Token: {usage.estimated_output_tokens:,}")
        print(f"   📊 总Token: {usage.total_tokens:,}")
        print(f"   🎯 模型限制: {usage.model_limit:,}")
        print(f"   📈 使用率: {(usage.total_tokens/usage.model_limit)*100:.1f}%")
        print(f"   💡 建议: {usage.recommendation}")

# 便捷函数
def quick_token_check(text: str, model: str = "claude-3-5-sonnet-20241022") -> TokenUsage:
    """快速检查文本的token使用情况"""
    calculator = TokenCalculator()
    return calculator.calculate_prompt_tokens(text, model)

def estimate_file_tokens(file_content: str) -> int:
    """估算文件的token数量"""
    calculator = TokenCalculator()
    return calculator.estimate_tokens(file_content)

def suggest_optimal_batching(files_content: Dict[str, str], 
                           model: str = "claude-3-5-sonnet-20241022") -> Tuple[int, List[List[str]]]:
    """建议最优的文件分批方案"""
    calculator = TokenCalculator()
    return calculator.suggest_batch_size(files_content, model) 