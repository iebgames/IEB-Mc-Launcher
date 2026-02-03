from pypresence import Presence
import time
import threading

class DiscordRPC:
    CLIENT_ID = "123456789012345678" # Replace with real App ID
    
    def __init__(self):
        self.rpc = None
        self.connected = False
        self.start_time = None

    def connect(self):
        try:
            self.rpc = Presence(self.CLIENT_ID)
            self.rpc.connect()
            self.connected = True
            self.start_time = time.time()
            self.update_presence("In Launcher", "Idle")
            print("Discord RPC Connected")
        except Exception as e:
            print(f"Discord RPC Error: {e}")
            self.connected = False

    def update_presence(self, state, details, large_image="logo", large_text="IEB-MC-Launcher"):
        if not self.connected:
            return
        try:
            self.rpc.update(
                state=state,
                details=details,
                start=self.start_time,
                large_image=large_image,
                large_text=large_text
            )
        except Exception as e:
            print(f"Failed to update RPC: {e}")

    def close(self):
        if self.connected:
            self.rpc.close()

# Singleton instance
rpc_client = DiscordRPC()
