# arena_nervous_system.py
import asyncio
import websockets
import json
import random
import requests
from pathlib import Path
from datetime import datetime

LM_STUDIO_URL = "http://localhost:1234/v1/chat/completions"
LOG_DIR = Path("battle_logs")
LOG_DIR.mkdir(exist_ok=True)

class IntelligentArenaServer:
    def __init__(self, host="127.0.0.1", port=8888):
        self.host = host
        self.port = port
        self.session_id = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        self.log_file = LOG_DIR / f"battle_{self.session_id}.jsonl"
        self.agent_personalities = {
            0: "A fierce Fire Mage, aggressive and direct.",
            1: "A calm Water Monk, defensive and tactical.",
            2: "A chaotic Spark, unpredictable and fast.",
            3: "A deep Sea Guardian, slow but powerful.",
            4: "An Elemental Rogue, uses both fire and water."
        }

    def log_event(self, state, action):
        entry = {
            "timestamp": datetime.now().isoformat(),
            "state": state,
            "action": action
        }
        with open(self.log_file, "a") as f:
            f.write(json.dumps(entry) + "\n")

    async def get_llm_action(self, agent_id, state):
        personality = self.agent_personalities.get(agent_id, "A generic gladiator.")
        prompt = f"You are {personality} in the Silicon Arena. STATE: {json.dumps(state)}. Rules: Output ONLY JSON {{'type': 'MOVE', 'vector': [x, y], 'attack': bool}}"
        
        try:
            response = requests.post(LM_STUDIO_URL, json={
                "messages": [{"role": "system", "content": prompt}],
                "temperature": 0.7, "max_tokens": 40
            }, timeout=0.4)
            action = json.loads(response.json()['choices'][0]['message']['content'])
        except:
            action = {"type": "MOVE", "vector": [random.uniform(-1, 1), random.uniform(-1, 1)], "attack": random.random() > 0.9}
        
        return action

    async def handle_agent(self, websocket):
        print(f"[*] SESSION {self.session_id} - AGENT LINKED.")
        try:
            async for message in websocket:
                state = json.loads(message)
                agent_id = state['agents'][0]['id'] if state['agents'] else 0
                
                action = await self.get_llm_action(agent_id, state)
                self.log_event(state, action)
                await websocket.send(json.dumps(action))
        except websockets.exceptions.ConnectionClosed:
            print(f"[!] SESSION CLOSED. Chronicling Battle...")
            # Trigger Chronicler (Placeholder for Phase 2)

    async def start(self):
        print(f"\n[🏟️] SILICON ARENA LIVE | LOGGING TO: {self.log_file}")
        async with websockets.serve(self.handle_agent, self.host, self.port):
            await asyncio.Future()

if __name__ == "__main__":
    server = IntelligentArenaServer()
    asyncio.run(server.start())
