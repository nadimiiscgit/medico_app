import { REDEEM_CODE_HASHES } from './redeemCodeHashes';

const STORAGE_KEY = 'neetpg_pro';

export interface ProState {
  unlocked: boolean;
  unlockedAt?: string;
}

const DEFAULT_STATE: ProState = { unlocked: false };

export function loadProState(): ProState {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return { ...DEFAULT_STATE };
    return { ...DEFAULT_STATE, ...JSON.parse(raw) };
  } catch {
    return { ...DEFAULT_STATE };
  }
}

function saveProState(state: ProState): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  } catch {
    // Storage quota exceeded or unavailable
  }
}

async function sha256(text: string): Promise<string> {
  const digest = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(text));
  return Array.from(new Uint8Array(digest))
    .map((b) => b.toString(16).padStart(2, '0'))
    .join('');
}

function normalizeCode(code: string): string {
  return code.trim().toUpperCase();
}

// Client-only validation: fine for a lean MVP with a known, trusted audience.
// A shared/leaked code will work on any device — there's no server to enforce
// single use. Move to server-verified auth once volume justifies the backend.
export async function redeemCode(code: string): Promise<ProState> {
  const normalized = normalizeCode(code);
  if (!normalized) {
    throw new Error('Enter a code first.');
  }
  const hash = await sha256(normalized);
  if (!REDEEM_CODE_HASHES.includes(hash)) {
    throw new Error('That code isn\'t valid. Double-check and try again.');
  }
  const state: ProState = { unlocked: true, unlockedAt: new Date().toISOString() };
  saveProState(state);
  return state;
}
