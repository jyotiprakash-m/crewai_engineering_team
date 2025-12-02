import os
import tempfile
import time
import threading
import json
import pytest

from chat_app import ChatEngine


def make_engine(persist=False, history_file=None):
    eng = ChatEngine(persist=persist, history_file=history_file)
    # speed up poll loop for tests
    eng._poll_interval = 0.01
    return eng


def test_login_logout_and_contacts():
    eng = make_engine(persist=False)
    try:
        # login sets user and adds a self contact
        assert eng.login('alice') is True
        assert eng.user == 'alice'
        assert 'alice' in eng.contacts

        # initially no other contacts
        assert eng.list_contacts() == []

        # add a contact
        eng.add_contact('bob')
        contacts = eng.list_contacts()
        assert 'bob' in contacts and 'alice' not in contacts

        # adding existing contact should raise
        with pytest.raises(ValueError):
            eng.add_contact('bob')

        # logout
        eng.logout()
        assert eng.user is None

        # operations that require login should raise
        with pytest.raises(ValueError):
            eng.send_message('bob', 'hi')
    finally:
        eng.stop()


def test_send_and_receive_messages_flow():
    eng = make_engine(persist=False)
    try:
        eng.login('alice')
        eng.add_contact('bob')

        # send a message to bob
        msg = eng.send_message('bob', 'Hello Bob')
        assert msg['sender'] == 'alice'
        assert msg['recipient'] == 'bob'
        assert msg['direction'] == 'outbound'
        assert any(m is msg or (m['sender'] == 'alice' and m['recipient'] == 'bob') for m in eng.chat_history)

        # receive a message from bob (this places it into the incoming queue)
        eng.receive_message('bob', 'Hi Alice')

        # wait for poll loop to process
        time.sleep(0.05)

        # chat_history should now include inbound message
        inbound = [m for m in eng.chat_history if m['direction'] == 'inbound']
        assert inbound, 'Expected at least one inbound message'
        assert inbound[-1]['sender'] == 'bob'

    finally:
        eng.stop()


def test_receive_auto_add_contact_and_get_history_filter_limit():
    eng = make_engine(persist=False)
    try:
        eng.login('alice')
        # alice has no 'eve' contact
        assert 'eve' not in eng.contacts

        # receive message should auto-add 'eve'
        eng.receive_message('eve', 'Hello from Eve')
        time.sleep(0.05)
        assert 'eve' in eng.contacts

        # send/receive multiple messages to test filtering and limit
        eng.add_contact('bob')
        eng.send_message('bob', 'm1')
        eng.receive_message('bob', 'm2')
        eng.send_message('bob', 'm3')
        time.sleep(0.05)

        history_all = eng.get_chat_history()
        history_bob = eng.get_chat_history(contact='bob')
        assert len(history_bob) <= len(history_all)

        # limit parameter: ask for last 2 messages
        last_two = eng.get_chat_history(contact='bob', limit=2)
        assert len(last_two) == 2

        # requesting history for unknown contact raises
        with pytest.raises(ValueError):
            eng.get_chat_history(contact='nonexistent')

    finally:
        eng.stop()


def test_persistence_save_and_load(tmp_path):
    # create a temporary history file
    hf = tmp_path / "hist.json"
    path = str(hf)

    # create engine, add state and save
    eng = make_engine(persist=True, history_file=path)
    try:
        eng.login('alice')
        eng.add_contact('bob')
        eng.send_message('bob', 'persisted message')
        # ensure save
        eng.save_history()
    finally:
        eng.stop()

    # create a new engine that should load the saved history
    eng2 = make_engine(persist=True, history_file=path)
    try:
        # stop briefly to allow load in __init__ (load is synchronous), check state
        assert 'bob' in eng2.contacts
        assert any('persisted message' in m.get('message','') for m in eng2.chat_history)
    finally:
        eng2.stop()


def test_listeners_and_exception_isolated():
    eng = make_engine(persist=False)
    try:
        eng.login('alice')
        eng.add_contact('bob')

        calls = []

        def good_listener(msg):
            calls.append(('good', msg['message']))

        def bad_listener(msg):
            raise RuntimeError('listener failure')

        eng.register_listener(good_listener)
        eng.register_listener(bad_listener)

        eng.receive_message('bob', 'hey')
        time.sleep(0.05)

        # ensure good listener was called despite bad listener raising
        assert any(c[0] == 'good' for c in calls)

        # unregister and ensure no further calls
        eng.unregister_listener(good_listener)
        calls.clear()
        eng.receive_message('bob', 'hey2')
        time.sleep(0.05)
        assert calls == []

    finally:
        eng.stop()


def test_append_message_validation_raises():
    eng = make_engine(persist=False)
    try:
        eng.login('alice')
        # missing keys must raise ValueError
        with pytest.raises(ValueError):
            eng._append_message({'sender': 'alice'})
    finally:
        eng.stop()


def test_invalid_inputs_raise_on_login_add_and_messages():
    eng = make_engine(persist=False)
    try:
        # empty username
        with pytest.raises(ValueError):
            eng.login('')

        eng.login('alice')

        with pytest.raises(ValueError):
            eng.add_contact('')

        # sending to unknown contact
        with pytest.raises(ValueError):
            eng.send_message('unknown', 'hi')

        # empty recipient or message
        with pytest.raises(ValueError):
            eng.send_message('', 'hi')
        with pytest.raises(ValueError):
            eng.send_message('bob', '')

        # receiving while logged in: empty sender/message
        with pytest.raises(ValueError):
            eng.receive_message('', 'hi')
        with pytest.raises(ValueError):
            eng.receive_message('bob', '')

    finally:
        eng.stop()


if __name__ == '__main__':
    # allow running tests without pytest runner for quick checks
    import sys
    sys.exit(pytest.main([__file__]))