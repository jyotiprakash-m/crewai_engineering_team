class Todo:
    def __init__(self):
        """
        Initializes the Todo list as an empty list.
        """
        self.tasks = []
        self.next_id = 1  # To keep track of the next available ID

    def add_task(self, title: str, description: str) -> int:
        """
        Adds a new task to the todo list with the provided title and description.
        Each task is assigned a unique integer ID.
        
        Parameters:
            title (str): The title of the task.
            description (str): The description of the task.
            
        Returns:
            int: The ID of the newly created task.
        """
        task = {
            'id': self.next_id,
            'title': title,
            'description': description,
            'completed': False
        }
        self.tasks.append(task)
        self.next_id += 1
        return task['id']

    def view_tasks(self) -> list:
        """
        Returns a list of all tasks. Each task is represented as a dictionary.
        
        Returns:
            list: A list of dictionaries. Each dictionary contains details of a task
                  (ID, title, description, status).
        """
        return self.tasks

    def get_task_details(self, task_id: int) -> dict:
        """
        Retrieves the details of a specific task by its ID.
        
        Parameters:
            task_id (int): The ID of the task to retrieve.
            
        Returns:
            dict: A dictionary containing the details of the task 
                  (ID, title, description, status).
        """
        for task in self.tasks:
            if task['id'] == task_id:
                return task
        return None

    def update_task(self, task_id: int, title: str = None, description: str = None, completed: bool = None) -> bool:
        """
        Updates the specified task's title, description, or completion status 
        based on the provided arguments.
        
        Parameters:
            task_id (int): The ID of the task to update.
            title (str): The new title of the task (optional).
            description (str): The new description of the task (optional).
            completed (bool): The new completion status of the task (optional).
            
        Returns:
            bool: True if the task was successfully updated, False otherwise.
        """
        for task in self.tasks:
            if task['id'] == task_id:
                if title is not None:
                    task['title'] = title
                if description is not None:
                    task['description'] = description
                if completed is not None:
                    task['completed'] = completed
                return True
        return False

    def delete_task(self, task_id: int) -> bool:
        """
        Deletes the task with the specified ID from the todo list.
        
        Parameters:
            task_id (int): The ID of the task to be deleted.
            
        Returns:
            bool: True if the task was successfully deleted, False otherwise.
        """
        for i, task in enumerate(self.tasks):
            if task['id'] == task_id:
                self.tasks.pop(i)
                return True
        return False

# Test the Todo class functionality
if __name__ == "__main__":
    # Create a new Todo instance
    todo = Todo()
    
    # Add some tasks
    task1_id = todo.add_task("Complete project", "Finish the Python todo application")
    task2_id = todo.add_task("Buy groceries", "Milk, eggs, bread")
    
    # View all tasks
    print("All tasks:")
    for task in todo.view_tasks():
        print(f"ID: {task['id']}, Title: {task['title']}, Completed: {task['completed']}")
    
    # Get details of a specific task
    print("\nTask details:")
    task_details = todo.get_task_details(task1_id)
    print(task_details)
    
    # Update a task
    print("\nUpdating task...")
    todo.update_task(task1_id, title="Complete Python project", completed=True)
    
    # View updated task
    updated_task = todo.get_task_details(task1_id)
    print(f"Updated task: {updated_task}")
    
    # Delete a task
    print("\nDeleting task...")
    result = todo.delete_task(task2_id)
    print(f"Task deleted: {result}")
    
    # View all tasks after deletion
    print("\nRemaining tasks:")
    for task in todo.view_tasks():
        print(f"ID: {task['id']}, Title: {task['title']}, Completed: {task['completed']}")