# src/financial_researcher/crew.py
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import SerperDevTool

@CrewBase
class ResearchCrew():
    """Research crew for comprehensive topic analysis and reporting"""

    @agent
    def researcher(self) -> Agent:
        return Agent(config=self.agents_config['researcher'],verbose=True,tools=[SerperDevTool()])  # type: ignore

    @agent
    def analyst(self) -> Agent:
        return Agent(config=self.agents_config['analyst'],verbose=True,tools=[SerperDevTool()])  # type: ignore


    @task
    def research_task(self) -> Task:
        return Task(config=self.tasks_config['research_task'])  # type: ignore

    @task
    def analysis_task(self) -> Task:
        return Task(config=self.tasks_config['analysis_task'], output_file='output/report.md')  # type: ignore

    @crew
    def crew(self) -> Crew:
        """Creates the research crew"""
        return Crew(
            agents=self.agents, # type: ignore
            tasks=self.tasks,# type: ignore
            process=Process.sequential,
            verbose=True,
        )