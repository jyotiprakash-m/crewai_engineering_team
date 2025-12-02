from __future__ import annotations

import atexit
import html
import threading
from datetime import datetime
from typing import List, Optional

import gradio as gr

from chat_app import ChatEngine

# Instantiate a single engine for the demo (persist to default file)
engine = ChatEngine(persist=True)


def _safe_iso_to_display(iso_ts: str) -> str:
    # Convert ISO timestamp (UTC Z) to a readable local-ish time string (HH:MM)
    try:
        # strip trailing Z to parse
        if iso_ts.endswith("Z"):
            iso_ts = iso_ts[:-1]
        dt = datetime.fromisoformat(iso_ts)
        return dt.strftime("%Y-%m-%d %H:%M")
    except Exception:
        return iso_ts


def render_chat_html(contact: Optional[str]) -> str:
    """
    Build an HTML string that visually resembles chat bubbles between the logged-in
    user and the selected contact. Left-aligned bubbles = inbound, right-aligned =
    outbound. If no contact selected, return a placeholder.
    """
    if not engine.user:
        return "<div style='color: #666'>Please log in to see chats.</div>"

    if not contact:
        return "<div style='color: #666'>Select a contact from the left to open a chat.</div>"

    try:
        messages = engine.get_chat_history(contact=contact)
    except Exception as e:
        return f"<div style='color: red'>Error loading chat: {html.escape(str(e))}</div>"

    # Basic CSS for chat bubbles
    css = """
    <style>
      .chat-window { font-family: Arial, sans-serif; max-height: 60vh; overflow-y: auto; padding: 10px; }
      .bubble { display: block; clear: both; padding: 8px 12px; margin: 6px 0; max-width: 72%; border-radius: 10px; }
      .left { background: #f1f0f0; float: left; text-align: left; }
      .right { background: #dcf8c6; float: right; text-align: right; }
      .ts { display:block; font-size: 10px; color: #666; margin-top: 4px; }
      .meta { font-size: 11px; color: #333; margin-bottom: 6px; }
      .clearfix::after { content: ""; clear: both; display: table; }
    </style>
    """

    html_parts = [css, "<div class='chat-window'>"]

    for m in messages:
        sender = m.get("sender", "")
        msg = html.escape(m.get("message", ""))
        ts = _safe_iso_to_display(m.get("timestamp", ""))
        direction = m.get("direction", None)
        # Determine side: if sender is user -> outbound/right, else inbound/left
        is_outbound = sender == engine.user
        side_class = "right" if is_outbound else "left"
        # bubble HTML
        part = (
            f"<div class='clearfix'>"
            f"<div class='bubble {side_class}'>"
            f"{msg}"
            f"<span class='ts'>{ts}</span>"
            f"</div>"
            f"</div>"
        )
        html_parts.append(part)

    html_parts.append("</div>")
    return "\n".join(html_parts)


def render_recent_html() -> str:
    """
    Build a sidebar HTML listing recent chats (last message per contact).
    """
    if not engine.user:
        return "<div style='color: #666'>Login to see recent chats.</div>"

    # Gather last message per contact
    last_per_contact = {}
    for m in engine.chat_history:
        # ignore messages that don't involve the user
        if engine.user not in (m.get("sender"), m.get("recipient")):
            continue
        # determine the other participant
        other = m["sender"] if m["sender"] != engine.user else m["recipient"]
        prev = last_per_contact.get(other)
        # use timestamp lexicographic (ISO) for ordering
        if not prev or m.get("timestamp", "") > prev.get("timestamp", ""):
            last_per_contact[other] = m

    # Ensure that all contacts are represented even without messages
    for c in engine.list_contacts():
        if c not in last_per_contact:
            last_per_contact[c] = None

    # Build HTML list sorted by most recent
    items = sorted(list(last_per_contact.items()), key=lambda kv: kv[1]["timestamp"] if kv[1] else "", reverse=True)
    parts = ["<div style='font-family: Arial, sans-serif; padding:6px;'>"]
    parts.append("<h4 style='margin:6px 0;'>Recent</h4>")
    parts.append("<ul style='list-style:none; padding-left:0;'>")
    for contact, msg in items:
        display_msg = ""
        ts = ""
        if msg:
            snippet = html.escape(msg["message"][:40])
            ts = _safe_iso_to_display(msg.get("timestamp", ""))
            sender_label = "You: " if msg.get("sender") == engine.user else ""
            display_msg = f"{sender_label}{snippet}"
        else:
            display_msg = "<i>No messages yet</i>"
        parts.append(
            f"<li style='padding:6px 0; border-bottom: 1px solid #eee;'>"
            f"<div style='font-weight:bold'>{html.escape(contact)}</div>"
            f"<div style='font-size:12px; color:#555'>{display_msg} <span style='float:right; font-size:11px; color:#999'>{ts}</span></div>"
            f"</li>"
        )
    parts.append("</ul></div>")
    return "\n".join(parts)


def get_contact_choices() -> List[str]:
    """
    Helper to read engine contacts and return a list for the dropdown.
    """
    if not engine.user:
        return []
    try:
        return engine.list_contacts()
    except Exception:
        return []


# ----------------- Gradio event handlers -----------------


def do_login(username: str):
    """
    Login handler: authenticates user and seeds a couple of demo contacts.
    Returns: status message, updated contacts list, recent-chats HTML, chat HTML.
    """
    username = (username or "").strip()
    if not username:
        return "Username cannot be empty", gr.Dropdown.update(choices=[], value=None), render_recent_html(), render_chat_html(None)

    try:
        engine.login(username)
    except Exception as e:
        return f"Login failed: {e}", gr.Dropdown.update(choices=[], value=None), render_recent_html(), render_chat_html(None)

    # Seed demo contacts if they don't exist (ignore errors)
    for demo in ("bob", "charlie"):
        try:
            if demo != username and demo not in engine.contacts:
                engine.add_contact(demo)
        except Exception:
            pass

    contacts = get_contact_choices()
    selected = contacts[0] if contacts else None
    status = f"Logged in as {html.escape(username)}"
    recent_html = render_recent_html()
    chat_html = render_chat_html(selected) if selected else render_chat_html(None)
    return status, gr.Dropdown.update(choices=contacts, value=selected), recent_html, chat_html


def add_contact_ui(contact_username: str, contacts_dropdown_value: Optional[str]):
    """
    Add a contact and update contact dropdown and recent list.
    """
    contact_username = (contact_username or "").strip()
    if not engine.user:
        return "Not logged in", gr.Dropdown.update(), render_recent_html()

    if not contact_username:
        return "Contact username cannot be empty", gr.Dropdown.update(), render_recent_html()

    try:
        engine.add_contact(contact_username)
    except Exception as e:
        return f"Failed to add contact: {e}", gr.Dropdown.update(choices=get_contact_choices(), value=contacts_dropdown_value), render_recent_html()

    contacts = get_contact_choices()
    return f"Added {html.escape(contact_username)}", gr.Dropdown.update(choices=contacts, value=contact_username), render_recent_html()


def send_message_ui(contact: Optional[str], message: str):
    """
    Send message to selected contact, schedule a simulated reply, and return updated views.
    """
    message = (message or "").strip()
    if not engine.user:
        return "Not logged in", render_chat_html(contact), render_recent_html(), ""

    if not contact:
        return "Please select a contact", render_chat_html(contact), render_recent_html(), ""

    if not message:
        return "Cannot send empty message", render_chat_html(contact), render_recent_html(), ""

    try:
        sent = engine.send_message(contact, message)
    except Exception as e:
        return f"Send failed: {e}", render_chat_html(contact), render_recent_html(), ""

    # simulate an incoming reply after 0.8-1.6s (simple echo)
    try:
        engine.simulate_incoming_reply(contact, f"Auto-reply to: {message}", delay=1.0)
    except Exception:
        pass

    chat_html = render_chat_html(contact)
    recent_html = render_recent_html()
    # clear message box (return empty string)
    return "Message sent", chat_html, recent_html, ""


def poll_update(contact: Optional[str]):
    """
    Periodic polling callback invoked by the hidden polling button on the client.
    Refreshes chat view and recent chats. Returns updated HTML for chat and recent area
    and updates the contact dropdown choices if changed.
    """
    if not engine.user:
        return render_chat_html(None), render_recent_html(), gr.Dropdown.update(choices=[], value=None)

    # refresh contacts and views
    contacts = get_contact_choices()
    # keep selected contact if present; else pick the first
    selected = contact if (contact and contact in contacts) else (contacts[0] if contacts else None)
    chat_html = render_chat_html(selected)
    recent_html = render_recent_html()
    return chat_html, recent_html, gr.Dropdown.update(choices=contacts, value=selected)


def on_contact_change(contact: Optional[str]):
    """
    When the user selects a different contact, refresh the chat window for that contact.
    """
    return render_chat_html(contact), render_recent_html()


# Ensure engine is stopped cleanly on exit
def _shutdown():
    try:
        engine.stop()
    except Exception:
        pass


atexit.register(_shutdown)

# ----------------- Build Gradio UI -----------------

with gr.Blocks(title="WhatsApp-like Chat Demo") as demo:
    gr.Markdown("<h2>WhatsApp-like Chat Demo (Prototype)</h2>")
    with gr.Row():
        with gr.Column(scale=1):
            # Login area
            gr.Markdown("### Login")
            username_in = gr.Textbox(label="Username", placeholder="Enter username (e.g. alice)")
            login_btn = gr.Button("Login")

            status = gr.HTML("<div style='color:#666'>Not logged in</div>")

            gr.Markdown("### Contacts")
            contacts_dropdown = gr.Dropdown(label="Contacts", choices=[], value=None)
            add_contact_in = gr.Textbox(label="Add contact", placeholder="username")
            add_contact_btn = gr.Button("Add")

            gr.Markdown("### Recent Chats")
            recent_html = gr.HTML(render_recent_html())

            # A small note and a hidden poll button is included below (the JS will click it periodically)
            poll_button = gr.Button("poll", visible=False, elem_id="poll-btn")
            # Add a small HTML snippet that will click the hidden poll button every second to simulate periodic polling.
            poll_script = gr.HTML(
                """
                <script>
                // Poll the server by clicking the hidden button every 1s.
                // This triggers the Gradio server function bound to the hidden button.
                setInterval(function(){
                  try {
                    const btn = document.getElementById('poll-btn');
                    if(btn) { btn.click(); }
                  } catch(e) {}
                }, 1000);
                </script>
                """
            )

        with gr.Column(scale=3):
            gr.Markdown("### Chat")
            chat_html = gr.HTML(render_chat_html(None))
            with gr.Row():
                message_input = gr.Textbox(label="", placeholder="Type a message and press Send...", lines=2)
                send_btn = gr.Button("Send")

    # Wire up events
    login_btn.click(fn=do_login, inputs=[username_in], outputs=[status, contacts_dropdown, recent_html, chat_html])
    add_contact_btn.click(fn=add_contact_ui, inputs=[add_contact_in, contacts_dropdown], outputs=[status, contacts_dropdown, recent_html])
    contacts_dropdown.change(fn=on_contact_change, inputs=[contacts_dropdown], outputs=[chat_html, recent_html])
    send_btn.click(fn=send_message_ui, inputs=[contacts_dropdown, message_input], outputs=[status, chat_html, recent_html, message_input])

    # Hidden poll button will call poll_update every second (client-side JS clicks it)
    poll_button.click(fn=poll_update, inputs=[contacts_dropdown], outputs=[chat_html, recent_html, contacts_dropdown])

# Expose the app as 'app' for frameworks that expect it
app = demo

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", share=False)