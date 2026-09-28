"use client";

import { useSyncExternalStore } from "react";

export const THEME_STORAGE_KEY = "theme";

function applyTheme(dark: boolean) {
  document.documentElement.classList.toggle("dark", dark);
}

function SunIcon() {
  return (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" aria-hidden="true">
      <circle cx="12" cy="12" r="4" />
      <path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41" />
    </svg>
  );
}

function MoonIcon() {
  return (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
      <path d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 1020.354 15.354z" />
    </svg>
  );
}

// The "dark" class on <html> is the source of truth (set before paint by the theme script);
// watch it so every toggle instance stays in sync
function subscribeToTheme(onChange: () => void) {
  const observer = new MutationObserver(onChange);
  observer.observe(document.documentElement, { attributes: true, attributeFilter: ["class"] });
  return () => observer.disconnect();
}

const isDark = () => document.documentElement.classList.contains("dark");
const noopSubscribe = () => () => {};

export function ThemeToggle() {
  // false during server render and hydration, true once running in the browser
  const mounted = useSyncExternalStore(noopSubscribe, () => true, () => false);
  const dark = useSyncExternalStore(subscribeToTheme, isDark, () => false);

  function handleToggle() {
    const next = !dark;
    applyTheme(next);
    try {
      localStorage.setItem(THEME_STORAGE_KEY, next ? "dark" : "light");
    } catch {
      // localStorage unavailable (private browsing, etc.) - theme just won't persist
    }
  }

  if (!mounted) {
    return (
      <button
        aria-hidden="true"
        tabIndex={-1}
        className="p-1.5 text-sun-muted rounded shrink-0"
      >
        <MoonIcon />
      </button>
    );
  }

  return (
    <button
      onClick={handleToggle}
      aria-pressed={dark}
      aria-label={dark ? "Switch to light mode" : "Switch to dark mode"}
      title={dark ? "Switch to light mode" : "Switch to dark mode"}
      className="p-1.5 text-sun-muted hover:text-sun-dark hover:bg-sun-yellow-dim rounded transition-colors shrink-0"
    >
      {dark ? <SunIcon /> : <MoonIcon />}
    </button>
  );
}
