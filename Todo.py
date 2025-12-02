
from __future__ import annotations
from typing import Dict, Any, List, Optional
from datetime import datetime
import copy


class Todo:
    """Manage a collection of todo tasks.

    Each task is stored as a dictionary with the following keys:
    - id (int)
    - title (str)
    - description (str)
    - status (str)
    - created_at (str, ISO 8601)
    - updated_at (str, ISO 8601)

    Example statuses: 'pending', 'in_progress', 'completed', 'archived'
    """

    DEFAULT_STATUS = "pending"
    ALLOWED_STATUSES = {"pending", "in_progress", "completed", "archived"}

    def __init__(self) -> None:
        """Initialize the Todo manager with an empty task collection."""
        self.tasks: Dict[int, Dict[str, Any]] = {}
        self._next_id: int = 1

    def _now_iso(self) -> str:
        return datetime.utcnow().isoformat() + "Z"

    def add_task(self, title: str, description: str) -> int:
        """Add a new task and return its unique ID.

        Raises ValueError if title or description is empty or only whitespace.
        """
        if not isinstance(title, str) or not title.strip():
            raise ValueError("Title must be a non-empty string.")
        if not isinstance(description, str) or not description.strip():
            raise ValueError("Description must be a non-empty string.")

        task_id = self._next_id
        now = self._now_iso()
        task = {
            "id": task_id,
            "title": title.strip(),
            "description": description.strip(),
            "status": self.DEFAULT_STATUS,
            "created_at": now,
            "updated_at": now,
        }
        self.tasks[task_id] = task
        self._next_id += 1
        return task_id

    def get_task(self, task_id: int) -> Dict[str, Any]:
        """Retrieve a copy of the task by ID.

        Raises KeyError if the task_id does not exist.
        """
        if task_id not in self.tasks:
            raise KeyError(f"Task with id {task_id} not found.")
        # Return a deep copy to prevent external mutation
        return copy.deepcopy(self.tasks[task_id])

    def update_task(
        self,
        task_id: int,
        title: Optional[str] = None,
        description: Optional[str] = None,
        status: Optional[str] = None,
    ) -> None:
        """Update title, description and/or status of a task.

        Raises KeyError if the task_id does not exist.
        Raises ValueError if status is invalid or provided title/description is empty.
        """
        if task_id not in self.tasks:
            raise KeyError(f"Task with id {task_id} not found.")

        task = self.tasks[task_id]
        updated = False

        if title is not None:
            if not isinstance(title, str) or not title.strip():
                raise ValueError("Title must be a non-empty string when provided.")
            task["title"] = title.strip()
            updated = True

        if description is not None:
            if not isinstance(description, str) or not description.strip():
                raise ValueError("Description must be a non-empty string when provided.")
            task["description"] = description.strip()
            updated = True

        if status is not None:
            if not isinstance(status, str) or not status.strip():
                raise ValueError("Status must be a non-empty string when provided.")
            normalized = status.strip().lower()
            # allow certain common variants
            if normalized == "in progress":
                normalized = "in_progress"
            if normalized not in self.ALLOWED_STATUSES:
                raise ValueError(
                    f"Invalid status '{status}'. Allowed: {', '.join(sorted(self.ALLOWED_STATUSES))}"
                )
            task["status"] = normalized
            updated = True

        if updated:
            task["updated_at"] = self._now_iso()

    def delete_task(self, task_id: int) -> None:
        """Delete a task by ID.

        Raises KeyError if the task_id does not exist.
        """
        if task_id not in self.tasks:
            raise KeyError(f"Task with id {task_id} not found.")
        del self.tasks[task_id]

    def list_tasks(self) -> List[Dict[str, Any]]:
        """Return a list of copies of all tasks, sorted by task id ascending."""
        return [copy.deepcopy(self.tasks[k]) for k in sorted(self.tasks.keys())]

    def __len__(self) -> int:
        return len(self.tasks)

    def __repr__(self) -> str:
        return f"<Todo tasks={len(self.tasks)}>"


# If this module is executed directly, demonstrate simple usage (not UI):
if __name__ == "__main__":
    # Simple demonstration; meant for quick manual testing only.
    todo = Todo()
    tid1 = todo.add_task("Buy milk", "Remember to buy milk on the way home")
    tid2 = todo.add_task("Read book", "Finish the current chapter")
    print("Added tasks:", todo.list_tasks())
    todo.update_task(tid1, status="in progress")
    print("After update:", todo.get_task(tid1))
    todo.delete_task(tid2)
    print("Remaining:", todo.list_tasks())
