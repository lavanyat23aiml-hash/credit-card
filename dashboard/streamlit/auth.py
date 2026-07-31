import streamlit as st
import bcrypt
from dashboard.streamlit.styles import render_login_header, render_login_footer, render_user_profile_sidebar, render_access_denied_page
from dashboard.streamlit.database import log_audit_event

import time

def validate_password_strength(password: str) -> tuple[bool, str]:
    """Validates if a password meets enterprise security requirements."""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not any(c.isupper() for c in password):
        return False, "Password must contain an uppercase letter."
    if not any(c.islower() for c in password):
        return False, "Password must contain a lowercase letter."
    if not any(c.isdigit() for c in password):
        return False, "Password must contain a number."
    if not any(c in "!@#$%^&*()-_=+" for c in password):
        return False, "Password must contain a special character (!@#$%^&*()-_=+)."
    return True, "Valid password"

def verify_password(password: str, password_hash: str) -> bool:
    """Verifies a password against a bcrypt hash."""
    try:
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    except Exception:
        return False

def authenticate_user(username, password):
    """Checks if the user exists, handles rate limiting, and verifies password securely."""
    if "failed_attempts" not in st.session_state:
        st.session_state["failed_attempts"] = {}
    if "lockouts" not in st.session_state:
        st.session_state["lockouts"] = {}
        
    current_time = time.time()
    
    # Check lockout status
    if username in st.session_state["lockouts"]:
        lockout_expiry = st.session_state["lockouts"][username]
        if current_time < lockout_expiry:
            remaining = int((lockout_expiry - current_time) / 60) + 1
            return False, f"Account temporarily locked due to repeated failed attempts. Try again in {remaining} minutes."
        else:
            del st.session_state["lockouts"][username]
            st.session_state["failed_attempts"][username] = 0

    try:
        users = st.secrets["users"]
    except Exception:
        return False, "Authentication is not configured. Please contact the administrator."

    # Generic error message for both non-existent user and wrong password
    generic_error = "Invalid username or password."

    if username not in users:
        # Simulate delay to prevent timing attacks
        time.sleep(0.1)
        _record_failed_attempt(username, current_time)
        return False, generic_error

    user_info = users[username]
    if "password_hash" not in user_info:
        return False, generic_error

    if verify_password(password, user_info["password_hash"]):
        # Reset attempts on success
        st.session_state["failed_attempts"][username] = 0
        return True, user_info
    else:
        _record_failed_attempt(username, current_time)
        return False, generic_error

def _record_failed_attempt(username: str, current_time: float):
    """Records a failed attempt and locks account if threshold exceeded."""
    attempts = st.session_state["failed_attempts"].get(username, 0) + 1
    st.session_state["failed_attempts"][username] = attempts
    
    # Lockout after 5 failed attempts
    if attempts >= 5:
        # 15 minute lockout
        st.session_state["lockouts"][username] = current_time + (15 * 60)

def initialize_auth_state():
    """Initializes session state variables for authentication."""
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False
    if "username" not in st.session_state:
        st.session_state["username"] = None
    if "display_name" not in st.session_state:
        st.session_state["display_name"] = None
    if "user_role" not in st.session_state:
        st.session_state["user_role"] = None

def is_authenticated():
    """Returns True if the user is currently authenticated."""
    return st.session_state.get("authenticated", False)

def get_current_user():
    """Returns the current user's display name."""
    return st.session_state.get("display_name")

def get_current_role():
    """Returns the current user's role."""
    return st.session_state.get("user_role")

def login_form():
    """Renders the login page."""
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        render_login_header()
        
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login")
            
            if submit:
                if not username or not password:
                    st.error("Please enter both username and password.")
                else:
                    success, result = authenticate_user(username, password)
                    if success:
                        st.session_state["authenticated"] = True
                        st.session_state["username"] = username
                        st.session_state["display_name"] = result.get("name", username)
                        st.session_state["user_role"] = result.get("role", "User")
                        log_audit_event(username, st.session_state["user_role"], "LOGIN", "System", "Session", "SUCCESS", "User logged in")
                        st.rerun()
                    else:
                        log_audit_event(username, "Unknown", "LOGIN", "System", "Session", "FAILED", result)
                        st.error(result)
        
        render_login_footer()

def logout_button():
    """Renders a logout button and current user info in the sidebar."""
    name = get_current_user()
    role = get_current_role()
    
    render_user_profile_sidebar(name, role)
    
    if st.sidebar.button("Logout", use_container_width=True):
        if st.session_state.get("username"):
            log_audit_event(st.session_state["username"], st.session_state["user_role"], "LOGOUT", "System", "Session", "SUCCESS", "User logged out")
            
        st.session_state["authenticated"] = False
        st.session_state["username"] = None
        st.session_state["display_name"] = None
        st.session_state["user_role"] = None
        
        # Clear sensitive analytical session data
        sensitive_keys = [
            "use_uploaded_data", "uploaded_df", "uploaded_filename", 
            "uploaded_validation_report", "fraud_indicator_df", 
            "fraud_filter_state", "fraud_selected_customer",
            "xai_current_model", "xai_explainer", "xai_base_values"
        ]
        for key in sensitive_keys:
            if key in st.session_state:
                del st.session_state[key]

        st.rerun()

def require_authentication():
    """Stops execution if the user is not authenticated."""
    if not is_authenticated():
        login_form()
        st.stop()

def has_role(allowed_roles: list) -> bool:
    """Checks if the current user has one of the allowed roles."""
    role = get_current_role()
    return role in allowed_roles

def render_access_denied():
    """Renders the access denied page and stops execution."""
    render_access_denied_page()
    st.stop()
