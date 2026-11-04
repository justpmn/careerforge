import {
  createContext,
  useContext,
  useEffect,
  useState,
} from 'react';
import type { ReactNode } from 'react';

export type Appearance = 'cozy' | 'neon';
export type CozyTheme = 'light' | 'dark';

type AppearanceContextType = {
  appearance: Appearance;
  setAppearance: (value: Appearance) => void;
  cozyTheme: CozyTheme;
  setCozyTheme: (value: CozyTheme) => void;
  theme: CozyTheme;
  toggleTheme: () => void;
};

const AppearanceContext = createContext<AppearanceContextType | null>(null);

const APPEARANCE_KEY = 'careerforge-appearance';
const COZY_THEME_KEY = 'careerforge-cozy-theme';
const LEGACY_THEME_KEY = 'careerforge-theme';

function loadAppearance(): Appearance {
  const saved = localStorage.getItem(APPEARANCE_KEY);
  return saved === 'neon' ? 'neon' : 'cozy';
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
  const [appearance, setAppearance] = useState<Appearance>(loadAppearance);
  const [cozyTheme, setCozyTheme] = useState<CozyTheme>(loadCozyTheme);

  const theme: CozyTheme =
    appearance === 'neon' ? 'dark' : cozyTheme;

  useEffect(() => {
    document.documentElement.dataset.appearance = appearance;
    document.documentElement.dataset.theme = theme;

    localStorage.setItem(APPEARANCE_KEY, appearance);
    localStorage.setItem(COZY_THEME_KEY, cozyTheme);
    localStorage.setItem(LEGACY_THEME_KEY, cozyTheme);
  }, [appearance, cozyTheme, theme]);

  function toggleTheme() {
    if (appearance !== 'cozy') return;

    setCozyTheme((current) =>
      current === 'light' ? 'dark' : 'light'
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
