import { useEffect, useState } from "react";
import {
  api,
  type BnVerseBundle,
  type Chapter,
  type LayerInfo,
  type RootDictEntry,
  type VerseData,
  type WordData,
} from "./lib/api";
import { STRINGS, type UiLang } from "./lib/i18n";
import { ErrorBoundary } from "./components/ErrorBoundary";
import { LoadingSpinner, VerseSkeleton, ChapterSkeleton } from "./components/LoadingStates";

type View = "read" | "search" | "roots";

/* ── tajweed demo tinting (rule-based reading aid) ── */
const AR_DIGIT = /^[٠-٩۰-۹]+$/;

function tajClass(w: string): string {
  if (w.includes("ّ")) return "tj-shadda";
  if (/[ٰٓ]/.test(w)) return "tj-madd";
  if (/[قطبجد]/.test(w) && w.includes("ْ")) return "tj-qalqalah";
  return "";
}

function tajName(w: string, ui: UiLang): string | null {
  const c = tajClass(w);
  if (!c) return null;
  if (ui === "bn") {
    if (c === "tj-shadda") return "তাশদীদ (গুন্নাহসহ পড়ুন)";
    if (c === "tj-madd") return "মাদ (টেনে পড়ুন)";
    return "কালকালা (প্রতিধ্বনিসহ)";
  }
  if (c === "tj-shadda") return "shadda (geminate)";
  if (c === "tj-madd") return "madd (elongate)";
  return "qalqalah (echo)";
}

/* ── transparency chips ── */

function MethodChip({ label }: { label: string }) {
  return (
    <span className="rounded-full bg-stone-200/70 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-stone-600">
      {label}
    </span>
  );
}

function PlannedBadge({ label }: { label: string }) {
  return (
    <span className="rounded-full border border-dashed border-stone-300 px-2 py-0.5 text-[10px] font-semibold text-stone-400">
      {label}
    </span>
  );
}

/* ── layers sidebar ── */

function LayersPanel({
  layers,
  showEn,
  showBn,
  showTr,
  showTj,
  setShowEn,
  setShowBn,
  setShowTr,
  setShowTj,
  ui,
  seedScope,
}: {
  layers: LayerInfo[];
  showEn: boolean;
  showBn: boolean;
  showTr: boolean;
  showTj: boolean;
  setShowEn: (v: boolean) => void;
  setShowBn: (v: boolean) => void;
  setShowTr: (v: boolean) => void;
  setShowTj: (v: boolean) => void;
  ui: UiLang;
  seedScope: string | null;
}) {
  const [open, setOpen] = useState(false);
  const t = STRINGS[ui];
  return (
    <div className="rounded-2xl border border-stone-200 bg-white p-4 shadow-sm">
      <button className="flex w-full items-center justify-between font-semibold" onClick={() => setOpen(!open)}>
        <span lang={ui}>{t.layersTitle}</span>
        <span className="text-stone-400 sm:hidden">{open ? "−" : "+"}</span>
      </button>
      <div className={`${open ? "block" : "hidden"} mt-3 space-y-3 sm:block`}>
        <ToggleRow
          title={t.showEn}
          sub="Saheeh International — translation, not revelation"
          on={showEn}
          set={setShowEn}
        />
        <ToggleRow
          title={t.showBn}
          sub="তাইসিরুল কুরআন — অনুবাদ, ওহী নয়"
          on={showBn}
          set={setShowBn}
        />
        <ToggleRow
          title={t.showTr}
          sub="transliteration — pronunciation aid"
          on={showTr}
          set={setShowTr}
        />
        <ToggleRow
          title={t.showTj}
          sub={ui === "bn" ? "নিয়ম-ভিত্তিক রঙ (পাঠ-সহায়ক; পূর্ণ তাজউীদ পরিকল্পিত)" : "rule-based tints (reading aid; full tajweed planned)"}
          on={showTj}
          set={setShowTj}
        />
        {layers
          .filter((l) => l.code !== "quran")
          .map((l) => (
            <div key={l.code} className={`rounded-xl border p-3 ${l.has_data ? "border-emerald-200 bg-emerald-50/50" : "border-stone-200 bg-stone-50"}`}>
              <div className="flex items-center justify-between gap-2">
                <p className="text-sm font-semibold">{l.name}</p>
                {l.has_data ? <MethodChip label={l.methodology.split(" ")[0]} /> : <PlannedBadge label="planned" />}
              </div>
              <p className="mt-1 text-xs text-stone-500">{l.reliability}</p>
              {!l.has_data && l.code === "morphology" && (
                <p className="mt-1 text-xs text-amber-600">
                  Run <code>import_quran.py</code> with a corpus morphology file to enable roots.
                </p>
              )}
            </div>
          ))}
        {seedScope && <p className="rounded-xl bg-sky-50 p-2 text-[11px] leading-relaxed text-sky-800" lang="bn">{seedScope}</p>}
        <p className="pt-1 text-[11px] leading-relaxed text-stone-400" lang={ui}>
          {t.onlyQuran}
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

function WordPanel({ word, ui, onClose }: { word: WordData; ui: UiLang; onClose: () => void }) {
  const t = STRINGS[ui];
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
    <div className="fixed inset-x-0 bottom-0 z-40 max-h-[85vh] overflow-auto rounded-t-2xl border-t border-stone-200 bg-white p-5 shadow-2xl sm:inset-auto sm:bottom-6 sm:right-6 sm:w-[26rem] sm:rounded-2xl sm:border">
      <div className="flex items-start justify-between">
        <div>
          <p className="font-quran text-3xl">{word.text_uthmani}</p>
          {word.transliteration && <p className="mt-1 text-xs italic text-stone-500">{word.transliteration}</p>}
          {word.translation_bn && <p className="mt-1 text-sm text-stone-700" lang="bn">“{word.translation_bn}”</p>}
          {word.translation_en && <p className="mt-0.5 text-xs text-stone-500">“{word.translation_en}”</p>}
        </div>
        <button onClick={onClose} className="rounded-full p-1 text-stone-400 hover:bg-stone-100" aria-label={t.close}>
          ✕
        </button>
      </div>
      <dl className="mt-3 space-y-2 text-sm">
        <div className="flex items-center justify-between gap-2">
          <dt className="text-stone-500" lang={ui}>{t.root}</dt>
          <dd className="text-right">
            {word.root_ar ? (
              <span className="font-quran rounded-lg bg-emerald-700 px-2 py-1 text-xl text-white" dir="rtl">
                {word.root_ar}
              </span>
            ) : (
              <span className="text-xs text-stone-400">—</span>
            )}
            {(word.root_bn || rootData?.meaning_bn) && (
              <span className="mt-1 block text-xs text-stone-600" lang="bn">{word.root_bn ?? rootData?.meaning_bn}</span>
            )}
          </dd>
        </div>
        {word.lemma && (
          <div className="flex items-center justify-between gap-2">
            <dt className="text-stone-500" lang={ui}>{t.lemma}</dt>
            <dd className="font-quran text-lg" dir="rtl">{word.lemma}</dd>
          </div>
        )}
        <div className="flex items-center justify-between gap-2">
          <dt className="text-stone-500" lang={ui}>{t.pos}</dt>
          <dd>{word.part_of_speech ? <MethodChip label={word.part_of_speech} /> : <span className="text-xs text-stone-400">—</span>}</dd>
        </div>
        {word.verb_form && (
          <div className="flex items-center justify-between gap-2">
            <dt className="text-stone-500" lang={ui}>{t.verbForm}</dt>
            <dd><MethodChip label={word.verb_form} /></dd>
          </div>
        )}
        {word.grammar_bn && (
          <div className="gap-1">
            <dt className="text-stone-500" lang={ui}>{t.grammar}</dt>
            <dd className="mt-0.5 text-xs leading-relaxed text-stone-600" lang="bn">{word.grammar_bn}</dd>
          </div>
        )}
      </dl>
      {word.root_ar ? (
        <div className="mt-3 border-t border-stone-100 pt-3">
          <p className="text-xs font-semibold uppercase tracking-wide text-stone-400" lang={ui}>
            {ui === "bn" ? "অর্থ-পরিধি — ব্যবহার" : "Semantic range — occurrences"}
          </p>
          {rootErr && <p className="mt-1 text-xs text-red-500">{rootErr}</p>}
          {rootData && (
            <p className="mt-1 text-sm" lang={ui}>
              <b>{rootData.total_occurrences}</b> {ui === "bn" ? "টি শব্দরূপ এই ধাতু থেকে।" : `${t.totalRoots} ${t.acrossQuran}`}
            </p>
          )}
          {rootData?.verb_forms && <p className="mt-1 text-xs text-stone-500">{rootData.verb_forms}</p>}
          {rootData?.source && <p className="mt-1 text-[11px] text-stone-400">{t.works}: {rootData.source}</p>}
          {rootData && rootData.occurrences.length > 0 && (
            <ul className="mt-2 max-h-40 space-y-1 overflow-auto text-xs text-stone-600">
              {rootData.occurrences.slice(0, 30).map((o, i) => (
                <li key={i} className="flex items-center justify-between rounded bg-stone-50 px-2 py-1">
                  <span className="font-quran text-base">{o.word}</span>
                  {o.translation_bn && <span lang="bn" className="mx-2 flex-1 truncate">{o.translation_bn}</span>}
                  <span>{o.chapter}:{o.verse}</span>
                </li>
              ))}
            </ul>
          )}
        </div>
      ) : (
        <p className="mt-3 text-xs text-amber-600" lang={ui}>{t.notLoaded}</p>
      )}
      <p className="mt-3 text-[11px] leading-relaxed text-stone-400">
        {t.method}: linguistic analysis (Quranic Arabic Corpus + Bengali glossaries). Descriptive grammar, not interpretation.
      </p>
    </div>
  );
}

/* ── verse card with Bengali layers ── */

type VerseTab = "words" | "tafsir" | "context";

function VerseCard({
  v,
  showEn,
  showBn,
  showTr,
  showTj,
  ui,
  onWord,
}: {
  v: VerseData;
  showEn: boolean;
  showBn: boolean;
  showTr: boolean;
  showTj: boolean;
  ui: UiLang;
  onWord: (w: WordData) => void;
}) {
  const t = STRINGS[ui];
  const [bundle, setBundle] = useState<BnVerseBundle | null>(null);
  const [tab, setTab] = useState<VerseTab | null>(null);
  const [loading, setLoading] = useState(false);

  const openTab = async (next: VerseTab) => {
    if (tab === next) {
      setTab(null);
      return;
    }
    setTab(next);
    if (!bundle) {
      setLoading(true);
      try {
        setBundle(await api.bnVerse(v.chapter_id, v.number));
      } catch {
        /* fall back to plain words endpoint */
      } finally {
        setLoading(false);
      }
    }
  };

  const en = v.translations["en"]?.[0];
  const bn = v.translations["bn"]?.[0];
  const words = bundle?.words ?? null;
  const cov = bundle?.coverage;

  return (
    <article className="rounded-2xl border border-stone-200 bg-white p-5 shadow-sm">
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <span className="flex h-7 w-7 items-center justify-center rounded-full bg-emerald-700 text-xs font-bold text-white">
            {v.number}
          </span>
          {en && showEn && <span className="text-[10px] font-semibold uppercase tracking-wide text-stone-400">{en.translator_name}</span>}
          {cov && (
            <span className={`rounded-full px-2 py-0.5 text-[10px] font-semibold ${cov.has_bn_words && cov.has_tafsir ? "bg-emerald-100 text-emerald-800" : "bg-stone-100 text-stone-500"}`} lang={ui}>
              {cov.has_bn_words && cov.has_tafsir ? t.coverageFull : t.coveragePartial}
            </span>
          )}
        </div>
        <div className="flex gap-1">
          {(["words", "tafsir", "context"] as VerseTab[]).map((tb) => (
            <button
              key={tb}
              onClick={() => openTab(tb)}
              className={`rounded-full border px-3 py-1 text-xs font-semibold ${tab === tb ? "border-emerald-700 bg-emerald-700 text-white" : "border-stone-200 text-stone-500 hover:bg-stone-50"}`}
              lang={ui}
            >
              {tb === "words" ? t.words : tb === "tafsir" ? t.tafsir : t.context}
            </button>
          ))}
        </div>
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

      {loading && <p className="mt-3 text-xs text-stone-400" lang={ui}>{t.loading}</p>}

      {tab === "words" && words && (
        <div className="mt-4 border-t border-stone-100 pt-4">
          <div className="flex flex-wrap gap-2">
            {words.filter((w) => !AR_DIGIT.test(w.text_uthmani.trim())).map((w) => {
              const tj = showTj ? tajClass(w.text_uthmani) : "";
              return (
                <button
                  key={w.position}
                  onClick={() => onWord(w)}
                  title={w.translation_bn ?? w.translation_en ?? undefined}
                  className={`rounded-lg border px-2 py-1 transition hover:shadow ${tj} ${w.root_ar ? "border-emerald-200 bg-emerald-50/60" : "border-stone-200 bg-stone-50"} ${w.has_bn_data ? "" : "opacity-80"}`}
                >
                  <span className="font-quran block text-xl leading-snug" dir="rtl">
                    {w.text_uthmani}
                  </span>
                  {w.translation_bn && <span className="block text-[11px] font-medium text-stone-700" lang="bn">{w.translation_bn}</span>}
                  {showTr && w.transliteration && <span className="block text-[10px] italic text-stone-400">{w.transliteration}</span>}
                  {!w.translation_bn && w.translation_en && <span className="block text-[10px] text-stone-500">{w.translation_en}</span>}
                  {showTj && tajName(w.text_uthmani, ui) && (
                    <span className="block text-[9px] text-stone-400">{tajName(w.text_uthmani, ui)}</span>
                  )}
                </button>
              );
            })}
          </div>
          {bundle && !bundle.coverage.has_bn_words && (
            <p className="mt-2 text-[11px] text-stone-400" lang={ui}>{t.seedNote}</p>
          )}
        </div>
      )}

      {tab === "tafsir" && bundle && (
        <div className="mt-4 space-y-3 border-t border-stone-100 pt-4">
          {bundle.tafsir.length === 0 && <p className="text-xs text-stone-400" lang={ui}>{t.seedNote}</p>}
          {bundle.tafsir.map((tf) => (
            <div key={tf.work_code} className="rounded-xl bg-stone-50 p-3">
              <div className="flex flex-wrap items-center gap-2">
                <p className="text-sm font-bold" lang="bn">{tf.work_name}</p>
                <MethodChip label={tf.methodology} />
              </div>
              <p className="mt-1 max-h-64 overflow-auto whitespace-pre-line text-sm leading-relaxed text-stone-700" lang={tf.language === "bn" ? "bn" : undefined}>{tf.text}</p>
              <p className="mt-1 text-[11px] text-stone-400">{t.works}: {tf.source}</p>
            </div>
          ))}
        </div>
      )}

      {tab === "context" && bundle && (
        <div className="mt-4 space-y-3 border-t border-stone-100 pt-4">
          {bundle.context.length === 0 && <p className="text-xs text-stone-400" lang={ui}>{t.seedNote}</p>}
          {bundle.context.map((c, i) => (
            <div key={i} className="rounded-xl bg-amber-50/60 p-3">
              <div className="flex items-center gap-2">
                <p className="text-xs font-bold uppercase tracking-wide text-amber-800" lang="bn">{c.kind}</p>
                {c.scope === "chapter" && (
                  <span className="rounded-full bg-amber-100 px-2 py-0.5 text-[10px] font-semibold text-amber-700" lang={ui}>
                    {ui === "bn" ? "সূরা-পর্যায়" : "chapter-level"}
                  </span>
                )}
              </div>
              <p className="mt-1 text-sm leading-relaxed text-stone-700" lang="bn">{c.text_bn}</p>
              {c.text_en && <p className="mt-1 text-xs text-stone-500">{c.text_en}</p>}
              <p className="mt-1 text-[11px] text-stone-400">{t.works}: {c.source}</p>
            </div>
          ))}
        </div>
      )}
    </article>
  );
}

/* ── root explorer ── */

function RootExplorer({ ui, onWord }: { ui: UiLang; onWord: (w: WordData) => void }) {
  const t = STRINGS[ui];
  const [q, setQ] = useState("");
  const [rows, setRows] = useState<RootDictEntry[] | null>(null);
  const [loading, setLoading] = useState(false);
  void onWord;

  const run = async (e?: React.FormEvent) => {
    e?.preventDefault();
    setLoading(true);
    try {
      setRows(await api.roots(q, 60));
    } catch {
      setRows([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    run();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="space-y-4">
      <form onSubmit={run} className="flex gap-2">
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder={t.rootSearchPh}
          lang={ui}
          className="flex-1 rounded-xl border border-stone-300 bg-white px-4 py-2.5 text-sm outline-none focus:border-emerald-700"
        />
        <button className="rounded-xl bg-emerald-700 px-5 py-2.5 text-sm font-semibold text-white hover:bg-emerald-800" lang={ui}>
          {t.searchBtn}
        </button>
      </form>
      {loading ? (
        <LoadingSpinner text={t.loading} />
      ) : (
        <div className="grid gap-3 sm:grid-cols-2">
          {rows?.map((r) => (
            <div key={r.root_ar} className="rounded-2xl border border-stone-200 bg-white p-4 shadow-sm">
              <div className="flex items-center justify-between">
                <span className="font-quran rounded-lg bg-emerald-700 px-3 py-1 text-2xl text-white" dir="rtl">{r.root_ar}</span>
                <span className="text-xs text-stone-400">{r.occurrences} {ui === "bn" ? "টি" : ""}</span>
              </div>
              <p className="mt-2 text-sm font-semibold text-stone-800" lang="bn">{r.meaning_bn}</p>
              {r.meaning_en && <p className="text-xs text-stone-500">{r.meaning_en}</p>}
              {r.verb_forms && <p className="mt-1 text-xs text-stone-500">{r.verb_forms}</p>}
              <p className="mt-1 text-[11px] text-stone-400">{r.source}</p>
            </div>
          ))}
          {rows && !rows.length && <p className="text-sm text-stone-400" lang={ui}>{t.noResults}</p>}
        </div>
      )}
    </div>
  );
}

/* ── app ── */

export default function App() {
  const [ui, setUi] = useState<UiLang>("bn");
  const t = STRINGS[ui];
  const [view, setView] = useState<View>("read");
  const [chapters, setChapters] = useState<Chapter[]>([]);
  const [chapterId, setChapterId] = useState(1);
  const [verses, setVerses] = useState<VerseData[]>([]);
  const [layers, setLayers] = useState<LayerInfo[]>([]);
  const [seedScope, setSeedScope] = useState<string | null>(null);
  const [showEn, setShowEn] = useState(false);
  const [showBn, setShowBn] = useState(true);
  const [showTr, setShowTr] = useState(true);
  const [showTj, setShowTj] = useState(true);
  const [selectedWord, setSelectedWord] = useState<WordData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [searchLang, setSearchLang] = useState<"bn" | "en">("bn");
  const [results, setResults] = useState<Awaited<ReturnType<typeof api.search>> | null>(null);
  const [loadingChapters, setLoadingChapters] = useState(true);
  const [loadingVerses, setLoadingVerses] = useState(false);
  const [loadingSearch, setLoadingSearch] = useState(false);

  useEffect(() => {
    setLoadingChapters(true);
    setError(null);
    api.chapters()
      .then(setChapters)
      .catch((e) => setError(String(e.message ?? e)))
      .finally(() => setLoadingChapters(false));
    api.layers().then(setLayers).catch(() => {});
    api.bnStatus().then((s) => setSeedScope(s.seed_scope)).catch(() => {});
  }, []);

  useEffect(() => {
    if (view !== "read") return;
    setVerses([]);
    setLoadingVerses(true);
    setError(null);
    api.chapterVerses(chapterId)
      .then(setVerses)
      .catch((e) => setError(String(e.message ?? e)))
      .finally(() => setLoadingVerses(false));
  }, [chapterId, view]);

  const doSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim().length < 2) return;
    setResults(null);
    setLoadingSearch(true);
    setError(null);
    try {
      setResults(await api.search(query, searchLang));
    } catch (err) {
      setError(String((err as Error).message));
    } finally {
      setLoadingSearch(false);
    }
  };

  const chapter = chapters.find((c) => c.id === chapterId);
  const chapterName = chapter ? (ui === "bn" ? (chapter.name_bn ?? chapter.name_en) : chapter.name_en) : "";

  return (
    <ErrorBoundary>
    <div className="min-h-screen" lang={ui}>
      <header className="sticky top-0 z-30 border-b border-stone-200 bg-[#f7f6f2]/90 backdrop-blur">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-3 px-4 py-3">
          <div className="flex items-baseline gap-2">
            <h1 className="text-xl font-extrabold tracking-tight">
              মিরাজ <span className="font-medium text-stone-500">Miraz</span>{" "}
              <span className="hidden text-sm font-medium text-stone-400 sm:inline">— {t.appTag}</span>
            </h1>
          </div>
          <div className="flex items-center gap-2">
            <nav className="flex gap-1">
              {(["read", "search", "roots"] as View[]).map((v) => (
                <button
                  key={v}
                  onClick={() => setView(v)}
                  className={`rounded-full px-4 py-1.5 text-sm font-semibold capitalize ${
                    view === v ? "bg-emerald-700 text-white" : "text-stone-500 hover:bg-stone-200/60"
                  }`}
                  lang={ui}
                >
                  {v === "read" ? t.read : v === "search" ? t.search : t.roots}
                </button>
              ))}
            </nav>
            <button
              onClick={() => setUi(ui === "bn" ? "en" : "bn")}
              className="rounded-full border border-stone-300 px-3 py-1.5 text-xs font-bold text-stone-600 hover:bg-stone-100"
              title={ui === "bn" ? "Switch to English UI" : "বাংলা ইন্টারফেস"}
            >
              {ui === "bn" ? "EN" : "বাং"}
            </button>
          </div>
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
                  {c.id}. {ui === "bn" ? (c.name_bn ?? c.name_en) : c.name_en}
                </span>
                <span className={c.id === chapterId ? "text-emerald-100" : "text-stone-400"}>{c.verses_count}</span>
              </button>
            ))}
          </aside>
        )}

        <section className="space-y-4">
          {error && (
            <div className="rounded-2xl border border-amber-300 bg-amber-50 p-4 text-sm text-amber-800">
              <b>{t.apiError}</b> {error}
              <p className="mt-1 text-xs">{t.startBackend}</p>
            </div>
          )}

          {view === "read" && (
            <>
              {loadingChapters ? (
                <ChapterSkeleton />
              ) : chapter ? (
                <div className="rounded-2xl border border-emerald-800/20 bg-white p-5 text-center shadow-sm">
                  <h2 className="text-2xl font-bold">{chapterName}</h2>
                  <p className="font-quran text-3xl" dir="rtl" lang="ar">
                    {chapter.name_ar}
                  </p>
                  <p className="mt-1 text-xs text-stone-400">
                    {t.chapter} {chapter.id} · {chapter.verses_count} {t.verses} ·{" "}
                    <MethodChip label="scripture" /> <span className="text-stone-400">{t.onlyQuran}</span>
                  </p>
                </div>
              ) : null}
              {loadingVerses ? (
                <div className="space-y-4">
                  {Array.from({ length: 5 }).map((_, i) => (
                    <VerseSkeleton key={i} />
                  ))}
                </div>
              ) : (
                verses.map((v) => (
                  <VerseCard key={v.id} v={v} showEn={showEn} showBn={showBn} showTr={showTr} showTj={showTj} ui={ui} onWord={setSelectedWord} />
                ))
              )}
            </>
          )}

          {view === "search" && (
            <div className="space-y-4">
              <form onSubmit={doSearch} className="flex gap-2">
                <input
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder={t.searchPh}
                  lang={searchLang}
                  className="flex-1 rounded-xl border border-stone-300 bg-white px-4 py-2.5 text-sm outline-none focus:border-emerald-700"
                />
                <select
                  value={searchLang}
                  onChange={(e) => setSearchLang(e.target.value as "bn" | "en")}
                  className="rounded-xl border border-stone-300 bg-white px-2 text-sm"
                  title="search language"
                >
                  <option value="bn">বাং</option>
                  <option value="en">EN</option>
                </select>
                <button
                  disabled={loadingSearch}
                  className="rounded-xl bg-emerald-700 px-5 py-2.5 text-sm font-semibold text-white hover:bg-emerald-800 disabled:opacity-50"
                  lang={ui}
                >
                  {loadingSearch ? t.searching : t.searchBtn}
                </button>
              </form>
              <p className="text-xs text-stone-400" lang={ui}>
                {searchLang === "bn" ? t.searchHintBn : t.searchHintEn}
              </p>
              {loadingSearch ? (
                <LoadingSpinner text={t.searching} />
              ) : (
                <>
                  {results?.map((r, i) => (
                    <button
                      key={i}
                      onClick={() => {
                        setChapterId(r.chapter);
                        setView("read");
                      }}
                      className="block w-full rounded-xl border border-stone-200 bg-white p-4 text-left shadow-sm hover:border-emerald-300 transition-colors"
                    >
                      <span className="text-xs font-bold text-emerald-700">
                        {r.chapter}:{r.verse}
                      </span>
                      <span className="ml-2 text-[10px] uppercase text-stone-400">{r.translator_name}</span>
                      <p className="mt-1 line-clamp-2 text-sm text-stone-700" lang={r.language === "bn" ? "bn" : undefined}>{r.snippet}</p>
                    </button>
                  ))}
                  {results && !results.length && <p className="text-sm text-stone-400" lang={ui}>{t.noResults}</p>}
                </>
              )}
            </div>
          )}

          {view === "roots" && <RootExplorer ui={ui} onWord={setSelectedWord} />}
        </section>

        <aside className="space-y-4">
          <LayersPanel layers={layers} showEn={showEn} showBn={showBn} showTr={showTr} showTj={showTj} setShowEn={setShowEn} setShowBn={setShowBn} setShowTr={setShowTr} setShowTj={setShowTj} ui={ui} seedScope={seedScope} />
          {view === "read" && (
            <select
              value={chapterId}
              onChange={(e) => setChapterId(Number(e.target.value))}
              className="w-full rounded-xl border border-stone-300 bg-white px-3 py-2 text-sm lg:hidden"
            >
              {chapters.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.id}. {ui === "bn" ? (c.name_bn ?? c.name_en) : c.name_en}
                </option>
              ))}
            </select>
          )}
        </aside>
      </main>

      {selectedWord && <WordPanel word={selectedWord} ui={ui} onClose={() => setSelectedWord(null)} />}

      <footer className="border-t border-stone-200 py-6 text-center text-xs text-stone-400" lang={ui}>
        {t.footer}
      </footer>
    </div>
    </ErrorBoundary>
  );
}
