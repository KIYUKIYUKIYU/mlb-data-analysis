import base64
import os

token_path = 'credentials/token.pickle'

if os.path.exists(token_path):
    with open(token_path, 'rb') as f:
        token_data = f.read()
    
    # base64エンコード
    encoded_token = base64.b64encode(token_data).decode('utf-8')
    
    print(f"File size: {len(token_data)} bytes")
    print(f"Encoded length: {len(encoded_token)} characters")
    print("\n=== Copy this entire encoded token for GitHub Secrets ===")
    print(encoded_token)
    print("=== End of token ===")
    
    # 検証用：デコードして確認
    decoded = base64.b64decode(encoded_token)
    if decoded == token_data:
        print("\n✅ Encoding verified successfully!")
    else:
        print("\n❌ Encoding verification failed!")
else:
    print(f"Token file not found: {token_path}")