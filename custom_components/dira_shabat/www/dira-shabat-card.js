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
  show_times_entity: (p) => `binary_sensor.${p}_mostrar_horarios`,
  modo_shabat_entity: (p) => `switch.${p}_modo_shabat`,
  candle_lighting_entity: (p) => `sensor.${p}_encendido_velas`,
  havdalah_entity: (p) => `sensor.${p}_finaliza`,
  total_days_entity: (p) => `sensor.${p}_dias_totales`,
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

  /* Times row: icon + label + time, inline, no backgrounds */
  .times-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 12px;
    flex-wrap: wrap;
  }
  .time-block {
    display: flex;
    align-items: center;
    gap: 6px;
    min-width: 0;
  }
  .time-icon {
    color: var(--accent);
    --mdc-icon-size: 18px;
    line-height: 1;
    flex: 0 0 auto;
  }
  .time-label {
    font-size: 13px;
    color: var(--text-secondary);
    font-weight: 500;
  }
  .time-value {
    font-size: 15px;
    font-weight: 600;
    color: var(--text-primary);
  }

  /* Mode row: pressable, state-aware */
  .mode-row {
    margin-top: 10px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    padding: 10px 12px;
    border-top: 1px solid var(--divider-color);
    border-bottom: 1px solid var(--divider-color);
    border-left: 3px solid transparent;
    cursor: pointer;
    user-select: none;
    -webkit-user-select: none;
    position: relative;
    overflow: hidden;
    transition: border-left-color 0.25s ease;
  }
  .mode-row.on {
    border-left-color: var(--accent);
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
  .mode-left {
    display: flex;
    align-items: center;
    gap: 10px;
    min-width: 0;
  }
  .mode-icon {
    --mdc-icon-size: 22px;
    line-height: 1;
    color: var(--text-secondary);
    transition: color 0.25s ease, filter 0.25s ease;
  }
  .mode-row.on .mode-icon {
    color: var(--accent);
    filter: drop-shadow(0 0 6px var(--accent));
    animation: flicker 2.5s ease-in-out infinite;
  }
  @keyframes flicker {
    0%, 100% { opacity: 1; }
    45% { opacity: 0.85; }
    55% { opacity: 1; }
    70% { opacity: 0.9; }
  }
  .mode-label {
    font-size: 15px;
    font-weight: 600;
  }
  .mode-status {
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.8px;
    text-transform: uppercase;
    padding: 4px 12px;
    border-radius: 999px;
    background: var(--toggle-off-bg);
    color: var(--text-secondary);
    transition: background 0.25s ease, color 0.25s ease;
  }
  .mode-row.on .mode-status {
    background: var(--accent);
    color: white;
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
    grid-template-columns: repeat(var(--meal-count, 2), 1fr);
    gap: 4px;
    padding-bottom: 2px;
  }
  .meal-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 4px;
    min-width: 0;
  }
  .meal-label {
    font-size: 12px;
    font-weight: 500;
    color: var(--text-primary);
    line-height: 1.2;
  }
  .meal-day {
    font-size: 11px;
    color: var(--text-secondary);
    line-height: 1.2;
  }

  /* Toggle switch */
  .toggle {
    position: relative;
    display: inline-block;
    width: 40px;
    height: 22px;
    cursor: pointer;
    margin: 2px 0;
  }
  .toggle input {
    opacity: 0;
    width: 0;
    height: 0;
    position: absolute;
  }
  .slider {
    position: absolute;
    inset: 0;
    background-color: var(--toggle-off-bg);
    border-radius: 22px;
    transition: background-color 0.25s ease;
  }
  .slider::before {
    content: "";
    position: absolute;
    height: 16px;
    width: 16px;
    left: 3px;
    bottom: 3px;
    background-color: white;
    border-radius: 50%;
    transition: transform 0.25s ease;
  }
  .toggle input:checked + .slider {
    background-color: var(--accent);
  }
  .toggle input:checked + .slider::before {
    transform: translateX(18px);
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
      parts.push(`switch.${prefix}_dia_${d}_cena`);
      parts.push(`switch.${prefix}_dia_${d}_almuerzo`);
    }
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
      const cenaEntity = `switch.${prefix}_dia_${day}_cena`;
      const almuerzoEntity = `switch.${prefix}_dia_${day}_almuerzo`;

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

    const firstDay = periodDays[0] || {};
    const lastDay = periodDays[numDays - 1] || firstDay;
    const candleWeekday = t.days_of_week[firstDay.dinner_weekday] || firstDay.dinner_weekday || "";
    const havdalahWeekday = t.days_of_week[lastDay.lunch_weekday] || lastDay.lunch_weekday || "";

    const mealsHTML = mealItems
      .map(
        (m) => `
        <div class="meal-item">
          <span class="meal-label">${m.label}</span>
          <label class="toggle" data-entity="${m.entity}">
            <input type="checkbox" ${m.on ? "checked" : ""} />
            <span class="slider"></span>
          </label>
          ${m.day ? `<span class="meal-day">${m.day}</span>` : ""}
        </div>
      `,
      )
      .join("");

    this.shadowRoot.innerHTML = `
      <ha-card>
        <div class="times-row">
          <div class="time-block">
            <span class="time-icon"><ha-icon icon="mdi:candle"></ha-icon></span>
            <span class="time-label">${t.candle_lighting}${candleWeekday ? ` (${candleWeekday})` : ""}</span>
            <span class="time-value">${candleTime}</span>
          </div>
          <div class="time-block">
            <span class="time-icon"><ha-icon icon="mdi:moon-waning-crescent"></ha-icon></span>
            <span class="time-label">${t.ends}${havdalahWeekday ? ` (${havdalahWeekday})` : ""}</span>
            <span class="time-value">${havdalahTime}</span>
          </div>
        </div>

        <div class="mode-row ${modoOn ? "on" : ""}" id="mode-toggle" title="${t.hold_hint}">
          <div class="mode-left">
            <span class="mode-icon"><ha-icon icon="${modoOn ? "mdi:candle" : "mdi:candle-outline"}"></ha-icon></span>
            <span class="mode-label">${t.shabbat_mode}</span>
          </div>
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

    this.shadowRoot.querySelectorAll(".meal-chip").forEach((chip) => {
      chip.addEventListener("click", () => {
        const entityId = chip.dataset.entity;
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
