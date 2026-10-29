// Minimal native IndexedDB key-value store. All writes report success only
// after the transaction completes.

const DB_NAME = 'meridian';
const DB_VERSION = 1;
const STORE = 'kv';

export class StorageUnavailableError extends Error {
  constructor(msg: string) {
    super(msg);
    this.name = 'StorageUnavailableError';
  }
}

function req<T>(r: IDBRequest<T>): Promise<T> {
  return new Promise((resolve, reject) => {
    r.onsuccess = () => resolve(r.result);
    r.onerror = () => reject(r.error ?? new Error('IndexedDB request failed'));
  });
}

function done(tx: IDBTransaction): Promise<void> {
  return new Promise((resolve, reject) => {
    tx.oncomplete = () => resolve();
    tx.onabort = () => reject(tx.error ?? new Error('IndexedDB transaction aborted'));
    tx.onerror = () => reject(tx.error ?? new Error('IndexedDB transaction failed'));
  });
}

export class KvStore {
  private constructor(private readonly db: IDBDatabase) {}

  static open(): Promise<KvStore> {
    return new Promise((resolve, reject) => {
      let r: IDBOpenDBRequest;
      try {
        if (typeof indexedDB === 'undefined') throw new StorageUnavailableError('IndexedDB is not available');
        r = indexedDB.open(DB_NAME, DB_VERSION);
      } catch (e) {
        reject(e instanceof Error ? e : new StorageUnavailableError(String(e)));
        return;
      }
      r.onupgradeneeded = () => {
        const db = r.result;
        if (!db.objectStoreNames.contains(STORE)) db.createObjectStore(STORE);
      };
      r.onsuccess = () => resolve(new KvStore(r.result));
      r.onerror = () => reject(new StorageUnavailableError(r.error?.message ?? 'IndexedDB open failed'));
      r.onblocked = () => reject(new StorageUnavailableError('IndexedDB open blocked'));
    });
  }

  async get<T = unknown>(key: string): Promise<T | undefined> {
    const tx = this.db.transaction(STORE, 'readonly');
    const v = await req(tx.objectStore(STORE).get(key));
    return v as T | undefined;
  }

  async put(key: string, value: unknown): Promise<void> {
    const tx = this.db.transaction(STORE, 'readwrite');
    tx.objectStore(STORE).put(value, key);
    await done(tx);
  }

  async delete(key: string): Promise<void> {
    const tx = this.db.transaction(STORE, 'readwrite');
    tx.objectStore(STORE).delete(key);
    await done(tx);
  }

  /**
   * Atomically move the current value of `key` to `backupKey` (only when
   * `keepAsBackup(current)` approves it) and write `value` to `key`, all in
   * one readwrite transaction.
   */
  async rotateAndPut(key: string, backupKey: string, value: unknown, keepAsBackup: (old: unknown) => boolean): Promise<void> {
    const tx = this.db.transaction(STORE, 'readwrite');
    const store = tx.objectStore(STORE);
    const getReq = store.get(key);
    getReq.onsuccess = () => {
      const old = getReq.result;
      if (old !== undefined && keepAsBackup(old)) store.put(old, backupKey);
      store.put(value, key);
    };
    await done(tx);
  }

  close(): void {
    this.db.close();
  }
}
