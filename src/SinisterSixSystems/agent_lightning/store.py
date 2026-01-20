import json
import os
from pathlib import Path

class LightningStore:
    def __init__(self, path="./artifacts/agent_memory"):
        self.path = Path(path)
        self.path.mkdir(parents=True, exist_ok=True)
        self.store_file = self.path / "trajectories.json"
        self._load_store()
    
    def _load_store(self):
        """Load existing trajectories from disk"""
        if self.store_file.exists():
            with open(self.store_file, 'r', encoding='utf-8') as f:
                self.trajectories = json.load(f)
        else:
            self.trajectories = {}
    
    def _save_store(self):
        """Save trajectories to disk"""
        with open(self.store_file, 'w', encoding='utf-8') as f:
            json.dump(self.trajectories, f, indent=2, ensure_ascii=False)
    
    def get_best_trajectory(self, task):
        """Get the best previous solution for a similar task"""
        if task in self.trajectories:
            # Sort by reward and return the best one
            trajectories = self.trajectories[task]
            if trajectories:
                best = max(trajectories, key=lambda x: x.get('reward', 0))
                return best
        return None
    
    def save_trajectory(self, task, content, reward):
        """Save a new trajectory with its reward"""
        if task not in self.trajectories:
            self.trajectories[task] = []
        
        self.trajectories[task].append({
            'content': content,
            'reward': reward
        })
        
        # Keep only top 5 trajectories per task to avoid memory bloat
        self.trajectories[task] = sorted(
            self.trajectories[task], 
            key=lambda x: x.get('reward', 0), 
            reverse=True
        )[:5]
        
        self._save_store()