from app.modules.users.service import create_user, list_users


def test_create_user_is_idempotent_by_email():
    first_user = create_user(email="Owner@Example.com", name="Owner")
    second_user = create_user(email="owner@example.com", name="Different Name")

    assert first_user["id"] == second_user["id"]
    assert first_user["email"] == "owner@example.com"
    assert len(list_users()) == 1
