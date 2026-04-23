# arena_nervous_system.py
import asyncio
import websockets
import json
import random
import requests
from pathlib import Path
from datetime import datetime
from resilience import resilient, ForensicLogger

LM_STUDIO_URL = "http://localhost:1234/v1/chat/completions"
logger = ForensicLogger("arena_nervous")

class IntelligentArenaServer:
    def __init__(self, host="127.0.0.1", port=8888):
        self.host = host
        self.port = port
        self.session_id = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        self.agent_personalities = {
            0: "A fierce Fire Mage, aggressive and direct.",
            1: "A calm Water Monk, defensive and tactical.",
            2: "A chaotic Spark, unpredictable and fast.",
            3: "A deep Sea Guardian, slow but powerful.",
            4: "An Elemental Rogue, uses both fire and water."
        }

    @resilient(retries=2, delay=0.1, backoff=1.5)
    async def get_llm_action(self, agent_id, state):
        personality = self.agent_personalities.get(agent_id, "A generic gladiator.")
        prompt = f"You are {personality}. STATE: {json.dumps(state)}. Rules: Output ONLY JSON {{'type': 'MOVE', 'vector': [x, y], 'attack': bool}}"
        
        response = requests.post(LM_STUDIO_URL, json={
            "messages": [{"role": "system", "content": prompt}],
            "temperature": 0.7, "max_tokens": 40
        }, timeout=0.4)
        
        raw_content = response.json()['choices'][0]['message']['content']
        # Robust JSON cleaning: extract first { to last }
        json_match = re.search(r"(\{.*\})", raw_content.replace("\n", " "))
        if json_match:
            return json.loads(json_match.group(1))
        raise ValueError("Invalid LLM JSON response")

    async def handle_agent(self, websocket):
        logger.log("INFO", f"SESSION {self.session_id} - AGENT LINKED.")
        try:
            async for message in websocket:
                state = json.loads(message)
                agent_id = state['agents'][0]['id'] if state['agents'] else 0
                
                try:
                    action = await self.get_llm_action(agent_id, state)
                    logger.log("SUCCESS", "Action generated", agent_id=agent_id, action=action)
                except:
                    action = {"type": "MOVE", "vector": [random.uniform(-1, 1), random.uniform(-1, 1)], "attack": random.random() > 0.9}
                    logger.log("WARNING", "LLM Failed, using random fallback", agent_id=agent_id)
                
                await websocket.send(json.dumps(action))
        except websockets.exceptions.ConnectionClosed:
            logger.log("INFO", "SESSION CLOSED.")

    async def start(self):
        print(f"\n[🏟️] SILICON ARENA LIVE | LOGGING TO: {self.log_file}")
        async with websockets.serve(self.handle_agent, self.host, self.port):
            await asyncio.Future()

if __name__ == "__main__":
    server = IntelligentArenaServer()
    asyncio.run(server.start())
