import { useEffect, useState } from 'react';
import {
  careerPreferencesApi,
  type CareerPreference,
  type CareerPreferences,
} from '../lib/careerpreferences';

const emptyPreferences = (): CareerPreferences => ({
  preferred: [],
  avoid: [],
});

export function useCareerPreferences(userId?: number) {
  const [preferences, setPreferences] =
    useState<CareerPreferences>(emptyPreferences);

  const [loading, setLoading] = useState(true);
  const [savingKey, setSavingKey] = useState<string | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    let active = true;

    setPreferences(emptyPreferences());
    setError('');

    if (userId == null) {
      setLoading(false);
      return;
    }

    setLoading(true);

    careerPreferencesApi.get(userId)
      .then((result) => {
        if (active) setPreferences(result);
      })
      .catch((err) => {
        if (active) {
          setError(
            err instanceof Error
              ? err.message
              : 'Could not load career preferences.'
          );
        }
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => {
      active = false;
    };
  }, [userId]);

  function preferenceFor(
    careerKey: string
  ): CareerPreference | null {
    if (preferences.preferred.includes(careerKey)) {
      return 'preferred';
    }

    if (preferences.avoid.includes(careerKey)) {
      return 'avoid';
    }

    return null;
  }

    async function choose(
    careerKey: string,
    next: CareerPreference
    ): Promise<boolean> {
    if (userId == null || loading || savingKey !== null) {
        return false;
    }

    const current = preferenceFor(careerKey);
    const removing = current === next;

    setSavingKey(careerKey);
    setError('');

    try {
        if (removing) {
        await careerPreferencesApi.remove(userId, careerKey);
        } else {
        await careerPreferencesApi.set(userId, careerKey, next);
        }

        setPreferences((previous) => {
        const preferred = previous.preferred.filter(
            (key) => key !== careerKey
        );
        const avoid = previous.avoid.filter(
            (key) => key !== careerKey
        );

        if (!removing) {
            if (next === 'preferred') {
            preferred.push(careerKey);
            } else {
            avoid.push(careerKey);
            }
        }

        return { preferred, avoid };
        });

        return true;
    } catch (err) {
        setError(
        err instanceof Error
            ? err.message
            : 'Could not update career preference.'
        );

        return false;
    } finally {
        setSavingKey(null);
    }
    }
    async function resetAll(): Promise<boolean> {
  if (userId == null || loading || savingKey !== null) {
    return false;
  }

  const keys = [...new Set([
    ...preferences.preferred,
    ...preferences.avoid,
  ])];

  if (keys.length === 0) return true;

  setSavingKey('__reset__');
  setError('');

  try {
    const results = await Promise.allSettled(
      keys.map((key) =>
        careerPreferencesApi.remove(userId, key)
      )
    );

    const updated = await careerPreferencesApi.get(userId);
    setPreferences(updated);

    if (results.some((result) => result.status === 'rejected')) {
      setError('Some preferences could not be removed. Please try again.');
      return false;
    }

    return true;
  } catch (err) {
    setError(
      err instanceof Error
        ? err.message
        : 'Could not reset career preferences.'
    );
    return false;
  } finally {
    setSavingKey(null);
  }
}


  return {
    preferences,
    loading,
    savingKey,
    error,
    preferenceFor,
    choose,
    resetAll,
  };
}