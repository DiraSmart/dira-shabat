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
    confirm_off: "¿Deseas apagar el Modo Shabat?",
    hold_hint: "Mantener presionado",
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

  _attachHoldHandler(element, callback, holdMs = 500) {
    let timer = null;
    let fired = false;

    const start = (e) => {
      if (e.type === "touchstart") e.preventDefault();
      fired = false;
      element.classList.add("holding");
      timer = setTimeout(() => {
        fired = true;
        element.classList.remove("holding");
        element.classList.add("hold-complete");
        setTimeout(() => element.classList.remove("hold-complete"), 200);
        // Haptic feedback if available
        if (navigator.vibrate) navigator.vibrate(50);
        callback();
      }, holdMs);
    };

    const cancel = () => {
      if (timer) {
        clearTimeout(timer);
        timer = null;
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

    // Build a flat list of all meals (all days, all meals in one row)
    const mealItems = [];
    for (let day = 1; day <= numDays; day++) {
      const dayInfo = periodDays[day - 1] || {};
      const dinnerWeekday = dayInfo.dinner_weekday || "";
      const lunchWeekday = dayInfo.lunch_weekday || "";
      const dinnerDay = t.days_of_week[dinnerWeekday] || dinnerWeekday;
      const lunchDay = t.days_of_week[lunchWeekday] || lunchWeekday;

      const cenaEntity = `switch.${prefix}_dia_${day}_cena`;
      const almuerzoEntity = `switch.${prefix}_dia_${day}_almuerzo`;
      const cenaState = this._getState(cenaEntity);
      const almuerzoState = this._getState(almuerzoEntity);

      mealItems.push({
        label: t.dinner,
        day: dinnerDay,
        entity: cenaEntity,
        on: cenaState && cenaState.state === "on",
      });
      mealItems.push({
        label: t.lunch,
        day: lunchDay,
        entity: almuerzoEntity,
        on: almuerzoState && almuerzoState.state === "on",
      });
    }

    const mealsHTML = mealItems
      .map(
        (m) => `
        <div class="meal-item">
          <div class="meal-label">${m.label}${m.day ? ` (${m.day})` : ""}</div>
          <label class="toggle" data-entity="${m.entity}">
            <input type="checkbox" ${m.on ? "checked" : ""} />
            <span class="slider"></span>
          </label>
        </div>
      `,
      )
      .join("");

    this.shadowRoot.innerHTML = `
      <style>
        :host {
          --text-primary: var(--primary-text-color);
          --text-secondary: var(--secondary-text-color);
          --accent-color: var(--primary-color);
          --section-bg: var(--secondary-background-color);
          --toggle-off-bg: var(--switch-unchecked-track-color, rgba(128,128,128,0.3));
          --divider-color: var(--divider-color);
        }

        ha-card {
          color: var(--text-primary);
          font-family: var(--ha-card-font-family, inherit);
          overflow: hidden;
        }

        .times-section {
          display: flex;
          justify-content: space-around;
          align-items: center;
          padding: 10px 16px 8px;
          border-bottom: 1px solid var(--divider-color);
        }

        .time-block {
          display: flex;
          flex-direction: row;
          align-items: center;
          gap: 8px;
        }

        .time-label {
          font-size: 12px;
          color: var(--text-secondary);
          font-weight: 500;
        }

        .time-icon {
          font-size: 18px;
          color: var(--accent-color);
          line-height: 1;
          --mdc-icon-size: 18px;
        }

        .time-value {
          font-size: 17px;
          font-weight: 600;
          color: var(--text-primary);
        }

        .mode-section {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 10px 16px;
          cursor: pointer;
          user-select: none;
          -webkit-user-select: none;
          position: relative;
          overflow: hidden;
          transition: background 0.2s ease;
        }

        .meals-container + .mode-section,
        .mode-section + .meals-container {
          border-top: 1px solid var(--divider-color);
        }

        .mode-section::before {
          content: "";
          position: absolute;
          left: 0;
          top: 0;
          bottom: 0;
          width: 0;
          background: var(--accent-color);
          opacity: 0.15;
          transition: width 0s;
        }

        .mode-section.holding::before {
          width: 100%;
          transition: width 500ms linear;
        }

        .mode-section.hold-complete {
          background: var(--accent-color);
          opacity: 0.8;
        }

        .mode-left {
          display: flex;
          align-items: center;
          gap: 10px;
        }

        .mode-icon {
          font-size: 18px;
          color: var(--accent-color);
          --mdc-icon-size: 18px;
        }

        .mode-label {
          font-size: 14px;
          font-weight: 500;
        }

        .mode-status {
          font-size: 13px;
          font-weight: 600;
          color: var(--accent-color);
        }

        .mode-status.off {
          color: var(--text-secondary);
        }

        .meals-container {
          padding: 10px 16px 12px;
          border-top: 1px solid var(--divider-color);
        }

        .meals-header {
          display: flex;
          align-items: center;
          gap: 10px;
          margin-bottom: 10px;
        }

        .meals-icon {
          font-size: 18px;
          color: var(--accent-color);
          --mdc-icon-size: 18px;
        }

        .meals-title {
          font-size: 14px;
          font-weight: 500;
        }

        .meals-row {
          display: grid;
          grid-template-columns: repeat(var(--meal-count, 2), 1fr);
          gap: 8px;
        }

        .meal-item {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 6px;
          min-width: 0;
        }

        .meal-label {
          font-size: 11px;
          color: var(--text-secondary);
          font-weight: 500;
          text-align: center;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
          max-width: 100%;
        }

        /* Toggle Switch */
        .toggle {
          position: relative;
          display: inline-block;
          width: 40px;
          height: 22px;
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
          border-radius: 22px;
          transition: background-color 0.3s ease;
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
          transition: transform 0.3s ease;
        }

        .toggle input:checked + .slider {
          background-color: var(--accent-color);
        }

        .toggle input:checked + .slider::before {
          transform: translateX(18px);
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

        <!-- Meals Section (only when Shabbat mode is on) -->
        ${modoOn ? `
        <div class="meals-container">
          <div class="meals-header">
            <span class="meals-icon">
              <ha-icon icon="mdi:silverware-fork-knife"></ha-icon>
            </span>
            <span class="meals-title">${t.meals}</span>
          </div>
          <div class="meals-row" style="--meal-count: ${mealItems.length};">
            ${mealsHTML}
          </div>
        </div>
        ` : ""}
      </ha-card>
    `;

    // Attach event listeners
    const modeToggle = this.shadowRoot.getElementById("mode-toggle");
    if (modeToggle) {
      this._attachHoldHandler(modeToggle, () => {
        const state = this._getState(this._config.modo_shabat_entity);
        const isOn = state && state.state === "on";
        if (isOn) {
          // Turning OFF requires confirmation
          if (window.confirm(t.confirm_off)) {
            this._toggleEntity(this._config.modo_shabat_entity);
          }
        } else {
          // Turning ON is direct
          this._toggleEntity(this._config.modo_shabat_entity);
        }
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
