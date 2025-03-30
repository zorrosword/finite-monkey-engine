class ChecklistPipelinePrompt:


    def generate_checklist_prompt(self, business_description):
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

    def extract_business_prompt(self, code_to_be_tested):
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
    def generate_consensus_prompt(self, checklists):
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

    def generate_add_on_checklist_prompt(self, base_checklist):
        return f"""
        <optimized_prompt>
        <task>基于现有检查清单进行深化和扩展</task>

        <context>
        以下是现有的基础检查清单：

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
    
