import os
import shutil
from pathlib import Path

def move_files():
    # Project root
    root = Path('.')
    
    # Create directories if they don't exist
    directories = [
        'src/shared/NPCSystem/config',
        'src/shared/NPCSystem/services',
        'src/shared/NPCSystem/chat'
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    # Files to move
    moves = [
        # Move PerformanceConfig to config folder
        ('src/shared/PerformanceConfig.lua', 'src/shared/NPCSystem/config/PerformanceConfig.lua'),
        
        # Move services
        ('src/shared/services/MovementService.lua', 'src/shared/NPCSystem/services/MovementService.lua'),
        ('src/shared/services/VisionService.lua', 'src/shared/NPCSystem/services/VisionService.lua'),
        ('src/shared/services/InteractionService.lua', 'src/shared/NPCSystem/services/InteractionService.lua'),
        ('src/shared/services/AnimationService.lua', 'src/shared/NPCSystem/services/AnimationService.lua'),
        ('src/shared/services/LoggerService.lua', 'src/shared/NPCSystem/services/LoggerService.lua'),
    ]
    
    for src, dst in moves:
        src_path = root / src
        dst_path = root / dst
        
        if src_path.exists():
            print(f"Moving {src} to {dst}")
            # Create parent directories if they don't exist
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            # Move the file
            shutil.move(str(src_path), str(dst_path))
        else:
            print(f"Warning: Source file {src} not found")

if __name__ == "__main__":
    move_files() 