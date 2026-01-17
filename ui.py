import streamlit as st
import os
import asyncio
from livekit import api
from dotenv import load_dotenv

# Load environment variables
load_dotenv(".env.local")

# Set up page layout
st.set_page_config(page_title="Voice Agent Interface", layout="centered")

st.title("🎙️ RAG Voice Agent Client")
st.caption("A simple frontend to interact with your LiveKit Voice Agent")

# --- Configuration Side ---
with st.sidebar:
    st.header("Connection Settings")
    # Default to the room name often used in standard agent examples or allow custom
    room_name = st.text_input("Room Name", value="chat-room-1")
    participant_identity = st.text_input("Your Name", value="user-frontend")

# --- Helper: Generate Token ---
def get_token(room_name, participant_name):
    try:
        lk_api_key = os.getenv("LIVEKIT_API_KEY")
        lk_api_secret = os.getenv("LIVEKIT_API_SECRET")
        
        if not lk_api_key or not lk_api_secret:
            st.error("LiveKit credentials not found. Please check .env.local")
            return None

        # Create a token with permissions to join, publish (mic), and subscribe (hear agent)
        token = api.AccessToken(lk_api_key, lk_api_secret) \
            .with_identity(participant_name) \
            .with_name(participant_name) \
            .with_grants(api.VideoGrants(
                room_join=True,
                room=room_name,
                can_publish=True,
                can_subscribe=True,
            ))
        
        return token.to_jwt()
    except Exception as e:
        st.error(f"Error generating token: {e}")
        return None

# --- Main UI Logic ---

# We use session state to hold the token so it doesn't regenerate on every interaction
if "token" not in st.session_state:
    st.session_state.token = None

if st.button("🔌 Connect to Agent", type="primary"):
    token = get_token(room_name, participant_identity)
    if token:
        st.session_state.token = token
        st.success(f"Token generated for room: {room_name}")
    else:
        st.error("Failed to generate token.")

# --- The Frontend Component (HTML/JS) ---
# Since Streamlit runs on Python (server-side), we need to inject JavaScript 
# to handle the Microphone and Audio Playback in the user's browser.

if st.session_state.token:
    livekit_url = os.getenv("LIVEKIT_URL")
    
    # This HTML block loads the LiveKit Client SDK and handles the logic
    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <script src="https://cdn.jsdelivr.net/npm/livekit-client/dist/livekit-client.umd.min.js"></script>
        <style>
            body {{ font-family: sans-serif; background-color: #f0f2f6; padding: 20px; border-radius: 10px; text-align: center; }}
            #status {{ font-weight: bold; margin-bottom: 20px; color: #333; }}
            .control-btn {{
                background-color: #ff4b4b; color: white; border: none; padding: 10px 20px;
                border-radius: 5px; cursor: pointer; font-size: 16px; margin: 5px;
            }}
            .control-btn:disabled {{ background-color: #ccc; cursor: not-allowed; }}
            .visualizer {{ height: 50px; background-color: #ddd; margin-top: 20px; border-radius: 4px; transition: width 0.1s; width: 0%; }}
        </style>
    </head>
    <body>
        <div id="status">Ready to connect...</div>
        <button id="connectBtn" class="control-btn" onclick="connectToRoom()">Start Conversation</button>
        <button id="disconnectBtn" class="control-btn" onclick="disconnectRoom()" disabled>Disconnect</button>
        
        <div id="audio-container"></div>

        <script>
            let room;
            const url = "{livekit_url}";
            const token = "{st.session_state.token}";
            const statusDiv = document.getElementById('status');
            const connectBtn = document.getElementById('connectBtn');
            const disconnectBtn = document.getElementById('disconnectBtn');

            async function connectToRoom() {{
                statusDiv.innerText = "Connecting...";
                
                try {{
                    room = new LivekitClient.Room({{
                        // AdaptiveStream ensures we handle network changes gracefully
                        adaptiveStream: true,
                        dynacast: true,
                    }});

                    // 1. Handle Remote Tracks (The Agent's Voice)
                    room.on(LivekitClient.RoomEvent.TrackSubscribed, (track, publication, participant) => {{
                        if (track.kind === LivekitClient.Track.Kind.Audio) {{
                            const element = track.attach();
                            document.getElementById('audio-container').appendChild(element);
                            statusDiv.innerText = "Agent Connected & Speaking";
                        }}
                    }});

                    // 2. Handle Disconnection
                    room.on(LivekitClient.RoomEvent.Disconnected, () => {{
                        statusDiv.innerText = "Disconnected";
                        connectBtn.disabled = false;
                        disconnectBtn.disabled = true;
                    }});

                    // 3. Connect
                    await room.connect(url, token);
                    statusDiv.innerText = "Connected! Opening Microphone...";

                    // 4. Publish Local Microphone
                    await room.localParticipant.setMicrophoneEnabled(true);
                    statusDiv.innerText = "🎙️ You are live. Speak to the agent.";
                    
                    connectBtn.disabled = true;
                    disconnectBtn.disabled = false;

                }} catch (error) {{
                    console.error(error);
                    statusDiv.innerText = "Error: " + error.message;
                }}
            }}

            function disconnectRoom() {{
                if (room) {{
                    room.disconnect();
                }}
            }}
        </script>
    </body>
    </html>
    """

    # Embed the HTML/JS into Streamlit
    st.components.v1.html(html_code, height=300)

else:
    st.info("Please generate a token above to load the client interface.")