/**
 * Dira Shabat Card - Custom Lovelace Card for Home Assistant
 * Manages Shabbat and Jewish Holiday display with meal toggles
 */

console.info(
  `%c DIRA-SHABAT-CARD %c v1.0.0 `,
  "color: white; background: #6a3de8; font-weight: 700; padding: 2px 8px; border-radius: 4px 0 0 4px;",
  "color: #6a3de8; background: #ede7f6; font-weight: 700; padding: 2px 8px; border-radius: 0 4px 4px 0;"
);

const AUTO_ENTITIES = {
  show_times_entity: (p) => `binary_sensor.${p}_show_times`,
  modo_shabat_entity: (p) => `switch.${p}_shabbat_mode`,
  candle_lighting_entity: (p) => `sensor.${p}_candle_lighting`,
  havdalah_entity: (p) => `sensor.${p}_havdalah`,
  total_days_entity: (p) => `sensor.${p}_total_days`,
};

const CARD_CSS = `
  :host {
    --text-primary: var(--primary-text-color);
    --text-secondary: var(--secondary-text-color);
    --accent: var(--primary-color);
    --toggle-off-bg: var(--switch-unchecked-track-color, rgba(128,128,128,0.3));
  }
  ha-card {
    color: var(--text-primary);
    font-family: var(--ha-card-font-family, inherit);
    overflow: hidden;
    padding: 12px 16px;
  }

  /* Times row: split evenly, larger text */
  .times-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
    padding: 6px 0 10px;
  }
  .time-block {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 12px;
    min-width: 0;
  }
  .time-icon {
    color: var(--accent);
    --mdc-icon-size: 26px;
    line-height: 1;
    flex: 0 0 auto;
  }
  .time-text {
    display: flex;
    flex-direction: column;
    min-width: 0;
  }
  .time-label {
    font-size: 12px;
    color: var(--text-secondary);
    font-weight: 500;
    line-height: 1.3;
  }
  .time-value {
    font-size: 18px;
    font-weight: 700;
    color: var(--text-primary);
    line-height: 1.2;
  }

  /* Mode row: pressable, simple row */
  .mode-row {
    margin-top: 4px;
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 10px 0;
    border-top: 1px solid var(--divider-color);
    border-bottom: 1px solid var(--divider-color);
    cursor: pointer;
    user-select: none;
    -webkit-user-select: none;
    position: relative;
    overflow: hidden;
  }
  .mode-row::before {
    content: "";
    position: absolute;
    inset: 0 auto 0 0;
    width: 0;
    background: var(--accent);
    opacity: 0.1;
    transition: width 0s;
    pointer-events: none;
  }
  .mode-row.holding::before {
    width: 100%;
    transition: width 500ms linear;
  }
  .mode-icon {
    --mdc-icon-size: 20px;
    line-height: 1;
    color: var(--accent);
    flex: 0 0 auto;
  }
  .mode-label {
    font-size: 14px;
    font-weight: 500;
  }
  .mode-status {
    font-size: 14px;
    font-weight: 600;
    color: var(--text-secondary);
  }
  .mode-row.on .mode-status {
    color: var(--accent);
  }

  /* Meals section header */
  .meals-header {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-top: 12px;
    margin-bottom: 10px;
  }
  .meals-header .mode-icon {
    --mdc-icon-size: 18px;
  }
  .meals-title {
    font-size: 14px;
    font-weight: 600;
  }

  /* Meals row: auto-sized grid (2, 4, or 6 columns) */
  .meals-row {
    display: grid;
    grid-template-columns: repeat(var(--meal-count, 2), minmax(0, 1fr));
    gap: 6px;
  }
  .meal-item {
    display: flex;
    flex-direction: column;
    align-items: stretch;
    gap: 4px;
    min-width: 0;
  }
  .meal-label {
    font-size: 11px;
    font-weight: 500;
    color: var(--text-primary);
    line-height: 1.2;
    text-align: center;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .meal-day {
    font-size: 10px;
    color: var(--text-secondary);
    line-height: 1.2;
    text-align: center;
  }

  /* Options section (generic user-renamable switches) */
  .options-section {
    display: flex;
    flex-direction: column;
    gap: 6px;
    margin-top: 8px;
    padding-top: 8px;
    border-top: 1px solid var(--divider-color);
  }
  .option-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
    padding: 4px 0;
  }
  .option-label {
    font-size: 13px;
    font-weight: 500;
    color: var(--text-primary);
    min-width: 0;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  /* ON/OFF pill button */
  .pill {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 100%;
    max-width: 90px;
    margin: 0 auto;
    padding: 5px 10px;
    border-radius: 999px;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.5px;
    text-transform: uppercase;
    cursor: pointer;
    user-select: none;
    -webkit-user-select: none;
    transition: background 0.2s ease, color 0.2s ease, border-color 0.2s ease;
    border: 1.5px solid var(--toggle-off-bg);
    background: transparent;
    color: var(--text-secondary);
    box-sizing: border-box;
  }
  .pill.on {
    background: var(--accent);
    border-color: var(--accent);
    color: white;
  }
`;

let SHARED_STYLESHEET = null;
const getStyleSheet = () => {
  if (SHARED_STYLESHEET) return SHARED_STYLESHEET;
  if (typeof CSSStyleSheet !== "undefined" && "replaceSync" in CSSStyleSheet.prototype) {
    SHARED_STYLESHEET = new CSSStyleSheet();
    SHARED_STYLESHEET.replaceSync(CARD_CSS);
  }
  return SHARED_STYLESHEET;
};

const TRANSLATIONS = {
  es: {
    candle_lighting: "Velas",
    ends: "Finaliza",
    shabbat_mode: "Modo Shabat",
    dinner: "Cena",
    lunch: "Almuerzo",
    meals: "Comidas",
    on: "On",
    off: "Off",
    confirm_off: "¿Deseas apagar el Modo Shabat?",
    hold_hint: "Mantener presionado",
    days_of_week: {
      Monday: "Lun.",
      Tuesday: "Mar.",
      Wednesday: "Mié.",
      Thursday: "Jue.",
      Friday: "Vie.",
      Saturday: "Sáb.",
      Sunday: "Dom.",
    },
    days_of_week_full: {
      Monday: "Lunes",
      Tuesday: "Martes",
      Wednesday: "Miércoles",
      Thursday: "Jueves",
      Friday: "Viernes",
      Saturday: "Sábado",
      Sunday: "Domingo",
    },
  },
  en: {
    candle_lighting: "Candles",
    ends: "Ends",
    shabbat_mode: "Shabbat Mode",
    dinner: "Dinner",
    lunch: "Lunch",
    meals: "Meals",
    on: "On",
    off: "Off",
    confirm_off: "Turn off Shabbat Mode?",
    hold_hint: "Press and hold",
    days_of_week: {
      Monday: "Mon",
      Tuesday: "Tue",
      Wednesday: "Wed",
      Thursday: "Thu",
      Friday: "Fri",
      Saturday: "Sat",
      Sunday: "Sun",
    },
    days_of_week_full: {
      Monday: "Monday",
      Tuesday: "Tuesday",
      Wednesday: "Wednesday",
      Thursday: "Thursday",
      Friday: "Friday",
      Saturday: "Saturday",
      Sunday: "Sunday",
    },
  },
};

class DiraShabatCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._config = {};
    this._hass = null;
  }

  set hass(hass) {
    this._hass = hass;
    const sig = this._stateSignature();
    if (sig === this._lastSig) return;
    this._lastSig = sig;
    this._render();
  }

  _stateSignature() {
    if (!this._hass || !this._config) return "";
    const parts = [
      this._config.show_times_entity,
      this._config.modo_shabat_entity,
      this._config.candle_lighting_entity,
      this._config.havdalah_entity,
      this._config.total_days_entity,
    ];
    const prefix = this._config.entity_prefix;
    for (let d = 1; d <= 3; d++) {
      parts.push(`switch.${prefix}_day_${d}_dinner`);
      parts.push(`switch.${prefix}_day_${d}_lunch`);
    }
    parts.push(`switch.${prefix}_option_1`);
    parts.push(`switch.${prefix}_option_2`);
    return parts
      .map((id) => {
        const s = this._hass.states[id];
        if (!s) return "_";
        const attr = id === this._config.total_days_entity ? JSON.stringify(s.attributes?.period_days || 0) : "";
        return `${s.state}${attr}`;
      })
      .join("|");
  }

  _isEntityOn(entityId) {
    const s = this._getState(entityId);
    return !!(s && s.state === "on");
  }

  setConfig(config) {
    if (!config) {
      throw new Error("Invalid configuration");
    }
    this._config = {
      language: "es",
      show_header: true,
      entity_prefix: "dira_shabat",
      show_times_entity: "",
      modo_shabat_entity: "",
      candle_lighting_entity: "",
      havdalah_entity: "",
      total_days_entity: "",
      ...config,
    };

    const prefix = this._config.entity_prefix;
    for (const [key, builder] of Object.entries(AUTO_ENTITIES)) {
      if (!this._config[key]) this._config[key] = builder(prefix);
    }
  }

  getCardSize() {
    return 4;
  }

  static getConfigElement() {
    return document.createElement("dira-shabat-card-editor");
  }

  static getStubConfig() {
    return {
      language: "es",
      entity_prefix: "dira_shabat",
    };
  }

  _getState(entityId) {
    if (!this._hass || !entityId) return null;
    return this._hass.states[entityId];
  }

  _toggleEntity(entityId) {
    if (!this._hass || !entityId) return;
    this._hass.callService("switch", "toggle", {
      entity_id: entityId,
    });
  }

  _attachHoldHandler(element, callback, holdMs = 500) {
    const start = (e) => {
      if (e.type === "touchstart") e.preventDefault();
      element.classList.add("holding");
      this._holdTimer = setTimeout(() => {
        this._holdTimer = null;
        element.classList.remove("holding");
        if (navigator.vibrate) navigator.vibrate(50);
        callback();
      }, holdMs);
    };

    const cancel = () => {
      if (this._holdTimer) {
        clearTimeout(this._holdTimer);
        this._holdTimer = null;
      }
      element.classList.remove("holding");
    };

    element.addEventListener("mousedown", start);
    element.addEventListener("mouseup", cancel);
    element.addEventListener("mouseleave", cancel);
    element.addEventListener("touchstart", start, { passive: false });
    element.addEventListener("touchend", cancel);
    element.addEventListener("touchcancel", cancel);
  }

  _render() {
    if (!this._hass || !this._config) return;

    // Cancel any in-progress hold before replacing DOM
    if (this._holdTimer) {
      clearTimeout(this._holdTimer);
      this._holdTimer = null;
    }

    const lang = this._config.language || "es";
    const t = TRANSLATIONS[lang] || TRANSLATIONS.es;
    const prefix = this._config.entity_prefix;

    // Tri-state visibility: hidden only when show_times entity is explicitly "off"
    const showTimesState = this._getState(this._config.show_times_entity);
    const entityExists = showTimesState && showTimesState.state !== "unavailable";
    const shouldShow = !entityExists || showTimesState.state === "on" || this._config.always_show;

    if (!shouldShow) {
      this.shadowRoot.innerHTML = "";
      this.style.display = "none";
      return;
    }
    this.style.display = "";

    const candleLighting = this._getState(this._config.candle_lighting_entity);
    const havdalah = this._getState(this._config.havdalah_entity);
    const totalDays = this._getState(this._config.total_days_entity);

    const candleTime = candleLighting ? candleLighting.state : "--:--";
    const havdalahTime = havdalah ? havdalah.state : "--:--";
    const modoOn = this._isEntityOn(this._config.modo_shabat_entity);
    const numDays = totalDays ? parseInt(totalDays.state, 10) || 1 : 1;
    const periodDays = totalDays?.attributes?.period_days || [];

    const mealItems = [];
    for (let day = 1; day <= numDays; day++) {
      const dayInfo = periodDays[day - 1] || {};
      const dinnerDay = t.days_of_week[dayInfo.dinner_weekday] || dayInfo.dinner_weekday || "";
      const lunchDay = t.days_of_week[dayInfo.lunch_weekday] || dayInfo.lunch_weekday || "";
      const cenaEntity = `switch.${prefix}_day_${day}_dinner`;
      const almuerzoEntity = `switch.${prefix}_day_${day}_lunch`;

      mealItems.push({
        label: t.dinner,
        day: dinnerDay,
        entity: cenaEntity,
        on: this._isEntityOn(cenaEntity),
      });
      mealItems.push({
        label: t.lunch,
        day: lunchDay,
        entity: almuerzoEntity,
        on: this._isEntityOn(almuerzoEntity),
      });
    }

    const isMultiDay = numDays > 1;
    const firstDay = periodDays[0] || {};
    const lastDay = periodDays[numDays - 1] || firstDay;
    const fullDays = t.days_of_week_full || t.days_of_week;
    const candleWeekday = isMultiDay
      ? fullDays[firstDay.dinner_weekday] || firstDay.dinner_weekday || ""
      : "";
    const havdalahWeekday = isMultiDay
      ? fullDays[lastDay.lunch_weekday] || lastDay.lunch_weekday || ""
      : "";

    const mealsHTML = mealItems
      .map(
        (m) => `
        <div class="meal-item">
          <span class="meal-label">${m.label}</span>
          <div class="pill ${m.on ? "on" : ""}" data-entity="${m.entity}">${m.on ? t.on : t.off}</div>
          ${m.day ? `<span class="meal-day">${m.day}</span>` : ""}
        </div>
      `,
      )
      .join("");

    // Options (generic user-configurable switches, shown by friendly_name)
    const optionItems = [1, 2]
      .map((n) => {
        const entityId = `switch.${prefix}_option_${n}`;
        const state = this._getState(entityId);
        if (!state) return null;
        const label = state.attributes?.friendly_name || `Option ${n}`;
        return { entity: entityId, label, on: state.state === "on" };
      })
      .filter(Boolean);

    const optionsHTML = optionItems
      .map(
        (o) => `
        <div class="option-row">
          <span class="option-label">${o.label}</span>
          <div class="pill ${o.on ? "on" : ""}" data-entity="${o.entity}">${o.on ? t.on : t.off}</div>
        </div>
      `,
      )
      .join("");

    this.shadowRoot.innerHTML = `
      <ha-card>
        <div class="times-row">
          <div class="time-block">
            <span class="time-icon"><ha-icon icon="mdi:candle"></ha-icon></span>
            <div class="time-text">
              <span class="time-label">${t.candle_lighting}${candleWeekday ? ` (${candleWeekday})` : ""}</span>
              <span class="time-value">${candleTime}</span>
            </div>
          </div>
          <div class="time-block">
            <span class="time-icon"><ha-icon icon="mdi:moon-waning-crescent"></ha-icon></span>
            <div class="time-text">
              <span class="time-label">${t.ends}${havdalahWeekday ? ` (${havdalahWeekday})` : ""}</span>
              <span class="time-value">${havdalahTime}</span>
            </div>
          </div>
        </div>

        <div class="mode-row ${modoOn ? "on" : ""}" id="mode-toggle" title="${t.hold_hint}">
          <span class="mode-icon"><ha-icon icon="mdi:power-plug"></ha-icon></span>
          <span class="mode-label">${t.shabbat_mode}</span>
          <span class="mode-status">${modoOn ? t.on : t.off}</span>
        </div>

        ${modoOn ? `
        <div class="meals-header">
          <span class="mode-icon"><ha-icon icon="mdi:silverware-fork-knife"></ha-icon></span>
          <span class="meals-title">${t.meals}</span>
        </div>
        <div class="meals-row" style="--meal-count: ${mealItems.length};">
          ${mealsHTML}
        </div>
        ${optionItems.length ? `<div class="options-section">${optionsHTML}</div>` : ""}
        ` : ""}
      </ha-card>
    `;

    const sheet = getStyleSheet();
    if (sheet) {
      this.shadowRoot.adoptedStyleSheets = [sheet];
    } else {
      const style = document.createElement("style");
      style.textContent = CARD_CSS;
      this.shadowRoot.insertBefore(style, this.shadowRoot.firstChild);
    }

    const modeToggle = this.shadowRoot.getElementById("mode-toggle");
    if (modeToggle) {
      this._attachHoldHandler(modeToggle, () => {
        const isOn = this._isEntityOn(this._config.modo_shabat_entity);
        if (isOn && !window.confirm(t.confirm_off)) return;
        this._toggleEntity(this._config.modo_shabat_entity);
      });
    }

    this.shadowRoot.querySelectorAll(".pill").forEach((pill) => {
      pill.addEventListener("click", (e) => {
        e.stopPropagation();
        const entityId = pill.dataset.entity;
        if (entityId) this._toggleEntity(entityId);
      });
    });
  }
}

/**
 * Card Editor for visual configuration
 */
class DiraShabatCardEditor extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._config = {};
    this._hass = null;
  }

  set hass(hass) {
    this._hass = hass;
  }

  setConfig(config) {
    this._config = { ...config };
    this._render();
  }

  _render() {
    this.shadowRoot.innerHTML = `
      <style>
        .editor-row {
          display: flex;
          flex-direction: column;
          gap: 8px;
          padding: 8px 0;
        }
        label {
          font-weight: 500;
          font-size: 14px;
          color: var(--primary-text-color);
        }
        select, input {
          padding: 8px 12px;
          border-radius: 8px;
          border: 1px solid var(--divider-color, #ccc);
          background: var(--card-background-color, #fff);
          color: var(--primary-text-color);
          font-size: 14px;
        }
        .checkbox-row {
          display: flex;
          align-items: center;
          gap: 8px;
        }
      </style>

      <div class="editor-row">
        <label>Language / Idioma</label>
        <select id="language">
          <option value="es" ${this._config.language === "es" ? "selected" : ""}>Espa\u00f1ol</option>
          <option value="en" ${this._config.language === "en" ? "selected" : ""}>English</option>
        </select>
      </div>

      <div class="editor-row">
        <label>Entity Prefix</label>
        <input type="text" id="entity_prefix" value="${this._config.entity_prefix || "dira_shabat"}" />
      </div>

      <div class="editor-row">
        <div class="checkbox-row">
          <input type="checkbox" id="always_show" ${this._config.always_show ? "checked" : ""} />
          <label for="always_show">Always show card / Mostrar siempre</label>
        </div>
      </div>

      <div class="editor-row">
        <div class="checkbox-row">
          <input type="checkbox" id="show_header" ${this._config.show_header !== false ? "checked" : ""} />
          <label for="show_header">Show times header / Mostrar horarios</label>
        </div>
      </div>
    `;

    // Attach change listeners
    this.shadowRoot.getElementById("language").addEventListener("change", (e) => {
      this._updateConfig("language", e.target.value);
    });
    this.shadowRoot.getElementById("entity_prefix").addEventListener("input", (e) => {
      this._updateConfig("entity_prefix", e.target.value);
    });
    this.shadowRoot.getElementById("always_show").addEventListener("change", (e) => {
      this._updateConfig("always_show", e.target.checked);
    });
    this.shadowRoot.getElementById("show_header").addEventListener("change", (e) => {
      this._updateConfig("show_header", e.target.checked);
    });
  }

  _updateConfig(key, value) {
    this._config = { ...this._config, [key]: value };
    if (key === "entity_prefix") {
      for (const k of Object.keys(AUTO_ENTITIES)) delete this._config[k];
    }
    this.dispatchEvent(
      new CustomEvent("config-changed", {
        detail: { config: this._config },
        bubbles: true,
        composed: true,
      }),
    );
  }
}

for (const [tag, cls] of [
  ["dira-shabat-card", DiraShabatCard],
  ["dira-shabat-card-editor", DiraShabatCardEditor],
]) {
  if (!customElements.get(tag)) customElements.define(tag, cls);
}

window.customCards = window.customCards || [];
if (!window.customCards.some((c) => c.type === "dira-shabat-card")) {
  window.customCards.push({
    type: "dira-shabat-card",
    name: "Dira Shabat",
    description: "Manage Shabbat and Jewish Holiday modes with meal toggles",
    preview: true,
    documentationURL: "https://github.com/jbran/dira-shabat",
  });
}
