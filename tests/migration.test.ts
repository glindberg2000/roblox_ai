import { jest } from '@jest/globals';
import { migrate } from '../src/lib/migration';
import { getDb } from '../src/lib/db';

describe('Database Migration', () => {
    beforeAll(async () => {
        await migrate();
    });
    
    test('should migrate all existing items', async () => {
        const db = await getDb();
        const items = await db.all('SELECT * FROM items');
        expect(items.length).toBeGreaterThan(0);
    });
}); 