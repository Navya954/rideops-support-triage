import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title='RideOps Support Triage', page_icon='🚕', layout='wide')
st.title('RideOps Support — Ticket Triage & Backlog Monitor')
st.caption('Working v0 • Reads the supplied ticket CSV • Rule-based triage suggestions, not automated decisions')

DEFAULT_FILE='rideops_support_tickets.csv'
up=st.sidebar.file_uploader('Upload ticket CSV (optional)', type=['csv'])
try:
    df=pd.read_csv(up if up is not None else DEFAULT_FILE)
except Exception:
    st.error('Could not load CSV. Upload rideops_support_tickets.csv to continue.')
    st.stop()

required=['ticket_id','created_at','category','priority','status','escalated_to_eng','eng_outcome','assigned_agent','reopen_count','csat_score']
missing=[c for c in required if c not in df.columns]
if missing:
    st.error('Required columns missing: '+', '.join(missing)); st.stop()
for col in ['created_at','first_response_at','first_closed_at','final_closed_at']:
    if col in df: df[col]=pd.to_datetime(df[col], errors='coerce')
df['is_open']=df.status.astype(str).str.startswith('Open')
df['is_escalated']=df.escalated_to_eng.astype(str).str.lower().eq('yes')
df['is_reopened']=pd.to_numeric(df.reopen_count,errors='coerce').fillna(0).gt(0)

checklists={
 'Roster / booking not syncing':['Confirm employee and trip/booking identifiers','Check roster upload/sync timestamp and latest status','Check whether booking exists and is assigned','Capture error message and affected shift/date','Escalate only if sync failure persists after checks'],
 'Live tracking / GPS incorrect':['Confirm trip is active and driver/vehicle assigned','Check last GPS update timestamp','Verify tracking link and device/network status','Capture trip ID, timestamp and screenshot/error','Escalate if GPS feed remains stale after checks'],
 'Report export failing':['Confirm report type, date range and user permissions','Try a smaller date range / alternate export format','Capture error text and report parameters','Check whether other users can reproduce'],
 'OTP / boarding issue':['Confirm trip/employee details and OTP time','Check OTP expiry/resend flow','Verify phone number/contact details','Capture exact error and timestamp'],
 'Billing / invoice discrepancy':['Confirm trip completed and billed period','Compare trip record with invoice line','Check duplicate/adjustment entries','Capture invoice and trip references'],
 'Login / access issue':['Confirm user and role/permission needed','Check account activation and password/reset flow','Try whether issue affects other users','Capture error and affected module'],
 'Cab delay / no-show complaint':['Confirm scheduled pickup time and pickup location','Check driver/vehicle assignment and live status','Record client contact and incident timeline','Escalate operational safety/critical cases promptly'],
 'Employee address / geocode change':['Validate address format and pin/location','Confirm employee ID and effective date','Check geocode result and map pin','Capture corrected address and failed result'],
 'Driver / vehicle compliance docs':['Check driver/vehicle identifiers and document expiry','Confirm document upload and status','Capture missing/invalid document type'],
 'How-to / feature request':['Identify module and user goal','Check help article / known workflow','Provide steps or record feature request separately']}

st.sidebar.header('Filters')
cat_opts=sorted(df.category.dropna().unique().tolist())
selected_cats=st.sidebar.multiselect('Category',cat_opts,default=cat_opts)
pri_opts=sorted(df.priority.dropna().unique().tolist())
selected_pri=st.sidebar.multiselect('Priority',pri_opts,default=pri_opts)
status_opts=sorted(df.status.dropna().unique().tolist())
selected_status=st.sidebar.multiselect('Status',status_opts,default=status_opts)
agent_opts=sorted(df.assigned_agent.dropna().unique().tolist()) if 'assigned_agent' in df else []
selected_agents=st.sidebar.multiselect('Assigned agent',agent_opts,default=agent_opts)
filtered=df[df.category.isin(selected_cats)&df.priority.isin(selected_pri)&df.status.isin(selected_status)]
if agent_opts: filtered=filtered[filtered.assigned_agent.isin(selected_agents)]

# Top-level KPIs
n=len(filtered); open_n=int(filtered.is_open.sum()); esc_n=int(filtered.is_escalated.sum()); reopen_n=int(filtered.is_reopened.sum())
col1,col2,col3,col4=st.columns(4)
col1.metric('Tickets in selection',f'{n:,}')
col2.metric('Open tickets',f'{open_n:,}',f'{(open_n/n*100 if n else 0):.1f}% of selection')
col3.metric('Escalated to engineering',f'{esc_n:,}',f'{(esc_n/n*100 if n else 0):.1f}% of selection')
col4.metric('Reopened at least once',f'{reopen_n:,}',f'{(reopen_n/n*100 if n else 0):.1f}% of selection')

# tabs
tab1,tab2,tab3,tab4=st.tabs(['Overview','Ticket explorer & triage','Escalation quality','Data & definitions'])
with tab1:
    left,right=st.columns(2)
    with left:
        st.subheader('Ticket inflow by month')
        if filtered.created_at.notna().any():
            monthly=filtered.groupby(filtered.created_at.dt.to_period('M').astype(str)).size().rename('Tickets')
            st.bar_chart(monthly)
            st.caption('Ticket creation volume—not a historical open-backlog snapshot.')
    with right:
        st.subheader('Open tickets by category')
        opens=filtered[filtered.is_open].groupby('category').size().sort_values(ascending=False)
        st.bar_chart(opens)
    st.subheader('Category summary')
    summary=filtered.groupby('category').agg(Tickets=('ticket_id','count'),Open=('is_open','sum'),Escalated=('is_escalated','sum'),Reopened=('is_reopened','sum'),Mean_CSAT=('csat_score','mean')).sort_values('Tickets',ascending=False)
    summary['Escalation %']=filtered.groupby('category').is_escalated.mean()*100
    st.dataframe(summary.round(2),use_container_width=True)
    st.subheader('Weekly trend (ticket creation)')
    if filtered.created_at.notna().any():
        wk=filtered.dropna(subset=['created_at']).set_index('created_at').resample('W').size().rename('New tickets')
        st.line_chart(wk)
with tab2:
    st.subheader('Find a ticket')
    ticket_ids=filtered.ticket_id.astype(str).tolist()
    chosen=st.selectbox('Ticket ID',ticket_ids) if ticket_ids else None
    if chosen:
        t=filtered[filtered.ticket_id.astype(str)==chosen].iloc[0]
        st.write('**Description:**',t.get('description','—'))
        a,b,c=st.columns(3)
        a.write('**Category**\n'+str(t.category)); b.write('**Priority**\n'+str(t.priority)); c.write('**Status**\n'+str(t.status))
        d,e,f=st.columns(3)
        d.write('**Agent**\n'+str(t.assigned_agent)); e.write('**Engineering escalation**\n'+str(t.escalated_to_eng)); f.write('**Reopen count**\n'+str(t.reopen_count))
        st.markdown('### Suggested L1 checks')
        checklist=checklists.get(str(t.category),['Review ticket details and reproduce the issue','Collect relevant IDs, timestamps and error evidence','Check known issue / configuration guidance','Escalate with evidence if unresolved'])
        for item in checklist: st.checkbox(item,key=f'{chosen}_{item}')
        st.info('Use this checklist as a guide. P1/safety-critical cases and known incident procedures should bypass routine checks where appropriate.')
        st.markdown('### Ticket record')
        st.dataframe(pd.DataFrame(t).T, use_container_width=True)
    else: st.warning('No tickets match the selected filters.')
    st.subheader('Export filtered tickets')
    st.download_button('Download filtered CSV',filtered.to_csv(index=False).encode('utf-8'),file_name='rideops_filtered_tickets.csv',mime='text/csv')
with tab3:
    st.subheader('Engineering escalation outcomes')
    escal=filtered[filtered.is_escalated]
    if len(escal):
        outcomes=escal.eng_outcome.fillna('Outcome missing').value_counts()
        st.bar_chart(outcomes)
        returned=escal.eng_outcome.astype(str).str.contains('returned to L1|Duplicate|Not a bug|Not reproducible',case=False,regex=True).sum()
        fixed=escal.eng_outcome.astype(str).eq('Fixed').sum()
        x,y,z=st.columns(3); x.metric('Escalations',len(escal)); y.metric('Fixed by engineering',fixed,f'{fixed/len(escal)*100:.1f}%'); z.metric('Returned / non-fix outcome',returned,f'{returned/len(escal)*100:.1f}%')
        st.write('Handoff count distribution')
        st.bar_chart(escal.eng_handoffs.value_counts().sort_index())
        st.caption('Returned/non-fix grouping is a triage signal, not proof that the escalation was avoidable. Validate with Engineering before changing policy.')
    else: st.info('No escalated tickets in the current selection.')
with tab4:
    st.subheader('Definitions used')
    st.markdown('''- **Open:** status begins with `Open` as of 30 Sep 2026.\n- **Escalation rate:** tickets marked `Yes` divided by tickets in selection.\n- **Reopened rate:** tickets with `reopen_count > 0` divided by tickets in selection.\n- **CSAT:** mean of non-blank ratings; blanks are excluded.\n- **Resolution time:** final close minus created time, only for tickets with final close timestamp.\n- **Inflow:** tickets created in the period. This is not the same as backlog.\n\nThe dataset is a single snapshot. It does not contain historic weekly/daily open-ticket snapshots, so historic backlog reduction cannot be calculated from this file alone.''')
    st.write('Rows and columns',df.shape)
    st.write('Missing values')
    st.dataframe(df.isna().sum().rename('Missing').to_frame(),use_container_width=True)
    st.download_button('Download source data',df.to_csv(index=False).encode('utf-8'),file_name='rideops_source_copy.csv',mime='text/csv')

st.divider()
st.caption('v0 limitation: checklist recommendations are category-based rules; they are not AI-generated, do not update ticket records, and do not replace escalation policy. Pilot with agents and measure impact before rollout.')
