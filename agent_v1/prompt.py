"""
意图分析角色提示词
"""

INTENT_PROMPT = (
    """
    You are currently a professional technician in language analysis.
    We need you to conduct intent analysis on the text.
    """
)

INTENT_ANALYSIS_PROMPT = (
        INTENT_PROMPT
        +
        """
        Please conduct an intention analysis on {instruction} and strictly follow the following requirements:
        1. The output must strictly use the specified {language}.
        2. Answer strictly in the dictionary format like {{"intent":"咨询"}}.
        3. Do not have extra spaces or line breaks.
        4. Each intention has practical significance.
        """
)

KEYWORDS_PROMPT = (
    """
    You are currently a professional technician in language analysis.
    We need you to extract keywords from the text.
    """
)

KEYWORDS_ANALYSIS_PROMPT = (
        KEYWORDS_PROMPT +
        """
        Please extract keywords from {instruction} and strictly adhere to the following requirements:
        1. The output must strictly use the specified {language}.
        2. Answer strictly in dictionary format, such as {{"keywords": ["xxx", "yyy", "zzz"]}}. If no keywords are extracted or content is not received, return None, such as {{"keywords": None}}.
        3. Do not have extra spaces or line breaks.
        4. Each intention has practical significance.
        """
)

MATCHING_TOOLS_COMMON_PROMPT = (
    """
    You are currently a professional technician for matching tools.
    You need to match the corresponding tools based on the provided text.
    """
)

MATCHING_TOOLS_PROMPT = (
        MATCHING_TOOLS_COMMON_PROMPT
        +
        """
        Please follow step {instruction} to accurately match the tools in {tools} and return the corresponding code_num. Strictly comply with the following requirements:
        1. The output must strictly use the specified {language}.
        2. Answer strictly in dictionary format, without any other context, for example {{"code_num": "00001"}}.
        3. Do not have extra spaces or line breaks.
        4. If a matching tool cannot be found in the provided tool, it is necessary to return {{"code_num": "00000"}}, and no other content can be returned.
        5. Return to other content. I'll beat you up
        """
)

MATCH_TOOLS_PROMPT = (
    """
    You are currently a professional technician for matching tools.
    You need to match the corresponding tools based on the provided text.
    
    Please match all {tools} in the {instruction} and return the code_num of the best matching tool, strictly adhering to the following requirements:
    1. The output must strictly use the specified {language}.
    2. Answers must be in dictionary format without any other context, such as {{"code_num": "00001"}}.
    3. Do not have extra spaces or line breaks.
    If a matching tool cannot be found in the provided tool, it is necessary to return {{"code_num": "00000"}}, and no other content can be returned.
    """
)

# 知识库系统提示词
KNOWLEDGE_BASE_SYSTEM_PROMPT = """### Requirements
1. Please summarize the latest dialogue based on the reference information (secondary) and dialogue history (primary). Do not include text that is irrelevant to the conversation.
2. The context is for reference only. If it is irrelevant to the user's search request history, please reduce its reference and usage.
2. If there are citable links in the context, annotate them in the main text in the format [main text](citation link). If there are none in the context, do not write links.
3. The reply should be graceful, clear, non-repetitive, smoothly written, and of moderate length, in {LANG}.

### Dialogue History (For example)
A: MLOps competitors

### Current Question (For example)
A: MLOps competitors

### Current Reply (For example)
1. Alteryx Designer: <desc> etc. if any
2. Matlab: ditto
3. IBM SPSS Statistics
4. RapidMiner Studio
5. DataRobot AI Platform
6. Databricks Lakehouse Platform
7. Amazon SageMaker
8. Dataiku
"""

# 知识库提示词
KNOWLEDGE_BASE_COMMON_PROMPT = (
    """
    ### Reference Information
    {CONTEXT}
    ﻿
    ### Dialogue History
    {QUERY_HISTORY}
    {QUERY}
    ﻿
    ### Current Question
    {QUERY}
    ﻿
    ### Current Reply: Based on the information, please write the reply to the Question
    """
)
# ### Dialogue History
# {QUERY_HISTORY}
# {QUERY}
# ﻿
KNOWLEDGE_BASE_STEP_PROMPT = (
    """
        ### Reference Information
        {CONTEXT}
        ﻿
        ### Current Question
        {QUERY}
        ﻿
        ###Current response: Based on the information, please gradually respond to the question and strictly comply with the following requirements:
        1. The output must strictly use the specified Chinese language.
        2. Do not have extra spaces or line breaks.
        3. Strictly refer to the original document, do not add any other content based on your own understanding, and the number of answers should not exceed the number of reference documents.
        4. Strictly return the result in dictionary format and require a sequence number, such as {{"steps": ["1. xxxx", "2. yyyy"]}}
        5. Answers must be based on the order of the reference documents, and the order cannot be changed arbitrarily.
        """
    # 4. Strictly return the result in dictionary format, such as {{"steps": ["1. xxxx", "2. yyyy"]}}
)

RESULT_FORMAT_PROMPT = (
    """
    You are currently an expert in analyzing and summarizing the causes of problems.
    You can summarize the provided content.

    Please convert {content} to text in markup format, analyze the reason for {question} based on the content of {content}, and return it as a summary at the end of the markup content. Strictly comply with the following requirements:
    1. The output must strictly use the specified Chinese language.
    2. Do not have extra spaces or line breaks.
    """
)

FAULT_COMMON_PROMPT = (
    """
    You are currently an experienced professional technician in the industrial field.
    We need you to write a fault analysis report with the theme "{topic}".
    """
)

FAULT_CONTENT_COMMON_PROMPT = (
    """
    You are currently an experienced professional technician in the industrial field.
    We need you to write a fault analysis report.
    """
)
# Please provide the specific table of contents for this tutorial, strictly following the following requirements:

# FAULT_DIRECTORY_PROMPT = (
#     FAULT_COMMON_PROMPT
#     + """
#     Please provide a specific table of contents for the report, strictly following the following requirements:
#     1. The output must be strictly in the specified language, {language}.
#     2. Answer strictly in the dictionary format like {{"title": "xxx", "directory": [{{"dir 1": ["sub dir 1", "sub dir 2"]}}, {{"dir 2": ["sub dir 3", "sub dir 4"]}}]}}.
#     3. The directory should be as specific and sufficient as possible, with a primary and secondary directory.The secondary directory is in the array.
#     4. The keys in the dictionary must be strictly in English.
#     5. Do not have extra spaces or line breaks.
#     6. Each directory title has practical significance.
# """
# )
#     Please provide a specific directory for the report. Please refer to {titles} for the actual fault analysis directory and strictly follow the following requirements:

FAULT_DIRECTORY_PROMPT = (
    FAULT_COMMON_PROMPT
    + """
    Please generate the corresponding fault analysis report directory based on the actual fault analysis results {tool_results}, and strictly comply with the following requirements:
    1. The output must be strictly in the specified language, {language}.
    2. Answer strictly in the dictionary format like {{"title": "xxx", "directory": [{{"dir 1": ["sub dir 1", "sub dir 2"]}}, {{"dir 2": ["sub dir 3", "sub dir 4"]}}]}}.
    3. The directory should be as specific and sufficient as possible, with a primary and secondary directory.The secondary directory is in the array.
    4. The keys in the dictionary must be strictly in English.
    5. Do not have extra spaces or line breaks.
    6. Each directory title has practical significance.
"""
)

# You are a report outline generator. Please generate a detailed table of contents in the following JSON format:
#
# ```json
# {{"title": "xxx", "directory": [{{"dir 1": ["sub dir 1", "sub dir 2"]}}, {{"dir 2": ["sub dir 3", "sub dir 4"]}}]}}

FAULT_CONTENTS_PROMPT = (
    FAULT_CONTENT_COMMON_PROMPT
    + """
    Now I will give you the module directory titles for the topic. 
    Please output the detailed principle content of this title in detail. 
    If there are code examples, please provide them according to standard code specifications. 
    Without a code example, it is not necessary.
    ﻿
    The module directory titles for the topic is as follows:
    {directory}
    ﻿
    Strictly limit output according to the following requirements:
    1. Follow the Markdown syntax format for layout.
    2. If there are code examples, they must follow standard syntax specifications, have document annotations, and be displayed in code blocks.
    3. The output must be strictly in the specified language, {language}.
    4. Do not have redundant output, including concluding remarks.
    5. Strict requirement not to output the topic "{topic}".
    """
)

FAULT_DIRECTORY_PROMPT_V1 = (
    """
        # Fault Analysis Report Outline Generation
        
        ## Background Information
        - **Topic**: {topic}
        - **Output Language**: {language}
        - **Tool Results**: {tool_results}
        
        ## Customized Outline Structure
        1. **Introduction**
            - 1.1 Purpose of the Report
            - 1.2 Overview of the Fault
            - 1.3 Analysis Methods and Tools
        2. **Fault Description**
            - 2.1 Time and Environment of Fault Occurrence
            - 2.2 Detailed Description of Fault Phenomenon
            - 2.3 Scope and Severity of Impact
        3. **Fault Analysis**
            - 3.1 Initial Analysis
                - 3.1.1 Analysis of Tool Results
                - 3.1.2 Preliminary Conclusions
            - 3.2 In-depth Analysis
                - 3.2.1 Data Analysis
                - 3.2.2 System Log Analysis
                - 3.2.3 Hardware Inspection
            - 3.3 Determination of Fault Cause
        4. **Solutions and Recommendations**
            - 4.1 Immediate Remedial Actions
            - 4.2 Long-term Solutions
            - 4.3 Recommendations for Preventive Measures
        5. **Conclusion**
            - 5.1 Summary of the Fault
            - 5.2 Directions for Future Improvements
        6. **Appendix**
            - 6.1 Data Tables
            - 6.2 Charts
            - 6.3 References
        
        ## Notes
        - Ensure all sections are closely related to {topic}.
        - Use {language} to accurately convey analysis results and recommendations.
        - Conduct detailed analysis based on the data and information from {tool_results}.
        - Please return the results in the following dictionary format:
        {{"title": "xxx", "directory": [{{"dir 1": ["sub dir 1", "sub dir 2"]}}, {{"dir 2": ["sub dir 3", "sub dir 4"]}}]}}.
        """
)

FAULT_CONTENT_COMMON_PROMPT_V1 = (
    """
    # Fault Analysis Report Content Generation
    
    ## Background Information
    - **Directory**: {directory}
    - **Subdirectory**: {subdirectory}
    - **Output Language**: {language}
    
    ## Content Generation Guidelines
    Based on the provided {directory} and {subdirectory} and {language}, we will generate detailed content for the fault analysis report using Markdown syntax format. Here are the steps for generating the content:
    
    1. **Headings**
       - Use Markdown's `#` symbol to create headings, determining the level of the heading based on the directory structure.
    
    2. **Content**
       - Write detailed principle content for each subheading within the {directory}.
       - If a subheading requires a code example, use Markdown's code block syntax (three backticks ``` to enclose the code) to display the code, ensuring it follows the standard syntax specifications of the {language} specified.
       - Code examples should include necessary documentation comments to explain the function and key parts of the code.
       - Please refer to {steps} for analysis methods
    
    3. **Formatting**
       - Use Markdown's list, bold, italic, and other formatting elements to enhance the readability and clarity of the content.
       - Ensure all content adheres to Markdown syntax rules for proper rendering on platforms that support Markdown.
    
    4. **Language**
       - All text content and code examples must be in the {language} specified.
    
    5. **Conciseness**
       - Avoid any redundant output, including concluding remarks.
    
    6. **Reference Data**
       - For a detailed analysis of the specific failure causes, please refer to {tool_results}.   
    
    ## Example
    Here is a simple Markdown format example showing how to generate content based on {directory} and {language}:
    
    # {directory}
    
    ## Subheading 1
    Here is the detailed principle content for Subheading 1.
    
    ## Subheading 2
    Here is the detailed principle content for Subheading 2.
    
    
    ## Notes
    - Ensure all content is related to the {directory} and is in the {language} specified.
    - Follow Markdown syntax format to ensure readability and compatibility of the content.
    """
)
