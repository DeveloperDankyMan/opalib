"""
opalib.ai - Access artificial intelligence for free, including making sessions; we have our own ways of doing it. 
Without any other Python installation packages.
"""

import os
import json
import time
import ssl
import http.cookiejar
import urllib.request
import urllib.error

class AutomatedSessionTracker:
    """Manages an automated cookie jar and dynamically handles browser headers."""
    
    def __init__(self):
        # Create an automated cookie container that tracks updates across web calls
        self.cookie_jar = http.cookiejar.CookieJar()
        
        # Build a custom network opener equipped to handle cookies and ignore basic SSL blocks
        ssl_context = ssl._create_unverified_context()
        cookie_handler = urllib.request.HTTPCookieProcessor(self.cookie_jar)
        ssl_handler = urllib.request.HTTPSHandler(context=ssl_context)
        
        self.opener = urllib.request.build_opener(cookie_handler, ssl_handler)
        
        # Base browser footprint to pass through standard edge walls
        self.base_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Origin": "https://duckduckgo.com",
            "Referer": "https://duckduckgo.com"
        }
        
    def initialize_session(self, handshake_url: str, custom_headers: dict = None) -> bool:
        """Hits the initial splash page to harvest tracking cookies before making AI requests."""
        headers = self.base_headers.copy()
        if custom_headers:
            headers.update(custom_headers)
            
        req = urllib.request.Request(handshake_url, headers=headers, method="GET")
        try:
            with self.opener.open(req, timeout=10) as response:
                print("📡 Handshake Successful. Captured Cookies:")
                for cookie in self.cookie_jar:
                    print(f" 🍪 {cookie.name} = {cookie.value[:20]}...")
                return True
        except Exception as e:
            print(f"⚠️ Handshake Failed: {str(e)}")
            return False

    def send_authenticated_post(self, url: str, payload: dict, custom_headers: dict = None) -> str:
        """Sends the AI text prompt with all accumulated tracking cookies automatically attached."""
        headers = self.base_headers.copy()
        headers["Content-Type"] = "application/json"
        if custom_headers:
            headers.update(custom_headers)
            
        json_data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=json_data, headers=headers, method="POST")
        
        try:
            with self.opener.open(req, timeout=15) as response:
                raw_body = response.read().decode("utf-8")
                return raw_body
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8")
            return f"⚠️ HTTP Error {e.code}: {error_body}"
        except Exception as e:
            return f"⚠️ Network Execution Error: {str(e)}"


class AIAgent:
    """An AI Agent that leverages the automated tracker for its backend requests."""
    def __init__(self, name: str, role: str, target_model: str, tracker: AutomatedSessionTracker):
        self.name = name
        self.role = role
        self.target_model = target_model
        self.tracker = tracker
        self.chat_history = []
        
        # Enforce agent context
        self.chat_history.append({
            "role": "system", 
            "content": f"Your name is {self.name}. Your role: {self.role}. Stay in character."
        })

    def ask(self, message: str) -> str:
        """Prepares history format and coordinates with the live tracker infrastructure."""
        self.chat_history.append({"role": "user", "content": message})
        
        # Target endpoint using standard public endpoints (e.g., DuckDuckGo AI gateway routing)
        api_url = "https://duckduckgo.com/duckchat/v1/chat"
        
        # Format conversation payload
        payload = {
            "model": "meta-llama/Llama-3-70b-instruct" if "llama" in self.target_model else "gpt-4o-mini",
            "messages": self.chat_history
        }
        
        # Add required tracking tokens in headers if needed
        v_token = ""
        for cookie in self.tracker.cookie_jar:
            if cookie.name == "vqd":
                v_token = cookie.value
                
        headers = {"x-vqd-4": v_token} if v_token else {}
        
        # Dispatch request through our tracking layer
        raw_response = self.tracker.send_authenticated_post(api_url, payload, custom_headers=headers)
        
        # Quick fallback processing for streaming or raw text formats
        try:
            # Look for classic OpenAI style JSON responses
            data = json.loads(raw_response)
            reply = data["choices"][0]["message"]["content"]
        except Exception:
            # Handle server raw stream chunk responses if JSON parsing fails directly
            if "⚠️" in raw_response:
                reply = raw_response
            else:
                reply = "[Parsing Response]: Server layout updated or streaming block detected."

        self.chat_history.append({"role": "assistant", "content": reply})
        return reply


class AgentSession:
    """Orchestrates conversations between cookie-tracked agents."""
    def __init__(self, session_name: str, tracker: AutomatedSessionTracker):
        self.session_name = session_name
        self.tracker = tracker
        self.agents = []

    def add_agent(self, agent: AIAgent):
        self.agents.append(agent)
        print(f"🔄 Registered Tracker Agent: [{agent.name}] Target: ({agent.target_model})")

    def run_discussion(self, topic: str, rounds: int = 1):
        print(f"\n🚀 Session '{self.session_name}' Active\nTopic: {topic}\n" + "="*60)
        
        current_context = f"The active topic is: {topic}. Give your professional assessment."
        
        for r in range(rounds):
            for agent in self.agents:
                print(f"📡 {agent.name} is executing a cookie-authenticated request...")
                response = agent.ask(current_context)
                
                print(f"\033[96m[{agent.name}]\033[0m: {response}\n")
                
                current_context = f"{agent.name} stated: '{response}'. Address this statement directly."
                time.sleep(2) # Protect against rapid-fire IP ban rules

