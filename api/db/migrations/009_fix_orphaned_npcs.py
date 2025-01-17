def migrate(db):
    """Fix NPCs with null asset_ids"""
    print("Fixing NPCs with null asset_ids...")
    
    try:
        # First, let's see how many NPCs need fixing
        cursor = db.execute("""
            SELECT COUNT(*) as count 
            FROM npcs 
            WHERE asset_id IS NULL OR asset_id = 'undefined'
        """)
        count = cursor.fetchone()[0]
        print(f"Found {count} NPCs to fix")
        
        # Update NPCs with default asset_id
        db.execute("""
            UPDATE npcs 
            SET asset_id = '4446576906'  -- Default Noob2 model
            WHERE asset_id IS NULL 
            OR asset_id = 'undefined'
            OR asset_id = '';
        """)
        
        db.commit()
        print("✓ Successfully fixed orphaned NPCs")
        
        # Verify the fix
        cursor = db.execute("""
            SELECT COUNT(*) as count 
            FROM npcs 
            WHERE asset_id IS NULL OR asset_id = 'undefined'
        """)
        remaining = cursor.fetchone()[0]
        print(f"Remaining NPCs with null asset_id: {remaining}")
        
    except Exception as e:
        print(f"! Failed to fix orphaned NPCs: {str(e)}")
        db.rollback()
        raise

def rollback(db):
    """No rollback needed for this fix"""
    pass 