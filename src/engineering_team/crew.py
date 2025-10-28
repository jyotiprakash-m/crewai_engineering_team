from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task



@CrewBase
class Coder():
    """Coder crew"""

    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    # One click install for Docker Desktop:
    # https://docs.docker.com/desktop/

    @agent
    def coder(self) -> Agent:
        return Agent(config=self.agents_config['coder'], verbose=True, allow_code_execution=True, code_execution_mode="safe", max_execution_time=100, max_retry_limit=3) # type: ignore


    @task
    def coding_task(self) -> Task:
        return Task( config=self.tasks_config['coding_task'] ) # type: ignore


    @crew
    def crew(self) -> Crew:
        """Creates the Coder crew"""


        return Crew(
            agents=self.agents,  # type: ignore
            tasks=self.tasks,  # type: ignore
            process=Process.sequential,
            verbose=True,
        )
