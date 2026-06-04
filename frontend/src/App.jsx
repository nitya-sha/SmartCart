import { useState, useEffect, useCallback } from "react";
import {
  AreaChart, Area, BarChart, Bar, XAxis, YAxis,
  CartesianGrid, Tooltip, ResponsiveContainer, Cell
} from "recharts";

const API = "http://localhost:8000/api/v1";

const fmt = (n) => new Intl.NumberFormat("en-IN", { maximumFractionDigits: 0 }).format(n);
const fmtR = (n) => `R$ ${fmt(n)}`;

/* ── Colour palette ─────────────────────────────────────────── */
const C = {
  bg:      "#0A0E1A",
  panel:   "#111827",
  border:  "#1F2937",
  accent:  "#00D4AA",
  accent2: "#FF6B6B",
  accent3: "#FFD93D",
  text:    "#F9FAFB",
  muted:   "#6B7280",
  chart:   ["#00D4AA","#00B894","#00A381","#008F6F","#007A5C"],
};

/* ── Tiny components ────────────────────────────────────────── */
function Loader() {
  return (
    <div style={{ display:"flex", alignItems:"center", gap:8, color:C.muted, fontSize:13 }}>
      <span style={{ display:"inline-block", width:16, height:16, border:`2px solid ${C.accent}`,
        borderTopColor:"transparent", borderRadius:"50%",
        animation:"spin 0.8s linear infinite" }} />
      Loading…
    </div>
  );
}

function KPICard({ label, value, sub, color = C.accent }) {
  return (
    <div style={{ background:C.panel, border:`1px solid ${C.border}`, borderRadius:16,
      padding:"24px 28px", display:"flex", flexDirection:"column", gap:6,
      borderTop:`3px solid ${color}` }}>
      <p style={{ color:C.muted, fontSize:12, fontFamily:"'DM Mono',monospace",
        letterSpacing:"0.08em", textTransform:"uppercase", margin:0 }}>{label}</p>
      <p style={{ color:C.text, fontSize:28, fontWeight:700, margin:0,
        fontFamily:"'Syne',sans-serif" }}>{value}</p>
      {sub && <p style={{ color:C.muted, fontSize:12, margin:0 }}>{sub}</p>}
    </div>
  );
}

const CustomTooltip = ({ active, payload, label, prefix="" }) => {
  if (!active || !payload?.length) return null;
  return (
    <div style={{ background:C.panel, border:`1px solid ${C.border}`, borderRadius:10,
      padding:"10px 16px", fontSize:13 }}>
      <p style={{ color:C.muted, margin:"0 0 4px" }}>{label}</p>
      {payload.map((p, i) => (
        <p key={i} style={{ color:p.color || C.accent, margin:0, fontWeight:600 }}>
          {prefix}{fmt(p.value)}
        </p>
      ))}
    </div>
  );
};

/* ── Section wrapper ────────────────────────────────────────── */
function Section({ title, children, action }) {
  return (
    <div style={{ background:C.panel, border:`1px solid ${C.border}`, borderRadius:16,
      padding:28, marginBottom:24 }}>
      <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center",
        marginBottom:20 }}>
        <h2 style={{ color:C.text, fontSize:16, fontWeight:600, margin:0,
          fontFamily:"'Syne',sans-serif" }}>{title}</h2>
        {action}
      </div>
      {children}
    </div>
  );
}

/* ── Main App ───────────────────────────────────────────────── */
export default function SmartCart() {
  const [tab, setTab]           = useState("overview");
  const [kpi, setKpi]           = useState(null);
  const [trend, setTrend]       = useState([]);
  const [cats, setCats]         = useState([]);
  const [forecast, setForecast] = useState([]);
  const [delivery, setDelivery] = useState(null);
  const [customerId, setCustomerId] = useState("");
  const [recs, setRecs]         = useState([]);
  const [recsLoading, setRecsLoading] = useState(false);
  const [loading, setLoading]   = useState(true);

  /* fetch overview data */
  useEffect(() => {
    Promise.all([
      fetch(`${API}/orders/summary`).then(r => r.json()),
      fetch(`${API}/orders/monthly-trend`).then(r => r.json()),
      fetch(`${API}/orders/revenue-by-category?limit=10`).then(r => r.json()),
      fetch(`${API}/orders/delivery-performance`).then(r => r.json()),
      fetch(`${API}/ml/forecast?days=30`).then(r => r.json()).catch(() => []),
    ]).then(([k, t, c, d, f]) => {
      setKpi(k);
      setTrend(t.map(x => ({ ...x, revenue: Math.round(x.revenue) })));
      setCats(c.map(x => ({ ...x, category: x.category.replace(/_/g," ") })));
      setDelivery(d);
      setForecast(f.map ? f.map(x => ({ ...x, revenue: Math.round(x.revenue) })) : []);
      setLoading(false);
    });
  }, []);

  const fetchRecs = useCallback(() => {
    if (!customerId.trim()) return;
    setRecsLoading(true);
    fetch(`${API}/ml/recommend/${customerId.trim()}`)
      .then(r => r.json())
      .then(data => { setRecs(Array.isArray(data) ? data : []); setRecsLoading(false); })
      .catch(() => setRecsLoading(false));
  }, [customerId]);

  /* ── Tabs ── */
  const tabs = [
    { id:"overview",     label:"Overview"     },
    { id:"forecast",     label:"Forecast"     },
    { id:"categories",   label:"Categories"   },
    { id:"recommender",  label:"Recommender"  },
  ];

  return (
    <>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Mono:wght@400;500&family=DM+Sans:wght@400;500;600&display=swap');
        *, *::before, *::after { box-sizing:border-box; margin:0; padding:0; }
        body { background:${C.bg}; color:${C.text}; font-family:'DM Sans',sans-serif; }
        @keyframes spin { to { transform:rotate(360deg); } }
        @keyframes fadeUp { from { opacity:0; transform:translateY(16px); } to { opacity:1; transform:none; } }
        .fadein { animation: fadeUp 0.5s ease both; }
        input:focus { outline:none; }
        ::-webkit-scrollbar { width:6px; }
        ::-webkit-scrollbar-track { background:${C.bg}; }
        ::-webkit-scrollbar-thumb { background:${C.border}; border-radius:3px; }
      `}</style>

      <div style={{ minHeight:"100vh", background:C.bg }}>

        {/* ── Header ── */}
        <header style={{ borderBottom:`1px solid ${C.border}`, padding:"0 32px",
          display:"flex", alignItems:"center", justifyContent:"space-between", height:64,
          position:"sticky", top:0, background:C.bg, zIndex:100 }}>
          <div style={{ display:"flex", alignItems:"center", gap:12 }}>
            <div style={{ width:32, height:32, borderRadius:8, background:C.accent,
              display:"flex", alignItems:"center", justifyContent:"center",
              fontSize:16 }}>🛒</div>
            <span style={{ fontFamily:"'Syne',sans-serif", fontWeight:800,
              fontSize:18, color:C.text }}>SmartCart</span>
            <span style={{ background:`${C.accent}22`, color:C.accent, fontSize:11,
              padding:"2px 8px", borderRadius:20, fontFamily:"'DM Mono',monospace" }}>
              ANALYTICS
            </span>
          </div>
          <div style={{ display:"flex", gap:4 }}>
            {tabs.map(t => (
              <button key={t.id} onClick={() => setTab(t.id)} style={{
                background: tab===t.id ? `${C.accent}22` : "transparent",
                color: tab===t.id ? C.accent : C.muted,
                border: tab===t.id ? `1px solid ${C.accent}44` : "1px solid transparent",
                borderRadius:8, padding:"6px 16px", cursor:"pointer", fontSize:13,
                fontFamily:"'DM Sans',sans-serif", fontWeight:500,
                transition:"all 0.2s",
              }}>{t.label}</button>
            ))}
          </div>
        </header>

        <main style={{ maxWidth:1200, margin:"0 auto", padding:"32px 24px" }}>

          {loading ? (
            <div style={{ display:"flex", justifyContent:"center", paddingTop:80 }}>
              <Loader />
            </div>
          ) : (
            <>
              {/* ── OVERVIEW TAB ── */}
              {tab === "overview" && (
                <div className="fadein">
                  {/* KPI cards */}
                  <div style={{ display:"grid", gridTemplateColumns:"repeat(3,1fr)",
                    gap:16, marginBottom:24 }}>
                    <KPICard label="Total Revenue"    value={fmtR(kpi.total_revenue)}
                      sub={`${fmt(kpi.total_orders)} delivered orders`} color={C.accent} />
                    <KPICard label="Avg Order Value"  value={fmtR(kpi.avg_order_value)}
                      sub={`${fmt(kpi.total_customers)} unique customers`} color={C.accent3} />
                    <KPICard label="Avg Review Score" value={`${kpi.avg_review_score} / 5`}
                      sub={`Across ${fmt(kpi.total_sellers)} sellers`} color={C.accent2} />
                  </div>

                  {/* Delivery performance */}
                  {delivery && (
                    <div style={{ display:"grid", gridTemplateColumns:"repeat(3,1fr)",
                      gap:16, marginBottom:24 }}>
                      <KPICard label="Avg Delivery Time"
                        value={`${delivery.avg_delivery_days} days`}
                        sub="From purchase to door" color={C.accent} />
                      <KPICard label="Late Deliveries"
                        value={`${delivery.late_delivery_pct}%`}
                        sub="Past estimated date" color={C.accent2} />
                      <KPICard label="Delivered Orders"
                        value={fmt(delivery.delivered_count)}
                        sub="Successfully completed" color={C.accent3} />
                    </div>
                  )}

                  {/* Monthly trend */}
                  <Section title="Monthly Revenue Trend">
                    <ResponsiveContainer width="100%" height={260}>
                      <AreaChart data={trend}>
                        <defs>
                          <linearGradient id="g1" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%"  stopColor={C.accent} stopOpacity={0.3} />
                            <stop offset="95%" stopColor={C.accent} stopOpacity={0}   />
                          </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" stroke={C.border} />
                        <XAxis dataKey="month" tick={{ fill:C.muted, fontSize:11 }}
                          tickLine={false} axisLine={false} />
                        <YAxis tick={{ fill:C.muted, fontSize:11 }} tickLine={false}
                          axisLine={false} tickFormatter={v => `R$${(v/1000).toFixed(0)}k`} />
                        <Tooltip content={<CustomTooltip prefix="R$ " />} />
                        <Area type="monotone" dataKey="revenue" stroke={C.accent}
                          strokeWidth={2} fill="url(#g1)" dot={false} />
                      </AreaChart>
                    </ResponsiveContainer>
                  </Section>
                </div>
              )}

              {/* ── FORECAST TAB ── */}
              {tab === "forecast" && (
                <div className="fadein">
                  <div style={{ marginBottom:24 }}>
                    <h1 style={{ fontFamily:"'Syne',sans-serif", fontSize:24,
                      fontWeight:800, color:C.text }}>30-Day Revenue Forecast</h1>
                    <p style={{ color:C.muted, fontSize:14, marginTop:4 }}>
                      XGBoost model trained on historical daily sales data
                    </p>
                  </div>

                  {forecast.length === 0 ? (
                    <div style={{ color:C.muted, padding:40, textAlign:"center" }}>
                      No forecast data. Make sure the forecaster model is trained.
                    </div>
                  ) : (
                    <>
                      {/* Summary cards */}
                      <div style={{ display:"grid", gridTemplateColumns:"repeat(3,1fr)",
                        gap:16, marginBottom:24 }}>
                        <KPICard label="Total Forecast Revenue"
                          value={fmtR(forecast.reduce((a,b) => a+b.revenue, 0))}
                          sub="Next 30 days" color={C.accent} />
                        <KPICard label="Peak Day Revenue"
                          value={fmtR(Math.max(...forecast.map(f => f.revenue)))}
                          sub={forecast.find(f => f.revenue === Math.max(...forecast.map(x => x.revenue)))?.date}
                          color={C.accent3} />
                        <KPICard label="Avg Daily Revenue"
                          value={fmtR(forecast.reduce((a,b) => a+b.revenue,0) / forecast.length)}
                          sub="Predicted average" color={C.accent2} />
                      </div>

                      <Section title="Daily Revenue Forecast — Next 30 Days">
                        <ResponsiveContainer width="100%" height={300}>
                          <AreaChart data={forecast}>
                            <defs>
                              <linearGradient id="g2" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%"  stopColor={C.accent3} stopOpacity={0.3} />
                                <stop offset="95%" stopColor={C.accent3} stopOpacity={0}   />
                              </linearGradient>
                            </defs>
                            <CartesianGrid strokeDasharray="3 3" stroke={C.border} />
                            <XAxis dataKey="date" tick={{ fill:C.muted, fontSize:10 }}
                              tickLine={false} axisLine={false}
                              tickFormatter={v => v.slice(5)} />
                            <YAxis tick={{ fill:C.muted, fontSize:11 }} tickLine={false}
                              axisLine={false}
                              tickFormatter={v => `R$${(v/1000).toFixed(0)}k`} />
                            <Tooltip content={<CustomTooltip prefix="R$ " />} />
                            <Area type="monotone" dataKey="revenue" stroke={C.accent3}
                              strokeWidth={2} fill="url(#g2)" dot={false} />
                          </AreaChart>
                        </ResponsiveContainer>
                      </Section>

                      {/* Forecast table */}
                      <Section title="Day-by-Day Forecast">
                        <div style={{ display:"grid", gridTemplateColumns:"repeat(5,1fr)", gap:8 }}>
                          {forecast.map((f, i) => (
                            <div key={i} style={{ background:C.bg, borderRadius:10,
                              padding:"12px 14px", border:`1px solid ${C.border}` }}>
                              <p style={{ color:C.muted, fontSize:11,
                                fontFamily:"'DM Mono',monospace", margin:"0 0 4px" }}>
                                {f.date.slice(5)}
                              </p>
                              <p style={{ color:C.accent3, fontSize:15,
                                fontWeight:600, margin:0 }}>
                                {fmtR(f.revenue)}
                              </p>
                            </div>
                          ))}
                        </div>
                      </Section>
                    </>
                  )}
                </div>
              )}

              {/* ── CATEGORIES TAB ── */}
              {tab === "categories" && (
                <div className="fadein">
                  <div style={{ marginBottom:24 }}>
                    <h1 style={{ fontFamily:"'Syne',sans-serif", fontSize:24,
                      fontWeight:800, color:C.text }}>Revenue by Category</h1>
                    <p style={{ color:C.muted, fontSize:14, marginTop:4 }}>
                      Top 10 product categories by total sales
                    </p>
                  </div>

                  <Section title="Category Revenue Breakdown">
                    <ResponsiveContainer width="100%" height={360}>
                      <BarChart data={cats} layout="vertical"
                        margin={{ left:20 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke={C.border} horizontal={false} />
                        <XAxis type="number" tick={{ fill:C.muted, fontSize:11 }}
                          tickLine={false} axisLine={false}
                          tickFormatter={v => `R$${(v/1000).toFixed(0)}k`} />
                        <YAxis type="category" dataKey="category"
                          tick={{ fill:C.muted, fontSize:11 }} tickLine={false}
                          axisLine={false} width={160} />
                        <Tooltip content={<CustomTooltip prefix="R$ " />} />
                        <Bar dataKey="revenue" radius={[0,6,6,0]}>
                          {cats.map((_, i) => (
                            <Cell key={i} fill={C.chart[i % C.chart.length]} />
                          ))}
                        </Bar>
                      </BarChart>
                    </ResponsiveContainer>
                  </Section>

                  {/* Category table */}
                  <Section title="Category Details">
                    <table style={{ width:"100%", borderCollapse:"collapse" }}>
                      <thead>
                        <tr style={{ borderBottom:`1px solid ${C.border}` }}>
                          {["Category","Orders","Revenue","Avg Review"].map(h => (
                            <th key={h} style={{ color:C.muted, fontSize:12, fontWeight:500,
                              textAlign:"left", padding:"0 0 12px",
                              fontFamily:"'DM Mono',monospace" }}>{h}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {cats.map((c, i) => (
                          <tr key={i} style={{ borderBottom:`1px solid ${C.border}` }}>
                            <td style={{ padding:"12px 0", color:C.text, fontSize:13,
                              textTransform:"capitalize" }}>{c.category}</td>
                            <td style={{ padding:"12px 0", color:C.muted, fontSize:13 }}>
                              {fmt(c.order_count)}</td>
                            <td style={{ padding:"12px 0", color:C.accent, fontSize:13,
                              fontWeight:600 }}>{fmtR(c.revenue)}</td>
                            <td style={{ padding:"12px 0", fontSize:13 }}>
                              <span style={{ color: c.avg_review_score >= 4 ? C.accent : C.accent2 }}>
                                ⭐ {c.avg_review_score}
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </Section>
                </div>
              )}

              {/* ── RECOMMENDER TAB ── */}
              {tab === "recommender" && (
                <div className="fadein">
                  <div style={{ marginBottom:24 }}>
                    <h1 style={{ fontFamily:"'Syne',sans-serif", fontSize:24,
                      fontWeight:800, color:C.text }}>Product Recommender</h1>
                    <p style={{ color:C.muted, fontSize:14, marginTop:4 }}>
                      Collaborative filtering — item-item cosine similarity
                    </p>
                  </div>

                  {/* Customer lookup */}
                  <Section title="Customer Lookup">
                    <p style={{ color:C.muted, fontSize:13, marginBottom:16 }}>
                      Try: <code style={{ color:C.accent, fontFamily:"'DM Mono',monospace",
                        fontSize:12 }}>0000366f3b9a7992bf8c76cfdf3221e2</code>
                    </p>
                    <div style={{ display:"flex", gap:12 }}>
                      <input
                        value={customerId}
                        onChange={e => setCustomerId(e.target.value)}
                        onKeyDown={e => e.key === "Enter" && fetchRecs()}
                        placeholder="Enter customer unique ID..."
                        style={{ flex:1, background:C.bg, border:`1px solid ${C.border}`,
                          borderRadius:10, padding:"10px 16px", color:C.text, fontSize:13,
                          fontFamily:"'DM Mono',monospace" }}
                      />
                      <button onClick={fetchRecs} style={{
                        background:C.accent, color:"#000", border:"none", borderRadius:10,
                        padding:"10px 24px", cursor:"pointer", fontWeight:600, fontSize:13,
                        fontFamily:"'DM Sans',sans-serif",
                      }}>
                        {recsLoading ? "Loading…" : "Get Recs →"}
                      </button>
                    </div>

                    {recs.length > 0 && (
                      <div style={{ marginTop:24 }}>
                        <p style={{ color:C.muted, fontSize:12,
                          fontFamily:"'DM Mono',monospace", marginBottom:12 }}>
                          RECOMMENDED PRODUCTS
                        </p>
                        <div style={{ display:"grid", gridTemplateColumns:"repeat(5,1fr)", gap:12 }}>
                          {recs.map((r, i) => (
                            <div key={i} style={{ background:C.bg, border:`1px solid ${C.border}`,
                              borderRadius:12, padding:16,
                              borderTop:`3px solid ${C.chart[i % C.chart.length]}` }}>
                              <p style={{ color:C.muted, fontSize:10,
                                fontFamily:"'DM Mono',monospace",
                                textTransform:"uppercase", margin:"0 0 8px" }}>
                                #{i+1}
                              </p>
                              <p style={{ color:C.text, fontSize:13, fontWeight:600,
                                margin:"0 0 8px", textTransform:"capitalize",
                                lineHeight:1.4 }}>
                                {r.category.replace(/_/g," ")}
                              </p>
                              <p style={{ color:C.accent, fontSize:16,
                                fontWeight:700, margin:"0 0 4px" }}>
                                {fmtR(r.avg_price)}
                              </p>
                              <p style={{ color:C.muted, fontSize:11, margin:"0 0 4px" }}>
                                ⭐ {r.avg_review_score}
                              </p>
                              <p style={{ color:C.muted, fontSize:11, margin:0 }}>
                                {fmt(r.times_ordered)} orders
                              </p>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </Section>
                </div>
              )}
            </>
          )}
        </main>
      </div>
    </>
  );
}