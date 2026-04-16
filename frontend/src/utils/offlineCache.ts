import AsyncStorage from '@react-native-async-storage/async-storage';

const KEYS = {
  SUBJECTS: 'offline_subjects',
  FLASHCARDS: (sid: string) => `offline_cards_${sid}`,
  PENDING: 'offline_pending',
  META: 'offline_meta',
};

export async function cacheSubjects(subjects: any[]) {
  try {
    await AsyncStorage.setItem(KEYS.SUBJECTS, JSON.stringify(subjects));
    await AsyncStorage.setItem(KEYS.META, JSON.stringify({ cached_at: new Date().toISOString(), subject_count: subjects.length }));
  } catch {}
}

export async function getCachedSubjects(): Promise<any[]> {
  try {
    const data = await AsyncStorage.getItem(KEYS.SUBJECTS);
    return data ? JSON.parse(data) : [];
  } catch { return []; }
}

export async function cacheFlashcards(subjectId: string, cards: any[]) {
  try {
    await AsyncStorage.setItem(KEYS.FLASHCARDS(subjectId), JSON.stringify(cards));
  } catch {}
}

export async function getCachedFlashcards(subjectId: string): Promise<any[]> {
  try {
    const data = await AsyncStorage.getItem(KEYS.FLASHCARDS(subjectId));
    return data ? JSON.parse(data) : [];
  } catch { return []; }
}

export async function savePendingResult(payload: any) {
  try {
    const existing = await AsyncStorage.getItem(KEYS.PENDING);
    const list = existing ? JSON.parse(existing) : [];
    list.push({ ...payload, _ts: Date.now() });
    await AsyncStorage.setItem(KEYS.PENDING, JSON.stringify(list));
  } catch {}
}

export async function getPendingResults(): Promise<any[]> {
  try {
    const data = await AsyncStorage.getItem(KEYS.PENDING);
    return data ? JSON.parse(data) : [];
  } catch { return []; }
}

export async function clearPendingResults() {
  try { await AsyncStorage.removeItem(KEYS.PENDING); } catch {}
}

export async function getOfflineStatus() {
  try {
    const meta = await AsyncStorage.getItem(KEYS.META);
    const pending = await AsyncStorage.getItem(KEYS.PENDING);
    const metaObj = meta ? JSON.parse(meta) : {};
    const pendingList = pending ? JSON.parse(pending) : [];
    return {
      hasCache: !!metaObj.cached_at,
      subjectCount: metaObj.subject_count || 0,
      lastCached: metaObj.cached_at || null,
      pendingCount: pendingList.length,
    };
  } catch {
    return { hasCache: false, subjectCount: 0, lastCached: null, pendingCount: 0 };
  }
}
