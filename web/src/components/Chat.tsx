import { useEffect, useRef, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";

import { api, ApiError } from "../api";
import { routeForScreen } from "../screens";
import type { ChatReply, ClientKind } from "../types";

interface Message {
  from: "user" | "bot";
  text: string;
  reply?: ChatReply;
}

/** Electron uygulaması preload ile `window.faturaDesktop` ekler; böylece asistan istemci türünü doğru bilir. */
function clientKind(): ClientKind {
  return (window as unknown as { faturaDesktop?: unknown }).faturaDesktop ? "desktop" : "web";
}

/** Bulunulan yola göre ekran kodu: asistan "bunu nasıl yaparım" gibi kısa soruları buna göre yanıtlar. */
function currentScreen(pathname: string, search: string): string | undefined {
  if (pathname === "/") return "home";
  if (pathname === "/upload") return "upload";
  if (pathname === "/documents") return search.includes("needs_review") ? "review" : "documents";
  if (pathname === "/export") return "export";
  if (pathname === "/team") return "team";
  if (pathname === "/profile") return "profile";
  if (pathname === "/help") return "help";
  return undefined;
}

export default function Chat() {
  const [open, setOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const [input, setInput] = useState("");
  const [topics, setTopics] = useState<string[]>([]);
  const [messages, setMessages] = useState<Message[]>([
    { from: "bot", text: "Merhaba! Bir şeyi bulamazsan veya nasıl yapacağını bilmiyorsan bana sor, seni doğrudan o ekrana götürürüm." },
  ]);
  const listRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();
  const location = useLocation();
  const kind = clientKind();

  useEffect(() => {
    if (open && topics.length === 0) api.chatTopics(kind).then(setTopics).catch(() => undefined);
  }, [open, topics.length, kind]);

  useEffect(() => {
    listRef.current?.scrollTo({ top: listRef.current.scrollHeight });
  }, [messages, open]);

  async function ask(text: string) {
    const message = text.trim();
    if (!message || busy) return;
    setInput("");
    setMessages((m) => [...m, { from: "user", text: message }]);
    setBusy(true);
    try {
      const reply = await api.chat(message, kind, currentScreen(location.pathname, location.search));
      setMessages((m) => [...m, { from: "bot", text: reply.answer, reply }]);
    } catch (e) {
      const text = e instanceof ApiError ? e.message : "Şu an cevap veremiyorum.";
      setMessages((m) => [...m, { from: "bot", text }]);
    } finally {
      setBusy(false);
    }
  }

  function go(screen: string) {
    const route = routeForScreen(screen);
    if (route) {
      navigate(route);
      setOpen(false);
    }
  }

  return (
    <>
      <button className="chat-fab" onClick={() => setOpen((o) => !o)} aria-expanded={open} aria-controls="chat-panel">
        {open ? "Kapat" : "Yardım?"}
      </button>
      {open && (
        <section className="chat-panel" id="chat-panel" aria-label="Yardım asistanı">
          <header>Yardım asistanı</header>
          <div className="chat-list" ref={listRef} aria-live="polite">
            {messages.map((m, i) => (
              <div key={i} className={`bubble ${m.from}`}>
                <p>{m.text}</p>
                {m.reply && m.reply.steps.length > 0 && (
                  <ol>
                    {m.reply.steps.map((s, k) => (
                      <li key={k}>{s}</li>
                    ))}
                  </ol>
                )}
                {m.reply?.action && (
                  <button className="btn small" onClick={() => go(m.reply!.action!.screen)}>
                    {m.reply.action.label}
                  </button>
                )}
                {m.reply && m.reply.suggestions.length > 0 && (
                  <div className="chips">
                    {m.reply.suggestions.map((s) => (
                      <button key={s} className="chip" onClick={() => ask(s)}>
                        {s}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            ))}
            {messages.length === 1 && topics.length > 0 && (
              <div className="chips">
                {topics.slice(0, 5).map((s) => (
                  <button key={s} className="chip" onClick={() => ask(s)}>
                    {s}
                  </button>
                ))}
              </div>
            )}
            {busy && <p className="muted">Yazıyor…</p>}
          </div>
          <form
            onSubmit={(e) => {
              e.preventDefault();
              void ask(input);
            }}
          >
            <label className="sr-only" htmlFor="chat-input">
              Sorunu yaz
            </label>
            <input
              id="chat-input"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Örn. dışa aktarma nerede?"
              maxLength={1000}
              autoComplete="off"
            />
            <button className="btn" type="submit" disabled={busy || !input.trim()}>
              Gönder
            </button>
          </form>
        </section>
      )}
    </>
  );
}
