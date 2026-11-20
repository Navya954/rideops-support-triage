
# RideOps Support – Ticket Triage & Backlog Monitor

 **Live Demo:** (https://navya954-rideops-support-triage-rideops-app-fer0tb.streamlit.app/)
**GitHub Repository:** https://github.com/Navya954/rideops-support-triage

# RideOps Support Triage v0

A working Streamlit tool built from the provided ticket CSV. It includes ticket-volume and open-backlog views, filters, ticket explorer, category-specific L1 checklist suggestions, escalation-outcome analysis, and CSV export.


## Run locally

1. Install Python 3.10+.
2. Put `rideops_app.py` and `rideops_support_tickets.csv` in the same folder.
3. In a terminal in that folder:

```bash
python -m pip install streamlit pandas numpy
python -m streamlit run rideops_app.py
```

The browser opens the app. Or upload the CSV in the sidebar.

## Deploy (Streamlit Community Cloud)

1. Create a GitHub repository and add `rideops_app.py`, `rideops_support_tickets.csv`, and this README.
2. Push the files to GitHub.
3. On Streamlit Community Cloud, choose **New app**, select the repository, branch, and `rideops_app.py` as the main file.
4. Deploy and test the app link.

## Scope and caveats

- Category checklists are heuristic suggestions for a pilot and must be validated with Support/Engineering.
- This v0 reads data; it does not write changes back into the ticketing system.
- Dataset is one snapshot as of 30 September 2026. It can show open-ticket counts and ticket inflow by date, but not historical backlog snapshots or prove the reported +60% backlog change.
- No tickets are auto-closed or auto-escalated.
