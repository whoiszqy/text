from metagpt.environment import Environment
from metagpt.logs import logger
from agent_v4.roles import AnalysisIntentRole,PlanRole,DirectoryGenRole,StepAnalysisRole,SummarizeRole,DocumentGenerationRole

class AgentEnvironment(Environment):
    # 主题
    topic:str = None
    def __init__(self):
        super().__init__()
        self.add_roles([AnalysisIntentRole(), PlanRole(), DirectoryGenRole(), StepAnalysisRole(), SummarizeRole(),
                       DocumentGenerationRole()])
    desc:str = """
        In modern industrial production, intelligent assistants play an increasingly critical role as an integral part of industrial control systems. Here are some tasks that intelligent assistants can accomplish:

        1. **Real-time Monitoring and Data Analysis**: Intelligent assistants can monitor the operational status of production lines in real-time, collect critical data such as temperature, pressure, and speed, and analyze this data through advanced algorithms to promptly detect anomalies and issue warnings, ensuring the stability and safety of the production process.
        
        2. **Automated Control**: Intelligent assistants can automatically execute preset production processes, adjusting equipment parameters to optimize production efficiency. For instance, when encountering production bottlenecks, intelligent assistants can automatically adjust machine speeds or switch working modes to maintain the smooth operation of the production line.
        
        3. **Fault Diagnosis and Maintenance**: When equipment malfunctions, intelligent assistants can quickly pinpoint the cause of the problem by analyzing historical and real-time data, and provide solutions or maintenance recommendations. This significantly reduces downtime and improves equipment availability.
        
        4. **Energy Management**: Intelligent assistants can monitor and optimize energy usage by adjusting production schedules and equipment operating modes, reducing energy waste and lowering production costs. For example, adjusting equipment operation during off-peak hours or automatically shutting down unnecessary equipment during peak energy consumption times.
        
        5. **Quality Control**: Intelligent assistants can monitor product quality in real-time, ensuring that products meet strict quality standards through image recognition and data analysis technologies. Upon detecting quality issues, intelligent assistants can immediately notify relevant personnel and assist in adjusting production parameters to prevent defective products.
        
        6. **Human-Machine Interaction**: Intelligent assistants provide a user-friendly interface, allowing operators to easily interact with the system, access necessary information, and execute operation commands. Through voice recognition and natural language processing technologies, intelligent assistants can also understand operators' commands and provide more personalized services.
        
        Through these functionalities, intelligent assistants not only enhance the efficiency and quality of industrial production but also increase the flexibility and responsiveness of the production process, laying a solid foundation for the realization of Industry 4.0.
    """

    def get_topic(self):
        return self.topic




