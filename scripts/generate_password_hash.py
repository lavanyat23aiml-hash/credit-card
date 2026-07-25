import getpass
import bcrypt

def generate_hash():
    print("=== CreditGuard Password Hash Generator ===")
    print("This script generates a secure bcrypt hash for Streamlit secrets.")
    print("The password will not be displayed as you type.")
    
    password = getpass.getpass("Enter password to hash: ")
    
    if not password:
        print("Error: Password cannot be empty.")
        return
        
    # Generate bcrypt hash
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    
    print("\nSuccess! Copy the hash below into your .streamlit/secrets.toml file:")
    print("-" * 50)
    print(hashed.decode('utf-8'))
    print("-" * 50)
    print("Keep this hash secure and never commit it to version control.")

if __name__ == "__main__":
    generate_hash()
