#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
文档分块器 - 基于 adalflow TextSplitter 的智能分块工具

功能：
- 遍历指定文件夹中的所有文件
- 使用 adalflow TextSplitter 进行文档分块
- 支持多种分块策略和参数配置
- 专为长文本优化的段落分割
- 支持配置文件管理
- 输出结构化的分块结果

作者：基于 adalflow 组件实现，集成长文本处理能力
"""

import os
import re
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Literal
from dataclasses import dataclass, asdict

# 尝试导入 adalflow，如果不可用则使用简单实现
try:
    from adalflow.components.data_process.text_splitter import TextSplitter
    from adalflow.core.types import Document
    ADALFLOW_AVAILABLE = True
except ImportError:
    ADALFLOW_AVAILABLE = False
    print("⚠️  adalflow 不可用，使用简单文本分块实现")

# 导入配置管理器
try:
    from .chunk_config import ChunkConfig, ChunkConfigManager
except ImportError:
    try:
        from chunk_config import ChunkConfig, ChunkConfigManager
    except ImportError:
        print("⚠️  无法导入chunk_config，将使用基础配置")


@dataclass
class ChunkResult:
    """分块结果数据结构"""
    chunk_id: str
    original_file: str
    chunk_text: str
    chunk_order: int
    parent_doc_id: str
    chunk_size: int
    metadata: Dict[str, Any]


@dataclass
class ProcessingStats:
    """处理统计信息"""
    total_files: int
    processed_files: int
    total_chunks: int
    skipped_files: List[str]
    error_files: List[str]


class SimpleTextSplitter:
    """简单文本分块器实现（当adalflow不可用时使用）"""
    
    def __init__(self, split_by="word", chunk_size=800, chunk_overlap=200, **kwargs):
        self.split_by = split_by
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def call(self, documents):
        """分块处理文档列表"""
        result = []
        for doc in documents:
            chunks = self._split_document(doc)
            result.extend(chunks)
        return result
    
    def _split_document(self, doc):
        """分块单个文档"""
        text = doc.text
        chunks = []
        
        if self.split_by == "word":
            words = text.split()
            for i in range(0, len(words), self.chunk_size - self.chunk_overlap):
                chunk_words = words[i:i + self.chunk_size]
                chunk_text = ' '.join(chunk_words)
                
                if chunk_text.strip():
                    chunk_doc = type('Document', (), {
                        'id': f"{doc.id}_chunk_{len(chunks)}",
                        'text': chunk_text,
                        'order': len(chunks),
                        'parent_doc_id': doc.id,
                        'meta_data': doc.meta_data.copy() if doc.meta_data else {}
                    })()
                    chunks.append(chunk_doc)
        
        elif self.split_by == "sentence":
            # 简单按句子分割
            sentences = text.split('.')
            for i in range(0, len(sentences), self.chunk_size - self.chunk_overlap):
                chunk_sentences = sentences[i:i + self.chunk_size]
                chunk_text = '.'.join(chunk_sentences)
                
                if chunk_text.strip():
                    chunk_doc = type('Document', (), {
                        'id': f"{doc.id}_chunk_{len(chunks)}",
                        'text': chunk_text,
                        'order': len(chunks),
                        'parent_doc_id': doc.id,
                        'meta_data': doc.meta_data.copy() if doc.meta_data else {}
                    })()
                    chunks.append(chunk_doc)
        
        else:
            # 按字符分割
            for i in range(0, len(text), self.chunk_size - self.chunk_overlap):
                chunk_text = text[i:i + self.chunk_size]
                
                if chunk_text.strip():
                    chunk_doc = type('Document', (), {
                        'id': f"{doc.id}_chunk_{len(chunks)}",
                        'text': chunk_text,
                        'order': len(chunks),
                        'parent_doc_id': doc.id,
                        'meta_data': doc.meta_data.copy() if doc.meta_data else {}
                    })()
                    chunks.append(chunk_doc)
        
        return chunks


class SimpleDocument:
    """简单文档类（当adalflow不可用时使用）"""
    
    def __init__(self, text, id, meta_data=None):
        self.text = text
        self.id = id
        self.meta_data = meta_data or {}


class DocumentChunker:
    """文档分块器类"""
    
    # 支持的文件扩展名
    SUPPORTED_EXTENSIONS = {
        '.txt', '.md', '.rst', '.py', '.js', '.ts', '.html', '.xml',
        '.json', '.yaml', '.yml', '.css', '.sql', '.sh', '.bat',
        '.c', '.cpp', '.h', '.hpp', '.java', '.php', '.rb', '.go',
        '.rs', '.scala', '.kt', '.swift', '.dart', '.r', '.m', '.sol', '.move','.cc'
    }
    
    def __init__(
        self,
        split_by: Literal["word", "sentence", "page", "passage", "token"] = "word",
        chunk_size: int = 800,
        chunk_overlap: int = 200,
        batch_size: int = 1000,
        encoding: str = 'utf-8',
        max_file_size_mb: float = 50.0,
        include_extensions: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
        long_text_mode: bool = False
    ):
        """
        初始化文档分块器
        
        Args:
            split_by: 分割策略 ("word", "sentence", "page", "passage", "token")
            chunk_size: 每个块的最大单位数
            chunk_overlap: 块间重叠单位数  
            batch_size: 批处理大小
            encoding: 文件编码
            max_file_size_mb: 最大文件大小限制(MB)
            include_extensions: 指定包含的文件扩展名
            exclude_patterns: 排除的文件名模式
            long_text_mode: 长文本模式，自动优化参数用于处理长文档
        """
        
        # 长文本模式自动优化参数
        self.long_text_mode = long_text_mode
        if long_text_mode:
            # 为长文本passage分割优化参数
            if split_by == "passage":
                chunk_size = max(chunk_size, 5)  # 至少5个段落
                chunk_overlap = max(chunk_overlap, 2)  # 至少2个段落重叠
                max_file_size_mb = max(max_file_size_mb, 100.0)  # 增加文件大小限制
            elif split_by == "word":
                chunk_size = max(chunk_size, 1500)  # 长文本适用更大的块
                chunk_overlap = max(chunk_overlap, 300)
        
        # 初始化 TextSplitter
        if ADALFLOW_AVAILABLE:
            self.text_splitter = TextSplitter(
                split_by=split_by,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                batch_size=batch_size
            )
        else:
            self.text_splitter = SimpleTextSplitter(
                split_by=split_by,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap
            )
        
        self.encoding = encoding
        self.max_file_size_bytes = max_file_size_mb * 1024 * 1024
        self.include_extensions = set(include_extensions) if include_extensions else None  # None表示包含所有文件
        self.exclude_patterns = exclude_patterns or []
        
        # 配置日志
        self.logger = logging.getLogger(__name__)
        
        # 输出初始化信息
        print(f"📄 DocumentChunker 初始化:")
        print(f"  - 分割策略: {split_by}")
        print(f"  - 块大小: {chunk_size}")
        print(f"  - 重叠大小: {chunk_overlap}")
        print(f"  - 长文本模式: {'是' if long_text_mode else '否'}")
        print(f"  - Adalflow可用: {'是' if ADALFLOW_AVAILABLE else '否'}")
        
        if long_text_mode:
            print(f"  🔄 长文本模式已启用，参数已优化")
    
    @classmethod
    def from_config(cls, config: 'ChunkConfig'):
        """
        从配置对象创建分块器
        
        Args:
            config: ChunkConfig配置对象
            
        Returns:
            DocumentChunker: 配置好的分块器实例
        """
        return cls(
            split_by=config.split_by,
            chunk_size=config.chunk_size,
            chunk_overlap=config.chunk_overlap,
            batch_size=config.batch_size,
            encoding=config.encoding,
            max_file_size_mb=config.max_file_size_mb,
            include_extensions=config.include_extensions,
            exclude_patterns=config.exclude_patterns,
            long_text_mode=config.long_text_mode
        )
    
    @classmethod
    def for_long_text_passage(
        cls,
        chunk_size: int = 8,
        chunk_overlap: int = 3,
        max_file_size_mb: float = 200.0,
        include_extensions: Optional[List[str]] = None
    ):
        """
        专门为长文本passage分割创建的便捷构造器
        
        Args:
            chunk_size: 段落数量，建议5-15个段落
            chunk_overlap: 段落重叠数，建议2-5个段落
            max_file_size_mb: 最大文件大小，长文本建议100MB以上
            include_extensions: 支持的文件类型，默认支持文本类型
            
        Returns:
            DocumentChunker: 配置好的长文本处理器
        """
        
        # 长文本常见的文件类型
        if include_extensions is None:
            include_extensions = [
                '.txt', '.md', '.rst', '.doc', '.docx',  # 文档类型
                '.pdf', '.rtf', '.odt',                   # 富文本类型  
                '.epub', '.mobi',                         # 电子书类型
                '.html', '.xml'                           # 标记语言
            ]
        
        return cls(
            split_by="passage",
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            batch_size=500,  # 长文本减少批处理大小
            max_file_size_mb=max_file_size_mb,
            include_extensions=include_extensions,
            long_text_mode=True
        )
    
    def process_files(self, file_paths: List[str]) -> List[ChunkResult]:
        """
        处理文件列表并进行分块
        
        Args:
            file_paths: 文件路径列表
            
        Returns:
            分块结果列表
        """
        all_chunks = []
        
        for file_path in file_paths:
            try:
                chunks = self._process_single_file(Path(file_path))
                if chunks:
                    all_chunks.extend(chunks)
                    print(f"✅ 分块文件: {Path(file_path).name} -> {len(chunks)} 个块")
                    
            except Exception as e:
                print(f"❌ 分块文件失败: {Path(file_path).name} - {str(e)}")
                continue
        
        return all_chunks
    
    def _should_process_file(self, file_path: Path) -> bool:
        """判断是否应该处理该文件"""
        # 检查文件大小
        try:
            file_size = file_path.stat().st_size
            if file_size > self.max_file_size_bytes:
                print(f"⚠️  文件过大，跳过分块: {file_path.name} ({file_size / 1024 / 1024:.2f}MB)")
                return False
        except OSError:
            print(f"⚠️  无法访问文件: {file_path.name}")
            return False
        
        # 检查排除模式
        file_path_str = str(file_path)
        for pattern in self.exclude_patterns:
            # 如果模式以点开头，按扩展名精确匹配
            if pattern.startswith('.'):
                if file_path.suffix == pattern or file_path.name.endswith(pattern):
                    return False
            # 否则按路径包含匹配
            elif pattern in file_path_str:
                return False
        
        # 检查包含扩展名（只有当include_extensions不为None时才检查）
        if self.include_extensions is not None:
            file_ext = file_path.suffix.lower()
            # 将include_extensions也转换为小写进行比较
            include_exts_lower = {ext.lower() for ext in self.include_extensions}
            if file_ext not in include_exts_lower and file_path.name not in self.include_extensions:
                return False
        
        return True
    
    def _process_single_file(self, file_path: Path) -> List[ChunkResult]:
        """处理单个文件"""
        if not self._should_process_file(file_path):
            return []
            
        try:
            # 读取文件内容
            content = self._read_file_with_encoding(file_path)
            
            if not content or len(content.strip()) < 50:  # 跳过过短的文件
                return []
            
            # 长文本模式的特殊预处理
            if self.long_text_mode and self.text_splitter.split_by == "passage":
                content = self._preprocess_long_text(content)
            
            # 创建 Document 对象
            if ADALFLOW_AVAILABLE:
                doc = Document(
                    text=content,
                    id=str(file_path),
                    meta_data={
                        'file_name': file_path.name,
                        'file_path': str(file_path),
                        'file_size': file_path.stat().st_size,
                        'file_extension': file_path.suffix
                    }
                )
            else:
                doc = SimpleDocument(
                    text=content,
                    id=str(file_path),
                    meta_data={
                        'file_name': file_path.name,
                        'file_path': str(file_path),
                        'file_size': file_path.stat().st_size,
                        'file_extension': file_path.suffix
                    }
                )
            
            # 使用 TextSplitter 进行分块
            split_docs = self.text_splitter.call([doc])
            
            # 转换为 ChunkResult 对象
            chunks = []
            for split_doc in split_docs:
                chunk = ChunkResult(
                    chunk_id=split_doc.id,
                    original_file=str(file_path),
                    chunk_text=split_doc.text,
                    chunk_order=split_doc.order,
                    parent_doc_id=split_doc.parent_doc_id,
                    chunk_size=len(split_doc.text.split()) if self.text_splitter.split_by == "word" else len(split_doc.text),
                    metadata=split_doc.meta_data or {}
                )
                chunks.append(chunk)
            
            return chunks
            
        except Exception as e:
            print(f"⚠️  处理文件时出错 {file_path}: {e}")
            return []
    
    def _read_file_with_encoding(self, file_path: Path) -> str:
        """尝试用不同编码读取文件"""
        encodings = [self.encoding, 'utf-8', 'gbk', 'latin1', 'cp1252']
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding, errors='ignore') as f:
                    content = f.read().strip()
                return content
            except UnicodeDecodeError:
                continue
            except Exception:
                continue
        
        # 如果所有编码都失败，返回空字符串
        return ""
    
    def _preprocess_long_text(self, content: str) -> str:
        """
        长文本预处理，优化passage分割效果
        
        Args:
            content: 原始文本内容
            
        Returns:
            str: 预处理后的文本
        """
        # 1. 标准化换行符
        content = content.replace('\r\n', '\n').replace('\r', '\n')
        
        # 2. 清理多余的空行，但保留段落分隔
        lines = content.split('\n')
        cleaned_lines = []
        prev_empty = False
        
        for line in lines:
            line = line.strip()
            if line:  # 非空行
                cleaned_lines.append(line)
                prev_empty = False
            else:  # 空行
                if not prev_empty:  # 只保留一个空行作为段落分隔
                    cleaned_lines.append('')
                    prev_empty = True
        
        # 3. 重新组合，确保段落之间有双换行
        processed_content = '\n'.join(cleaned_lines)
        
        # 4. 确保段落分隔符正确
        # 将单换行后的空行转换为双换行
        processed_content = processed_content.replace('\n\n', '\n\n')  # 保持现有的双换行
        
        # 5. 处理章节标题（如果有明显的标题标记）
        if self._detect_chapter_markers(processed_content):
            processed_content = self._enhance_chapter_separation(processed_content)
        
        # 6. 统计处理结果
        original_paragraphs = content.count('\n\n') + 1
        processed_paragraphs = processed_content.count('\n\n') + 1
        
        if hasattr(self, 'logger') and self.logger:
            self.logger.info(f"📝 长文本预处理完成: {original_paragraphs} -> {processed_paragraphs} 个段落")
        
        return processed_content
    
    def _detect_chapter_markers(self, content: str) -> bool:
        """检测是否有章节标记"""
        chapter_patterns = [
            r'第[一二三四五六七八九十\d]+章',  # 中文章节
            r'Chapter\s+\d+',                   # 英文章节
            r'^#{1,3}\s+',                      # Markdown标题
            r'^\d+\.\s+[A-Z]',                 # 数字标题
        ]
        
        for pattern in chapter_patterns:
            if re.search(pattern, content, re.MULTILINE):
                return True
        return False
    
    def _enhance_chapter_separation(self, content: str) -> str:
        """增强章节分隔"""
        # 在章节标题前添加额外的分隔
        patterns = [
            (r'(第[一二三四五六七八九十\d]+章)', r'\n\n\1'),
            (r'(Chapter\s+\d+)', r'\n\n\1'),
            (r'^(#{1,3}\s+)', r'\n\n\1', re.MULTILINE),
        ]
        
        for pattern, replacement, *flags in patterns:
            flag = flags[0] if flags else 0
            content = re.sub(pattern, replacement, content, flags=flag)
        
        return content


def chunk_project_files(file_paths: List[str], config: Optional['ChunkConfig'] = None, **kwargs) -> List[ChunkResult]:
    """
    对项目文件进行分块的便捷函数
    
    Args:
        file_paths: 文件路径列表
        config: ChunkConfig配置对象，如果提供则优先使用
        **kwargs: DocumentChunker的参数（当config为None时使用）
    
    Returns:
        分块结果列表
    """
    if config:
        chunker = DocumentChunker.from_config(config)
    else:
        chunker = DocumentChunker(**kwargs)
    return chunker.process_files(file_paths)


def chunk_project_files_with_preset(file_paths: List[str], preset: str = "code_project") -> List[ChunkResult]:
    """
    使用预设配置对项目文件进行分块
    
    Args:
        file_paths: 文件路径列表
        preset: 预设配置名称，默认为'code_project'
    
    Returns:
        分块结果列表
    """
    config = ChunkConfigManager.get_config(preset)
    return chunk_project_files(file_paths, config=config)


if __name__ == "__main__":
    # 简单测试
    import tempfile
    
    print("🧪 测试DocumentChunker...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # 创建测试文件
        test_file = Path(temp_dir) / 'test.txt'
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write("这是一个测试文档。" * 100)  # 创建较长的内容
        
        # 测试分块
        chunker = DocumentChunker(chunk_size=50, chunk_overlap=10)
        chunks = chunker.process_files([str(test_file)])
        
        print(f"✅ 测试完成，生成 {len(chunks)} 个分块")
        for i, chunk in enumerate(chunks[:3]):  # 显示前3个
            print(f"  块 {i+1}: {len(chunk.chunk_text)} 字符")