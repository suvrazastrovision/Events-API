from datetime import datetime

from models import Event, RSVP, User, db


def test_user_password_hashing_behaves_correctly():
    user = User(username="alice")
    user.set_password("secret-password")

    assert user.password_hash != "secret-password"
    assert user.check_password("secret-password") is True
    assert user.check_password("wrong-password") is False


def test_event_to_dict_includes_attending_users(app):
    with app.app_context():
        user = User(username="bob", password_hash="hash")
        event = Event(title="Workshop", date=datetime(2026, 9, 1, 18, 0))
        db.session.add_all([user, event])
        db.session.flush()
        db.session.add(RSVP(event_id=event.id, user_id=user.id, attending=True))
        db.session.commit()
        result = event.to_dict()
        assert result["title"] == "Workshop"
        assert result["rsvp_count"] == 1
        assert result["attendees"] == [user.id]


def test_deleting_event_deletes_its_rsvps(app):
    with app.app_context():
        event = Event(title="Meetup", date=datetime(2026, 9, 2, 18, 0))
        db.session.add(event)
        db.session.flush()
        db.session.add(RSVP(event_id=event.id, attending=True))
        db.session.commit()
        db.session.delete(event)
        db.session.commit()
        assert RSVP.query.count() == 0

