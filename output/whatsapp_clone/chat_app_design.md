# ChatEngine.py Design Document

## Main Class: ChatEngine

### Responsibilities:
The `ChatEngine` class is responsible for handling the core functionalities of the chat application, including user authentication, message sending and receiving, contact management, and chat history storage. This class will also manage real-time updates and ensure that messages are displayed correctly in the chat interface.

## Class Definition

```python
class ChatEngine:
    """
    ChatEngine class provides functionalities for managing chat communication,
    user authentication, and chat history storage in a real-time chat application.

    Attributes:
        user (str): The currently logged-in user's username.
        contacts (dict): A dictionary containing user contacts.
        chat_history (list): A list storing the chat messages.
    """
```

## Initializer Method

```python
def __init__(self):
    """
    Initializes the ChatEngine with an empty user, contacts list, 
    and chat history.
    """
```

## Methods

### User Authentication

```python
def login(self, username: str) -> bool:
    """
    Authenticates the user by setting the username.

    Args:
        username (str): The username of the user trying to log in.

    Returns:
        bool: True if login is successful, otherwise False.
    """
```

### Messaging Functionality

```python
def send_message(self, recipient: str, message: str) -> None:
    """
    Sends a message to the specified recipient and stores it in chat history.

    Args:
        recipient (str): The recipient's username.
        message (str): The message content to be sent.

    Raises:
        ValueError: If recipient is not a contact or message is empty.
    """
```

```python
def receive_message(self, sender: str, message: str) -> None:
    """
    Receives a message from the specified sender and stores it in chat history.

    Args:
        sender (str): The sender's username.
        message (str): The message content received.

    Raises:
        ValueError: If sender is not a contact or message is empty.
    """
```

### Chat History Management

```python
def get_chat_history(self) -> list:
    """
    Retrieves the entire chat history.

    Returns:
        list: A list of chat messages, including timestamps and sender info.
    """
```

### Contacts Management

```python
def add_contact(self, contact_username: str) -> None:
    """
    Adds a new contact to the user's contact list.

    Args:
        contact_username (str): The username of the contact to be added.

    Raises:
        ValueError: If the contact is already in the contact list.
    """
```

```python
def list_contacts(self) -> list:
    """
    Returns a list of all contacts for the logged-in user.

    Returns:
        list: A list of usernames of the user's contacts.
    """
```

## Data Structures

- **contacts**: A dictionary to store the username and any associated metadata (like recent chat).
- **chat_history**: A list of dictionaries, with each dictionary containing message details such as sender, recipient, timestamp, and message content.

Example of a chat message:
```python
{
    "sender": "user1",
    "recipient": "user2",
    "timestamp": "2023-10-01T12:00:00Z",
    "message": "Hello!"
}
```

## Helper Functions (optional)

These can be private methods if needed for internal processing, such as formatting message timestamps or validating usernames and messages.

```python
def _format_timestamp(self) -> str:
    """
    Returns the current timestamp formatted for message storage.
    
    Returns:
        str: Current timestamp in ISO 8601 format.
    """
```

## Edge Cases & Error Handling

- Handling empty usernames during login.
- Checking for duplicate contacts when adding to the contact list.
- Throwing errors for message operations if user is not logged in or if sender/recipient is not in contacts.
- Robust error handling for file operations if chat history is stored in a JSON file (like I/O errors).

## Extensibility Notes

- Future versions could extend built-in support for media messages (images, files).
- Could implement encryption for messages to enhance privacy.
- Easily replaceable chat storage backends by modifying the chat_history property.

This design should provide a comprehensive overview for the implementation of the ChatEngine class, ensuring clarity and functionality for the backend engineer.