/**
 * Dira Shabat Card - Custom Lovelace Card for Home Assistant
 * Manages Shabbat and Jewish Holiday display with meal toggles
 */

console.info(
  `%c DIRA-SHABAT-CARD %c v1.0.0 `,
  "color: white; background: #6a3de8; font-weight: 700; padding: 2px 8px; border-radius: 4px 0 0 4px;",
  "color: #6a3de8; background: #ede7f6; font-weight: 700; padding: 2px 8px; border-radius: 0 4px 4px 0;"
);

const SVG_CANDLES = `<svg viewBox="0 0 28 24" width="26" height="22" fill="none">
  <rect x="8" y="10" width="3.5" height="11" rx="1.2" fill="#E8D5B7"/>
  <rect x="16.5" y="10" width="3.5" height="11" rx="1.2" fill="#E8D5B7"/>
  <line x1="9.75" y1="10" x2="9.75" y2="6" stroke="#D4C4A0" stroke-width="0.7"/>
  <line x1="18.25" y1="10" x2="18.25" y2="6" stroke="#D4C4A0" stroke-width="0.7"/>
  <ellipse cx="9.75" cy="5" rx="2.5" ry="4" fill="#FF9800" opacity="0.85"/>
  <ellipse cx="9.75" cy="4.2" rx="1.3" ry="2.3" fill="#FFD54F"/>
  <ellipse cx="9.75" cy="3.5" rx="0.5" ry="1" fill="#FFF9C4"/>
  <ellipse cx="18.25" cy="5" rx="2.5" ry="4" fill="#FF9800" opacity="0.85"/>
  <ellipse cx="18.25" cy="4.2" rx="1.3" ry="2.3" fill="#FFD54F"/>
  <ellipse cx="18.25" cy="3.5" rx="0.5" ry="1" fill="#FFF9C4"/>
</svg>`;

const SVG_MOON = `<svg viewBox="0 0 24 24" width="22" height="22" fill="none">
  <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" fill="#5C6BC0"/>
  <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" fill="url(#mg)"/>
  <defs><linearGradient id="mg" x1="6" y1="3" x2="18" y2="21"><stop stop-color="#7986CB"/><stop offset="1" stop-color="#3949AB"/></linearGradient></defs>
  <circle cx="7" cy="7.5" r="0.7" fill="#FFD54F"/>
  <circle cx="5" cy="12" r="0.5" fill="#FFD54F" opacity="0.7"/>
  <circle cx="9" cy="17" r="0.6" fill="#FFD54F" opacity="0.8"/>
</svg>`;

const SVG_PLUG = `<svg viewBox="0 0 24 24" width="20" height="20" fill="none">
  <rect x="7" y="2" width="2.5" height="6" rx="1" fill="#66BB6A"/>
  <rect x="14.5" y="2" width="2.5" height="6" rx="1" fill="#66BB6A"/>
  <rect x="5" y="7" width="14" height="8" rx="3" fill="#43A047"/>
  <rect x="10" y="15" width="4" height="3" rx="1" fill="#388E3C"/>
  <rect x="8" y="18" width="8" height="3" rx="1.5" fill="#2E7D32"/>
</svg>`;

const SVG_MEALS = `<svg viewBox="0 0 24 24" width="20" height="20" fill="none">
  <ellipse cx="12" cy="14" rx="8" ry="6" fill="#8D6E63" opacity="0.3"/>
  <ellipse cx="12" cy="13" rx="7.5" ry="5.5" fill="none" stroke="#A1887F" stroke-width="1"/>
  <path d="M7 3v7c0 1.5 1 2.5 2 2.5S11 11.5 11 10V3" stroke="#FFB74D" stroke-width="1.2" stroke-linecap="round"/>
  <line x1="9" y1="3" x2="9" y2="7" stroke="#FFB74D" stroke-width="1.2" stroke-linecap="round"/>
  <path d="M16 3c0 0 2 1.5 2 4s-2 3.5-2 3.5v9" stroke="#90A4AE" stroke-width="1.3" stroke-linecap="round"/>
</svg>`;

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
    font-size: 22px;
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
    font-size: 18px;
    line-height: 1;
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

    this.shadowRoot.innerHTML = `
      <ha-card>
        <div class="times-row">
          <div class="time-block">
            <span class="time-icon">${SVG_CANDLES}</span>
            <div class="time-text">
              <span class="time-label">${t.candle_lighting}${candleWeekday ? ` (${candleWeekday})` : ""}</span>
              <span class="time-value">${candleTime}</span>
            </div>
          </div>
          <div class="time-block">
            <span class="time-icon">${SVG_MOON}</span>
            <div class="time-text">
              <span class="time-label">${t.ends}${havdalahWeekday ? ` (${havdalahWeekday})` : ""}</span>
              <span class="time-value">${havdalahTime}</span>
            </div>
          </div>
        </div>

        <div class="mode-row ${modoOn ? "on" : ""}" id="mode-toggle" title="${t.hold_hint}">
          <span class="mode-icon">${SVG_PLUG}</span>
          <span class="mode-label">${t.shabbat_mode}</span>
          <span class="mode-status">${modoOn ? t.on : t.off}</span>
        </div>

        ${modoOn ? `
        <div class="meals-header">
          <span class="mode-icon">${SVG_MEALS}</span>
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
