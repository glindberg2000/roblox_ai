import shutil
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def cleanup_templates():
    project_root = Path(__file__).parent.parent
    
    # Directories to remove
    cleanup_paths = [
        project_root / "templates",
        project_root / "templates_backup",
        project_root / "games" / "game_template_backup",
        project_root / "scripts" / "game_template.py",
        # Don't remove api/templates/game_template yet until we update the API
        # project_root / "api" / "templates" / "game_template"
    ]
    
    for path in cleanup_paths:
        if path.exists():
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()
            logger.info(f"Removed: {path}")
        else:
            logger.info(f"Already clean: {path}")
    
    # After cleanup, we should:
    # 1. Copy our new template to the API templates directory
    source = project_root / "games" / "_template"
    api_template = project_root / "api" / "templates" / "game_template"
    
    if source.exists():
        if api_template.exists():
            shutil.rmtree(api_template)
        shutil.copytree(source, api_template)
        logger.info(f"Updated API template at: {api_template}")
    else:
        logger.error(f"Source template not found at: {source}")
            
    logger.info("Cleanup complete")

if __name__ == "__main__":
    cleanup_templates() 