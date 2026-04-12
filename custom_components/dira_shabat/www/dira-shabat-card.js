/**
 * Dira Shabat Card - Custom Lovelace Card for Home Assistant
 * Manages Shabbat and Jewish Holiday display with meal toggles
 */

console.info(
  `%c DIRA-SHABAT-CARD %c v1.0.0 `,
  "color: white; background: #6a3de8; font-weight: 700; padding: 2px 8px; border-radius: 4px 0 0 4px;",
  "color: #6a3de8; background: #ede7f6; font-weight: 700; padding: 2px 8px; border-radius: 0 4px 4px 0;"
);

const TRANSLATIONS = {
  es: {
    candle_lighting: "Encendido velas",
    ends: "Finaliza",
    shabbat_mode: "Modo Shabat",
    dinner: "Cena",
    lunch: "Almuerzo",
    meals: "Comidas",
    on: "On",
    off: "Off",
    days_of_week: {
      Monday: "Lun",
      Tuesday: "Mar",
      Wednesday: "Mié",
      Thursday: "Jue",
      Friday: "Vie",
      Saturday: "Sáb",
      Sunday: "Dom",
    },
  },
  en: {
    candle_lighting: "Candle Lighting",
    ends: "Ends",
    shabbat_mode: "Shabbat Mode",
    dinner: "Dinner",
    lunch: "Lunch",
    meals: "Meals",
    on: "On",
    off: "Off",
    days_of_week: {
      Monday: "Mon",
      Tuesday: "Tue",
      Wednesday: "Wed",
      Thursday: "Thu",
      Friday: "Fri",
      Saturday: "Sat",
      Sunday: "Sun",
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
    this._render();
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

    // Auto-detect entities if not specified
    const prefix = this._config.entity_prefix;
    if (!this._config.show_times_entity) {
      this._config.show_times_entity = `binary_sensor.${prefix}_mostrar_horarios`;
    }
    if (!this._config.modo_shabat_entity) {
      this._config.modo_shabat_entity = `switch.${prefix}_modo_shabat`;
    }
    if (!this._config.candle_lighting_entity) {
      this._config.candle_lighting_entity = `sensor.${prefix}_encendido_velas`;
    }
    if (!this._config.havdalah_entity) {
      this._config.havdalah_entity = `sensor.${prefix}_finaliza`;
    }
    if (!this._config.total_days_entity) {
      this._config.total_days_entity = `sensor.${prefix}_dias_totales`;
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

  _render() {
    if (!this._hass || !this._config) return;

    const lang = this._config.language || "es";
    const t = TRANSLATIONS[lang] || TRANSLATIONS.es;
    const prefix = this._config.entity_prefix;

    // Check visibility
    const showTimesState = this._getState(this._config.show_times_entity);
    // Show if: entity is "on", entity doesn't exist yet, or always_show is true
    const entityExists = showTimesState && showTimesState.state !== "unavailable";
    const shouldShow = !entityExists || showTimesState.state === "on" || this._config.always_show;

    if (!shouldShow) {
      this.shadowRoot.innerHTML = "";
      this.style.display = "none";
      return;
    }
    this.style.display = "";

    // Get states
    const modoShabat = this._getState(this._config.modo_shabat_entity);
    const candleLighting = this._getState(this._config.candle_lighting_entity);
    const havdalah = this._getState(this._config.havdalah_entity);
    const totalDays = this._getState(this._config.total_days_entity);

    const candleTime = candleLighting ? candleLighting.state : "--:--";
    const havdalahTime = havdalah ? havdalah.state : "--:--";
    const modoOn = modoShabat && modoShabat.state === "on";
    const numDays = totalDays ? parseInt(totalDays.state) || 1 : 1;
    const periodDays =
      totalDays && totalDays.attributes && totalDays.attributes.period_days
        ? totalDays.attributes.period_days
        : [];

    // Build meal toggles HTML
    let mealsHTML = "";
    for (let day = 1; day <= numDays; day++) {
      const dayInfo = periodDays[day - 1] || {};
      const dayName = dayInfo.day_name || (lang === "es" ? "Shabat" : "Shabbat");
      const dinnerWeekday = dayInfo.dinner_weekday || "";
      const lunchWeekday = dayInfo.lunch_weekday || "";
      const dinnerDay = t.days_of_week[dinnerWeekday] || dinnerWeekday;
      const lunchDay = t.days_of_week[lunchWeekday] || lunchWeekday;

      const cenaEntity = `switch.${prefix}_dia_${day}_cena`;
      const almuerzoEntity = `switch.${prefix}_dia_${day}_almuerzo`;
      const cenaState = this._getState(cenaEntity);
      const almuerzoState = this._getState(almuerzoEntity);
      const cenaOn = cenaState && cenaState.state === "on";
      const almuerzoOn = almuerzoState && almuerzoState.state === "on";

      const isMultiDay = numDays > 1;

      mealsHTML += `
        <div class="day-section ${isMultiDay ? "multi-day" : ""}">
          ${
            isMultiDay
              ? `<div class="day-header">
                  <span class="day-name">${dayName}</span>
                </div>`
              : ""
          }
          <div class="meals-row">
            <div class="meal-item">
              <div class="meal-label">${t.dinner}${dinnerDay ? ` (${dinnerDay})` : ""}</div>
              <label class="toggle" data-entity="${cenaEntity}">
                <input type="checkbox" ${cenaOn ? "checked" : ""} />
                <span class="slider"></span>
              </label>
            </div>
            <div class="meal-item">
              <div class="meal-label">${t.lunch}${lunchDay ? ` (${lunchDay})` : ""}</div>
              <label class="toggle" data-entity="${almuerzoEntity}">
                <input type="checkbox" ${almuerzoOn ? "checked" : ""} />
                <span class="slider"></span>
              </label>
            </div>
          </div>
        </div>
      `;
    }

    this.shadowRoot.innerHTML = `
      <style>
        :host {
          --card-bg: var(--ha-card-background, var(--card-background-color, #1c1c1e));
          --section-bg: var(--primary-background-color, #2c2c2e);
          --text-primary: var(--primary-text-color, #ffffff);
          --text-secondary: var(--secondary-text-color, #a0a0a5);
          --accent-color: var(--primary-color, #4a9eff);
          --toggle-off-bg: #3a3a3c;
          --divider-color: var(--divider-color, rgba(255,255,255,0.08));
        }

        ha-card {
          background: var(--card-bg);
          border-radius: 16px;
          overflow: hidden;
          color: var(--text-primary);
          font-family: var(--ha-card-font-family, inherit);
        }

        .times-section {
          display: flex;
          justify-content: space-around;
          align-items: center;
          padding: 20px 24px;
          background: var(--section-bg);
          border-radius: 12px;
          margin: 12px;
        }

        .time-block {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 8px;
        }

        .time-label {
          font-size: 13px;
          color: var(--text-secondary);
          font-weight: 500;
          letter-spacing: 0.3px;
        }

        .time-icon {
          font-size: 28px;
          color: var(--accent-color);
          line-height: 1;
        }

        .time-value {
          font-size: 24px;
          font-weight: 600;
          color: var(--text-primary);
          letter-spacing: 0.5px;
        }

        .mode-section {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 14px 20px;
          margin: 0 12px;
          background: var(--section-bg);
          border-radius: 12px;
          margin-bottom: 8px;
          cursor: pointer;
          transition: background 0.2s ease;
        }

        .mode-section:active {
          background: rgba(255,255,255,0.05);
        }

        .mode-left {
          display: flex;
          align-items: center;
          gap: 12px;
        }

        .mode-icon {
          font-size: 22px;
          color: var(--accent-color);
        }

        .mode-label {
          font-size: 15px;
          font-weight: 500;
        }

        .mode-status {
          font-size: 14px;
          font-weight: 600;
          color: var(--accent-color);
        }

        .mode-status.off {
          color: var(--text-secondary);
        }

        .meals-container {
          margin: 0 12px 12px;
          background: var(--section-bg);
          border-radius: 12px;
          padding: 14px 20px;
        }

        .meals-header {
          display: flex;
          align-items: center;
          gap: 12px;
          margin-bottom: 12px;
        }

        .meals-icon {
          font-size: 22px;
          color: var(--accent-color);
        }

        .meals-title {
          font-size: 15px;
          font-weight: 500;
        }

        .day-section {
          padding: 4px 0;
        }

        .day-section.multi-day {
          padding: 8px 0;
          border-bottom: 1px solid var(--divider-color);
        }

        .day-section.multi-day:last-child {
          border-bottom: none;
          padding-bottom: 0;
        }

        .day-header {
          margin-bottom: 8px;
        }

        .day-name {
          font-size: 13px;
          font-weight: 600;
          color: var(--accent-color);
          text-transform: uppercase;
          letter-spacing: 0.5px;
        }

        .meals-row {
          display: flex;
          justify-content: space-around;
          gap: 16px;
        }

        .meal-item {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 8px;
          flex: 1;
        }

        .meal-label {
          font-size: 12px;
          color: var(--text-secondary);
          font-weight: 500;
          text-align: center;
        }

        /* Toggle Switch */
        .toggle {
          position: relative;
          display: inline-block;
          width: 48px;
          height: 26px;
          cursor: pointer;
        }

        .toggle input {
          opacity: 0;
          width: 0;
          height: 0;
        }

        .slider {
          position: absolute;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background-color: var(--toggle-off-bg);
          border-radius: 26px;
          transition: background-color 0.3s ease;
        }

        .slider::before {
          content: "";
          position: absolute;
          height: 20px;
          width: 20px;
          left: 3px;
          bottom: 3px;
          background-color: white;
          border-radius: 50%;
          transition: transform 0.3s ease;
        }

        .toggle input:checked + .slider {
          background-color: var(--accent-color);
        }

        .toggle input:checked + .slider::before {
          transform: translateX(22px);
        }
      </style>

      <ha-card>
        <!-- Times Section -->
        <div class="times-section">
          <div class="time-block">
            <span class="time-label">${t.candle_lighting}</span>
            <span class="time-icon">
              <ha-icon icon="mdi:candle"></ha-icon>
            </span>
            <span class="time-value">${candleTime}</span>
          </div>
          <div class="time-block">
            <span class="time-label">${t.ends}</span>
            <span class="time-icon">
              <ha-icon icon="mdi:moon-waning-crescent"></ha-icon>
            </span>
            <span class="time-value">${havdalahTime}</span>
          </div>
        </div>

        <!-- Mode Section -->
        <div class="mode-section" id="mode-toggle">
          <div class="mode-left">
            <span class="mode-icon">
              <ha-icon icon="mdi:candle"></ha-icon>
            </span>
            <span class="mode-label">${t.shabbat_mode}</span>
          </div>
          <span class="mode-status ${modoOn ? "" : "off"}">${modoOn ? t.on : t.off}</span>
        </div>

        <!-- Meals Section -->
        <div class="meals-container">
          <div class="meals-header">
            <span class="meals-icon">
              <ha-icon icon="mdi:silverware-fork-knife"></ha-icon>
            </span>
            <span class="meals-title">${t.meals}</span>
          </div>
          ${mealsHTML}
        </div>
      </ha-card>
    `;

    // Attach event listeners
    const modeToggle = this.shadowRoot.getElementById("mode-toggle");
    if (modeToggle) {
      modeToggle.addEventListener("click", () => {
        this._toggleEntity(this._config.modo_shabat_entity);
      });
    }

    // Meal toggles
    const toggles = this.shadowRoot.querySelectorAll(".toggle");
    toggles.forEach((toggle) => {
      toggle.addEventListener("click", (e) => {
        e.preventDefault();
        const entityId = toggle.dataset.entity;
        if (entityId) {
          this._toggleEntity(entityId);
        }
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
    // Reset auto-detected entities when prefix changes
    if (key === "entity_prefix") {
      delete this._config.show_times_entity;
      delete this._config.modo_shabat_entity;
      delete this._config.candle_lighting_entity;
      delete this._config.havdalah_entity;
      delete this._config.total_days_entity;
    }
    const event = new CustomEvent("config-changed", {
      detail: { config: this._config },
      bubbles: true,
      composed: true,
    });
    this.dispatchEvent(event);
  }
}

// Register the card (guarded against double-loading)
if (!customElements.get("dira-shabat-card")) {
  customElements.define("dira-shabat-card", DiraShabatCard);
}
if (!customElements.get("dira-shabat-card-editor")) {
  customElements.define("dira-shabat-card-editor", DiraShabatCardEditor);
}

// Register with Lovelace (guarded against double-loading)
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
