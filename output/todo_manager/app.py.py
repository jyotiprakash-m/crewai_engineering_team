from Todo import Todo
import gradio as gr
import json
from typing import List

# Instantiate the Todo backend
todo = Todo()

def _format_choices():
    """Return dropdown choices as list of strings like '1: Buy milk'."""
    tasks = todo.list_tasks()
    return [f"{t['id']}: {t['title']} [{t['status']}]" for t in tasks]

def _tasks_text():
    """Return a plain text summary of all tasks."""
    tasks = todo.list_tasks()
    if not tasks:
        return "No tasks yet."
    lines = []
    for t in tasks:
        lines.append(f"ID: {t['id']}\nTitle: {t['title']}\nStatus: {t['status']}\nDescription: {t['description']}\nCreated: {t['created_at']}\nUpdated: {t['updated_at']}")
    return "\n\n".join(lines)

def add_task(title: str, description: str):
    """Add a new task and refresh the UI elements."""
    try:
        tid = todo.add_task(title, description)
        msg = f"Added task {tid}."
    except Exception as e:
        return gr.Textbox.update(value=_tasks_text()), gr.Dropdown.update(choices=_format_choices()), gr.Label.update(value=f"Error: {e}"), gr.Textbox.update(value=""), gr.Textbox.update(value="")
    return gr.Textbox.update(value=_tasks_text()), gr.Dropdown.update(choices=_format_choices()), gr.Label.update(value=msg), gr.Textbox.update(value=""), gr.Textbox.update(value="")

def select_task(choice: str):
    """Show details of the selected task and populate update fields."""
    if not choice:
        return gr.Markdown.update(value="No task selected."), gr.Textbox.update(value=""), gr.Textarea.update(value=""), gr.Textbox.update(value="")
    try:
        tid = int(choice.split(":")[0])
        task = todo.get_task(tid)
        md = f"**ID:** {task['id']}\n\n**Title:** {task['title']}\n\n**Description:** {task['description']}\n\n**Status:** {task['status']}\n\n**Created:** {task['created_at']}\n\n**Updated:** {task['updated_at']}"
        return gr.Markdown.update(value=md), gr.Textbox.update(value=task['title']), gr.Textarea.update(value=task['description']), gr.Textbox.update(value=task['status'])
    except Exception as e:
        return gr.Markdown.update(value=f"Error: {e}"), gr.Textbox.update(value=""), gr.Textarea.update(value=""), gr.Textbox.update(value="")

def update_task(choice: str, title: str, description: str, status: str):
    """Update the selected task with provided fields. Empty strings mean no change."""
    if not choice:
        return gr.Textbox.update(value=_tasks_text()), gr.Dropdown.update(choices=_format_choices()), gr.Label.update(value="No task selected."), gr.Markdown.update(value="No task selected.")
    try:
        tid = int(choice.split(":")[0])
        kwargs = {}
        if title is not None and title.strip() != "":
            kwargs['title'] = title
        if description is not None and description.strip() != "":
            kwargs['description'] = description
        if status is not None and status.strip() != "":
            kwargs['status'] = status
        if not kwargs:
            return gr.Textbox.update(value=_tasks_text()), gr.Dropdown.update(choices=_format_choices()), gr.Label.update(value="No changes provided."), gr.Markdown.update(value=_tasks_text())
        todo.update_task(tid, **kwargs)
        msg = f"Task {tid} updated."
        return gr.Textbox.update(value=_tasks_text()), gr.Dropdown.update(choices=_format_choices()), gr.Label.update(value=msg), gr.Markdown.update(value=f"Updated task {tid}.")
    except Exception as e:
        return gr.Textbox.update(value=_tasks_text()), gr.Dropdown.update(choices=_format_choices()), gr.Label.update(value=f"Error: {e}"), gr.Markdown.update(value=f"Error: {e}")

def delete_task(choice: str):
    """Delete the selected task."""
    if not choice:
        return gr.Textbox.update(value=_tasks_text()), gr.Dropdown.update(choices=_format_choices()), gr.Label.update(value="No task selected."), gr.Markdown.update(value=_tasks_text()), gr.Textbox.update(value=""), gr.Textarea.update(value=""), gr.Textbox.update(value="")
    try:
        tid = int(choice.split(":")[0])
        todo.delete_task(tid)
        msg = f"Deleted task {tid}."
        return gr.Textbox.update(value=_tasks_text()), gr.Dropdown.update(choices=_format_choices()), gr.Label.update(value=msg), gr.Markdown.update(value=_tasks_text()), gr.Textbox.update(value=""), gr.Textarea.update(value=""), gr.Textbox.update(value="")
    except Exception as e:
        return gr.Textbox.update(value=_tasks_text()), gr.Dropdown.update(choices=_format_choices()), gr.Label.update(value=f"Error: {e}"), gr.Markdown.update(value=f"Error: {e}"), gr.Textbox.update(value=""), gr.Textarea.update(value=""), gr.Textbox.update(value="")

# Build the Gradio UI
with gr.Blocks(title="Simple Todo Demo") as demo:
    gr.Markdown("## Todo App (Prototype)\nAdd, view, update, and delete tasks. Single-user demo.")
    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### Add Task")
            add_title = gr.Textbox(label="Title", placeholder="Task title")
            add_description = gr.Textbox(label="Description", placeholder="Task description", lines=3)
            add_btn = gr.Button("Add Task")
            add_status = gr.Label(value="")
        with gr.Column(scale=1):
            gr.Markdown("### All Tasks")
            tasks_box = gr.Textbox(value=_tasks_text(), lines=15, Interactive=False)
    gr.Markdown("---")
    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### Select Task")
            task_select = gr.Dropdown(choices=_format_choices(), label="Tasks", interactive=True)
            view_md = gr.Markdown("No task selected.")
        with gr.Column(scale=1):
            gr.Markdown("### Update Selected Task")
            update_title = gr.Textbox(label="Title")
            update_description = gr.Textbox(label="Description", lines=3)
            update_status = gr.Textbox(label="Status (pending, in_progress, completed, archived)")
            update_btn = gr.Button("Update Task")
            delete_btn = gr.Button("Delete Task")
            op_status = gr.Label(value="")

    # Wire up events
    add_btn.click(fn=add_task, inputs=[add_title, add_description], outputs=[tasks_box, task_select, add_status, add_title, add_description])
    task_select.change(fn=select_task, inputs=[task_select], outputs=[view_md, update_title, update_description, update_status])
    update_btn.click(fn=update_task, inputs=[task_select, update_title, update_description, update_status], outputs=[tasks_box, task_select, op_status, view_md])
    delete_btn.click(fn=delete_task, inputs=[task_select], outputs=[tasks_box, task_select, op_status, view_md, update_title, update_description, update_status])

if __name__ == "__main__":
    demo.launch()