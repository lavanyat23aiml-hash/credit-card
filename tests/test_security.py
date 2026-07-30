import pytest
import streamlit as st
import pandas as pd
from unittest.mock import patch
from dashboard.streamlit.auth import validate_password_strength, verify_password
from dashboard.streamlit.components import mask_customer_id

def test_password_strength_validation():
    # Too short
    valid, msg = validate_password_strength("Short1!")
    assert not valid
    assert "8 characters long" in msg

    # No uppercase
    valid, msg = validate_password_strength("lowercase1!")
    assert not valid
    assert "uppercase" in msg

    # No lowercase
    valid, msg = validate_password_strength("UPPERCASE1!")
    assert not valid
    assert "lowercase" in msg

    # No number
    valid, msg = validate_password_strength("NoNumberHere!")
    assert not valid
    assert "number" in msg

    # No special char
    valid, msg = validate_password_strength("NoSpecialChar1")
    assert not valid
    assert "special character" in msg

    # Valid
    valid, msg = validate_password_strength("ValidPassw0rd!")
    assert valid
    assert msg == "Valid password"

@patch('dashboard.streamlit.components.st.session_state', {'user_role': 'Loan Officer'})
def test_mask_customer_id_loan_officer():
    assert mask_customer_id("CUST12345") == "******345"
    assert mask_customer_id("ID9") == "***"
    assert mask_customer_id("") == ""

@patch('dashboard.streamlit.components.st.session_state', {'user_role': 'Admin'})
def test_mask_customer_id_admin():
    assert mask_customer_id("CUST12345") == "CUST12345"
    assert mask_customer_id("ID9") == "ID9"
    assert mask_customer_id("") == ""

@patch('dashboard.streamlit.components.st.session_state', {'user_role': 'Analyst'})
def test_mask_customer_id_analyst():
    assert mask_customer_id("CUST12345") == "CUST12345"
    assert mask_customer_id("ID9") == "ID9"
    assert mask_customer_id("") == ""
