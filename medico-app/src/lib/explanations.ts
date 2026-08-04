interface ExplanationEntry {
  text: string;
  ai?: boolean;
  images?: string[];
}

type ExplanationsMap = Record<string, ExplanationEntry>;

let cache: ExplanationsMap | null = null;
let loadPromise: Promise<ExplanationsMap> | null = null;

function load(): Promise<ExplanationsMap> {
  if (!loadPromise) {
    loadPromise = fetch('/explanations.json')
      .then((r) => {
        if (!r.ok) throw new Error('Failed to load explanations');
        return r.json() as Promise<ExplanationsMap>;
      })
      .then((data) => {
        cache = data;
        return data;
      });
  }
  return loadPromise;
}

export async function getExplanation(id: string): Promise<ExplanationEntry | null> {
  const map = cache ?? (await load());
  return map[id] ?? null;
}
