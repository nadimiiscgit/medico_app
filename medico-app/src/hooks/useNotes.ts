import { useState, useCallback } from 'react';

const NOTES_KEY = 'neetpg_notes';

function loadNotes(): Record<string, string> {
  try {
    const raw = localStorage.getItem(NOTES_KEY);
    return raw ? JSON.parse(raw) : {};
  } catch {
    return {};
  }
}

export function useNotes() {
  const [notes, setNotes] = useState<Record<string, string>>(() => loadNotes());

  const saveNote = useCallback((questionId: string, note: string) => {
    setNotes((prev) => {
      const next = { ...prev };
      if (note.trim()) {
        next[questionId] = note;
      } else {
        delete next[questionId];
      }
      try {
        localStorage.setItem(NOTES_KEY, JSON.stringify(next));
      } catch {}
      return next;
    });
  }, []);

  return { notes, saveNote };
}
