import requests
import webbrowser
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs, urlencode
import secrets

class ElyAuthenticator:
    """
    Ely.by OAuth2 Authentication Handler
    Uses Authorization Code Flow for desktop applications
    """
    
    # Ely.by OAuth endpoints
    AUTH_URL = "https://account.ely.by/oauth2/v1"
    API_URL = "https://account.ely.by/api"
    
    # Public client ID (you can register your own at account.ely.by)
    # For now using a generic launcher ID
    CLIENT_ID = "minecraft-launcher"
    CLIENT_SECRET = ""  # Public clients don't need secret
    REDIRECT_URI = "http://localhost:8888/callback"
    
    @staticmethod
    def authenticate():
        """
        Start OAuth flow and return access token + profile data
        Returns: dict with 'access_token', 'username', 'uuid'
        """
        # Generate state for CSRF protection
        state = secrets.token_urlsafe(32)
        
        # Build authorization URL
        auth_params = {
            'client_id': ElyAuthenticator.CLIENT_ID,
            'redirect_uri': ElyAuthenticator.REDIRECT_URI,
            'response_type': 'code',
            'scope': 'minecraft_server_session',
            'state': state
        }
        
        auth_url = f"{ElyAuthenticator.AUTH_URL}/authorize?{urlencode(auth_params)}"
        
        print(f"Opening browser for Ely.by login...")
        print(f"URL: {auth_url}")
        
        # Start local server to receive callback
        auth_code = {'code': None, 'state': None}
        
        class CallbackHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                # Parse callback URL
                parsed = urlparse(self.path)
                params = parse_qs(parsed.query)
                
                if 'code' in params:
                    auth_code['code'] = params['code'][0]
                    auth_code['state'] = params.get('state', [None])[0]
                    
                    # Send success response
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()
                    self.wfile.write(b"""
                        <html>
                        <body style="font-family: Arial; text-align: center; padding: 50px;">
                            <h1>Login Successful!</h1>
                            <p>You can close this window and return to the launcher.</p>
                            <script>setTimeout(() => window.close(), 2000);</script>
                        </body>
                        </html>
                    """)
                else:
                    self.send_response(400)
                    self.end_headers()
                    self.wfile.write(b"Error: No authorization code received")
                
            def log_message(self, format, *args):
                pass  # Suppress server logs
        
        # Start server in background
        server = HTTPServer(('localhost', 8888), CallbackHandler)
        server_thread = threading.Thread(target=server.handle_request, daemon=True)
        server_thread.start()
        
        # Open browser
        webbrowser.open(auth_url)
        
        # Wait for callback (timeout after 2 minutes)
        server_thread.join(timeout=120)
        server.server_close()
        
        if not auth_code['code']:
            raise Exception("Authentication failed: No code received")
        
        if auth_code['state'] != state:
            raise Exception("Authentication failed: State mismatch (CSRF)")
        
        # Exchange code for token
        token_data = ElyAuthenticator._exchange_code(auth_code['code'])
        
        # Get profile info
        profile = ElyAuthenticator._get_profile(token_data['access_token'])
        
        return {
            'access_token': token_data['access_token'],
            'refresh_token': token_data.get('refresh_token'),
            'username': profile['username'],
            'uuid': profile['id']
        }
    
    @staticmethod
    def _exchange_code(code):
        """Exchange authorization code for access token"""
        token_params = {
            'client_id': ElyAuthenticator.CLIENT_ID,
            'client_secret': ElyAuthenticator.CLIENT_SECRET,
            'redirect_uri': ElyAuthenticator.REDIRECT_URI,
            'grant_type': 'authorization_code',
            'code': code
        }
        
        response = requests.post(
            f"{ElyAuthenticator.AUTH_URL}/token",
            data=token_params
        )
        
        if response.status_code != 200:
            raise Exception(f"Token exchange failed: {response.text}")
        
        return response.json()
    
    @staticmethod
    def _get_profile(access_token):
        """Get user profile using access token"""
        headers = {'Authorization': f'Bearer {access_token}'}
        
        response = requests.get(
            f"{ElyAuthenticator.API_URL}/account/v1/info",
            headers=headers
        )
        
        if response.status_code != 200:
            raise Exception(f"Profile fetch failed: {response.text}")
        
        return response.json()
    
    @staticmethod
    def refresh_token(refresh_token):
        """Refresh an expired access token"""
        token_params = {
            'client_id': ElyAuthenticator.CLIENT_ID,
            'client_secret': ElyAuthenticator.CLIENT_SECRET,
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token
        }
        
        response = requests.post(
            f"{ElyAuthenticator.AUTH_URL}/token",
            data=token_params
        )
        
        if response.status_code != 200:
            raise Exception(f"Token refresh failed: {response.text}")
        
        return response.json()
