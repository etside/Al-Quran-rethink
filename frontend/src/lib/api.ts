export const API_BASE = import.meta.env.VITE_API_BASE ?? "";

export interface Chapter {
  id: number;
  name_ar: string;
  name_en: string;
  name_bn?: string;
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
  translation_bn?: string | null;
  transliteration?: string | null;
  lemma?: string | null;
  root_ar: string | null;
  root_bn?: string | null;
  verb_form?: string | null;
  grammar_bn?: string | null;
  part_of_speech: string | null;
  has_root_data: boolean;
  has_bn_data?: boolean;
}

export interface TafsirEntry {
  work_code: string;
  work_name: string;
  language: string;
  text: string;
  source: string;
  methodology: string;
}

export interface ContextEntry {
  kind: string;
  kind_label?: string;
  scope?: string;
  text_bn: string;
  text_en?: string | null;
  source: string;
}

export interface BnVerseBundle extends VerseData {
  words: WordData[];
  tafsir: TafsirEntry[];
  context: ContextEntry[];
  coverage: { has_bn_words: boolean; has_tafsir: boolean; has_context: boolean };
}

export interface RootDictEntry {
  root_ar: string;
  meaning_bn: string;
  meaning_en?: string | null;
  pos_summary?: string | null;
  verb_forms?: string | null;
  occurrences: number;
  source: string;
  methodology: string;
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
  const url = `${API_BASE}/api${path}`;
  const res = await fetch(url);
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
    get<{ root: string; total_occurrences: number; meaning_bn?: string | null; meaning_en?: string | null; pos_summary?: string | null; verb_forms?: string | null; source?: string | null; methodology: string; occurrences: { chapter: number; verse: number; word: string; translation_bn?: string | null; part_of_speech: string | null }[] }>(
      `/roots/${encodeURIComponent(root)}`
    ),
  roots: (q = "", limit = 50) =>
    get<RootDictEntry[]>(`/roots?q=${encodeURIComponent(q)}&limit=${limit}`),
  layers: () => get<LayerInfo[]>("/layers"),
  search: (q: string, lang: string) =>
    get<{ chapter: number; verse: number; translator_name: string; language: string; snippet: string }[]>(
      `/search?q=${encodeURIComponent(q)}&lang=${lang}`
    ),
  bnVerse: (ch: number, n: number) => get<BnVerseBundle>(`/bn/verse/${ch}/${n}`),
  bnStatus: () =>
    get<{ words_bn: number; roots_bn: number; tafsir_entries: number; context_notes: number; seed_scope: string }>(
      "/bn/status"
    ),
  tafsir: (ch: number, n: number, lang = "bn") => get<TafsirEntry[]>(`/tafsir/${ch}/${n}?lang=${lang}`),
  context: (ch: number, n: number) => get<ContextEntry[]>(`/context/${ch}/${n}`),
};
