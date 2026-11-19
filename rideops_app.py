import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="RideOps | Support Analytics", page_icon="📊", layout="wide")
from pathlib import Path

def load_css():
    css_path = Path(__file__).parent / "assets" / "style.css"

    with open(css_path, "r", encoding="utf-8") as f:
        st.markdown(
            f"<style>{f.read()}</style>",
            unsafe_allow_html=True
        )

load_css()


DEFAULT_FILE = "rideops_support_tickets.csv"
with st.sidebar:
    st.markdown("<div style='font-size:23px;font-weight:800;letter-spacing:-.5px;margin:3px 0 0'>RideOps</div><div style='font-size:12px;color:#98a2b3 !important;margin:0 0 18px'>SUPPORT OPERATIONS</div>", unsafe_allow_html=True)
    nav = st.radio("WORKSPACE", ["Overview", "Ticket explorer", "Escalation insights", "Data & definitions"], label_visibility="visible")
    st.markdown("---")
    st.markdown("**DATA SOURCE**")
    upload = st.file_uploader("Upload ticket CSV", type=["csv"], label_visibility="collapsed")
    st.caption("Using supplied case-study dataset unless a file is uploaded.")
    st.markdown("---")
    st.markdown("<div style='font-size:11px;color:#98a2b3 !important'>CASE STUDY • JUL–SEP 2026</div>", unsafe_allow_html=True)

try:
    df = pd.read_csv(upload if upload is not None else DEFAULT_FILE)
except Exception:
    st.error("Unable to read the CSV. Upload rideops_support_tickets.csv or keep it next to this app file.")
    st.stop()

required = ['ticket_id','created_at','category','priority','status','escalated_to_eng','eng_outcome','assigned_agent','reopen_count','csat_score']
missing = [c for c in required if c not in df.columns]
if missing:
    st.error("Missing required columns: " + ", ".join(missing)); st.stop()
for col in ['created_at','first_response_at','first_closed_at','final_closed_at']:
    if col in df.columns: df[col] = pd.to_datetime(df[col], errors='coerce')
df['is_open'] = df.status.astype(str).str.startswith('Open')
df['is_escalated'] = df.escalated_to_eng.astype(str).str.lower().eq('yes')
df['is_reopened'] = pd.to_numeric(df.reopen_count, errors='coerce').fillna(0).gt(0)
df['csat_numeric'] = pd.to_numeric(df.csat_score, errors='coerce')

# Checklists, intended as guidance not policy
checklists = {
 'Roster / booking not syncing':['Confirm employee and trip/booking identifiers','Check roster upload/sync timestamp and latest status','Confirm the booking exists and is assigned','Capture error message and affected shift/date','Escalate with evidence if sync failure persists'],
 'Live tracking / GPS incorrect':['Confirm trip is active and driver/vehicle assigned','Check last GPS update timestamp','Verify tracking link and device/network status','Capture trip ID, timestamp and screenshot/error','Escalate if GPS feed remains stale after checks'],
 'Report export failing':['Confirm report type, date range and user permissions','Try a smaller date range or alternate export format','Capture error text and report parameters','Check whether other users can reproduce'],
 'OTP / boarding issue':['Confirm trip/employee details and OTP time','Check OTP expiry/resend flow','Verify phone number/contact details','Capture exact error and timestamp'],
 'Billing / invoice discrepancy':['Confirm trip completed and billed period','Compare trip record with invoice line','Check duplicate/adjustment entries','Capture invoice and trip references'],
 'Login / access issue':['Confirm user and required role/permission','Check account activation and password/reset flow','Check if issue affects other users','Capture error and affected module'],
 'Cab delay / no-show complaint':['Confirm scheduled pickup time and location','Check driver/vehicle assignment and live status','Record client contact and incident timeline','Escalate operational/safety-critical cases promptly'],
 'Employee address / geocode change':['Validate address format and location pin','Confirm employee ID and effective date','Check geocode result and map pin','Capture corrected address and failed result'],
 'Driver / vehicle compliance docs':['Check driver/vehicle identifiers and document expiry','Confirm document upload and status','Capture missing/invalid document type'],
 'How-to / feature request':['Identify module and user goal','Check help article / known workflow','Provide steps or record feature request separately']}

# Sidebar filters
with st.sidebar:
    st.markdown("**FILTERS**")
    cats = sorted(df.category.dropna().unique())
    cat_sel = st.multiselect("Issue category", cats, default=cats)
    pri = sorted(df.priority.dropna().unique())
    pri_sel = st.multiselect("Priority", pri, default=pri)
    statuses = sorted(df.status.dropna().unique())
    status_sel = st.multiselect("Ticket status", statuses, default=statuses)
    if 'client_tier' in df:
        tiers = sorted(df.client_tier.dropna().unique())
        tier_sel = st.multiselect("Client tier", tiers, default=tiers)
    else: tier_sel = []
    agents = sorted(df.assigned_agent.dropna().unique())
    agent_sel = st.multiselect("Assigned agent", agents, default=agents)

f = df[df.category.isin(cat_sel) & df.priority.isin(pri_sel) & df.status.isin(status_sel)]
if 'client_tier' in df: f = f[f.client_tier.isin(tier_sel)]
f = f[f.assigned_agent.isin(agent_sel)]

# Header
st.markdown("<div class='header-title'>Support operations dashboard</div><div class='header-sub'>Ticket health, workload trends and escalation quality · Case-study dataset</div>", unsafe_allow_html=True)
st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

# KPI calculations
n = len(f); open_count = int(f.is_open.sum()); esc_count = int(f.is_escalated.sum()); reopen_count = int(f.is_reopened.sum())
csat_mean = f.csat_numeric.mean()
open_pct = open_count/n*100 if n else 0
esc_pct = esc_count/n*100 if n else 0
reopen_pct = reopen_count/n*100 if n else 0
k1,k2,k3,k4,k5 = st.columns(5)
k1.metric("Tickets in view", f"{n:,}")
k2.metric("Open tickets", f"{open_count:,}", f"{open_pct:.1f}% of tickets")
k3.metric("Escalated", f"{esc_count:,}", f"{esc_pct:.1f}% of tickets")
k4.metric("Reopened", f"{reopen_count:,}", f"{reopen_pct:.1f}% of tickets")
k5.metric("Average CSAT", f"{csat_mean:.2f} / 5" if not pd.isna(csat_mean) else "—", f"{f.csat_numeric.count():,} ratings")
st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

# Chart helpers
chart_template = "plotly_white"
chart_config = dict(displayModeBar=False)

def polish(fig, height=300):
    fig.update_layout(template=chart_template, height=height, margin=dict(l=12,r=12,t=18,b=8), font=dict(family="Inter, sans-serif", size=12, color="#475467"), paper_bgcolor="white", plot_bgcolor="white", legend=dict(orientation="h", y=-0.16))
    fig.update_xaxes(showgrid=False, linecolor="#e5eaf2")
    fig.update_yaxes(gridcolor="#eef2f7", zeroline=False)
    return fig

if nav == "Overview":
    # Two-column chart row
    left, right = st.columns([1.55,1])
    with left:
        st.markdown("<div class='card'><div class='section-title'>Ticket volume over time</div><div class='small-muted'>Created tickets by month · filtered data</div>", unsafe_allow_html=True)
        if f.created_at.notna().any():
            monthly = f.dropna(subset=['created_at']).groupby(f.dropna(subset=['created_at']).created_at.dt.to_period('M').astype(str)).size().reset_index(name='Tickets')
            monthly.columns = ['Month','Tickets']
            fig = px.line(monthly, x='Month', y='Tickets', markers=True)
            fig.update_traces(line=dict(color="#3b82f6", width=3), marker=dict(size=8, color="#3b82f6"), fill="tozeroy", fillcolor="rgba(59,130,246,.09)")
            st.plotly_chart(polish(fig, 300), use_container_width=True, config=chart_config)
        else: st.info("No dated tickets in current filters.")
        st.markdown("</div>", unsafe_allow_html=True)
    with right:
        st.markdown("<div class='card'><div class='section-title'>Ticket status mix</div><div class='small-muted'>Open vs closed in current view</div>", unsafe_allow_html=True)
        status_counts = f.status.value_counts().reset_index(); status_counts.columns=['Status','Tickets']
        fig2 = px.pie(status_counts, names='Status', values='Tickets', hole=.68)
        fig2.update_traces(textposition='inside', textinfo='percent', marker=dict(line=dict(color='white',width=2)))
        fig2.update_layout(showlegend=True, legend=dict(orientation='v', x=1.0, y=.5))
        st.plotly_chart(polish(fig2, 300), use_container_width=True, config=chart_config)
        st.markdown("</div>", unsafe_allow_html=True)
    l2,r2 = st.columns([1,1])
    with l2:
        st.markdown("<div class='card'><div class='section-title'>Open tickets by category</div><div class='small-muted'>Where the unresolved workload is concentrated</div>", unsafe_allow_html=True)
        oc = f[f.is_open].category.value_counts().sort_values().reset_index(); oc.columns=['Category','Open tickets']
        if len(oc):
            fig3 = px.bar(oc, x='Open tickets', y='Category', orientation='h', text='Open tickets')
            fig3.update_traces(marker_color="#f59e0b", textposition='outside')
            st.plotly_chart(polish(fig3, max(280, len(oc)*25)), use_container_width=True, config=chart_config)
        else: st.info("No open tickets in current view.")
        st.markdown("</div>", unsafe_allow_html=True)
    with r2:
        st.markdown("<div class='card'><div class='section-title'>Tickets by priority</div><div class='small-muted'>Distribution of ticket urgency</div>", unsafe_allow_html=True)
        pc = f.priority.value_counts().reindex(['P1','P2','P3','P4']).dropna().reset_index(); pc.columns=['Priority','Tickets']
        fig4 = px.bar(pc, x='Priority', y='Tickets', text='Tickets')
        fig4.update_traces(marker_color="#6366f1", textposition='outside')
        st.plotly_chart(polish(fig4, 300), use_container_width=True, config=chart_config)
        st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("### Recent tickets")
    recent = f.sort_values('created_at', ascending=False).head(10).copy()
    show_cols = [c for c in ['ticket_id','created_at','client_name','category','priority','status','assigned_agent','escalated_to_eng'] if c in recent]
    st.dataframe(recent[show_cols], use_container_width=True, hide_index=True)
    st.caption("Ticket creation volume is not historical backlog. The provided file is a single snapshot dated 30 Sep 2026.")

elif nav == "Ticket explorer":
    st.markdown("### Ticket search and triage")
    search = st.text_input("Search by ticket ID, client, description or engineering ID", placeholder="e.g. TKT-1042 or tracking issue")
    searchable = f.copy()
    if search.strip():
        cols = [c for c in ['ticket_id','client_name','description','eng_ticket_id','category'] if c in searchable]
        mask = searchable[cols].astype(str).apply(lambda col: col.str.contains(search, case=False, na=False)).any(axis=1)
        searchable = searchable[mask]
    st.markdown(f"**{len(searchable):,} matching tickets**")
    display_cols = [c for c in ['ticket_id','created_at','client_name','category','priority','status','assigned_agent','escalated_to_eng','reopen_count'] if c in searchable]
    st.dataframe(searchable[display_cols].sort_values('created_at', ascending=False), use_container_width=True, hide_index=True)
    st.markdown("---")
    ids = searchable.ticket_id.astype(str).tolist()
    chosen = st.selectbox("Open a ticket for triage", ids) if ids else None
    if chosen:
        t = searchable[searchable.ticket_id.astype(str)==chosen].iloc[0]
        c1,c2,c3,c4 = st.columns(4)
        c1.metric("Priority", str(t.priority)); c2.metric("Status", str(t.status)); c3.metric("Escalated", str(t.escalated_to_eng)); c4.metric("Reopens", int(pd.to_numeric(t.reopen_count,errors='coerce') or 0))
        st.markdown(f"**{t.get('client_name','Client')}** · {t.category} · Assigned: {t.assigned_agent}")
        st.info(str(t.get('description','No description available')))
        st.markdown("#### Suggested L1 checklist")
        checks = checklists.get(str(t.category), ['Review ticket details and reproduce issue','Collect relevant identifiers, timestamps and evidence','Check known issue/configuration guidance','Escalate with evidence if unresolved'])
        for item in checks: st.checkbox(item, key=f"triage_{chosen}_{item}")
        st.warning("Guidance only. Follow existing incident/safety escalation policy for critical cases; this tool does not update ticket records.")
        details = t.to_frame().T
        st.expander("View full ticket fields").dataframe(details, use_container_width=True)
    st.download_button("Download current filtered tickets", f.to_csv(index=False).encode('utf-8'), "rideops_filtered_tickets.csv", "text/csv")

elif nav == "Escalation insights":
    st.markdown("### Engineering escalation quality")
    escal = f[f.is_escalated].copy()
    if len(escal):
        outcome = escal.eng_outcome.fillna("Outcome missing").value_counts().reset_index(); outcome.columns=['Outcome','Tickets']
        c1,c2 = st.columns([1.4,1])
        with c1:
            fig5 = px.bar(outcome.sort_values('Tickets'), x='Tickets', y='Outcome', orientation='h', text='Tickets')
            fig5.update_traces(marker_color="#0ea5e9", textposition='outside')
            st.plotly_chart(polish(fig5, 320), use_container_width=True, config=chart_config)
        with c2:
            fixed = int(escal.eng_outcome.astype(str).eq('Fixed').sum())
            nonfix = int(escal.eng_outcome.astype(str).str.contains('returned to L1|Duplicate|Not a bug|Not reproducible', case=False, regex=True).sum())
            st.metric("Escalations", f"{len(escal):,}")
            st.metric("Fixed by Engineering", f"{fixed:,}", f"{fixed/len(escal)*100:.1f}%")
            st.metric("Returned / non-fix", f"{nonfix:,}", f"{nonfix/len(escal)*100:.1f}%")
        st.markdown("#### Engineering handoffs")
        handoffs = pd.to_numeric(escal.eng_handoffs, errors='coerce').fillna(0).value_counts().sort_index().reset_index(); handoffs.columns=['Handoffs','Tickets']
        fig6 = px.bar(handoffs, x='Handoffs', y='Tickets', text='Tickets')
        fig6.update_traces(marker_color="#8b5cf6", textposition='outside')
        st.plotly_chart(polish(fig6, 250), use_container_width=True, config=chart_config)
        st.caption("Returned/non-fix outcomes are a triage signal—not proof that escalations were avoidable. Validate with Support and Engineering.")
    else: st.info("No escalated tickets match these filters.")

else:
    st.markdown("### Data health & definitions")
    st.markdown("**Dataset dimensions:** {:,} rows × {} columns".format(*df.shape))
    st.markdown("**Definitions used**")
    st.markdown("- Open: status begins with `Open` in the 30 Sep snapshot.\n- Escalation rate: escalated tickets divided by tickets in selection.\n- Reopened: `reopen_count > 0`.\n- CSAT: mean of available scores; missing ratings excluded.\n- Inflow: tickets created in a period; not the same as backlog.\n- Historical backlog snapshots are not provided, so historical backlog growth cannot be verified from this CSV.")
    st.markdown("**Missing values by field**")
    miss = df.isna().sum().rename("Missing values").to_frame(); miss['Missing %']=(miss['Missing values']/len(df)*100).round(1)
    st.dataframe(miss, use_container_width=True)
    st.download_button("Download source CSV", df.to_csv(index=False).encode('utf-8'), "rideops_source_copy.csv", "text/csv")

st.markdown("<div style='padding:12px 0 0;color:#98a2b3;font-size:11px'>RideOps Support Case Study · Internal prototype · Rule-based triage guidance</div>", unsafe_allow_html=True)
