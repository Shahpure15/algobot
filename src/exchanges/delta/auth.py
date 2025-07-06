# src/exchanges/delta/auth.py
import hashlib
import hmac
import json
import time
from typing import Dict, Optional

class DeltaAuthenticator:
    """Handles Delta Exchange API authentication"""
    
    def __init__(self, api_key: str, api_secret: str):
        self.api_key = api_key
        self.api_secret = api_secret.encode('utf-8')
    
    def generate_signature(self, method: str, endpoint: str, payload: Optional[Dict] = None) -> Dict[str, str]:
        """Generate authentication headers for Delta Exchange API"""
        timestamp = str(int(time.time() * 1000))
        
        # Create the signature string
        signature_data = method.upper() + timestamp + endpoint
        
        if payload:
            signature_data += json.dumps(payload, separators=(',', ':'))
        
        # Generate HMAC signature
        signature = hmac.new(
            self.api_secret,
            signature_data.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return {
            'api-key': self.api_key,
            'timestamp': timestamp,
            'signature': signature,
            'Content-Type': 'application/json'
        }