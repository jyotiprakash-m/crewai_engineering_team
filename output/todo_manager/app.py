import gradio as gr
from todo import Todo

# Create a Todo instance
todo = Todo()

def add_task(title, description):
    """Add a new task to the todo list"""
    if not title.strip():
        return "Error: Title cannot be empty", None
    
    task_id = todo.add_task(title, description)
    return f"Task added with ID: {task_id}", get_all_tasks()

def get_all_tasks():
    """Return all tasks as a formatted string"""
    tasks = todo.view_tasks()
    if not tasks:
        return "No tasks available"
    
    result = ""
    for task in tasks:
        status = "Completed" if task['completed'] else "Pending"
        result += f"ID: {task['id']} | Title: {task['title']} | Status: {status}\n"
        result += f"Description: {task['description']}\n\n"
    
    return result

def update_task(task_id, title, description, completed):
    """Update an existing task"""
    try:
        task_id = int(task_id)
    except ValueError:
        return "Error: Task ID must be a number", None
    
    task = todo.get_task_details(task_id)
    if not task:
        return f"Error: No task found with ID {task_id}", None
    
    # Only pass parameters that have values
    kwargs = {}
    if title.strip():
        kwargs['title'] = title
    if description.strip():
        kwargs['description'] = description
    if completed is not None:
        kwargs['completed'] = completed
    
    success = todo.update_task(task_id, **kwargs)
    if success:
        return f"Task {task_id} updated successfully", get_all_tasks()
    else:
        return f"Error updating task {task_id}", None

def delete_task(task_id):
    """Delete a task by ID"""
    try:
        task_id = int(task_id)
    except ValueError:
        return "Error: Task ID must be a number", None
    
    success = todo.delete_task(task_id)
    if success:
        return f"Task {task_id} deleted successfully", get_all_tasks()
    else:
        return f"Error: No task found with ID {task_id}", None

def get_task_details(task_id):
    """Get details for a specific task"""
    try:
        task_id = int(task_id)
    except ValueError:
        return "Error: Task ID must be a number"
    
    task = todo.get_task_details(task_id)
    if task:
        status = "Completed" if task['completed'] else "Pending"
        result = f"ID: {task['id']}\nTitle: {task['title']}\nDescription: {task['description']}\nStatus: {status}"
        return result
    else:
        return f"No task found with ID {task_id}"

# Create sample tasks for demo purposes
todo.add_task("Complete Python project", "Finish the TODO application by Friday")
todo.add_task("Buy groceries", "Milk, eggs, bread, and vegetables")
todo.add_task("Exercise", "Go for a 30-minute run")

# Define the Gradio interface
with gr.Blocks(title="Todo Application") as app:
    gr.Markdown("# Todo Application")
    
    with gr.Tab("View All Tasks"):
        view_output = gr.Textbox(label="All Tasks", value=get_all_tasks(), lines=10)
        refresh_btn = gr.Button("Refresh Tasks")
        refresh_btn.click(fn=lambda: get_all_tasks(), outputs=view_output)
    
    with gr.Tab("Add Task"):
        with gr.Row():
            add_title = gr.Textbox(label="Title")
            add_description = gr.Textbox(label="Description", lines=3)
        add_btn = gr.Button("Add Task")
        add_output = gr.Textbox(label="Result")
        add_task_list = gr.Textbox(label="Updated Task List", lines=10)
        add_btn.click(fn=add_task, inputs=[add_title, add_description], outputs=[add_output, add_task_list])
    
    with gr.Tab("Update Task"):
        with gr.Row():
            update_id = gr.Textbox(label="Task ID")
            update_title = gr.Textbox(label="New Title (optional)")
        with gr.Row():
            update_description = gr.Textbox(label="New Description (optional)", lines=3)
            update_completed = gr.Checkbox(label="Mark as Completed")
        update_btn = gr.Button("Update Task")
        update_output = gr.Textbox(label="Result")
        update_task_list = gr.Textbox(label="Updated Task List", lines=10)
        update_btn.click(fn=update_task, 
                         inputs=[update_id, update_title, update_description, update_completed], 
                         outputs=[update_output, update_task_list])
    
    with gr.Tab("Delete Task"):
        delete_id = gr.Textbox(label="Task ID to Delete")
        delete_btn = gr.Button("Delete Task")
        delete_output = gr.Textbox(label="Result")
        delete_task_list = gr.Textbox(label="Updated Task List", lines=10)
        delete_btn.click(fn=delete_task, inputs=[delete_id], outputs=[delete_output, delete_task_list])
    
    with gr.Tab("Task Details"):
        details_id = gr.Textbox(label="Enter Task ID")
        details_btn = gr.Button("Get Details")
        details_output = gr.Textbox(label="Task Details", lines=5)
        details_btn.click(fn=get_task_details, inputs=[details_id], outputs=details_output)

if __name__ == "__main__":
    app.launch()