from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task


@CrewBase
class Debate():
    """Debate crew"""


    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    # type: ignore
    @agent
    def debater(self) -> Agent:
        return Agent(config=self.agents_config['debater'],verbose=True)  # type: ignore
        

    @agent
    def judge(self) -> Agent:
        return Agent(config=self.agents_config['judge'], verbose=True)  # type: ignore

    @task
    def propose(self) -> Task:
        return Task(config=self.tasks_config['propose'], verbose=True)  # type: ignore

    @task
    def oppose(self) -> Task:
        return Task(config=self.tasks_config['oppose'], verbose=True)  # type: ignore

    @task
    def decide(self) -> Task:
        return Task(config=self.tasks_config['decide'], verbose=True)  # type: ignore

    @crew
    def crew(self) -> Crew:
        """Creates the Debate crew"""

        return Crew(
            agents=self.agents,  # Automatically created by the @agent decorator # type: ignore
            tasks=self.tasks,  # Automatically created by the @task decorator # type: ignore
            process=Process.sequential,
            verbose=True,
        )
