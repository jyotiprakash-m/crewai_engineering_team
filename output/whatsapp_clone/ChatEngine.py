from __future__ import annotations

import json
import threading
import time
from collections import defaultdict, deque
from datetime import datetime
from queue import Queue, Empty
from typing import Callable, Dict, List, Optional


class ChatEngine:
    """
    ChatEngine class provides functionalities for managing chat communication,
    user authentication, and chat history storage in a real-time chat application.

    Attributes:
        user (Optional[str]): The currently logged-in user's username.
        contacts (Dict[str, Dict]): A dictionary of contacts to metadata.
        chat_history (List[Dict]): A chronological list of message dictionaries.
    """

    DEFAULT_HISTORY_FILE = "chat_history.json"

    def __init__(self, persist: bool = True, history_file: Optional[str] = None):
        """
        Initializes the ChatEngine with an empty user, contact list, and chat history.

        Args:
            persist (bool): Whether to persist chat history to a JSON file.
            history_file (Optional[str]): Path to the JSON file for persistence.
        """
        self.user: Optional[str] = None
        # contacts is a mapping username -> metadata (e.g., last_seen, recent_message)
        self.contacts: Dict[str, Dict] = {}
        # chat_history is a list of messages
        self.chat_history: List[Dict] = []

        # Incoming message queue simulating real-time inbound messages
        self._incoming_queue: Queue = Queue()
        # Listeners will be called when a new message is processed
        self._listeners: List[Callable[[Dict], None]] = []

        # Persistence
        self.persist = persist
        self.history_file = history_file or self.DEFAULT_HISTORY_FILE

        # Internal thread control
        self._stop_event = threading.Event()
        self._poll_interval = 0.3  # seconds
        self._poll_thread = threading.Thread(target=self._poll_incoming_loop, daemon=True)
        self._poll_thread.start()

        # For quick contact->messages lookup (indexing by tuple of participants)
        self._index: Dict[str, deque] = defaultdict(deque)

        # Lock for thread-safe operations
        self._lock = threading.RLock()

        # Try to load existing history if persisting
        if self.persist:
            try:
                self.load_history()
            except Exception:
                # If loading fails, continue with empty state
                pass

    # ----------------------- Authentication -----------------------
    def login(self, username: str) -> bool:
        """
        Authenticates the user by setting the username.

        Args:
            username (str): The username of the user trying to log in.

        Returns:
            bool: True if login is successful, otherwise False.
        """
        username = (username or "").strip()
        if not username:
            raise ValueError("Username cannot be empty")

        with self._lock:
            self.user = username
            # ensure the user's own contact entry exists
            if username not in self.contacts:
                self.contacts[username] = {"added_at": self._format_timestamp(), "me": True}
        return True

    def logout(self) -> None:
        """
        Logs out the current user.
        """
        with self._lock:
            self.user = None

    # ----------------------- Contacts -----------------------
    def add_contact(self, contact_username: str) -> None:
        """
        Adds a new contact to the user's contact list.

        Args:
            contact_username (str): The username of the contact to be added.

        Raises:
            ValueError: If the contact is already in the contact list or invalid.
        """
        contact_username = (contact_username or "").strip()
        if not contact_username:
            raise ValueError("Contact username cannot be empty")

        with self._lock:
            if contact_username in self.contacts:
                raise ValueError(f"Contact '{contact_username}' already exists")
            self.contacts[contact_username] = {"added_at": self._format_timestamp(), "me": False}

    def list_contacts(self) -> List[str]:
        """
        Returns a list of all contacts for the logged-in user.

        Returns:
            list: A list of usernames of the user's contacts.
        """
        with self._lock:
            # Exclude the user themselves from the contact listing if present
            return [c for c in self.contacts.keys() if c != self.user]

    # ----------------------- Messaging -----------------------
    def send_message(self, recipient: str, message: str) -> Dict:
        """
        Sends a message to the specified recipient and stores it in chat history.

        Args:
            recipient (str): The recipient's username.
            message (str): The message content to be sent.

        Returns:
            dict: The message dictionary that was stored.

        Raises:
            ValueError: If recipient is not a contact or message is empty or user not logged in.
        """
        if not self.user:
            raise ValueError("User must be logged in to send messages")

        recipient = (recipient or "").strip()
        message = (message or "").strip()

        if not recipient:
            raise ValueError("Recipient cannot be empty")
        if not message:
            raise ValueError("Message cannot be empty")

        with self._lock:
            if recipient not in self.contacts:
                raise ValueError(f"Recipient '{recipient}' is not in contacts")

            msg = {
                "sender": self.user,
                "recipient": recipient,
                "timestamp": self._format_timestamp(),
                "message": message,
                "direction": "outbound",
            }
            self._append_message(msg)

        # Simulate network by optionally enqueueing a delivery event to the recipient
        # (In a real system, this would be sent to a server which then delivers.)
        # For local simulation, do nothing further. The UI might show the sent message
        # immediately and may rely on receive_message to simulate replies.
        return msg

    def receive_message(self, sender: str, message: str) -> None:
        """
        Receives a message from the specified sender and stores it in chat history.
        This simulates an incoming message by placing it in the incoming queue.

        Args:
            sender (str): The sender's username.
            message (str): The message content received.

        Raises:
            ValueError: If sender is not a contact or message is empty or user not logged in.
        """
        if not self.user:
            raise ValueError("User must be logged in to receive messages")

        sender = (sender or "").strip()
        message = (message or "").strip()

        if not sender:
            raise ValueError("Sender cannot be empty")
        if not message:
            raise ValueError("Message cannot be empty")

        with self._lock:
            if sender not in self.contacts:
                # For received messages, automatically add the sender as a contact
                self.contacts[sender] = {"added_at": self._format_timestamp(), "me": False}

        # Place into incoming queue to be processed by the poll loop
        self._incoming_queue.put({
            "sender": sender,
            "recipient": self.user,
            "timestamp": self._format_timestamp(),
            "message": message,
            "direction": "inbound",
        })

    # ----------------------- Chat History -----------------------
    def get_chat_history(self, contact: Optional[str] = None, limit: Optional[int] = None) -> List[Dict]:
        """
        Retrieves chat history. If contact is provided, filters messages between
        the logged-in user and that contact.

        Args:
            contact (Optional[str]): Username to filter chat with. If None, returns full history.
            limit (Optional[int]): Optional maximum number of messages to return (most recent first).

        Returns:
            list: A list of chat messages, including timestamps and sender info.
        """
        if not self.user:
            raise ValueError("User must be logged in to fetch chat history")

        with self._lock:
            if contact:
                contact = contact.strip()
                if contact not in self.contacts:
                    raise ValueError(f"Contact '{contact}' not found")
                filtered = [m for m in self.chat_history if (m["sender"] == contact and m["recipient"] == self.user) or (m["sender"] == self.user and m["recipient"] == contact)]
            else:
                filtered = list(self.chat_history)

            if limit is not None and limit > 0:
                return filtered[-limit:]
            return filtered

    # ----------------------- Persistence -----------------------
    def save_history(self, path: Optional[str] = None) -> None:
        """
        Saves chat history and contacts to a JSON file.

        Args:
            path (Optional[str]): File path to save to. Uses configured history_file if None.
        """
        if not self.persist:
            return
        path = path or self.history_file
        data = {
            "contacts": self.contacts,
            "chat_history": self.chat_history,
            "saved_at": self._format_timestamp(),
        }
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except OSError as e:
            raise IOError(f"Failed to save history to {path}: {e}")

    def load_history(self, path: Optional[str] = None) -> None:
        """
        Loads chat history and contacts from a JSON file.

        Args:
            path (Optional[str]): File path to load from. Uses configured history_file if None.
        """
        path = path or self.history_file
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except FileNotFoundError:
            return
        except OSError as e:
            raise IOError(f"Failed to load history from {path}: {e}")

        with self._lock:
            self.contacts = data.get("contacts", {})
            self.chat_history = data.get("chat_history", [])

    # ----------------------- Listeners & Poll Loop -----------------------
    def register_listener(self, callback: Callable[[Dict], None]) -> None:
        """
        Register a callback to be invoked whenever a new message is processed
        from the incoming queue. The callback receives a single message dict.

        Args:
            callback (Callable[[Dict], None]): Function to be called on new messages.
        """
        with self._lock:
            if callback not in self._listeners:
                self._listeners.append(callback)

    def unregister_listener(self, callback: Callable[[Dict], None]) -> None:
        """
        Unregister a previously registered listener.
        """
        with self._lock:
            try:
                self._listeners.remove(callback)
            except ValueError:
                pass

    def _poll_incoming_loop(self) -> None:
        """
        Background loop that periodically polls the incoming queue and processes
        messages into chat_history while notifying listeners. This simulates
        receiving messages in real time.
        """
        while not self._stop_event.is_set():
            try:
                # Drain the queue
                while True:
                    msg = self._incoming_queue.get_nowait()
                    with self._lock:
                        self._append_message(msg)
                        # Notify listeners (don't block the loop)
                        for cb in list(self._listeners):
                            try:
                                cb(msg)
                            except Exception:
                                # Listener failures shouldn't break the poll loop
                                pass
            except Empty:
                # No messages right now
                pass

            # Sleep briefly before next poll
            time.sleep(self._poll_interval)

    def stop(self) -> None:
        """
        Stops the background poll thread gracefully and saves history if enabled.
        """
        self._stop_event.set()
        if self._poll_thread.is_alive():
            self._poll_thread.join(timeout=1.0)
        if self.persist:
            try:
                self.save_history()
            except Exception:
                pass

    # ----------------------- Internal Utilities -----------------------
    def _format_timestamp(self) -> str:
        """
        Returns the current timestamp formatted for message storage in ISO 8601.

        Returns:
            str: Current timestamp in ISO 8601 format with Z suffix.
        """
        return datetime.utcnow().isoformat(timespec="seconds") + "Z"

    def _append_message(self, msg: Dict) -> None:
        """
        Append a message to chat_history and maintain indices.
        """
        # Basic validation
        if not all(k in msg for k in ("sender", "recipient", "timestamp", "message")):
            raise ValueError("Message dict missing required fields")

        # Append
        self.chat_history.append(msg)

        # Update index for both participants (sorted key to unify)
        participants = tuple(sorted([msg["sender"], msg["recipient"]]))
        key = "::".join(participants)
        self._index[key].append(msg)

    # ----------------------- Simulation Helpers -----------------------
    def simulate_incoming_reply(self, sender: str, message: str, delay: float = 1.0) -> threading.Timer:
        """
        Convenience helper that schedules an incoming message after a delay to
        simulate a live reply from a contact.

        Args:
            sender (str): The sender contact's username.
            message (str): Message content to receive.
            delay (float): Seconds to wait before injecting the message.

        Returns:
            threading.Timer: The Timer object so caller can cancel if needed.
        """
        timer = threading.Timer(delay, lambda: self.receive_message(sender, message))
        timer.daemon = True
        timer.start()
        return timer

    # ----------------------- Cleanup -----------------------
    def __del__(self):
        try:
            self.stop()
        except Exception:
            pass


# ----------------------- Module Demo / Simple Tests -----------------------
if __name__ == "__main__":
    # Simple demonstration of ChatEngine usage.
    engine = ChatEngine(persist=False)

    print("Logging in as 'alice'")
    engine.login("alice")

    print("Adding contacts: bob, charlie")
    engine.add_contact("bob")
    engine.add_contact("charlie")

    print("Contacts:", engine.list_contacts())

    # Register a listener that prints incoming messages
    def on_new_message(msg: Dict):
        print(f"[Listener] New message: {msg['timestamp']} {msg['sender']} -> {msg['recipient']}: {msg['message']}")

    engine.register_listener(on_new_message)

    # Send a message from alice to bob
    print("Sending message to bob...")
    sent = engine.send_message("bob", "Hello Bob! Are you there?")
    print("Sent:", sent)

    # Simulate bob replying after 0.8s
    engine.simulate_incoming_reply("bob", "Hey Alice! I am here.", delay=0.8)

    # Simulate charlie sending an unsolicited message
    engine.simulate_incoming_reply("charlie", "Yo Alice, long time no see!", delay=1.4)

    # Wait a bit to let simulated messages deliver
    time.sleep(2.0)

    # Fetch full history
    history = engine.get_chat_history()
    print("\nFull chat history:")
    for m in history:
        direction = m.get('direction', 'inbound' if m['recipient'] == engine.user else 'outbound')
        side = '<-' if direction == 'inbound' else '->'
        print(f"  {m['timestamp']} {m['sender']} {side} {m['recipient']}: {m['message']}")

    # Fetch chat with bob
    print('\nChat with bob:')
    for m in engine.get_chat_history(contact='bob'):
        print(f"  {m['timestamp']} {m['sender']}: {m['message']}")

    print('\nStopping engine...')
    engine.stop()
    print('Demo complete.')