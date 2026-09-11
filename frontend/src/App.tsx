import { useEffect, useState } from "react";
import { api, type Chapter, type LayerInfo, type VerseData, type WordData } from "./lib/api";

type View = "read" | "search";

/* ── transparency chips ── */

function MethodChip({ label }: { label: string }) {
  return (
    <span className="rounded-full bg-stone-200/70 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-stone-600">
      {label}
    </span>
  );
}

function PlannedBadge() {
  return (
    <span className="rounded-full border border-dashed border-stone-300 px-2 py-0.5 text-[10px] font-semibold text-stone-400">
      planned
    </span>
  );
}

/* ── layers sidebar ── */

function LayersPanel({
  layers,
  showEn,
  showBn,
  setShowEn,
  setShowBn,
}: {
  layers: LayerInfo[];
  showEn: boolean;
  showBn: boolean;
  setShowEn: (v: boolean) => void;
  setShowBn: (v: boolean) => void;
}) {
  const [open, setOpen] = useState(false);
  return (
    <div className="rounded-2xl border border-stone-200 bg-white p-4 shadow-sm">
      <button className="flex w-full items-center justify-between font-semibold" onClick={() => setOpen(!open)}>
        Interpretive layers
        <span className="text-stone-400 sm:hidden">{open ? "−" : "+"}</span>
      </button>
      <div className={`${open ? "block" : "hidden"} mt-3 space-y-3 sm:block`}>
        <ToggleRow
          title="English translation"
          sub="Saheeh International — translation, not revelation"
          on={showEn}
          set={setShowEn}
        />
        <ToggleRow
          title="Bengali translation"
          sub="Taisirul Quran — translation, not revelation"
          on={showBn}
          set={setShowBn}
        />
        {layers
          .filter((l) => !["quran", "classical-tafsir"].includes(l.code))
          .map((l) => (
            <div key={l.code} className={`rounded-xl border p-3 ${l.has_data ? "border-emerald-200 bg-emerald-50/50" : "border-stone-200 bg-stone-50"}`}>
              <div className="flex items-center justify-between gap-2">
                <p className="text-sm font-semibold">{l.name}</p>
                {l.has_data ? <MethodChip label={l.methodology.split(" ")[0]} /> : <PlannedBadge />}
              </div>
              <p className="mt-1 text-xs text-stone-500">{l.reliability}</p>
              {!l.has_data && l.code === "morphology" && (
                <p className="mt-1 text-xs text-amber-600">
                  Run <code>import_quran.py</code> with a corpus morphology file to enable roots.
                </p>
              )}
            </div>
          ))}
        <p className="pt-1 text-[11px] leading-relaxed text-stone-400">
          Only the Quran itself is unqualified. Every other layer is labeled with methodology,
          source and reliability — and can be compared side by side.
        </p>
      </div>
    </div>
  );
}

function ToggleRow({ title, sub, on, set }: { title: string; sub: string; on: boolean; set: (v: boolean) => void }) {
  return (
    <label className="flex cursor-pointer items-start justify-between gap-3 rounded-xl border border-stone-200 p-3 hover:bg-stone-50">
      <span>
        <span className="block text-sm font-semibold">{title}</span>
        <span className="block text-xs text-stone-500">{sub}</span>
      </span>
      <input type="checkbox" checked={on} onChange={(e) => set(e.target.checked)} className="mt-1 h-4 w-4 accent-emerald-700" />
    </label>
  );
}

/* ── word / root detail panel ── */

function WordPanel({ word, onClose }: { word: WordData; onClose: () => void }) {
  const [rootData, setRootData] = useState<Awaited<ReturnType<typeof api.root>> | null>(null);
  const [rootErr, setRootErr] = useState<string | null>(null);

  useEffect(() => {
    setRootData(null);
    setRootErr(null);
    if (word.root_ar) {
      api
        .root(word.root_ar)
        .then(setRootData)
        .catch((e) => setRootErr(String(e)));
    }
  }, [word]);

  return (
    <div className="fixed inset-x-0 bottom-0 z-40 rounded-t-2xl border-t border-stone-200 bg-white p-5 shadow-2xl sm:inset-auto sm:bottom-6 sm:right-6 sm:w-96 sm:rounded-2xl sm:border">
      <div className="flex items-start justify-between">
        <div>
          <p className="font-quran text-3xl">{word.text_uthmani}</p>
          {word.translation_en && <p className="mt-1 text-sm text-stone-600">“{word.translation_en}”</p>}
        </div>
        <button onClick={onClose} className="rounded-full p-1 text-stone-400 hover:bg-stone-100" aria-label="close">
          ✕
        </button>
      </div>
      <dl className="mt-3 space-y-2 text-sm">
        <div className="flex items-center justify-between gap-2">
          <dt className="text-stone-500">Root</dt>
          <dd>
            {word.root_ar ? (
              <span className="font-quran rounded-lg bg-emerald-700 px-2 py-1 text-xl text-white" dir="rtl">
                {word.root_ar}
              </span>
            ) : (
              <span className="text-xs text-amber-600">not loaded (needs corpus morphology import)</span>
            )}
          </dd>
        </div>
        <div className="flex items-center justify-between gap-2">
          <dt className="text-stone-500">Part of speech</dt>
          <dd>{word.part_of_speech ? <MethodChip label={word.part_of_speech} /> : <span className="text-xs text-stone-400">—</span>}</dd>
        </div>
      </dl>
      {word.root_ar && (
        <div className="mt-3 border-t border-stone-100 pt-3">
          <p className="text-xs font-semibold uppercase tracking-wide text-stone-400">Semantic range — occurrences</p>
          {rootErr && <p className="mt-1 text-xs text-red-500">{rootErr}</p>}
          {rootData && (
            <p className="mt-1 text-sm">
              <b>{rootData.total_occurrences}</b> word-forms across the Quran trace to this root.
            </p>
          )}
          {rootData && rootData.occurrences.length > 0 && (
            <ul className="mt-2 max-h-40 space-y-1 overflow-auto text-xs text-stone-600">
              {rootData.occurrences.slice(0, 30).map((o, i) => (
                <li key={i} className="flex items-center justify-between rounded bg-stone-50 px-2 py-1">
                  <span className="font-quran text-base">{o.word}</span>
                  <span>
                    {o.chapter}:{o.verse}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
      <p className="mt-3 text-[11px] leading-relaxed text-stone-400">
        Methodology: linguistic analysis (Quranic Arabic Corpus). Descriptive grammar, not interpretation.
      </p>
    </div>
  );
}

/* ── verse card ── */

function VerseCard({
  v,
  showEn,
  showBn,
  onWord,
}: {
  v: VerseData;
  showEn: boolean;
  showBn: boolean;
  onWord: (w: WordData) => void;
}) {
  const [words, setWords] = useState<WordData[] | null>(null);
  const [wordsOpen, setWordsOpen] = useState(false);

  const loadWords = async () => {
    if (words) {
      setWordsOpen(!wordsOpen);
      return;
    }
    const w = await api.verseWords(v.chapter_id, v.number);
    setWords(w);
    setWordsOpen(true);
  };

  const en = v.translations["en"]?.[0];
  const bn = v.translations["bn"]?.[0];

  return (
    <article className="rounded-2xl border border-stone-200 bg-white p-5 shadow-sm">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="flex h-7 w-7 items-center justify-center rounded-full bg-emerald-700 text-xs font-bold text-white">
            {v.number}
          </span>
          {en && <span className="text-[10px] font-semibold uppercase tracking-wide text-stone-400">{en.translator_name}</span>}
        </div>
        <button onClick={loadWords} className="rounded-full border border-stone-200 px-3 py-1 text-xs font-semibold text-stone-500 hover:bg-stone-50">
          {wordsOpen ? "hide words" : "word by word"}
        </button>
      </div>

      <p className="font-quran mt-4 text-right" dir="rtl" lang="ar">
        {v.text_uthmani}
      </p>

      {showEn && en && <p className="mt-3 border-l-2 border-emerald-700/40 pl-3 text-[15px] leading-relaxed text-stone-700">{en.text}</p>}
      {showBn && bn && (
        <p className="mt-2 border-l-2 border-sky-700/40 pl-3 text-[15px] leading-relaxed text-stone-700" lang="bn">
          {bn.text}
        </p>
      )}

      {wordsOpen && words && (
        <div className="mt-4 flex flex-wrap gap-2 border-t border-stone-100 pt-4">
          {words.map((w) => (
            <button
              key={w.position}
              onClick={() => onWord(w)}
              title={w.translation_en ?? undefined}
              className={`rounded-lg border px-2 py-1 transition hover:shadow ${
                w.root_ar ? "border-emerald-200 bg-emerald-50/60" : "border-stone-200 bg-stone-50"
              }`}
            >
              <span className="font-quran block text-xl leading-snug" dir="rtl">
                {w.text_uthmani}
              </span>
              {w.translation_en && <span className="block text-[10px] text-stone-500">{w.translation_en}</span>}
            </button>
          ))}
        </div>
      )}
    </article>
  );
}

/* ── app ── */

export default function App() {
  const [view, setView] = useState<View>("read");
  const [chapters, setChapters] = useState<Chapter[]>([]);
  const [chapterId, setChapterId] = useState(1);
  const [verses, setVerses] = useState<VerseData[]>([]);
  const [layers, setLayers] = useState<LayerInfo[]>([]);
  const [showEn, setShowEn] = useState(true);
  const [showBn, setShowBn] = useState(true);
  const [selectedWord, setSelectedWord] = useState<WordData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<Awaited<ReturnType<typeof api.search>> | null>(null);

  useEffect(() => {
    api.chapters().then(setChapters).catch((e) => setError(String(e.message ?? e)));
    api.layers().then(setLayers).catch(() => {});
  }, []);

  useEffect(() => {
    if (view !== "read") return;
    setVerses([]);
    api.chapterVerses(chapterId).then(setVerses).catch((e) => setError(String(e.message ?? e)));
  }, [chapterId, view]);

  const doSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim().length < 2) return;
    setResults(null);
    try {
      setResults(await api.search(query, showBn ? "bn" : "en"));
    } catch (err) {
      setError(String((err as Error).message));
    }
  };

  const chapter = chapters.find((c) => c.id === chapterId);

  return (
    <div className="min-h-screen">
      <header className="sticky top-0 z-30 border-b border-stone-200 bg-[#f7f6f2]/90 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-4 py-3">
          <div className="flex items-baseline gap-2">
            <h1 className="text-xl font-extrabold tracking-tight">
              Miraz <span className="hidden text-sm font-medium text-stone-400 sm:inline">— Al-Quran Re-think</span>
            </h1>
          </div>
          <nav className="flex gap-1">
            {(["read", "search"] as View[]).map((v) => (
              <button
                key={v}
                onClick={() => setView(v)}
                className={`rounded-full px-4 py-1.5 text-sm font-semibold capitalize ${
                  view === v ? "bg-emerald-700 text-white" : "text-stone-500 hover:bg-stone-200/60"
                }`}
              >
                {v}
              </button>
            ))}
          </nav>
        </div>
      </header>

      <main className="mx-auto grid max-w-6xl gap-6 px-4 py-6 lg:grid-cols-[220px_1fr_300px]">
        {view === "read" && (
          <aside className="hidden max-h-[80vh] overflow-auto rounded-2xl border border-stone-200 bg-white p-2 shadow-sm lg:block">
            {chapters.map((c) => (
              <button
                key={c.id}
                onClick={() => setChapterId(c.id)}
                className={`flex w-full items-center justify-between rounded-xl px-3 py-2 text-left text-sm ${
                  c.id === chapterId ? "bg-emerald-700 text-white" : "hover:bg-stone-100"
                }`}
              >
                <span>
                  {c.id}. {c.name_en}
                </span>
                <span className={c.id === chapterId ? "text-emerald-100" : "text-stone-400"}>{c.verses_count}</span>
              </button>
            ))}
          </aside>
        )}

        <section className="space-y-4">
          {error && (
            <div className="rounded-2xl border border-amber-300 bg-amber-50 p-4 text-sm text-amber-800">
              <b>API:</b> {error}
              <p className="mt-1 text-xs">
                Start the backend (<code>uvicorn app.main:app</code>) and run <code>backend/scripts/import_quran.py</code>.
              </p>
            </div>
          )}

          {view === "read" && (
            <>
              {chapter && (
                <div className="rounded-2xl border border-emerald-800/20 bg-white p-5 text-center shadow-sm">
                  <h2 className="text-2xl font-bold">{chapter.name_en}</h2>
                  <p className="font-quran text-3xl" dir="rtl" lang="ar">
                    {chapter.name_ar}
                  </p>
                  <p className="mt-1 text-xs text-stone-400">
                    Chapter {chapter.id} · {chapter.verses_count} verses ·{" "}
                    <MethodChip label="scripture" /> <span className="text-stone-400">unqualified — the Quran itself</span>
                  </p>
                </div>
              )}
              {verses.map((v) => (
                <VerseCard key={v.id} v={v} showEn={showEn} showBn={showBn} onWord={setSelectedWord} />
              ))}
              {!verses.length && !error && <p className="text-sm text-stone-400">Loading…</p>}
            </>
          )}

          {view === "search" && (
            <div className="space-y-4">
              <form onSubmit={doSearch} className="flex gap-2">
                <input
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="Search by keyword (translation text)…"
                  className="flex-1 rounded-xl border border-stone-300 bg-white px-4 py-2.5 text-sm outline-none focus:border-emerald-700"
                />
                <button className="rounded-xl bg-emerald-700 px-5 py-2.5 text-sm font-semibold text-white hover:bg-emerald-800">
                  Search
                </button>
              </form>
              <p className="text-xs text-stone-400">
                Searching {showBn ? "Bengali" : "English"} translation. Root and theme search arrive with the corpus layer.
              </p>
              {results?.map((r, i) => (
                <button
                  key={i}
                  onClick={() => {
                    setChapterId(r.chapter);
                    setView("read");
                  }}
                  className="block w-full rounded-xl border border-stone-200 bg-white p-4 text-left shadow-sm hover:border-emerald-300"
                >
                  <span className="text-xs font-bold text-emerald-700">
                    {r.chapter}:{r.verse}
                  </span>
                  <span className="ml-2 text-[10px] uppercase text-stone-400">{r.translator_name}</span>
                  <p className="mt-1 line-clamp-2 text-sm text-stone-700">{r.snippet}</p>
                </button>
              ))}
              {results && !results.length && <p className="text-sm text-stone-400">No results.</p>}
            </div>
          )}
        </section>

        <aside className="space-y-4">
          <LayersPanel layers={layers} showEn={showEn} showBn={showBn} setShowEn={setShowEn} setShowBn={setShowBn} />
          {view === "read" && (
            <select
              value={chapterId}
              onChange={(e) => setChapterId(Number(e.target.value))}
              className="w-full rounded-xl border border-stone-300 bg-white px-3 py-2 text-sm lg:hidden"
            >
              {chapters.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.id}. {c.name_en}
                </option>
              ))}
            </select>
          )}
        </aside>
      </main>

      {selectedWord && <WordPanel word={selectedWord} onClose={() => setSelectedWord(null)} />}

      <footer className="border-t border-stone-200 py-6 text-center text-xs text-stone-400">
        Miraz · open scholarly research · data: quran.com API (Tanzil), Quranic Arabic Corpus — attribution in README
      </footer>
    </div>
  );
}
