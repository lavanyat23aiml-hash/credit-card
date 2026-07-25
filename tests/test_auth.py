import pytest
import bcrypt
import streamlit as st
from unittest.mock import patch
from dashboard.streamlit.auth import (
    verify_password,
    authenticate_user,
    initialize_auth_state,
    is_authenticated,
    has_role,
    get_current_role
)

def test_verify_password():
    password = "secure_password"
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    assert verify_password(password, hashed) is True
    assert verify_password("wrong_password", hashed) is False

@patch("dashboard.streamlit.auth.st.secrets")
def test_authenticate_user_success(mock_secrets):
    password = "admin_password"
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    mock_secrets.__getitem__.side_effect = lambda k: {
        "users": {
            "admin": {
                "name": "Admin User",
                "password_hash": hashed,
                "role": "Admin"
            }
        }
    }[k]

    success, result = authenticate_user("admin", password)
    assert success is True
    assert result["name"] == "Admin User"
    assert result["role"] == "Admin"

@patch("dashboard.streamlit.auth.st.secrets")
def test_authenticate_user_invalid_password(mock_secrets):
    password = "admin_password"
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    mock_secrets.__getitem__.side_effect = lambda k: {
        "users": {
            "admin": {
                "name": "Admin User",
                "password_hash": hashed,
                "role": "Admin"
            }
        }
    }[k]

    success, result = authenticate_user("admin", "wrong_password")
    assert success is False
    assert result == "Invalid username or password."

@patch("dashboard.streamlit.auth.st.secrets")
def test_authenticate_user_invalid_username(mock_secrets):
    mock_secrets.__getitem__.side_effect = lambda k: {
        "users": {}
    }[k]

    success, result = authenticate_user("unknown_user", "password")
    assert success is False
    assert result == "Invalid username or password."

@patch("dashboard.streamlit.auth.st.session_state", {})
def test_initialize_auth_state():
    import dashboard.streamlit.auth as auth
    
    with patch.object(auth.st, "session_state", {}) as mock_session:
        initialize_auth_state()
        assert mock_session["authenticated"] is False
        assert mock_session["username"] is None
        assert mock_session["display_name"] is None
        assert mock_session["user_role"] is None

@patch("dashboard.streamlit.auth.st.session_state", {"authenticated": True})
def test_is_authenticated_true():
    import dashboard.streamlit.auth as auth
    with patch.object(auth.st, "session_state", {"authenticated": True}):
        assert is_authenticated() is True

@patch("dashboard.streamlit.auth.st.session_state", {"user_role": "Analyst"})
def test_has_role():
    import dashboard.streamlit.auth as auth
    with patch.object(auth.st, "session_state", {"user_role": "Analyst"}):
        assert has_role(["Analyst", "Admin"]) is True
        assert has_role(["Admin"]) is False
