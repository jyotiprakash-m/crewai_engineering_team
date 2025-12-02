import pytest
from datetime import datetime
from Todo import Todo


def _iso_to_dt(s: str) -> datetime:
    # strip trailing Z used in the module's ISO format
    return datetime.fromisoformat(s.rstrip('Z'))


def test_add_and_get_task_and_copy_behavior():
    todo = Todo()
    tid = todo.add_task("Title", "Description")
    assert isinstance(tid, int)

    task = todo.get_task(tid)
    assert task["id"] == tid
    assert task["title"] == "Title"
    assert task["description"] == "Description"
    assert task["status"] == Todo.DEFAULT_STATUS

    # timestamps present and valid ISO-ish format ending with Z
    assert task["created_at"].endswith("Z")
    assert task["updated_at"].endswith("Z")
    # get_task returns a deep copy
    task_copy = todo.get_task(tid)
    task_copy["title"] = "Hacked"
    assert todo.get_task(tid)["title"] == "Title"


def test_add_task_invalid_inputs():
    todo = Todo()
    with pytest.raises(ValueError):
        todo.add_task("", "desc")
    with pytest.raises(ValueError):
        todo.add_task("   ", "desc")
    with pytest.raises(ValueError):
        todo.add_task("title", "")
    with pytest.raises(ValueError):
        todo.add_task("title", "   ")


def test_update_task_fields_and_status_normalization_and_timestamps():
    todo = Todo()
    tid = todo.add_task("Start", "Do work")
    before = todo.get_task(tid)["updated_at"]

    # updating title and description updates updated_at but not created_at
    created_before = todo.get_task(tid)["created_at"]
    todo.update_task(tid, title="New Title", description="New Desc")
    after = todo.get_task(tid)
    assert after["title"] == "New Title"
    assert after["description"] == "New Desc"
    assert after["created_at"] == created_before
    assert after["updated_at"] != before

    # status normalization for 'in progress' -> 'in_progress'
    todo.update_task(tid, status="in progress")
    assert todo.get_task(tid)["status"] == "in_progress"

    # case-insensitive status should work
    todo.update_task(tid, status="COMPLETED")
    assert todo.get_task(tid)["status"] == "completed"


def test_update_invalid_inputs_and_missing_task():
    todo = Todo()
    tid = todo.add_task("A", "B")
    with pytest.raises(ValueError):
        todo.update_task(tid, title="")
    with pytest.raises(ValueError):
        todo.update_task(tid, description="   ")
    with pytest.raises(ValueError):
        todo.update_task(tid, status="not_a_status")
    with pytest.raises(KeyError):
        todo.update_task(9999, title="x")


def test_update_no_changes_does_not_modify_updated_at():
    todo = Todo()
    tid = todo.add_task("X", "Y")
    before = todo.get_task(tid)["updated_at"]
    todo.update_task(tid)  # no changes provided
    after = todo.get_task(tid)["updated_at"]
    assert before == after


def test_delete_task_and_len_and_repr_and_exceptions():
    todo = Todo()
    ids = [todo.add_task(f"t{i}", "d") for i in range(3)]
    assert len(todo) == 3
    assert repr(todo) == "<Todo tasks=3>"

    # delete middle
    todo.delete_task(ids[1])
    assert len(todo) == 2
    with pytest.raises(KeyError):
        todo.get_task(ids[1])
    with pytest.raises(KeyError):
        todo.delete_task(9999)


def test_list_tasks_ordering():
    todo = Todo()
    ids = [todo.add_task(f"title{i}", "d") for i in range(5)]
    listed = todo.list_tasks()
    assert [t["id"] for t in listed] == ids


def test_get_task_missing_raises():
    todo = Todo()
    with pytest.raises(KeyError):
        todo.get_task(123456)