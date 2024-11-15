import { getDb } from './db';
import fs from 'fs/promises';
import path from 'path';

export async function migrate() {
    const db = await getDb();
    
    try {
        // Execute schema.sql first
        const schemaSQL = await fs.readFile(
            path.join(__dirname, '../../db/schema.sql'),
            'utf-8'
        );
        await db.exec(schemaSQL);
        
        // Then execute any pending migrations
        const migrationsDir = path.join(__dirname, '../../db/migrations');
        const files = await fs.readdir(migrationsDir);
        
        for (const file of files.sort()) {
            if (file.endsWith('.sql')) {
                const sql = await fs.readFile(
                    path.join(migrationsDir, file),
                    'utf-8'
                );
                await db.exec(sql);
            }
        }
    } catch (error) {
        console.error('Migration failed:', error);
        throw error;
    }
} 