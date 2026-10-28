class EufyS1ProInspector extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({mode: "open"});
    this._pending = false;
    this._selected = "";
    this._direction = "all";
    this._running = false;
  }
  set hass(value) {
    this._hass = value;
    if (this.isConnected && !this._running) this.connectedCallback();
  }
  connectedCallback() {
    if (this._running || !this._hass) return;
    this._running = true;
    this.refresh();
    this._timer = setInterval(() => this.refresh(), 2000);
  }
  disconnectedCallback() {
    this._running = false;
    clearInterval(this._timer);
  }
  async refresh() {
    if (this._pending || !this._running || !this._hass) return;
    this._pending = true;
    try {
      this._data = await this._hass.callWS({type: "eufy_robovac_s1_pro/inspector"});
      this._error = "";
      if (this._running) this.render();
    } catch (err) {
      this._error = err.message || "Inspector request failed";
      if (this._running) this.render();
    } finally {
      this._pending = false;
    }
  }
  node(tag, text, parent) {
    const element = document.createElement(tag);
    if (text !== undefined) element.textContent = text;
    if (parent) parent.append(element);
    return element;
  }
  async action(action) {
    if (!this._robot || this._actionPending) return;
    this._actionPending = true;
    try {
      await this._hass.callWS({type: "eufy_robovac_s1_pro/capture", robot: this._robot.id, action});
    } catch (err) {
      this._error = err.message || "Capture action failed";
    } finally {
      this._actionPending = false;
      await this.refresh();
    }
  }
  render() {
    const root = this.shadowRoot;
    root.replaceChildren();
    const style = this.node("style", undefined, root);
    style.textContent = `:host{display:block;color:var(--primary-text-color);background:var(--primary-background-color);min-height:100vh;font:15px system-ui}main{padding:24px;max-width:1200px;margin:auto}button,select{padding:8px;margin:4px;color:inherit;background:var(--card-background-color);border:1px solid var(--divider-color);border-radius:6px}table{width:100%;border-collapse:collapse}th,td{text-align:left;padding:8px;border-bottom:1px solid var(--divider-color);overflow-wrap:anywhere}.scroll{overflow:auto}.error{color:var(--error-color)}small{display:block;margin:12px 0}`;
    const main = this.node("main", undefined, root);
    this.node("h1", "S1 Pro Inspector", main);
    this.node("p", "Metadata-only observation of this integration's local connection. No raw payload values, cloud interception, or unknown command replay.", main);
    if (this._error) this.node("p", this._error, main).className = "error";
    const robots = this._data?.robots || [];
    if (!robots.length) {
      this.node("p", "No loaded robots. Complete integration setup or check connection retries.", main);
      return;
    }
    const select = this.node("select", undefined, main);
    select.setAttribute("aria-label", "Robot");
    for (const robot of robots) {
      const option = this.node("option", robot.label, select);
      option.value = robot.id;
    }
    if (!robots.some(r => r.id === this._selected)) this._selected = robots[0].id;
    select.value = this._selected;
    select.onchange = () => {this._selected = select.value; this.render();};
    this._robot = robots.find(r => r.id === this._selected);
    const trace = this._robot.trace;
    this.node("p", `${this._robot.connected ? "Last update succeeded" : "Last update failed"} | Capture ${trace.enabled ? "ON" : "OFF"} | RX ${trace.rx} | TX ${trace.tx}`, main);
    this.node("p", `Observed datapoints: ${trace.seen_dps.join(", ") || "none"}`, main);
    for (const [label, action] of [["Capture for 10 minutes", "start"], ["Stop capture", "stop"], ["Clear timeline", "clear"]]) {
      const button = this.node("button", label, main);
      button.onclick = () => this.action(action);
    }
    const filter = this.node("select", undefined, main);
    filter.setAttribute("aria-label", "Direction filter");
    for (const direction of ["all", "incoming", "outgoing"]) {
      const option = this.node("option", direction, filter);
      option.value = direction;
    }
    filter.value = this._direction;
    filter.onchange = () => {this._direction = filter.value; this.render();};
    this.node("small", `At most ${trace.capacity} records held in memory; capture expires after 10 minutes. HA event entities, if enabled, may also be retained by Recorder.`, main);
    const scroll = this.node("div", undefined, main); scroll.className = "scroll";
    const table = this.node("table", undefined, scroll);
    const heading = this.node("tr", undefined, this.node("thead", undefined, table));
    for (const label of ["Time", "Direction", "Tuya command", "Datapoint shapes", "Outcome"]) this.node("th", label, heading);
    const body = this.node("tbody", undefined, table);
    for (const row of [...trace.rows].reverse()) {
      if (this._direction !== "all" && this._direction !== row.direction) continue;
      const tr = this.node("tr", undefined, body);
      for (const value of [row.time, row.direction, row.command ?? "—", JSON.stringify(row.datapoints), row.outcome]) this.node("td", String(value), tr);
    }
  }
}
if (!customElements.get("eufy-s1-pro-inspector")) customElements.define("eufy-s1-pro-inspector", EufyS1ProInspector);
