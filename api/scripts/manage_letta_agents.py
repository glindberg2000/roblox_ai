import argparse
from letta_roblox.client import LettaRobloxClient

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=['list', 'delete-all', 'cleanup'])
    
    args = parser.parse_args()
    
    letta_client = LettaRobloxClient("http://localhost:8283") 