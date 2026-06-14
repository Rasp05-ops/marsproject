import { useEffect, useMemo, useRef, useState } from "react";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

const NAV_ITEMS = [
  { id: "home", icon: "ti-home", label: "Home" },
  { id: "library", icon: "ti-books", label: "Library" },
  { id: "cafeteria", icon: "ti-tools-kitchen-2", label: "Cafeteria" },
  { id: "events", icon: "ti-calendar-event", label: "Events" },
  { id: "academics", icon: "ti-school", label: "Academics" },
  { id: "notices", icon: "ti-bell", label: "Notices" },
];

const TAG_COLORS = {
  Tech: { bg: "#1E3A5F", color: "#60A5FA" },
  Fest: { bg: "#3B1F5A", color: "#C084FC" },
  Cultural: { bg: "#1F3D2A", color: "#6EE7A0" },
  Career: { bg: "#3D2A1A", color: "#FDBA74" },
};

const statusColors = {
  available: { bg: "#0F3D28", color: "#4ADE80" },
  borrowed: { bg: "#3D1A10", color: "#FB923C" },
  reserved: { bg: "#1A2A3D", color: "#60A5FA" },
};

async function fetchJSON(path, options) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.detail || `Request failed: ${response.status}`);
  }
  return data;
}

function formatDate(value, fallback = "") {
  if (!value) return fallback;
  const date = new Date(`${value}T00:00:00`);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

function formatFullDate(value) {
  if (!value) return "Campus dashboard";
  const date = new Date(`${value}T00:00:00`);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleDateString("en-US", {
    weekday: "long",
    month: "long",
    day: "numeric",
    year: "numeric",
  });
}

function Panel({ children, style }) {
  return (
    <div style={{ background: "#0D1424", border: "1px solid #1E293B", borderRadius: 12, ...style }}>
      {children}
    </div>
  );
}

function SectionTitle({ children }) {
  return (
    <div style={{ fontSize: 13, fontWeight: 600, color: "#94A3B8", letterSpacing: 0.5, marginBottom: 14, textTransform: "uppercase" }}>
      {children}
    </div>
  );
}

export default function App() {
  const [active, setActive] = useState("home");
  const [aiOpen, setAiOpen] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [provider, setProvider] = useState(localStorage.getItem("llm_provider") || "");
  const [llmStatus, setLlmStatus] = useState({ mode: "unknown", provider: "none" });
  const [lastRoutedTools, setLastRoutedTools] = useState([]);
  const [messages, setMessages] = useState([
    { role: "ai", text: "Hey! I'm connected to the campus backend now. Ask about books, menus, events, attendance, exams, fees, or notices." },
  ]);
  const [input, setInput] = useState("");
  const [typing, setTyping] = useState(false);
  const [menuTab, setMenuTab] = useState("lunch");
  const [libSearch, setLibSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [reservingId, setReservingId] = useState("");
  const [dashboard, setDashboard] = useState(null);
  const [books, setBooks] = useState([]);
  const [libraryStats, setLibraryStats] = useState({ available: 0, borrowed: 0, reserved: 0 });
  const [menus, setMenus] = useState({});
  const [timings, setTimings] = useState({});
  const [events, setEvents] = useState([]);
  const [academics, setAcademics] = useState({ profile: {}, cgpa: 0, average_attendance: 0, courses: [], exams: [] });
  const [notices, setNotices] = useState([]);
  const chatEnd = useRef(null);

  async function loadCampusData() {
    setError("");
    const [dashboardData, booksData, statsData, menuData, eventsData, academicsData, noticesData] = await Promise.all([
      fetchJSON("/api/dashboard"),
      fetchJSON("/api/library/books"),
      fetchJSON("/api/library/stats"),
      fetchJSON("/api/cafeteria/menu"),
      fetchJSON("/api/events"),
      fetchJSON("/api/academics"),
      fetchJSON("/api/notices"),
    ]);
    setDashboard(dashboardData);
    setBooks(booksData);
    setLibraryStats(statsData);
    setMenus(menuData.menus);
    setTimings(menuData.timings);
    setEvents(eventsData);
    setAcademics(academicsData);
    setNotices(noticesData);
  }

  useEffect(() => {
    let alive = true;
    setLoading(true);
    loadCampusData()
      .catch((err) => alive && setError(err.message))
      .finally(() => alive && setLoading(false));
    return () => {
      alive = false;
    };
  }, []);

  useEffect(() => {
    if (chatEnd.current) chatEnd.current.scrollIntoView({ behavior: "smooth" });
  }, [messages, typing]);

  const profile = dashboard?.profile || academics.profile || {};
  const stats = dashboard?.stats || {};
  const courses = academics.courses || [];
  const exams = academics.exams || [];

  const filteredBooks = useMemo(() => {
    const query = libSearch.trim().toLowerCase();
    if (!query) return books;
    return books.filter((book) => book.title.toLowerCase().includes(query) || book.author.toLowerCase().includes(query));
  }, [books, libSearch]);

  async function sendMsg(nextText = input) {
    if (!nextText.trim()) return;
    const userMsg = nextText.trim();
    setMessages((items) => [...items, { role: "user", text: userMsg }]);
    setInput("");
    setTyping(true);
    try {
      const data = await fetchJSON("/api/assistant/query", {
        method: "POST",
        body: JSON.stringify({ message: userMsg, provider: provider || undefined }),
      });
      setLastRoutedTools(data.routed_tools || []);
      setLlmStatus(data.llm_status || { mode: "unknown", provider: provider || "auto" });
      const toolLine = data.routed_tools?.length ? `\n\nSources: ${data.routed_tools.join(", ")}` : "";
      setMessages((items) => [...items, { role: "ai", text: `${data.answer}${toolLine}` }]);
    } catch (err) {
      setMessages((items) => [...items, { role: "ai", text: `I could not reach the backend: ${err.message}` }]);
    } finally {
      setTyping(false);
    }
  }

  async function reserveBook(bookId) {
    setReservingId(bookId);
    try {
      const result = await fetchJSON(`/api/library/books/${bookId}/reserve`, { method: "POST" });
      await loadCampusData();
      setMessages((items) => [...items, { role: "ai", text: result.message }]);
      setAiOpen(true);
    } catch (err) {
      setMessages((items) => [...items, { role: "ai", text: err.message }]);
      setAiOpen(true);
    } finally {
      setReservingId("");
    }
  }

  const headerTitle = {
    home: `Good afternoon, ${profile.name || "Student"}`,
    library: "Library",
    cafeteria: "Cafeteria Menu",
    events: "Campus Events",
    academics: "Academics",
    notices: "Notices & Circulars",
  }[active];

  return (
    <div style={{ display: "flex", height: "100vh", background: "#0A0F1E", color: "#E2E8F0", fontFamily: "'Inter', sans-serif", overflow: "hidden" }}>
      <aside style={{ width: 220, background: "#0D1424", borderRight: "1px solid #1E293B", display: "flex", flexDirection: "column", padding: "24px 0", flexShrink: 0 }}>
        <div style={{ padding: "0 20px 28px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <div style={{ width: 34, height: 34, borderRadius: 10, background: "linear-gradient(135deg, #3B82F6, #8B5CF6)", display: "flex", alignItems: "center", justifyContent: "center" }}>
              <i className="ti ti-cpu" style={{ fontSize: 18, color: "#fff" }} aria-hidden="true" />
            </div>
            <div>
              <div style={{ fontSize: 14, fontWeight: 600, color: "#F1F5F9", letterSpacing: 0.3 }}>CampusIQ</div>
              <div style={{ fontSize: 11, color: "#64748B" }}>{profile.institute || "Campus"}</div>
            </div>
          </div>
        </div>

        <nav style={{ flex: 1 }}>
          {NAV_ITEMS.map((item) => (
            <button key={item.id} onClick={() => setActive(item.id)}
              style={{ display: "flex", alignItems: "center", gap: 12, width: "100%", padding: "10px 20px", border: "none", cursor: "pointer", background: active === item.id ? "#162033" : "transparent", borderLeft: active === item.id ? "3px solid #3B82F6" : "3px solid transparent", color: active === item.id ? "#60A5FA" : "#64748B", fontSize: 14 }}>
              <i className={`ti ${item.icon}`} style={{ fontSize: 18 }} aria-hidden="true" />
              {item.label}
            </button>
          ))}
        </nav>

        <div style={{ padding: "16px 20px", borderTop: "1px solid #1E293B" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <div style={{ width: 32, height: 32, borderRadius: "50%", background: "#1E3A5F", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 13, fontWeight: 600, color: "#60A5FA" }}>{(profile.name || "A")[0]}</div>
            <div>
              <div style={{ fontSize: 13, color: "#CBD5E1" }}>{profile.name || "Student"}</div>
              <div style={{ fontSize: 11, color: "#64748B" }}>{profile.program || "Program"} - {profile.semester || "Semester"}</div>
            </div>
          </div>
        </div>
      </aside>

      <main style={{ flex: 1, overflow: "auto", padding: "28px 32px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 28 }}>
          <div>
            <h1 style={{ margin: 0, fontSize: 22, fontWeight: 600, color: "#F1F5F9" }}>{headerTitle}</h1>
            <p style={{ margin: "4px 0 0", fontSize: 13, color: "#64748B" }}>{formatFullDate(profile.today)}</p>
          </div>
          <div style={{ display: "flex", gap: 10 }}>
            <button onClick={() => loadCampusData().catch((err) => setError(err.message))}
              style={{ display: "flex", alignItems: "center", gap: 8, padding: "9px 12px", borderRadius: 10, border: "1px solid #1E293B", background: "#0A0F1E", color: "#94A3B8", fontSize: 13, cursor: "pointer" }}>
              <i className="ti ti-refresh" style={{ fontSize: 16 }} aria-hidden="true" />
              Refresh
            </button>
            <button onClick={() => setAiOpen((open) => !open)}
              style={{ display: "flex", alignItems: "center", gap: 8, padding: "9px 16px", borderRadius: 10, border: "1px solid #3B82F6", background: aiOpen ? "#1E3A5F" : "#0A0F1E", color: "#60A5FA", fontSize: 13, cursor: "pointer" }}>
              <i className="ti ti-sparkles" style={{ fontSize: 16 }} aria-hidden="true" />
              AI Assistant
            </button>
            <button onClick={() => setShowSettings((s) => !s)}
              title="LLM settings"
              style={{ display: "flex", alignItems: "center", gap: 8, padding: "9px 10px", borderRadius: 10, border: "1px solid #1E293B", background: showSettings ? "#111827" : "#0A0F1E", color: "#94A3B8", fontSize: 13, cursor: "pointer" }}>
              <i className="ti ti-settings" style={{ fontSize: 16 }} aria-hidden="true" />
            </button>
          </div>
        </div>

        {showSettings && (
          <Panel style={{ padding: 12, marginBottom: 12 }}>
            <div style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 8 }}>
              <label style={{ fontSize: 12, color: "#94A3B8", minWidth: 80 }}>Provider</label>
              <select value={provider} onChange={(e) => setProvider(e.target.value)} style={{ flex: 1, padding: 8, borderRadius: 8, background: "#0D1424", border: "1px solid #1E293B", color: "#E2E8F0" }}>
                <option value="">Auto (prefer Google)</option>
                <option value="google">Google (Gemini)</option>
                <option value="openai">OpenAI</option>
              </select>
            </div>
            <div style={{ display: "flex", gap: 8, justifyContent: "flex-end" }}>
              <button onClick={() => { setProvider(""); localStorage.removeItem("llm_provider"); }}
                style={{ padding: "8px 10px", borderRadius: 8, border: "1px solid #1E293B", background: "transparent", color: "#64748B" }}>Clear</button>
              <button onClick={() => { localStorage.setItem("llm_provider", provider); setShowSettings(false); }}
                style={{ padding: "8px 10px", borderRadius: 8, border: "none", background: "#3B82F6", color: "#fff" }}>Save</button>
            </div>
          </Panel>
        )}

        {loading && <Panel style={{ padding: 18, color: "#94A3B8" }}>Loading campus data from backend...</Panel>}
        {error && <Panel style={{ padding: 18, borderColor: "#7F1D1D", color: "#FCA5A5" }}>Backend error: {error}. Make sure FastAPI is running on {API_BASE}.</Panel>}

        {!loading && active === "home" && (
          <div>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))", gap: 12, marginBottom: 28 }}>
              {[
                { label: "Books Borrowed", value: stats.books_borrowed ?? libraryStats.borrowed, icon: "ti-books", color: "#3B82F6" },
                { label: "Events This Week", value: stats.events_this_week ?? events.length, icon: "ti-calendar-event", color: "#8B5CF6" },
                { label: "Avg Attendance", value: `${stats.average_attendance ?? academics.average_attendance}%`, icon: "ti-chart-bar", color: "#10B981" },
                { label: "Pending Notices", value: stats.pending_notices ?? notices.filter((notice) => notice.urgent).length, icon: "ti-bell", color: "#F59E0B" },
              ].map((card) => (
                <Panel key={card.label} style={{ padding: "16px 18px" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 10 }}>
                    <span style={{ fontSize: 12, color: "#64748B" }}>{card.label}</span>
                    <i className={`ti ${card.icon}`} style={{ fontSize: 18, color: card.color }} aria-hidden="true" />
                  </div>
                  <div style={{ fontSize: 26, fontWeight: 600, color: "#F1F5F9" }}>{card.value}</div>
                </Panel>
              ))}
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20 }}>
              <Panel style={{ padding: "18px 20px" }}>
                <SectionTitle>Upcoming Events</SectionTitle>
                {events.slice(0, 3).map((event) => (
                  <div key={event.id} style={{ display: "flex", gap: 12, marginBottom: 14 }}>
                    <div style={{ width: 42, height: 42, borderRadius: 8, background: "#131929", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
                      <span style={{ fontSize: 14, fontWeight: 700, color: "#60A5FA" }}>{formatDate(event.date).split(" ")[1]}</span>
                      <span style={{ fontSize: 10, color: "#64748B" }}>{formatDate(event.date).split(" ")[0]}</span>
                    </div>
                    <div>
                      <div style={{ fontSize: 13, color: "#E2E8F0", fontWeight: 500 }}>{event.name}</div>
                      <div style={{ fontSize: 12, color: "#64748B" }}>{event.time} - {event.venue}</div>
                    </div>
                  </div>
                ))}
                <button onClick={() => setActive("events")} style={{ fontSize: 12, color: "#3B82F6", background: "none", border: "none", cursor: "pointer", padding: 0 }}>View all events</button>
              </Panel>

              <Panel style={{ padding: "18px 20px" }}>
                <SectionTitle>Today's Lunch</SectionTitle>
                {(menus.lunch || []).map((item) => (
                  <div key={item} style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8 }}>
                    <div style={{ width: 6, height: 6, borderRadius: "50%", background: "#10B981", flexShrink: 0 }} />
                    <span style={{ fontSize: 13, color: "#CBD5E1" }}>{item}</span>
                  </div>
                ))}
                <button onClick={() => setActive("cafeteria")} style={{ fontSize: 12, color: "#3B82F6", background: "none", border: "none", cursor: "pointer", padding: "8px 0 0" }}>Full menu</button>
              </Panel>

              <Panel style={{ padding: "18px 20px" }}>
                <SectionTitle>Attendance</SectionTitle>
                {courses.map((course) => (
                  <div key={course.code} style={{ marginBottom: 10 }}>
                    <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                      <span style={{ fontSize: 12, color: "#CBD5E1" }}>{course.name}</span>
                      <span style={{ fontSize: 12, color: course.attendance < 75 ? "#F87171" : "#4ADE80" }}>{course.attendance}%</span>
                    </div>
                    <div style={{ height: 4, background: "#1E293B", borderRadius: 4 }}>
                      <div style={{ height: 4, borderRadius: 4, width: `${course.attendance}%`, background: course.attendance < 75 ? "#EF4444" : course.attendance >= 85 ? "#10B981" : "#3B82F6" }} />
                    </div>
                  </div>
                ))}
              </Panel>

              <Panel style={{ padding: "18px 20px" }}>
                <SectionTitle>Recent Notices</SectionTitle>
                {notices.slice(0, 4).map((notice) => (
                  <div key={notice.id} style={{ display: "flex", gap: 10, marginBottom: 12, alignItems: "flex-start" }}>
                    <span style={{ fontSize: 10, background: notice.urgent ? "#3D1A10" : "#131929", color: notice.urgent ? "#FB923C" : "#64748B", padding: "2px 7px", borderRadius: 4, marginTop: 1, flexShrink: 0 }}>{notice.urgent ? "URGENT" : "INFO"}</span>
                    <div>
                      <div style={{ fontSize: 12, color: "#E2E8F0" }}>{notice.title}</div>
                      <div style={{ fontSize: 11, color: "#64748B" }}>{notice.from}</div>
                    </div>
                  </div>
                ))}
              </Panel>
            </div>
          </div>
        )}

        {!loading && active === "library" && (
          <div>
            <div style={{ display: "flex", gap: 12, marginBottom: 20 }}>
              {[
                { label: "Available", count: libraryStats.available, color: "#4ADE80" },
                { label: "Borrowed by You", count: libraryStats.borrowed, color: "#FB923C" },
                { label: "Reserved", count: libraryStats.reserved, color: "#60A5FA" },
              ].map((item) => (
                <Panel key={item.label} style={{ padding: "12px 18px", flex: 1 }}>
                  <div style={{ fontSize: 22, fontWeight: 700, color: item.color }}>{item.count}</div>
                  <div style={{ fontSize: 12, color: "#64748B" }}>{item.label}</div>
                </Panel>
              ))}
            </div>
            <div style={{ position: "relative", marginBottom: 20 }}>
              <i className="ti ti-search" style={{ position: "absolute", left: 12, top: "50%", transform: "translateY(-50%)", color: "#64748B", fontSize: 16 }} aria-hidden="true" />
              <input value={libSearch} onChange={(event) => setLibSearch(event.target.value)} placeholder="Search by title or author..."
                style={{ width: "100%", padding: "10px 12px 10px 38px", background: "#0D1424", border: "1px solid #1E293B", borderRadius: 8, color: "#E2E8F0", fontSize: 13, outline: "none" }} />
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))", gap: 14 }}>
              {filteredBooks.map((book) => {
                const colors = statusColors[book.status] || statusColors.reserved;
                return (
                  <Panel key={book.id} style={{ padding: "16px 18px" }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 10 }}>
                      <div>
                        <div style={{ fontSize: 14, fontWeight: 500, color: "#F1F5F9", marginBottom: 4 }}>{book.title}</div>
                        <div style={{ fontSize: 12, color: "#64748B" }}>{book.author}</div>
                      </div>
                      <span style={{ fontSize: 11, padding: "3px 9px", borderRadius: 6, background: colors.bg, color: colors.color, flexShrink: 0, whiteSpace: "nowrap" }}>{book.status}</span>
                    </div>
                    {book.due && <div style={{ fontSize: 11, color: "#F87171", marginTop: 10 }}>Due: {formatDate(book.due, book.due)}</div>}
                    {book.status === "available" && (
                      <button onClick={() => reserveBook(book.id)} disabled={reservingId === book.id}
                        style={{ marginTop: 12, width: "100%", padding: "7px", borderRadius: 7, border: "1px solid #1E3A5F", background: "transparent", color: "#60A5FA", fontSize: 12, cursor: "pointer" }}>
                        {reservingId === book.id ? "Reserving..." : "Reserve Book"}
                      </button>
                    )}
                  </Panel>
                );
              })}
            </div>
          </div>
        )}

        {!loading && active === "cafeteria" && (
          <div>
            <div style={{ display: "flex", gap: 8, marginBottom: 24, flexWrap: "wrap" }}>
              {Object.keys(menus).map((tab) => (
                <button key={tab} onClick={() => setMenuTab(tab)}
                  style={{ padding: "8px 18px", borderRadius: 8, border: "1px solid", borderColor: menuTab === tab ? "#3B82F6" : "#1E293B", background: menuTab === tab ? "#1E3A5F" : "transparent", color: menuTab === tab ? "#60A5FA" : "#64748B", fontSize: 13, cursor: "pointer", textTransform: "capitalize" }}>
                  {tab}
                </button>
              ))}
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(220px, 1fr))", gap: 14 }}>
              {(menus[menuTab] || []).map((item, index) => (
                <Panel key={item} style={{ padding: "18px 20px", display: "flex", alignItems: "center", gap: 14 }}>
                  <div style={{ width: 40, height: 40, borderRadius: 10, background: "#131929", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
                    <i className="ti ti-bowl" style={{ fontSize: 20, color: "#F59E0B" }} aria-hidden="true" />
                  </div>
                  <div>
                    <div style={{ fontSize: 14, fontWeight: 500, color: "#E2E8F0" }}>{item}</div>
                    <div style={{ fontSize: 11, color: "#64748B" }}>Item {index + 1}</div>
                  </div>
                </Panel>
              ))}
            </div>
            <Panel style={{ marginTop: 24, padding: "16px 20px" }}>
              <SectionTitle>Timings</SectionTitle>
              {Object.entries(timings).map(([meal, time]) => (
                <div key={meal} style={{ display: "flex", justifyContent: "space-between", padding: "8px 0", borderBottom: "1px solid #131929" }}>
                  <span style={{ fontSize: 13, color: "#CBD5E1", textTransform: "capitalize" }}>{meal}</span>
                  <span style={{ fontSize: 13, color: "#64748B" }}>{time}</span>
                </div>
              ))}
            </Panel>
          </div>
        )}

        {!loading && active === "events" && (
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))", gap: 16 }}>
            {events.map((event) => {
              const tag = TAG_COLORS[event.tag] || TAG_COLORS.Tech;
              return (
                <Panel key={event.id} style={{ padding: "18px 20px" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 12 }}>
                    <span style={{ fontSize: 11, padding: "3px 9px", borderRadius: 5, background: tag.bg, color: tag.color }}>{event.tag}</span>
                    <span style={{ fontSize: 12, color: "#64748B" }}>{formatDate(event.date)}</span>
                  </div>
                  <div style={{ fontSize: 15, fontWeight: 600, color: "#F1F5F9", marginBottom: 6 }}>{event.name}</div>
                  <div style={{ fontSize: 12, color: "#64748B", marginBottom: 4 }}>by {event.org}</div>
                  <div style={{ display: "flex", gap: 16, marginTop: 12 }}>
                    <span style={{ fontSize: 12, color: "#94A3B8", display: "flex", alignItems: "center", gap: 4 }}><i className="ti ti-clock" style={{ fontSize: 14 }} aria-hidden="true" />{event.time}</span>
                    <span style={{ fontSize: 12, color: "#94A3B8", display: "flex", alignItems: "center", gap: 4 }}><i className="ti ti-map-pin" style={{ fontSize: 14 }} aria-hidden="true" />{event.venue}</span>
                  </div>
                </Panel>
              );
            })}
          </div>
        )}

        {!loading && active === "academics" && (
          <div>
            <Panel style={{ overflow: "hidden", marginBottom: 20 }}>
              <div style={{ padding: "16px 20px", borderBottom: "1px solid #1E293B" }}>
                <SectionTitle>Current Semester Courses</SectionTitle>
              </div>
              <table style={{ width: "100%", borderCollapse: "collapse" }}>
                <thead>
                  <tr style={{ background: "#0A0F1E" }}>
                    {["Code", "Course", "Professor", "Attendance", "Grade"].map((heading) => (
                      <th key={heading} style={{ padding: "10px 20px", textAlign: "left", fontSize: 11, color: "#64748B", fontWeight: 500, letterSpacing: 0.5, textTransform: "uppercase" }}>{heading}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {courses.map((course) => (
                    <tr key={course.code} style={{ borderTop: "1px solid #131929" }}>
                      <td style={{ padding: "14px 20px", fontSize: 12, color: "#60A5FA", fontFamily: "monospace" }}>{course.code}</td>
                      <td style={{ padding: "14px 20px", fontSize: 13, color: "#E2E8F0", fontWeight: 500 }}>{course.name}</td>
                      <td style={{ padding: "14px 20px", fontSize: 12, color: "#64748B" }}>{course.prof}</td>
                      <td style={{ padding: "14px 20px" }}>
                        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                          <div style={{ flex: 1, height: 6, background: "#1E293B", borderRadius: 4 }}>
                            <div style={{ height: 6, borderRadius: 4, width: `${course.attendance}%`, background: course.attendance < 75 ? "#EF4444" : course.attendance >= 85 ? "#10B981" : "#3B82F6" }} />
                          </div>
                          <span style={{ fontSize: 12, color: course.attendance < 75 ? "#F87171" : "#94A3B8", minWidth: 32 }}>{course.attendance}%</span>
                        </div>
                      </td>
                      <td style={{ padding: "14px 20px" }}>
                        <span style={{ fontSize: 12, padding: "3px 10px", borderRadius: 5, background: course.grade.startsWith("A") ? "#0F3D28" : "#1E293B", color: course.grade.startsWith("A") ? "#4ADE80" : "#94A3B8" }}>{course.grade}</span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </Panel>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
              <Panel style={{ padding: "16px 20px" }}>
                <SectionTitle>CGPA Summary</SectionTitle>
                <div style={{ fontSize: 36, fontWeight: 700, color: "#F1F5F9" }}>{academics.cgpa}</div>
                <div style={{ fontSize: 12, color: "#64748B" }}>out of 10 - {profile.semester}</div>
              </Panel>
              <Panel style={{ padding: "16px 20px" }}>
                <SectionTitle>Exam Schedule</SectionTitle>
                {exams.map((exam) => (
                  <div key={`${exam.course_code}-${exam.date}`} style={{ fontSize: 12, color: "#CBD5E1", marginBottom: 7 }}>
                    <span style={{ color: "#60A5FA" }}>{exam.course_code}</span> {exam.course}: {formatDate(exam.date)} at {exam.time}
                  </div>
                ))}
              </Panel>
            </div>
          </div>
        )}

        {!loading && active === "notices" && (
          <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
            {notices.map((notice) => (
              <Panel key={notice.id} style={{ borderColor: notice.urgent ? "#3D1A10" : "#1E293B", borderLeft: `4px solid ${notice.urgent ? "#F97316" : "#1E293B"}`, padding: "16px 20px" }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 14 }}>
                  <div>
                    <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 6 }}>
                      {notice.urgent && <span style={{ fontSize: 10, background: "#3D1A10", color: "#FB923C", padding: "2px 8px", borderRadius: 4 }}>URGENT</span>}
                      <span style={{ fontSize: 14, fontWeight: 500, color: "#F1F5F9" }}>{notice.title}</span>
                    </div>
                    <div style={{ fontSize: 12, color: "#64748B" }}>Issued by: {notice.from}</div>
                  </div>
                  <span style={{ fontSize: 12, color: "#64748B", flexShrink: 0 }}>{formatDate(notice.date)}</span>
                </div>
              </Panel>
            ))}
          </div>
        )}
      </main>

      {aiOpen && (
        <aside style={{ width: 360, background: "#0D1424", borderLeft: "1px solid #1E293B", display: "flex", flexDirection: "column", flexShrink: 0 }}>
          <div style={{ padding: "18px 20px", borderBottom: "1px solid #1E293B", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
              <div style={{ width: 30, height: 30, borderRadius: "50%", background: "#1E3A5F", display: "flex", alignItems: "center", justifyContent: "center" }}>
                <i className="ti ti-sparkles" style={{ fontSize: 15, color: "#60A5FA" }} aria-hidden="true" />
              </div>
              <div>
                <div style={{ fontSize: 13, fontWeight: 600, color: "#F1F5F9" }}>Campus AI</div>
                <div
                  title={llmStatus?.reason || llmStatus?.last_error || ""}
                  style={{ fontSize: 10, color: error ? "#F87171" : llmStatus?.mode === "llm" ? "#22C55E" : "#F59E0B" }}
                >
                  {error ? "Backend offline" : llmStatus?.mode === "llm" ? `LLM: ${llmStatus.provider}` : "LLM fallback"}
                </div>
              </div>
            </div>
            <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
              <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
                {lastRoutedTools?.length > 0 && (
                  <div style={{ display: "flex", gap: 6, alignItems: "center", marginRight: 6 }}>
                    {lastRoutedTools.map((t) => (
                      <span key={t} style={{ fontSize: 11, padding: "4px 8px", borderRadius: 999, background: "#131929", color: "#94A3B8", border: "1px solid #1E293B" }}>{t}</span>
                    ))}
                  </div>
                )}
              </div>
              <button onClick={() => setAiOpen(false)} style={{ background: "none", border: "none", color: "#64748B", cursor: "pointer", padding: 4 }}>
                <i className="ti ti-x" style={{ fontSize: 18 }} aria-hidden="true" />
              </button>
            </div>
          </div>

          <div style={{ flex: 1, overflowY: "auto", padding: "16px 16px 8px" }}>
            {messages.map((msg, index) => (
              <div key={`${msg.role}-${index}`} style={{ display: "flex", justifyContent: msg.role === "user" ? "flex-end" : "flex-start", marginBottom: 12 }}>
                <div style={{ maxWidth: "88%", whiteSpace: "pre-wrap", padding: "9px 13px", borderRadius: msg.role === "user" ? "12px 12px 2px 12px" : "12px 12px 12px 2px", background: msg.role === "user" ? "#1E3A5F" : "#131929", color: msg.role === "user" ? "#93C5FD" : "#CBD5E1", fontSize: 13, lineHeight: 1.5 }}>
                  {msg.text}
                </div>
              </div>
            ))}
            {typing && (
              <div style={{ display: "flex", gap: 4, padding: "12px 14px", width: 56, background: "#131929", borderRadius: "12px 12px 12px 2px" }}>
                {[0, 1, 2].map((dot) => (
                  <div key={dot} style={{ width: 6, height: 6, borderRadius: "50%", background: "#475569", animation: `bounce 1.2s ${dot * 0.2}s infinite` }} />
                ))}
              </div>
            )}
            <div ref={chatEnd} />
          </div>

          <div style={{ padding: "12px 16px 16px", borderTop: "1px solid #1E293B" }}>
            <div style={{ display: "flex", gap: 8, marginBottom: 10, flexWrap: "wrap" }}>
              {["Today's menu?", "My attendance", "Events this week"].map((question) => (
                <button key={question} onClick={() => sendMsg(question)}
                  style={{ fontSize: 11, padding: "4px 10px", borderRadius: 6, border: "1px solid #1E293B", background: "transparent", color: "#64748B", cursor: "pointer" }}>
                  {question}
                </button>
              ))}
            </div>
            <div style={{ display: "flex", gap: 8 }}>
              <input value={input} onChange={(event) => setInput(event.target.value)} onKeyDown={(event) => event.key === "Enter" && sendMsg()}
                placeholder="Ask anything about campus..."
                style={{ flex: 1, padding: "9px 12px", background: "#131929", border: "1px solid #1E293B", borderRadius: 8, color: "#E2E8F0", fontSize: 13, outline: "none" }} />
              <button onClick={() => sendMsg()} disabled={typing}
                style={{ padding: "9px 12px", borderRadius: 8, border: "none", background: "#3B82F6", color: "#fff", cursor: "pointer", fontSize: 14, display: "flex", alignItems: "center" }}>
                <i className="ti ti-send" style={{ fontSize: 16 }} aria-hidden="true" />
              </button>
            </div>
          </div>
        </aside>
      )}

      <style>{`
        @keyframes bounce {
          0%, 60%, 100% { transform: translateY(0); }
          30% { transform: translateY(-5px); }
        }
        ::-webkit-scrollbar { width: 4px; height: 4px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: #1E293B; border-radius: 4px; }
      `}</style>
    </div>
  );
}
