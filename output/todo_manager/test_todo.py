import unittest
from todo import Todo

class TestTodo(unittest.TestCase):
    def setUp(self):
        # Create a fresh Todo instance for each test
        self.todo = Todo()
    
    def test_init(self):
        """Test that a new Todo instance has an empty tasks list and next_id=1"""
        self.assertEqual(self.todo.tasks, [])
        self.assertEqual(self.todo.next_id, 1)
    
    def test_add_task(self):
        """Test adding a task"""
        # Add a task and check the returned ID
        task_id = self.todo.add_task("Test Task", "Test Description")
        self.assertEqual(task_id, 1)
        
        # Check that the task was added correctly
        self.assertEqual(len(self.todo.tasks), 1)
        self.assertEqual(self.todo.tasks[0]["id"], 1)
        self.assertEqual(self.todo.tasks[0]["title"], "Test Task")
        self.assertEqual(self.todo.tasks[0]["description"], "Test Description")
        self.assertEqual(self.todo.tasks[0]["completed"], False)
        
        # Add another task and check ID incrementation
        second_id = self.todo.add_task("Second Task", "Second Description")
        self.assertEqual(second_id, 2)
        self.assertEqual(self.todo.next_id, 3)
    
    def test_view_tasks(self):
        """Test viewing all tasks"""
        # Empty list initially
        self.assertEqual(self.todo.view_tasks(), [])
        
        # Add tasks and check view_tasks returns them
        self.todo.add_task("Task 1", "Description 1")
        self.todo.add_task("Task 2", "Description 2")
        tasks = self.todo.view_tasks()
        
        self.assertEqual(len(tasks), 2)
        self.assertEqual(tasks[0]["title"], "Task 1")
        self.assertEqual(tasks[1]["title"], "Task 2")
    
    def test_get_task_details(self):
        """Test getting details of a specific task"""
        # Return None for non-existent task
        self.assertIsNone(self.todo.get_task_details(999))
        
        # Add a task and check we can get its details
        task_id = self.todo.add_task("Task Title", "Task Description")
        task = self.todo.get_task_details(task_id)
        
        self.assertEqual(task["id"], task_id)
        self.assertEqual(task["title"], "Task Title")
        self.assertEqual(task["description"], "Task Description")
        self.assertEqual(task["completed"], False)
    
    def test_update_task(self):
        """Test updating a task's details"""
        # Return False for non-existent task
        self.assertFalse(self.todo.update_task(999, title="New Title"))
        
        # Add a task then update each field
        task_id = self.todo.add_task("Original Title", "Original Description")
        
        # Update title only
        result = self.todo.update_task(task_id, title="Updated Title")
        self.assertTrue(result)
        task = self.todo.get_task_details(task_id)
        self.assertEqual(task["title"], "Updated Title")
        self.assertEqual(task["description"], "Original Description")
        self.assertEqual(task["completed"], False)
        
        # Update description only
        result = self.todo.update_task(task_id, description="Updated Description")
        self.assertTrue(result)
        task = self.todo.get_task_details(task_id)
        self.assertEqual(task["title"], "Updated Title")
        self.assertEqual(task["description"], "Updated Description")
        self.assertEqual(task["completed"], False)
        
        # Update completed status only
        result = self.todo.update_task(task_id, completed=True)
        self.assertTrue(result)
        task = self.todo.get_task_details(task_id)
        self.assertEqual(task["title"], "Updated Title")
        self.assertEqual(task["description"], "Updated Description")
        self.assertEqual(task["completed"], True)
        
        # Update multiple fields at once
        result = self.todo.update_task(task_id, title="Final Title", description="Final Description", completed=False)
        self.assertTrue(result)
        task = self.todo.get_task_details(task_id)
        self.assertEqual(task["title"], "Final Title")
        self.assertEqual(task["description"], "Final Description")
        self.assertEqual(task["completed"], False)
    
    def test_delete_task(self):
        """Test deleting a task"""
        # Return False for non-existent task
        self.assertFalse(self.todo.delete_task(999))
        
        # Add tasks and delete one
        task1_id = self.todo.add_task("Task 1", "Description 1")
        task2_id = self.todo.add_task("Task 2", "Description 2")
        
        result = self.todo.delete_task(task1_id)
        self.assertTrue(result)
        
        # Check task was deleted
        self.assertEqual(len(self.todo.tasks), 1)
        self.assertIsNone(self.todo.get_task_details(task1_id))
        self.assertIsNotNone(self.todo.get_task_details(task2_id))

if __name__ == "__main__":
    unittest.main()