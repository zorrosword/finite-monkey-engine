class ChecklistsPrompt:
    def checklists_prompt():
        return """
<task>Generate Code Review Checklist</task>

<context>

What are all the checklist items for this code? Please provide a comprehensive, detailed output without missing any specific code logic, considering all scenarios related to specific business and code logic.

</context>

<instructions>

Checklist requirements:

Must cover all code paths and business scenarios, ensuring all business-related normal, abnormal, and edge cases are within the test scope.
Deep inspection of every technical detail and boundary condition, ensuring coverage of all possible exceptional situations.
Special focus on core business logic (marked with *), ensuring coverage of core business flows, key algorithms, decision logic, and processing logic.
Generate based on considering the business logic and scenarios of the provided code as a whole, not just focusing on a single function, but considering from the overall code business scenario perspective. </instructions>
<output_format>
Output in Markdown table format with the following columns:

Item (no more than 15 characters)
Check Points (detailed description, including instructions on how to check, chain of thought)
Table should contain at least 30 entries, use English headers, mark key business-related items with *
</output_format>
        """