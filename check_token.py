# check_token.py として保存して実行
import os
import pickle

token_path = 'credentials/token.pickle'

if os.path.exists(token_path):
    file_size = os.path.getsize(token_path)
    print(f"Token file exists: {token_path}")
    print(f"File size: {file_size} bytes")
    
    if file_size > 0:
        try:
            with open(token_path, 'rb') as f:
                token = pickle.load(f)
            print("Token loaded successfully!")
            print(f"Token type: {type(token)}")
        except Exception as e:
            print(f"Error loading token: {e}")
    else:
        print("Token file is empty!")
else:
    print("Token file does not exist!")