import * as SQLite from 'expo-sqlite';

let db: SQLite.SQLiteDatabase | null = null;

async function getDB() {
  if (!db) {
    try {
      db = await SQLite.openDatabaseAsync('flashcards_cache');
      await db.execAsync(`
        CREATE TABLE IF NOT EXISTS subjects (id TEXT PRIMARY KEY, data TEXT);
        CREATE TABLE IF NOT EXISTS flashcards (id TEXT PRIMARY KEY, subject_id TEXT, data TEXT);
        CREATE TABLE IF NOT EXISTS card_progress (card_id TEXT PRIMARY KEY, data TEXT);
        CREATE TABLE IF NOT EXISTS pending_results (id INTEGER PRIMARY KEY AUTOINCREMENT, payload TEXT, created_at TEXT);
        CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT);
      `);
    } catch (e) {
      console.log('SQLite init error:', e);
      return null;
    }
  }
  return db;
}

export async function cacheSubjects(subjects: any[]) {
  const d = await getDB();
  if (!d) return;
  for (const s of subjects) {
    await d.runAsync('INSERT OR REPLACE INTO subjects (id, data) VALUES (?, ?)', s.id, JSON.stringify(s));
  }
  await d.runAsync("INSERT OR REPLACE INTO meta (key, value) VALUES ('subjects_cached_at', ?)", new Date().toISOString());
}

export async function getCachedSubjects(): Promise<any[]> {
  const d = await getDB();
  if (!d) return [];
  const rows = await d.getAllAsync('SELECT data FROM subjects');
  return rows.map((r: any) => JSON.parse(r.data));
}

export async function cacheFlashcards(subjectId: string, cards: any[]) {
  const d = await getDB();
  if (!d) return;
  for (const c of cards) {
    await d.runAsync('INSERT OR REPLACE INTO flashcards (id, subject_id, data) VALUES (?, ?, ?)', c.id || c.card_id, subjectId, JSON.stringify(c));
  }
}

export async function getCachedFlashcards(subjectId: string): Promise<any[]> {
  const d = await getDB();
  if (!d) return [];
  const rows = await d.getAllAsync('SELECT data FROM flashcards WHERE subject_id = ?', subjectId);
  return rows.map((r: any) => JSON.parse(r.data));
}

export async function cacheCardProgress(progress: any[]) {
  const d = await getDB();
  if (!d) return;
  for (const p of progress) {
    await d.runAsync('INSERT OR REPLACE INTO card_progress (card_id, data) VALUES (?, ?)', p.card_id, JSON.stringify(p));
  }
}

export async function savePendingResult(payload: any) {
  const d = await getDB();
  if (!d) return;
  await d.runAsync('INSERT INTO pending_results (payload, created_at) VALUES (?, ?)', JSON.stringify(payload), new Date().toISOString());
}

export async function getPendingResults(): Promise<any[]> {
  const d = await getDB();
  if (!d) return [];
  return d.getAllAsync('SELECT * FROM pending_results ORDER BY id');
}

export async function clearPendingResult(id: number) {
  const d = await getDB();
  if (!d) return;
  await d.runAsync('DELETE FROM pending_results WHERE id = ?', id);
}

export async function getOfflineStatus() {
  const d = await getDB();
  if (!d) return { hasCache: false, pendingCount: 0 };
  const subjectCount = await d.getFirstAsync('SELECT COUNT(*) as count FROM subjects') as any;
  const pendingCount = await d.getFirstAsync('SELECT COUNT(*) as count FROM pending_results') as any;
  const lastCached = await d.getFirstAsync("SELECT value FROM meta WHERE key = 'subjects_cached_at'") as any;
  return {
    hasCache: (subjectCount?.count || 0) > 0,
    pendingCount: pendingCount?.count || 0,
    lastCached: lastCached?.value || null,
    subjectCount: subjectCount?.count || 0,
  };
}
