import { useState, useCallback } from 'react';
import { loadProState, redeemCode } from '../lib/pro';

export function usePro() {
  const [state, setState] = useState(() => loadProState());
  const [error, setError] = useState<string | null>(null);
  const [isRedeeming, setIsRedeeming] = useState(false);

  const redeem = useCallback(async (code: string): Promise<boolean> => {
    setError(null);
    setIsRedeeming(true);
    try {
      const next = await redeemCode(code);
      setState(next);
      return true;
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Invalid code');
      return false;
    } finally {
      setIsRedeeming(false);
    }
  }, []);

  return { isPro: state.unlocked, unlockedAt: state.unlockedAt, redeem, error, isRedeeming };
}
