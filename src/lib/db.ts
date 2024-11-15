import sqlite3 from 'sqlite3';
import { open } from 'sqlite';

let db: any = null;

export async function getDb() {
    if (db) return db;
    
    db = await open({
        filename: './db/game_data.db',
        driver: sqlite3.Database
    });
    
    return db;
}

export async function closeDb() {
    if (db) {
        await db.close();
        db = null;
    }
} 