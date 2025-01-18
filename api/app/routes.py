from flask import request, jsonify
from flask_app import app
from flask_app.snapshot_processor import enrich_snapshot_with_locations
from flask_app.entity_processor import update_entity_memory
import logging

logger = logging.getLogger(__name__)

@app.route('/letta/v1/snapshot/game', methods=['POST'])
def process_game_snapshot():
    try:
        snapshot_data = request.json
        
        # Enrich with location data
        enriched_snapshot = enrich_snapshot_with_locations(snapshot_data)
        
        # Use enriched data for memory/state updates
        for entity in enriched_snapshot['entities']:
            if entity.get('location_context'):
                # Add to entity's memory/state
                update_entity_memory(entity['id'], {
                    'location_update': entity['location_context'],
                    'nearest_location': entity['nearest_location']['name']
                })
        
        # Rest of snapshot processing...
        
    except Exception as e:
        logger.error(f"Error processing snapshot: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500 