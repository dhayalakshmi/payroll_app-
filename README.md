# Payroll System (Flask)

A Flask rewrite of the original Tkinter desktop app. Same three sections
(Employees, Attendance, Leave Requests), same in-memory data, same look —
but served as a normal web app instead of a GUI window.

## Why this fixes the Jenkins problem

`tk.Tk().mainloop()` opens a **desktop GUI window** and blocks waiting for
window events. Jenkins agents are headless (no display), so the process
either fails to open a window or hangs forever with nothing to click —
that's the "runs infinite" symptom.

A Flask app's `app.run()` also "runs forever," but that's normal and
correct for a **web server**: it's supposed to sit and listen for HTTP
requests, not wait for GUI clicks. In Jenkins you don't run it in the
foreground of a build step — you either:

- **Start it in the background** during a pipeline stage (e.g. for
  integration tests), then curl/test it, then kill it:
  ```bash
  pip install -r requirements.txt
  nohup python app.py &
  sleep 2
  curl -f http://localhost:5000/ || exit 1
  kill %1
  ```
- Or, more commonly, **build and ship it** (e.g. into a Docker image) and
  let a separate deployment target (a server, container platform, etc.)
  run it long-term — not the Jenkins build agent itself.

Either way, Jenkins is no longer stuck waiting on a GUI event loop.

## Run it locally

```bash
pip install -r requirements.txt
python app.py
```

Then open http://localhost:5000 in a browser.

## Structure

```
app.py                  Flask routes + in-memory data (mirrors the Tkinter app's state)
templates/base.html     Shared sidebar/nav layout
templates/employees.html
templates/attendance.html
templates/leave.html
static/style.css        Same color palette as the original Tkinter UI
```

## Notes

- Data is in-memory only (no database), exactly like the original app —
  it resets whenever the process restarts.
- `app.run(debug=False)` on purpose, since this is meant to run
  unattended in CI/servers rather than in a dev environment with a human
  watching the reloader.
