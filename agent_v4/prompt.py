ANALYSIS_INTENT_PROMPT = """
Please analyze the intention of {instruction} and return the options in {options}, requiring:
1. Return the number corresponding to the option, for example: A
2. Do not have redundant output, including concluding remarks.
3. Only one option can be returned, multiple options cannot be returned
"""

ANALYSIS_INTENT_OPTIONS = """
A: Generate report
B: Problem consultation
C: Other
"""

WRITE_PLAN_ACTION_PROMPT = """
# Context:
{context}
# Available Task Types:
{task_type_desc}
# References:
{references}
# Task:
Based on the context, use the content from the references to write a plan or modify an existing plan, explaining what you should do to achieve the goal. A plan consists of one to {max_tasks} tasks.
If you are modifying an existing plan, carefully follow the instruction, don't make unnecessary changes. Give the whole plan unless instructed to modify only one task of the plan.
If you encounter errors on the current task, revise and output the current single task only.
Output a list of jsons following the format:
```json
[
    {{
        "task_id": str = "unique identifier for a task in plan, can be an ordinal",
        "dependent_task_ids": list[str] = "ids of tasks prerequisite to this task",
        "instruction": "what you should do in this task, one short phrase or sentence",
        "task_type": "type of this task, should be one of Available Task Types",
    }},
    ...
]
```
Please use {language} to return the content of the instruction.
"""

FAULT_DIRECTORY_PROMPT_V4 = (
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
        - Answer strictly in the dictionary format like {{"title": "xxx", "directory": [{{"dir 1": ["sub dir 1", "sub dir 2"]}}, {{"dir 2": ["sub dir 3", "sub dir 4"]}}]}}.
        """)

PRODUCTION_RUN_PROMPT_V5 = (
    """
        #  Production run report outline generation

        ##  Project Overview
        - **Project Name**: {topic}
        - **Report Language**: {language}
      
        ## Customized Outline Structure
        1. **Introduction**
            - 1.1 Purpose of the Report
            - 1.2 Overview of the Production Run
            - 1.3 Analysis Methods and Tools
        2. **Production Run Description**
            - 2.1 Time and Environment of Production Run
            - 2.2 Detailed Description of Production Phenomenon
            - 2.3 Scope and Severity of Impact
        3. **Production Analysis**
            - 3.1 Initial Analysis
                - 3.1.1 Analysis of Tool Results
                - 3.1.2 Preliminary Conclusions
            - 3.2 In-depth Analysis
                - 3.2.1 Data Analysis
                - 3.2.2 System Log Analysis
                - 3.2.3 Hardware Inspection
            - 3.3 Determination of Production Issues
        4. **Solutions and Recommendations**
            - 4.1 Immediate Remedial Actions
            - 4.2 Long-term Solutions
            - 4.3 Recommendations for Preventive Measures
        5. **Conclusion**
            - 5.1 Summary of the Production Run
            - 5.2 Directions for Future Improvements
        6. **Appendix**
            - 6.1 Data Tables
            - 6.2 Charts
            - 6.3 References

        ## Notes
        - Ensure all sections are closely related to {topic}.
        - Use {language} to accurately convey analysis results and recommendations.
        - Answer strictly in the dictionary format like {{"title": "xxx", /n"directory": /n[{{"dir 1": [/n"sub dir 1", /n"sub dir 2"]}}, /n{{"dir 2": [/n"sub dir 3", /n"sub dir 4"]}}]}}Please generate in Chinese.
        """
)

FAULT_DIRECTORY_PROMPT_V6 = (
    """
        #  Failure analysis report outline generation

        ##  Project Overview
        - **Project Name**: {topic}
        - **Report Language**: {language}
      
        ## Customized Outline Structure
        1. **Introduction**
            - 1.1 Overview of the Fault
            - 1.2 Analysis Methods and Tools
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
            - 3.3 Determination of Fault Causes
        4. **Solutions and Recommendations**
            - 4.1 Immediate Remedial Actions
            - 4.2 Long-term Solutions
            - 4.3 Recommendations for Preventive Measures
        5. **Conclusion**
            - 5.1 Summary of the Fault
            - 5.2 Directions for Future Improvements
        ## Notes
        - Ensure all sections are closely related to {topic}.
        - Use {language} to accurately convey analysis results and recommendations.
        - Answer strictly in the dictionary format like {{"title": "xxx", /n"directory": /n[{{"dir 1": [/n"sub dir 1", /n"sub dir 2"]}}, /n{{"dir 2": [/n"sub dir 3", /n"sub dir 4"]}}]}}Generate contents in Chinese.  
        - Answer in Chinese
    """
)

SELECT_PROMPT=(
    """
    #Prompt word selection
    ##Theme
    {topic}
    ##List of prompt words
    {prompts}
    ##Requirement
    Retrieve the corresponding prompt words from {prompts} based on the topic {topic} and return the results.
    ##Requirement
    1. To return the result, the key value needs to be returned, for example: PRODUCTION.
    2. If there are no matching items, return None.
    3. Other irrelevant content cannot be returned.
    """
)

COMMON_PROMPT1 = """
You are now a seasoned technical professional in the field of the internet. 
We need you to write a technical tutorial with the topic "{topic}".
"""

CONTENT_PROMPT1 = (
    COMMON_PROMPT1
    + """
Topic: {topic}
Directory: {directory}

Now I will give you the module directory titles for the topic. 
Please output the detailed principle content of this title in detail. 
If there are code examples, please provide them according to standard code specifications. 
Without a code example, it is not necessary.

The module directory titles for the topic is as follows:
{directory} 

Strictly limit output according to the following requirements:
1. Follow the Markdown syntax format for layout.
2. If there are code examples, they must follow standard syntax specifications, have document annotations, and be displayed in code blocks.
3. The output must be strictly in the specified language, {language}.
4. Do not have redundant output, including concluding remarks.
5. Strict requirement not to output the topic "{topic}".
"""
)