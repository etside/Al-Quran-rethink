export const API_BASE = import.meta.env.VITE_API_BASE ?? "/api";

export interface Chapter {
  id: number;
  name_ar: string;
  name_en: string;
  verses_count: number;
}

export interface TranslationEntry {
  translator_code: string;
  translator_name: string;
  text: string;
}

export interface VerseData {
  id: number;
  chapter_id: number;
  number: number;
  text_uthmani: string;
  translations: Record<string, TranslationEntry[]>;
}

export interface WordData {
  position: number;
  text_uthmani: string;
  translation_en: string | null;
  root_ar: string | null;
  part_of_speech: string | null;
  has_root_data: boolean;
}

export interface LayerInfo {
  code: string;
  name: string;
  methodology: string;
  reliability: string;
  sources: string[];
  status: string;
  has_data: boolean;
}

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`);
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error((body as { detail?: string }).detail ?? `${res.status} ${res.statusText}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  chapters: () => get<Chapter[]>("/chapters"),
  chapterVerses: (ch: number) => get<VerseData[]>(`/verses/${ch}`),
  verseWords: (ch: number, n: number) => get<WordData[]>(`/verses/${ch}/${n}/words`),
  root: (root: string) =>
    get<{ root: string; total_occurrences: number; occurrences: { chapter: number; verse: number; word: string; part_of_speech: string | null }[] }>(
      `/roots/${encodeURIComponent(root)}`
    ),
  layers: () => get<LayerInfo[]>("/layers"),
  search: (q: string, lang: string) =>
    get<{ chapter: number; verse: number; translator_name: string; snippet: string }[]>(
      `/search?q=${encodeURIComponent(q)}&lang=${lang}`
    ),
};
