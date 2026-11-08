
import {
  createContext,
  useContext,
  useEffect,
  useRef,
  useState,
} from 'react';
import type { ReactNode } from 'react';

import { useAuth } from './AuthContext';
import { csrfHeader } from '../lib/auth';

export type Appearance = 'cozy' | 'neon';
export type CozyTheme = 'light' | 'dark';

type Preferences = {
  appearance: Appearance;
  cozy_theme: CozyTheme;
};

type AppearanceContextType = {
  appearance: Appearance;
  setAppearance: (value: Appearance) => void;
  cozyTheme: CozyTheme;
  setCozyTheme: (value: CozyTheme) => void;
  theme: CozyTheme;
  toggleTheme: () => void;
};

const AppearanceContext =
  createContext<AppearanceContextType | null>(null);

const APPEARANCE_KEY = 'careerforge-appearance';
const COZY_THEME_KEY = 'careerforge-cozy-theme';
const LEGACY_THEME_KEY = 'careerforge-theme';

function loadAppearance(): Appearance {
  return localStorage.getItem(APPEARANCE_KEY) === 'neon'
    ? 'neon'
    : 'cozy';
}

function loadCozyTheme(): CozyTheme {
  const saved =
    localStorage.getItem(COZY_THEME_KEY) ||
    localStorage.getItem(LEGACY_THEME_KEY);

  return saved === 'dark' ? 'dark' : 'light';
}

export function AppearanceProvider({
  children,
}: {
  children: ReactNode;
}) {
  const { user, loading } = useAuth();

  const [appearance, setAppearanceState] =
    useState<Appearance>(loadAppearance);

  const [cozyTheme, setCozyThemeState] =
    useState<CozyTheme>(loadCozyTheme);

  const valuesRef = useRef<Preferences>({
    appearance,
    cozy_theme: cozyTheme,
  });

  const changeVersion = useRef(0);
  const writeQueue = useRef<Promise<void>>(Promise.resolve());
  const currentUserId = useRef(user?.id ?? null);

  currentUserId.current = user?.id ?? null;

  useEffect(() => {
    if (loading || !user) return;

    let active = true;
    const version = changeVersion.current;

    async function loadPreferences() {
      try {
        const response = await fetch('/api/appearance', {
          credentials: 'include',
          cache: 'no-store',
        });

        if (!response.ok) {
          throw new Error('Could not load appearance preferences.');
        }

        const data: Preferences = await response.json();

        if (!active || changeVersion.current !== version) {
          return;
        }

        const next: Preferences = {
          appearance: data.appearance === 'neon' ? 'neon' : 'cozy',
          cozy_theme: data.cozy_theme === 'dark' ? 'dark' : 'light',
        };

        valuesRef.current = next;
        setAppearanceState(next.appearance);
        setCozyThemeState(next.cozy_theme);
      } catch (error) {
        if (active) {
          console.error('Appearance preferences:', error);
        }
      }
    }

    void loadPreferences();

    return () => {
      active = false;
    };
  }, [user?.id, loading]);

  const theme: CozyTheme =
    appearance === 'neon' ? 'dark' : cozyTheme;

  useEffect(() => {
    document.documentElement.dataset.appearance = appearance;
    document.documentElement.dataset.theme = theme;

    localStorage.setItem(APPEARANCE_KEY, appearance);
    localStorage.setItem(COZY_THEME_KEY, cozyTheme);
    localStorage.setItem(LEGACY_THEME_KEY, cozyTheme);
  }, [appearance, cozyTheme, theme]);

  function persistPreferences(next: Preferences) {
    if (loading || !user) return;

    const accountId = user.id;

    writeQueue.current = writeQueue.current
      .catch(() => {})
      .then(async () => {
        if (currentUserId.current !== accountId) return;

        const response = await fetch('/api/appearance', {
          method: 'PUT',
          credentials: 'include',
          cache: 'no-store',
          headers: {
            'Content-Type': 'application/json',
            ...csrfHeader(),
          },
          body: JSON.stringify(next),
        });

        if (!response.ok) {
          throw new Error(
            `Could not save appearance (HTTP ${response.status}).`
          );
        }
      });

    void writeQueue.current.catch((error) => {
      console.error('Appearance save failed:', error);
    });
  }

  function applyPreferences(next: Preferences) {
    valuesRef.current = next;
    changeVersion.current += 1;

    setAppearanceState(next.appearance);
    setCozyThemeState(next.cozy_theme);
    persistPreferences(next);
  }

  function setAppearance(value: Appearance) {
    if (valuesRef.current.appearance === value) return;

    applyPreferences({
      ...valuesRef.current,
      appearance: value,
    });
  }

  function setCozyTheme(value: CozyTheme) {
    if (valuesRef.current.cozy_theme === value) return;

    applyPreferences({
      ...valuesRef.current,
      cozy_theme: value,
    });
  }

  function toggleTheme() {
    if (valuesRef.current.appearance !== 'cozy') return;

    setCozyTheme(
      valuesRef.current.cozy_theme === 'light' ? 'dark' : 'light'
    );
  }

  return (
    <AppearanceContext.Provider
      value={{
        appearance,
        setAppearance,
        cozyTheme,
        setCozyTheme,
        theme,
        toggleTheme,
      }}
    >
      {children}
    </AppearanceContext.Provider>
  );
}

export function useAppearance() {
  const context = useContext(AppearanceContext);

  if (!context) {
    throw new Error(
      'useAppearance must be used within AppearanceProvider'
    );
  }

  return context;
}
