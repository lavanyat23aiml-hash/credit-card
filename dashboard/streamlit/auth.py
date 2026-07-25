import streamlit as st
import bcrypt
from dashboard.streamlit.styles import render_login_header, render_login_footer, render_user_profile_sidebar, render_access_denied_page

def verify_password(password: str, password_hash: str) -> bool:
    """Verifies a password against a bcrypt hash."""
    try:
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    except Exception:
        return False

def authenticate_user(username, password):
    """Checks if the user exists and the password is correct."""
    try:
        users = st.secrets["users"]
    except KeyError:
        return False, "Authentication is not configured. Please contact the administrator."

    if username not in users:
        return False, "Invalid username or password."

    user_info = users[username]
    if "password_hash" not in user_info:
        return False, "Authentication is not configured properly."

    if verify_password(password, user_info["password_hash"]):
        return True, user_info
    else:
        return False, "Invalid username or password."

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
            submit = st.form_submit_button("Login", width="stretch")
            
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
                        st.rerun()
                    else:
                        st.error(result)
        
        render_login_footer()

def logout_button():
    """Renders a logout button and current user info in the sidebar."""
    name = get_current_user()
    role = get_current_role()
    
    render_user_profile_sidebar(name, role)
    
    if st.sidebar.button("Logout", use_container_width=True):
        st.session_state["authenticated"] = False
        st.session_state["username"] = None
        st.session_state["display_name"] = None
        st.session_state["user_role"] = None
        
        # Clear upload session data
        if "use_uploaded_data" in st.session_state:
            st.session_state["use_uploaded_data"] = False
        if "uploaded_df" in st.session_state:
            st.session_state["uploaded_df"] = None
        if "uploaded_filename" in st.session_state:
            st.session_state["uploaded_filename"] = None
            
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
