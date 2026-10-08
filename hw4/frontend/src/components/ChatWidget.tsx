import { FormEvent, useEffect, useRef, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { clearChatHistory, fetchChatHistory, formatPrice, sendChat } from "../api";
import { useAuth } from "../auth";
import { usePageResults } from "../pageResults";
import type { ChatMessage } from "../types";
import RichText from "./RichText";
import { ASK_EVENT } from "../askChat";

const HISTORY_SENT = 12; // earlier turns sent with each message (guests only)

const GREETING: ChatMessage = {
  role: "assistant",
  content: "Hi! I'm the Campus Customs assistant. Ask me about our Yale merch.",
};

// Current page -> context the agent uses to resolve "this" on a product page.
function pageContext(pathname: string) {
  const m = pathname.match(/^\/products\/([^/]+)$/);
  return { path: pathname, product_id: m ? decodeURIComponent(m[1]) : null };
}

export default function ChatWidget() {
  const { user, token } = useAuth();
  const pageResults = usePageResults();
  const [open, setOpen] = useState(false);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([GREETING]);
  const [historyNote, setHistoryNote] = useState("");
  const location = useLocation();
  const endRef = useRef<HTMLDivElement>(null);

  // Log in -> reload this customer's saved chat from the database. Log out -> start fresh as a guest.
  useEffect(() => {
    if (!token || !user) {
      setMessages([GREETING]);
      setHistoryNote("");
      return;
    }
    fetchChatHistory(token)
      .then((saved) => {
        const welcome: ChatMessage = {
          role: "assistant",
          content: saved.length
            ? `Welcome back, ${user.first_name}! Here's our earlier conversation.`
            : `Hi ${user.first_name}! Your chat with us will be saved to your account.`,
        };
        setMessages([
          welcome,
          ...saved.map((m) => ({ role: m.role, content: m.content, products: m.products.slice(0, 3) })),
        ]);
        setHistoryNote(saved.length ? `${saved.length} saved messages` : "");
      })
      .catch(() => setMessages([GREETING]));
  }, [token, user]);

  // "Ask about this item" on a product page opens the chat with a ready-to-send question.
  const inputRef = useRef<HTMLInputElement>(null);
  useEffect(() => {
    function onAsk(e: Event) {
      setOpen(true);
      setInput((e as CustomEvent<string>).detail);
      setTimeout(() => inputRef.current?.focus(), 50);
    }
    window.addEventListener(ASK_EVENT, onAsk);
    return () => window.removeEventListener(ASK_EVENT, onAsk);
  }, []);

  async function onClearHistory() {
    if (!token) return;
    await clearChatHistory(token).catch(() => undefined);
    setMessages([{ role: "assistant", content: "Your saved chat was cleared." }]);
    setHistoryNote("");
  }

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, busy, open]);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    const text = input.trim();
    if (!text || busy) return;
    const history = messages.slice(1).slice(-HISTORY_SENT).map(({ role, content }) => ({ role, content }));
    setMessages((m) => [...m, { role: "user", content: text }]);
    setInput("");
    setBusy(true);
    try {
      const res = await sendChat(text, history, token, pageContext(location.pathname));
      if (res.page_results && res.page_results.products.length > 0) pageResults.show(res.page_results);
      setMessages((m) => [
        // Replace the on-screen copy of the shopper's message with the masked version.
        ...(res.masked_message
          ? m.map((msg, i) => (i === m.length - 1 && msg.role === "user" ? { ...msg, content: res.masked_message! } : msg))
          : m),
        {
          role: "assistant",
          content: res.reply,
          products: res.products,
          tool_events: res.tool_events,
          pageTitle: res.page_results?.products.length ? res.page_results.title : undefined,
          notice: res.safety_notice ?? undefined,
        },
      ]);
    } catch (err) {
      setMessages((m) => [
        ...m,
        {
          role: "assistant",
          content: err instanceof Error ? err.message : "Sorry, I can't reach the shop server right now.",
        },
      ]);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="chat">
      {open && (
        <div className="chat-panel">
          <div className="chat-header">
            <span>Ask the shop counter</span>
            <button onClick={() => setOpen(false)} aria-label="Close chat">×</button>
          </div>
          <div className="chat-sub">
            {user ? (
              <>
                <span>Saved to your account{historyNote ? ` · ${historyNote}` : ""}</span>
                <button className="chat-sub-btn" onClick={onClearHistory}>Clear history</button>
              </>
            ) : (
              <span>Guest chat · <Link to="/login">log in</Link> to save your conversation</span>
            )}
          </div>
          <div className="chat-messages">
            {messages.map((m, i) => (
              <div key={i} className={`msg ${m.role}`}>
                {m.tool_events && m.tool_events.length > 0 && (
                  <div className="tool-chips">
                    {m.tool_events.map((t, j) => (
                      <span key={j} className="tool-chip" title={JSON.stringify(t.args)}>
                        ⚙ {t.tool}
                        {t.duration_ms != null ? ` · ${t.duration_ms} ms` : ""}
                      </span>
                    ))}
                  </div>
                )}
                <div className={`bubble ${m.role}`}>
                  {m.role === "assistant" ? <RichText text={m.content} /> : m.content}
                </div>
                {m.notice && <div className="safety-notice">🔒 {m.notice}</div>}
                {m.pageTitle && (
                  <button className="results-pill" onClick={() => window.scrollTo({ top: 0, behavior: "smooth" })}>
                    ▦ {m.pageTitle} shown on the page
                  </button>
                )}
                {m.products && m.products.length > 0 && (
                  <div className="chat-products">
                    {m.products.map((p) => (
                      <Link key={p.product_id} to={`/products/${p.product_id}`} className="chat-product">
                        <img src={p.image_url} alt={p.name} />
                        <span>{p.name}</span>
                        <strong>{formatPrice(p.price)}</strong>
                      </Link>
                    ))}
                  </div>
                )}
              </div>
            ))}
            {busy && <div className="bubble assistant typing">Thinking…</div>}
            <div ref={endRef} />
          </div>
          <form className="chat-input" onSubmit={onSubmit}>
            <input
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask about hoodies, sizes, prices…"
              maxLength={2000}
            />
            <button type="submit" disabled={busy}>Send</button>
          </form>
        </div>
      )}
      <button className="chat-toggle" onClick={() => setOpen((o) => !o)}>
        {open ? "Close chat" : "Chat with us"}
      </button>
    </div>
  );
}
