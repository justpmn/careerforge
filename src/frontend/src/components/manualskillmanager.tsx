
import { useEffect, useState } from 'react';
import type { FormEvent } from 'react';

import {
  addManualSkill,
  getManualSkills,
  removeManualSkill,
  searchSkillCatalog,
} from '../lib/manualskills';

import type {
  CatalogSkill,
  ManualSkill,
} from '../lib/manualskills';

import '../manual-skills.css';

type Props = {
  onChanged?: () => Promise<void>;
};

export default function ManualSkillManager({ onChanged }: Props) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<CatalogSkill[]>([]);
  const [manualSkills, setManualSkills] = useState<ManualSkill[]>([]);

  const [loading, setLoading] = useState(true);
  const [searching, setSearching] = useState(false);
  const [busyId, setBusyId] = useState<number | null>(null);

  const [error, setError] = useState('');
  const [message, setMessage] = useState('');

  useEffect(() => {
    let active = true;

    void getManualSkills()
      .then((skills) => {
        if (active) setManualSkills(skills);
      })
      .catch((cause: unknown) => {
        if (!active) return;

        setError(
          cause instanceof Error
            ? cause.message
            : 'Could not load manually added skills.'
        );
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    let active = true;
    const term = query.trim();

    if (term.length < 2) {
      setResults([]);
      setSearching(false);
      return;
    }

    setSearching(true);

    const timer = window.setTimeout(() => {
      void searchSkillCatalog(term)
        .then((skills) => {
          if (active) setResults(skills);
        })
        .catch((cause: unknown) => {
          if (!active) return;

          setResults([]);
          setError(
            cause instanceof Error
              ? cause.message
              : 'Could not search the skill catalog.'
          );
        })
        .finally(() => {
          if (active) setSearching(false);
        });
    }, 300);

    return () => {
      active = false;
      window.clearTimeout(timer);
    };
  }, [query]);

  async function notifyParent() {
    if (!onChanged) return;

    try {
      await onChanged();
    } catch {
      setError(
        'Your skill change was saved, but the competency summary ' +
        'could not refresh. Reload the page to update it.'
      );
    }
  }

  async function handleAdd(skill: CatalogSkill) {
    if (busyId !== null) return;

    setBusyId(skill.id);
    setError('');
    setMessage('');

    try {
      const saved = await addManualSkill(skill.id);

      setManualSkills((previous) => {
        if (previous.some((item) => item.id === saved.id)) {
          return previous;
        }

        return [...previous, saved].sort((a, b) =>
          a.name.localeCompare(b.name)
        );
      });

      setResults((previous) =>
        previous.filter((item) => item.id !== saved.id)
      );

      setMessage(`${saved.name} added to your skill profile.`);

      await notifyParent();
    } catch (cause) {
      setError(
        cause instanceof Error
          ? cause.message
          : 'Could not add the selected skill.'
      );
    } finally {
      setBusyId(null);
    }
  }

  async function handleRemove(skill: ManualSkill) {
    if (busyId !== null) return;

    setBusyId(skill.id);
    setError('');
    setMessage('');

    try {
      await removeManualSkill(skill.id);

      setManualSkills((previous) =>
        previous.filter((item) => item.id !== skill.id)
      );

      setMessage(`${skill.name} removed from your skill profile.`);

      await notifyParent();
    } catch (cause) {
      setError(
        cause instanceof Error
          ? cause.message
          : 'Could not remove the selected skill.'
      );
    } finally {
      setBusyId(null);
    }
  }

  function handleSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
  }

  const manualIds = new Set(manualSkills.map((skill) => skill.id));

  return (
    <section
      className="cf-manual-skills"
      aria-label="Manage your manually added skills"
    >
      <div className="cf-manual-skills-heading">
        <h3>Add skills to your profile</h3>

        <p>
          Search CareerForge's skill catalog and select skills you
          have experience with. Manually added skills are self-reported,
          not CV-verified.
        </p>
      </div>

      <form onSubmit={handleSearch} role="search">
        <label htmlFor="cf-manual-skill-search">
          Search available skills
        </label>

        <input
          id="cf-manual-skill-search"
          type="search"
          value={query}
          onChange={(event) => {
            setQuery(event.target.value);
            setError('');
            setMessage('');
          }}
          placeholder="Search Python, Docker, AWS..."
          autoComplete="off"
          maxLength={100}
        />
      </form>

      {query.trim().length === 1 && (
        <p className="cf-manual-skills-note">
          Enter at least two characters to search.
        </p>
      )}

      {searching && (
        <p className="cf-manual-skills-note" role="status">
          Searching skills...
        </p>
      )}

      {query.trim().length >= 2 && !searching && (
        <div className="cf-manual-results">
          {results.length > 0 ? (
            results.map((skill) => {
              const alreadyAdded = manualIds.has(skill.id);

              return (
                <div className="cf-manual-result" key={skill.id}>
                  <div>
                    <strong>{skill.name}</strong>
                    {skill.category && (
                      <small>{skill.category}</small>
                    )}
                  </div>

                  <button
                    type="button"
                    disabled={alreadyAdded || busyId !== null}
                    onClick={() => void handleAdd(skill)}
                  >
                    {alreadyAdded
                      ? 'Added'
                      : busyId === skill.id
                        ? 'Adding...'
                        : 'Add'}
                  </button>
                </div>
              );
            })
          ) : (
            <p className="cf-manual-skills-note">
              No matching skills found in the catalog.
            </p>
          )}
        </div>
      )}

      <div className="cf-manual-saved">
        <h4>
          Manually added skills ({manualSkills.length})
        </h4>

        {loading ? (
          <p className="cf-manual-skills-note">
            Loading your skills...
          </p>
        ) : manualSkills.length === 0 ? (
          <p className="cf-manual-skills-note">
            You haven't added any skills manually yet.
          </p>
        ) : (
          <div className="cf-manual-chip-list">
            {manualSkills.map((skill) => (
              <div className="cf-manual-chip" key={skill.id}>
                <span>{skill.name}</span>

                <button
                  type="button"
                  aria-label={`Remove ${skill.name}`}
                  title={`Remove ${skill.name}`}
                  disabled={busyId !== null}
                  onClick={() => void handleRemove(skill)}
                >
                  ×
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {message && (
        <p className="cf-manual-success" role="status">
          {message}
        </p>
      )}

      {error && (
        <p className="cf-manual-error" role="alert">
          {error}
        </p>
      )}
    </section>
  );
}
