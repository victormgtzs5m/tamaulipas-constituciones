"""Navegacion principal con submenus hover y estado nativo de Streamlit."""
import streamlit as st
from streamlit.components.v2 import component

VERSION_MENU = 2

GRUPOS = [
    ("Producci\u00f3n por pozo", ["Producci\u00f3n por pozo"]),
    ("Comparativa por pozo", ["Comparativa por pozo"]),
    ("Mapas", ["Mapas", "Modo Animado"]),
    ("Campa\u00f1as 2011-2020", ["Campa\u00f1as 2011-2020"]),
    ("RMA 2011-2020", ["RMA 2011-2020"]),
    ("Operaci\u00f3n Campo", ["Operaci\u00f3n Campo"]),
    ("Producci\u00f3n Campo", ["Producci\u00f3n Campo"]),
    ("Presiones", ["Presiones"]),
    ("Estad\u00edstica", ["Estad\u00edstica"]),
    ("Inyecci\u00f3n", ["Inyecci\u00f3n"]),
    ("Reservas", ["Reservas"]),
    ("Pron\u00f3stico", ["Pron\u00f3stico", "Type Curve"]),
    ("An\u00e1lisis", ["RGA por yacimiento", "Screening Pozos", "Waterflood"]),
]

CSS = """
* { box-sizing: border-box; }
.nav-shell { padding: 10px 0 18px; font-family: 'Segoe UI', Arial, sans-serif; }
.nav-bar { position: relative; display: flex; flex-wrap: wrap; align-items: center;
  gap: 4px; padding: 7px; border-radius: 12px; background: #34495e;
  box-shadow: 0 8px 22px rgba(20,35,50,.16); }
.nav-item { position: relative; z-index: 1; border: 0; border-radius: 8px;
  background: transparent; color: #edf3f7; padding: 13px 14px;
  font: 600 13px/1.3 'Segoe UI', Arial, sans-serif; cursor: pointer;
  display: inline-flex; align-items: center; justify-content: center; gap: 8px;
  min-height: 44px; transition: none; }
.nav-item[aria-current='page'] { background: rgba(26,188,156,.18); }
.nav-item:focus-visible, .menu-option:focus-visible { outline: 2px solid #7cf4db; outline-offset: -3px; }
.nav-item .chevron { font-size: 10px; transition: transform .2s; }
.nav-item[aria-expanded='true'] .chevron { transform: rotate(180deg); }
.nav-lava { position: absolute; top: 0; left: 0; border-radius: 8px;
  background: #1abc9c; box-shadow: 0 3px 12px rgba(26,188,156,.22);
  pointer-events: none; transition: none;
  z-index: 0; }
.nav-dropdown { position: fixed; inset: auto; margin: 0; padding: 7px;
  min-width: 230px; max-width: calc(100vw - 24px); border: 1px solid #496075;
  border-radius: 10px; background: #2c3e50; color: #fff;
  box-shadow: 0 14px 34px rgba(15,23,42,.3); overflow: auto;
  max-height: min(360px, 65vh); font-family: 'Segoe UI', Arial, sans-serif; }
.nav-dropdown:popover-open { display: grid; gap: 4px; }
.menu-option { display: block; width: 100%; text-align: left; padding: 12px 14px;
  min-height: 44px; border: 0; border-radius: 6px; background: transparent; color: #edf3f7;
  font: 600 13px/1.4 'Segoe UI', Arial, sans-serif; cursor: pointer;
  transition: none; }
.menu-option:hover, .menu-option:focus-visible { background: #40576d; }
.menu-option[aria-current='page'] { background: #1abc9c; color: #fff; }
@media (max-width: 700px) {
  .nav-item { flex: 1 1 auto; padding: 11px 10px; font-size: 12px; }
  .nav-bar { gap: 3px; }
}
@media (prefers-reduced-motion: reduce) {
  .nav-lava, .nav-item .chevron { transition: none; }
}
"""

JS = """
export default function(component) {
  const { parentElement, data, setTriggerValue } = component;
  const root = parentElement.querySelector('.nav-root');
  root.replaceChildren();
  const shell = document.createElement('div'); shell.className = 'nav-shell';
  const nav = document.createElement('nav'); nav.className = 'nav-bar';
  nav.setAttribute('aria-label', 'Navegaci\u00f3n principal');
  const lava = document.createElement('span'); lava.className = 'nav-lava';
  lava.setAttribute('aria-hidden', 'true'); nav.append(lava);
  shell.append(nav); root.append(shell);
  let activeButton = null, opened = null, timer = null;
  const buttons = [], menus = [];
  const move = (button) => {
    if (!button) return;
    lava.style.width = button.offsetWidth + 'px';
    lava.style.height = button.offsetHeight + 'px';
    lava.style.transform = `translate(${button.offsetLeft}px, ${button.offsetTop}px)`;
  };
  const close = () => {
    clearTimeout(timer);
    if (opened) {
      opened.menu.hidePopover(); opened.button.setAttribute('aria-expanded', 'false');
      opened = null;
    }
    move(activeButton);
  };
  const scheduleClose = () => { clearTimeout(timer); timer = setTimeout(close, 180); };
  const position = (button, menu) => {
    const r = button.getBoundingClientRect();
    menu.style.left = Math.max(12, Math.min(r.left, window.innerWidth - menu.offsetWidth - 12)) + 'px';
    const below = r.bottom + 6;
    menu.style.top = (below + menu.offsetHeight <= window.innerHeight
      ? below : Math.max(12, r.top - menu.offsetHeight - 6)) + 'px';
  };
  const open = (button, menu) => {
    clearTimeout(timer);
    if (opened && opened.menu !== menu) close();
    if (!menu.matches(':popover-open')) menu.showPopover();
    opened = { button, menu }; button.setAttribute('aria-expanded', 'true');
    position(button, menu); move(button);
  };
  const select = (value, button) => {
    close(); activeButton = button; move(button);
    setTriggerValue('selected', value);
  };
  data.groups.forEach(([label, options], groupIndex) => {
    const button = document.createElement('button'); button.type = 'button';
    button.className = 'nav-item'; button.textContent = label;
    buttons.push(button); nav.append(button);
    if (options.includes(data.active)) {
      activeButton = button; button.setAttribute('aria-current', 'page');
    }
    button.addEventListener('mouseenter', () => { clearTimeout(timer); move(button); });
    button.addEventListener('focus', () => move(button));
    if (options.length === 1) {
      button.addEventListener('mouseenter', () => { close(); move(button); });
      button.addEventListener('click', () => select(options[0], button));
      return;
    }
    const chevron = document.createElement('span'); chevron.className = 'chevron';
    chevron.textContent = '\u25be'; chevron.setAttribute('aria-hidden', 'true'); button.append(chevron);
    const menu = document.createElement('div'); menu.className = 'nav-dropdown';
    menu.id = 'module-menu-' + groupIndex; menu.setAttribute('popover', 'manual');
    menu.setAttribute('aria-label', label); root.append(menu); menus.push(menu);
    button.setAttribute('aria-expanded', 'false'); button.setAttribute('aria-controls', menu.id);
    options.forEach((option) => {
      const item = document.createElement('button'); item.type = 'button';
      item.className = 'menu-option'; item.textContent = option;
      if (option === data.active) item.setAttribute('aria-current', 'page');
      item.addEventListener('click', () => select(option, button)); menu.append(item);
    });
    button.addEventListener('mouseenter', () => open(button, menu));
    button.addEventListener('mouseleave', scheduleClose);
    button.addEventListener('click', () => {
      if (opened && opened.menu === menu && !window.matchMedia('(hover: hover)').matches) close();
      else open(button, menu);
    });
    button.addEventListener('keydown', (event) => {
      if (event.key === 'ArrowDown') {
        event.preventDefault(); open(button, menu); menu.querySelector('button').focus();
      }
    });
    menu.addEventListener('mouseenter', () => clearTimeout(timer));
    menu.addEventListener('mouseleave', scheduleClose);
    menu.addEventListener('keydown', (event) => {
      const items = [...menu.querySelectorAll('button')];
      const index = items.indexOf(menu.getRootNode().activeElement);
      if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
        event.preventDefault();
        items[(index + (event.key === 'ArrowDown' ? 1 : -1) + items.length) % items.length].focus();
      }
      if (event.key === 'Escape') { close(); button.focus(); }
    });
    menu.addEventListener('focusout', (event) => {
      if (!menu.contains(event.relatedTarget) && event.relatedTarget !== button) scheduleClose();
    });
  });
  nav.addEventListener('mouseleave', () => { if (!opened) move(activeButton); });
  nav.addEventListener('focusout', () => { if (!opened) move(activeButton); });
  const onOutside = (event) => {
    if (!event.composedPath().includes(root)) close();
  };
  const onEscape = (event) => { if (event.key === 'Escape') close(); };
  document.addEventListener('pointerdown', onOutside);
  document.addEventListener('keydown', onEscape);
  window.addEventListener('scroll', close, true);
  const observer = new ResizeObserver(() => { close(); move(activeButton); });
  observer.observe(nav);
  requestAnimationFrame(() => move(activeButton));
  return () => {
    clearTimeout(timer); observer.disconnect();
    document.removeEventListener('pointerdown', onOutside);
    document.removeEventListener('keydown', onEscape);
    window.removeEventListener('scroll', close, true);
    menus.forEach(menu => { if (menu.matches(':popover-open')) menu.hidePopover(); });
  };
}
"""

_menu = component("menu_principal_lavalamp", html='<div class="nav-root"></div>', css=CSS, js=JS)


def renderizar_menu():
    opciones = [opcion for _, grupo in GRUPOS for opcion in grupo]
    actual = st.session_state.get("vista_principal", opciones[0])
    if actual not in opciones:
        actual = opciones[0]
    resultado = _menu(
        key="menu_modulos", data={"groups": GRUPOS, "active": actual},
        on_selected_change=lambda: None,
    )
    if resultado.selected in opciones and resultado.selected != actual:
        st.session_state["vista_principal"] = resultado.selected
        st.rerun()
    st.session_state["vista_principal"] = actual
    return actual
