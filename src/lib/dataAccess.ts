import { getDb } from './db';

export async function getItems() {
    const db = await getDb();
    return db.all('SELECT * FROM items');
}

export async function exportToLua() {
    const db = await getDb();
    const items = await db.all('SELECT * FROM items');
    
    // Convert to Lua format
    const luaContent = generateLuaTable(items);
    return luaContent;
}

function generateLuaTable(data: any[]) {
    // Implement existing Lua conversion logic here
} 