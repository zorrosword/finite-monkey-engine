class ChecklistPipelinePrompt:


    def generate_checklist_prompt(business_description):
        return f"""
        {business_description}
        <optimized_prompt>
        <task>制定针对业务逻辑漏洞的详细检查清单</task>

        <context>

        以上是一段业务逻辑描述，应该有哪些专门的针对于漏洞的checklist，把他们列出来，务必要覆盖所有可能的业务逻辑，详细的列出来

        </context>

        <instructions>

        1. 仔细分析上述业务逻辑描述，明确各个业务逻辑环节和流程。

        2. 根据业务逻辑的特点，识别可能存在的漏洞类型，确保覆盖所有可能的逻辑漏洞场景

        4. 将所有检查项汇总后，按照业务逻辑流程顺序进行分类和整理，形成清晰明确的检查清单。

        5. 确保检查清单完整覆盖所有可能发生漏洞的业务逻辑场景，不遗漏任何关键环节。

        </instructions>

        <output_format>
        以清晰详细的列表形式输出，每个检查项需明确漏洞类型、检查内容和对应的业务逻辑环节，格式示例如下：

        漏洞类型：XXX漏洞
        检查内容：
        具体检查内容一
        具体检查内容二
        业务逻辑环节：XXX环节
        以此类推，覆盖所有漏洞检查项。
        </output_format>
        </optimized_prompt>

        """
    
    def generate_project_type_checklist_prompt(language,project_type_list):
        return f"""
        {project_type_list}
        <optimized_prompt>
        <task>制定针对不同项目中所有可能存在的漏洞的详细检查清单</task>

        <context>

        以上是针对blockchain ecosystem中{language}项目的细分，应该有哪些专门的细分中每个项目的漏洞的checklist，把他们列出来，务必要覆盖所有可能的漏洞，包括{language}通用(主流)以及该项目所涉及的技术栈的特定漏洞，详细的列出来

        </context>

        <instructions>

        1. 仔细分析上述所有solidity的项目细分，明确每个项目可能涉及的技术栈、协议、流程。

        2. 根据项目中涉及的技术栈、协议、流程，识别可能存在的漏洞，确保覆盖所有可能的漏洞

        4. 将所有检查项汇总后，按照项目类型分类和整理，形成清晰明确的不同项目下的检查清单。

        5. 确保检查清单完整覆盖项目中所有可能发生漏洞的技术栈、协议、流程，不遗漏任何关键环节。

        </instructions>

        <output_format>
        以清晰详细的列表形式输出，每个检查项需明确漏洞标题、漏洞描述、检查内容，格式示例如下：

        漏洞类型：XXX (如：还款恢复后借款人立即被清算)
        漏洞描述：XXX (如：如果在还款暂停期间市场条件恶化，当还款重新启用而没有宽限期时，未变更的清算阙值可能触发即时清算，让借款人几乎没有恢复机会)
        检查内容：
        具体检查内容一
        具体检查内容二
        以此类推，覆盖所有漏洞检查项。
        </output_format>
        </optimized_prompt>

        """
    
    def extract_business_prompt(code_to_be_tested):
        return f"""
        {code_to_be_tested}
        <optimized_prompt>
        <task>分析代码片段的业务逻辑并提炼相关关键词</task>

        <context>

        这个代码是什么业务逻辑相关的，把代码关键业务逻辑与数据操作抽象的描述出来，并描述出与代码业务相关的关键词 用中文

        </context>

        <instructions>

        1. 仔细阅读提供的代码片段，理解代码中体现的业务逻辑。

        2. 提取代码片段中涉及的关键业务流程和操作步骤，抽象成清晰易懂的中文描述。

        3. 明确代码涉及的数据操作，包括数据的增删改查、转换、校验等操作，并用中文进行抽象描述。

        4. 根据代码上下文和业务逻辑，归纳总结出与该代码密切相关的业务关键词，关键词需中文表达。

        5. 对抽象描述和关键词进行校对，确保准确体现原始代码的业务意图。

        </instructions>

        <output_format>
        输出内容应包括以下三部分：

        业务逻辑描述：

        以简洁明了的语言逐条描述代码实现的核心业务逻辑。
        每条描述单独成行，用短语或句子清晰表达。
        数据操作描述：

        明确指出代码中出现的数据操作类型（增、删、改、查、转换、校验等）。
        每种数据操作单独成行，分别描述其具体含义和作用。
        相关业务关键词：

        列出与代码业务逻辑紧密相关的关键词。
        关键词之间用中文逗号隔开，如："订单管理，库存更新，用户验证"。
        </output_format>
        </optimized_prompt>
        """
    def generate_consensus_prompt(checklists):
        checklists_str = "\n---\n".join(checklists)
        return f"""
        <optimized_prompt>
        <task>分析多个检查清单并提取共识内容</task>

        <context>
        以下是多个AI模型生成的检查清单：

        {checklists_str}

        请分析这些清单，提取出所有模型达成共识的检查项。
        </context>

        <instructions>
        1. 对比分析所有清单中的检查项
        2. 提取出在多个清单中重复出现的核心检查内容
        3. 合并相似的检查项，保持描述的准确性和完整性
        4. 确保提取的共识内容保持原有的逻辑结构
        5. 重新组织和优化检查项的表述，使其更加清晰和系统
        </instructions>

        <output_format>
        请按照原有的格式输出，包括：
        - 漏洞类型
        - 检查内容
        - 业务逻辑环节
        </output_format>
        </optimized_prompt>
        """
    
    def merge_project_type_list(language, project_type_lists):
        project_type_lists_str = "\n---\n".join(project_type_lists)
        return f"""
        <optimized_prompt>
        <task>分析多个检查清单并提取共识内容</task>

        <context>
        以下是多个AI模型生成的针对blockchain ecosystem中{language}项目所有可能存在的漏洞的检查清单：

        {project_type_lists_str}

        请分析这些清单，提取出所有模型达成共识的检查项。
        </context>

        <instructions>
        1. 对比分析所有清单中的检查项
        2. 提取出在多个清单中重复出现的核心检查内容
        3. 合并相似的检查项，保持描述的准确性和完整性
        4. 确保提取的共识内容保持原有的逻辑结构
        5. 重新组织和优化检查项的表述，使其更加清晰和系统
        </instructions>

        <output_format>
        请按照原有的格式输出，包括：
        - 漏洞标题
        - 漏洞描述
        - 检查内容
        </output_format>
        </optimized_prompt>
        """

    def generate_add_on_checklist_prompt(business_description, base_checklist):
        return f"""
        {business_description}
        <optimized_prompt>
        <task>基于现有检查清单进行深化和扩展</task>

        <context>
        以上是一段业务逻辑描述，现有的检查清单如下：

        {base_checklist}

        请基于这个清单，进一步深化和扩展检查内容。
        </context>

        <instructions>
        1. 分析现有检查项，找出可能的扩展点和深化方向
        2. 考虑每个检查项的边界情况和特殊场景
        3. 添加更细致的子检查项
        4. 补充可能遗漏的相关业务场景
        5. 确保新增的检查项与现有项目不重复
        6. 保持检查项之间的逻辑关联性
        </instructions>

        <output_format>
        
        - 漏洞类型：XXX漏洞
        - 检查内容：
          具体检查内容
        - 业务逻辑环节：XXX环节
        </output_format>
        </optimized_prompt>
        """
    
    def generate_add_on_project_type_checklist_prompt(language, project_type_list, base_checklist):
        return f"""
        {project_type_list}
        <optimized_prompt>
        <task>基于现有检查清单进行深化和扩展</task>

        <context>
        以上是针对blockchain ecosystem中{language}项目的细分，现有的针对项目中可能存在的漏洞的检查清单如下：

        {base_checklist}

        请基于这个清单，进一步深化和扩展检查内容。
        </context>

        <instructions>
        1. 分析现有检查项，找出可能的扩展点和深化方向
        2. 考虑每个检查项的边界情况和特殊场景
        3. 添加更细致的子检查项
        4. 考虑所有与该项目强相关的技术栈、协议、流程，以及可能存在的漏洞
        5. 确保新增的检查项与现有项目不重复
        6. 保持检查项之间的逻辑关联性
        </instructions>

        <output_format>
        
        漏洞类型：XXX (如：还款恢复后借款人立即被清算)
        漏洞描述：XXX (如：如果在还款暂停期间市场条件恶化，当还款重新启用而没有宽限期时，未变更的清算阙值可能触发即时清算，让借款人几乎没有恢复机会)
        检查内容：
        具体检查内容一
        具体检查内容二
        </output_format>
        </optimized_prompt>
        """
    
    def list_project_types_for_specific_language(language):
        return f"""### Context
You are a blockchain architect with expertise in multiple programming languages (Solidity, Rust, C++, Go) and their applications in blockchain ecosystem.

### Objective
Exhaustively list and describe all types of projects that can be developed using {language} in blockchain, covering both mainstream and niche domains.

### Structure
1. Categorize projects by domain (e.g., DeFi, NFTs, Infrastructure).
2. Define subcategories (e.g., lending protocols, oracle networks, slippage-related).
3. Provide examples (protocols, tools, frameworks) and technical specifics (libraries, standards, algorithms).

### Tone
Technical, precise, and thorough.

### Audience
Blockchain expert in using {language}.

### Response Requirements
1. Prioritize completeness over brevity.
2. Cover innovative use cases (e.g., zero-knowledge proofs in Rust, C++ for blockchain node clients).
3. Precise and technical language.
```
"""
# 4. Response format (in JSON style), MUST encapsulate with ```json and ```: 
# ```json
# {{
#     {{Domain 1}}:[
#             {{Subcategory 1}}:[{{protocol/tool/framework/library/standard/algorithm}}, {{protocol/tool/framework/library/standard/algorithm}}],
#             {{Subcategory 2}}:[{{protocol/tool/framework/library/standard/algorithm}}, {{protocol/tool/framework/library/standard/algorithm}}]
#         ],
#     ...
# }}


    def complement_project_type_list(language, project_types):
        return f"""### Context
You are a blockchain architect with expertise in multiple programming languages (Solidity, Rust, C++, Go) and their applications in blockchain ecosystem.

### Objective
Expand the list (encapsulated by <project type list> and </project type list>) by adding novel, non-overlapping project types that were omitted, focusing on niche domains, emerging trends, or underutilized technical capabilities of {language}.

### Structure
1. Review given list: Summarize key categories already covered (to avoid duplication).
2. Propose New Categories/Subcategory/examples/technical specifics: Identify gaps (e.g., overlooked domains, experimental use cases).

### Tone
Analytical, forward-looking, and technically rigorous.

### Audience
Developers seeking to innovate with {language} beyond mainstream applications.

### Response Requirements
1. Prioritize novel additions (e.g., projects using cutting-edge cryptography, novel governance models).
2. Highlight language-specific advantages (e.g., C++ for low-latency consensus engines).
3. Avoid overlap with prior categories—focus on gaps.
4. Add directly to the given list and comply with the original format.

<project type list>
{project_types}
</project type list>
"""
    
    def merge_project_type_list(language, lists):
        project_type_lists = "\n---\n".join(lists)
        return f"""### Context
You are a technical editor synthesizing inputs from multiple LLM-generated lists of {language} blockchain project types.

### Objective
Merge all input lists (encapsulated by <project type lists> and </project type lists>) into one unified taxonomy that:
1. Removes duplicates.
2. Groups overlapping entries under standardized category/subcategory names.
3. Preserves 100% of unique project types from all sources.

### Structure
1. Deduplication: Identify identical or semantically equivalent entries.
2. Hierarchical Merging:
        Align categories (e.g., "DeFi" vs. "Decentralized Finance" → use "DeFi").
        Consolidate subcategories (e.g., "Lending" and "Borrowing" → "Lending/Borrowing Platforms").
3. Validation: Cross-check merged list against inputs to ensure no omissions.

### Tone
Methodical, precise, and detail-oriented.

### Audience
Blockchain expert in using {language}.

### Response Requirements
1. Output a hierarchical markdown list with categories → subcategories → examples/technical specifics.
2. Prioritize clarity over source formatting (e.g., rename poorly named categories).

<project type lists>
{project_type_lists}
</project type lists>
"""