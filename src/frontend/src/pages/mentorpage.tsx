
import { useEffect, useRef, useState } from 'react';
import type { FormEvent, KeyboardEvent } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { onboardingApi } from '../lib/onboarding';
import { mentorApi } from '../lib/mentor';
import type {
  MentorConversation,
  MentorMessage,
} from '../lib/mentor';
import { useMentorJobs } from '../context/mentorjobscontext';

import '../mentor.css';

type CareerOption = {
  id: number;
  career_key: string;
  name: string;
};

export default function MentorPage() {
  const { jobs, sending, submitting, submit } = useMentorJobs();
  const location = useLocation();
  const navigate = useNavigate();

  const currentRoute = useRef(
    location.pathname + location.search
  );
  const bottomRef = useRef<HTMLDivElement>(null);

  const [careers, setCareers] = useState<CareerOption[]>([]);
  const [careerKey, setCareerKey] = useState('');
  const [careerNotice, setCareerNotice] = useState('');
  const [conversations, setConversations] = useState<
    MentorConversation[]
  >([]);
  const [messages, setMessages] = useState<MentorMessage[]>([]);
  const [draft, setDraft] = useState('');
  const [loading, setLoading] = useState(true);
  const [loadingThread, setLoadingThread] = useState(false);
  const [error, setError] = useState('');
  const [menuId, setMenuId] = useState<number | null>(null);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editingTitle, setEditingTitle] = useState('');
  const [deletingId, setDeletingId] = useState<number | null>(null);
  const [busyThreadId, setBusyThreadId] = useState<number | null>(null);

  const rawThreadId = new URLSearchParams(
    location.search
  ).get('conversation');

  const parsedThreadId = rawThreadId
    ? Number(rawThreadId)
    : null;

  const conversationId =
    parsedThreadId !== null &&
    Number.isSafeInteger(parsedThreadId) &&
    parsedThreadId > 0
      ? parsedThreadId
      : null;

  currentRoute.current = location.pathname + location.search;

  useEffect(() => {
    let active = true;

    async function initialize() {
      const [careerResult, selectedResult, historyResult] =
        await Promise.allSettled([
          onboardingApi.careers(),
          onboardingApi.selectedCareer(),
          mentorApi.conversations(),
        ]);

      if (!active) return;

      if (careerResult.status === 'fulfilled') {
        setCareers(careerResult.value as CareerOption[]);
      }

      if (selectedResult.status === 'fulfilled') {
        setCareerKey(selectedResult.value.career_key ?? '');
      }

      if (historyResult.status === 'fulfilled') {
        setConversations(historyResult.value);
      }

      if (
        careerResult.status === 'rejected' ||
        historyResult.status === 'rejected'
      ) {
        setError(
          'Some mentor information could not be loaded.'
        );
      }

      setLoading(false);
    }

    void initialize();

    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    let active = true;

    setError('');

    if (!conversationId) {
      setMessages([]);
      setLoadingThread(false);
      return;
    }

    setLoadingThread(true);

    mentorApi.messages(conversationId)
      .then((history) => {
        if (active) setMessages(history);
      })
      .catch((err) => {
        if (!active) return;

        setError(
          err instanceof Error
            ? err.message
            : 'Could not load conversation.'
        );
      })
      .finally(() => {
        if (active) setLoadingThread(false);
      });

    return () => {
      active = false;
    };
  }, [conversationId]);

  useEffect(() => {
    if (!conversationId) return;

    const thread = conversations.find(
      (item) => item.id === conversationId
    );

    const career = careers.find(
      (item) => item.id === thread?.career_id
    );

    if (career) setCareerKey(career.career_key);
  }, [conversationId, conversations, careers]);

  const latestJob = jobs.find(
    (job) => job.conversation_id === conversationId
  );

  const thinkingHere =
    latestJob?.status === 'queued' ||
    latestJob?.status === 'running';

  const failedHere = latestJob?.status === 'failed';

  useEffect(() => {
    if (
      !conversationId ||
      !latestJob ||
      latestJob.status !== 'completed'
    ) {
      return;
    }

    let active = true;

    mentorApi.messages(conversationId)
      .then((history) => {
        if (active) setMessages(history);
      })
      .catch(() => {
        // Saved history can be loaded again.
      });

    return () => {
      active = false;
    };
  }, [
    conversationId,
    latestJob?.id,
    latestJob?.status,
  ]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({
      behavior: 'smooth',
      block: 'nearest',
    });
  }, [messages, thinkingHere, submitting]);

  const selectedCareer = careers.find(
    (career) => career.career_key === careerKey
  );

  const sortedConversations = [...conversations].sort(
    (a, b) =>
      new Date(b.updated_at).getTime() -
      new Date(a.updated_at).getTime()
  );

  function newConversation() {
    setCareerNotice('');
    setError('');
    setDraft('');
    setMessages([]);
    navigate('/mentor');
  }

  function changeCareer(value: string) {
    setCareerKey(value);
    setCareerNotice('');
    setMessages([]);
    setDraft('');
    setError('');
    navigate('/mentor');
  }

  function openConversation(thread: MentorConversation) {
    setCareerNotice('');
    setError('');
    setDraft('');

    navigate(`/mentor?conversation=${thread.id}`);
  }

  async function sendMessage(
    event: FormEvent<HTMLFormElement>
  ) {
    event.preventDefault();

    const question = draft.trim();

    if (
      !question ||
      loading ||
      loadingThread ||
      sending
    ) {
      return;
    }

    const sourceRoute = currentRoute.current;
    const previousMessages = [...messages];

    setMessages([
      ...previousMessages,
      { role: 'user', content: question },
    ]);

    setDraft('');
    setError('');

    try {
      const result = await submit(
        question,
        careerKey || null,
        conversationId
      );

      if (currentRoute.current === sourceRoute) {
        if (result.target_updated) {
          const career = careers.find(
            (item) =>
              item.career_key === result.career_key
          );

          setCareerNotice(
            `Target career updated to ${
              career?.name ?? result.career_key
            }.`
          );
        }

        setCareerKey(result.career_key);

        if (conversationId !== result.conversation_id) {
          navigate(
            `/mentor?conversation=${result.conversation_id}`
          );
        } else {
          void mentorApi.messages(result.conversation_id)
            .then((history) => {
              if (currentRoute.current === sourceRoute) {
                setMessages(history);
              }
            })
            .catch(() => {});
        }
      }

      void mentorApi.conversations()
        .then(setConversations)
        .catch(() => {});
    } catch (err) {
      if (currentRoute.current !== sourceRoute) return;

      setMessages(previousMessages);
      setDraft(question);

      setError(
        err instanceof Error
          ? err.message
          : 'Could not submit the message.'
      );
    }
  }

  function handleComposerKeyDown(
    event: KeyboardEvent<HTMLTextAreaElement>
  ) {
    if (
      event.key === 'Enter' &&
      !event.shiftKey &&
      !event.nativeEvent.isComposing
    ) {
      event.preventDefault();

      if (
        !loading &&
        !loadingThread &&
        !sending &&
        draft.trim()
      ) {
        event.currentTarget.form?.requestSubmit();
      }
    }
  }


function startRename(thread: MentorConversation) {
  setMenuId(null);
  setDeletingId(null);
  setEditingId(thread.id);
  setEditingTitle(thread.title || '');
}

async function saveConversationTitle(id: number) {
  const title = editingTitle.replace(/\s+/g, ' ').trim();

  if (!title) {
    setError('Conversation title cannot be empty.');
    return;
  }

  setBusyThreadId(id);
  setError('');

  try {
    const updated = await mentorApi.renameConversation(id, title);

    setConversations((previous) =>
      previous.map((thread) =>
        thread.id === id ? updated : thread
      )
    );

    setEditingId(null);
    setEditingTitle('');
  } catch (err) {
    setError(
      err instanceof Error
        ? err.message
        : 'Could not rename conversation.'
    );
  } finally {
    setBusyThreadId(null);
  }
}

async function removeConversation(id: number) {
  const pending = jobs.some(
    (job) =>
      job.conversation_id === id &&
      (job.status === 'queued' || job.status === 'running')
  );

  if (pending) {
    setError('Wait for the mentor to finish before deleting.');
    return;
  }

  setBusyThreadId(id);
  setError('');

  try {
    await mentorApi.deleteConversation(id);

    setConversations((previous) =>
      previous.filter((thread) => thread.id !== id)
    );

    setDeletingId(null);
    setMenuId(null);

    if (conversationId === id) {
      setMessages([]);
      setDraft('');
      navigate('/mentor');
    }
  } catch (err) {
    setError(
      err instanceof Error
        ? err.message
        : 'Could not delete conversation.'
    );
  } finally {
    setBusyThreadId(null);
  }
}


  return (
    <section className="cf-mentor">
      <header className="cf-mentor-page-header">
        <div>
          <h1>Your career mentor.</h1>
          <p>
            Ask questions, explore career paths, and plan your next steps.
          </p>
        </div>

        <button
          type="button"
          className="cf-mentor-new"
          onClick={newConversation}
        >
          + New conversation
        </button>
      </header>

      <div className="cf-mentor-layout">
        <aside className="cf-mentor-history">
          <h2>Conversations</h2>

          {loading ? (
            <p className="cf-mentor-muted">Loading...</p>
          ) : sortedConversations.length === 0 ? (
            <p className="cf-mentor-muted">
              Your saved conversations will appear here.
            </p>
          ) : (
            <nav
              className="cf-mentor-thread-list"
              aria-label="Saved conversations"
            >
              {sortedConversations.map((thread) => {
                const pending = jobs.some(
                  (job) =>
                    job.conversation_id === thread.id &&
                    (job.status === 'queued' ||
                      job.status === 'running')
                );

                const busy = busyThreadId === thread.id;

                return (
                  <div
                    className="cf-mentor-thread-item"
                    key={thread.id}
                  >
                    <div className="cf-mentor-thread-row">
                      <button
                        type="button"
                        className={
                          'cf-mentor-thread' +
                          (conversationId === thread.id
                            ? ' cf-mentor-thread-active'
                            : '')
                        }
                        title={
                          thread.title ||
                          `Conversation ${thread.id}`
                        }
                        onClick={() => {
                          setMenuId(null);
                          openConversation(thread);
                        }}
                      >
                        {thread.title?.trim() ||
                          `Conversation ${thread.id}`}

                        {pending && (
                          <span
                            className="cf-mentor-thread-pending"
                            title="Generating response"
                            aria-label="Generating response"
                          />
                        )}
                      </button>

                      <button
                        type="button"
                        className="cf-mentor-thread-more"
                        aria-label={`Options for ${
                          thread.title || 'conversation'
                        }`}
                        aria-expanded={menuId === thread.id}
                        disabled={busy}
                        onClick={() => {
                          setMenuId(
                            menuId === thread.id
                              ? null
                              : thread.id
                          );
                          setEditingId(null);
                          setDeletingId(null);
                        }}
                      >
                        ⋯
                      </button>
                    </div>

                    {menuId === thread.id && (
                      <div className="cf-mentor-thread-menu">
                        <button
                          type="button"
                          onClick={() => startRename(thread)}
                        >
                          Rename
                        </button>

                        <button
                          type="button"
                          className="cf-mentor-danger"
                          disabled={pending}
                          title={
                            pending
                              ? 'Wait for the response to finish'
                              : 'Delete conversation'
                          }
                          onClick={() => {
                            setMenuId(null);
                            setDeletingId(thread.id);
                          }}
                        >
                          Delete
                        </button>
                      </div>
                    )}

                    {editingId === thread.id && (
                      <form
                        className="cf-mentor-thread-edit"
                        onSubmit={(event) => {
                          event.preventDefault();
                          void saveConversationTitle(thread.id);
                        }}
                      >
                        <input
                          autoFocus
                          aria-label="Conversation title"
                          maxLength={100}
                          value={editingTitle}
                          onChange={(event) =>
                            setEditingTitle(event.target.value)
                          }
                          disabled={busy}
                        />

                        <div className="cf-mentor-thread-actions">
                          <button
                            type="submit"
                            disabled={
                              busy || !editingTitle.trim()
                            }
                          >
                            Save
                          </button>

                          <button
                            type="button"
                            disabled={busy}
                            onClick={() => setEditingId(null)}
                          >
                            Cancel
                          </button>
                        </div>
                      </form>
                    )}

                    {deletingId === thread.id && (
                      <div className="cf-mentor-thread-confirm">
                        <p>
                          Delete this conversation and its messages?
                        </p>

                        <div className="cf-mentor-thread-actions">
                          <button
                            type="button"
                            className="cf-mentor-danger"
                            disabled={busy}
                            onClick={() =>
                              void removeConversation(thread.id)
                            }
                          >
                            Delete
                          </button>

                          <button
                            type="button"
                            disabled={busy}
                            onClick={() =>
                              setDeletingId(null)
                            }
                          >
                            Cancel
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </nav>
          )}
        </aside>

        <div className="cf-mentor-chat">
          <div className="cf-mentor-chat-header">
            <div>
              <h2>
                {selectedCareer?.name || 'Choose a career'}
              </h2>

              <p>
                {conversationId
                  ? 'Saved conversation'
                  : 'New conversation'}
              </p>
            </div>

            <div className="cf-mentor-career">
              <label htmlFor="mentor-career">
                Career context
              </label>

              <select
                id="mentor-career"
                value={careerKey}
                disabled={loading || submitting}
                onChange={(event) =>
                  changeCareer(event.target.value)
                }
              >
                <option value="">
                  Select a career
                </option>

                {careers.map((career) => (
                  <option
                    key={career.career_key}
                    value={career.career_key}
                  >
                    {career.name}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {careerNotice && (
            <p
              className="cf-mentor-career-notice"
              role="status"
            >
              {careerNotice}
            </p>
          )}

          <div className="cf-mentor-messages">
            {loadingThread ? (
              <p className="cf-mentor-muted">
                Loading conversation...
              </p>
            ) : messages.length === 0 ? (
              <div className="cf-mentor-welcome">
                <div className="cf-mentor-mark">CF</div>

                <h3>What can I help you with?</h3>

                <p>
                  {careerKey
                    ? 'Ask about your skills, career direction, or learning priorities.'
                    : 'Select a career above to begin a personalized conversation.'}
                </p>
              </div>
            ) : (
              messages.map((message, index) => (
                <div
                  key={message.id ?? index}
                  className={
                    'cf-mentor-message ' +
                    (message.role === 'user'
                      ? 'cf-mentor-user'
                      : 'cf-mentor-assistant')
                  }
                >
                  <span className="cf-mentor-role">
                    {message.role === 'user'
                      ? 'You'
                      : 'CareerForge'}
                  </span>

                  {message.role === 'assistant' ? (
                    <div className="cf-mentor-markdown">
                      <ReactMarkdown
                        remarkPlugins={[remarkGfm]}
                        skipHtml
                      >
                        {message.content}
                      </ReactMarkdown>
                    </div>
                  ) : (
                    <p>{message.content}</p>
                  )}
                </div>
              ))
            )}

            {(thinkingHere ||
              (submitting && !conversationId)) && (
              <div
                className="cf-mentor-thinking"
                role="status"
              >
                <span
                  className="cf-thinking-dot"
                  aria-hidden="true"
                />

                <span>
                  {submitting && !conversationId
                    ? 'Saving your message...'
                    : 'Thinking...'}
                </span>
              </div>
            )}

            {failedHere && (
              <p
                className="cf-mentor-error"
                role="alert"
              >
                {latestJob?.error ||
                  'The mentor could not respond.'}
              </p>
            )}

            <div ref={bottomRef} />
          </div>

          <div className="cf-mentor-composer">
            {error && (
              <p
                className="cf-mentor-error"
                role="alert"
              >
                {error}
              </p>
            )}

            {sending && !thinkingHere && !submitting && (
              <p className="cf-mentor-muted">
                Your mentor is replying in another
                conversation.
              </p>
            )}

            <form onSubmit={sendMessage}>
              <label
                htmlFor="mentor-input"
                className="cf-mentor-input-label"
              >
                Your message
              </label>

              <textarea
                id="mentor-input"
                rows={3}
                value={draft}
                maxLength={2000}
                onChange={(event) =>
                  setDraft(event.target.value)
                }
                onKeyDown={handleComposerKeyDown}
                placeholder="Ask anything about your career..."
                disabled={loading || loadingThread}
              />

              <div className="cf-mentor-composer-bottom">
                <span>
                  Enter to send · Shift+Enter for a new line
                </span>

                <button
                  type="submit"
                  disabled={
                    !draft.trim() ||
                    loading ||
                    loadingThread ||
                    sending
                  }
                >
                  {submitting
                    ? 'Saving...'
                    : thinkingHere
                      ? 'Thinking...'
                      : 'Send'}
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </section>
  );
}
