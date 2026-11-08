
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
  const { submit, sending } = useMentorJobs();
  const location = useLocation();
  const navigate = useNavigate();
const requestedThread = useRef<number | null>(null);
  const [careers, setCareers] = useState<CareerOption[]>([]);
  const [careerKey, setCareerKey] = useState('');
  const [careerNotice, setCareerNotice] = useState('');
  const [conversations, setConversations] = useState<
    MentorConversation[]
  >([]);

  const [conversationId, setConversationId] = useState<number | null>(
    null
  );

  const [messages, setMessages] = useState<DisplayMentorMessage[]>([]);
  const [draft, setDraft] = useState('');

  const [loading, setLoading] = useState(true);
  const [loadingThread, setLoadingThread] = useState(false);
  const [error, setError] = useState('');

    const bottomRef = useRef<HTMLDivElement>(null);

    
    

  // Load the available careers and saved conversations.
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
    if (sending || loadingThread) return;
    requestedThread.current = null;
    navigate('/mentor', { replace: true });
    setCareerNotice('');
    setConversationId(null);
    setMessages([]);
    setDraft('');
    setError('');
  }

  function changeCareer(value: string) {
    if (sending || loadingThread) return;

    requestedThread.current = null;
    navigate('/mentor', { replace: true });
    setCareerNotice('');
    setCareerKey(value);
    setConversationId(null);
    setMessages([]);
    setDraft('');
    setError('');
  }

  function openConversation(thread: MentorConversation) {
    if (sending || loadingThread) return;

    setCareerNotice('');
    setError('');

    navigate(`/mentor?conversation=${thread.id}`);
  }
  async function sendMessage(event: FormEvent<HTMLFormElement>) {
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

    const previousMessages = [...messages];
    const activeConversationId = conversationId;

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
        activeConversationId
      );

      const responseSeconds = result.responseSeconds;

      const switchedConversation =
        activeConversationId !== null &&
        result.conversation_id !== activeConversationId;

        setConversationId(result.conversation_id);
        setCareerKey(result.career_key);

        // Prepare the newly generated message pair.
        const newMessages: DisplayMentorMessage[] = [
        {
            role: 'user',
            content: question,
        },
        {
            role: 'assistant',
            content: result.response,
            responseSeconds,
        },
        ];

        // Preserve history unless the backend changed conversations.
        setMessages(
        switchedConversation
            ? newMessages
            : [...previousMessages, ...newMessages]
        );


        if (result.target_updated) {
        const career = careers.find(
            (item) => item.career_key === result.career_key
        );

        setCareerNotice(
            `Target career updated to ${career?.name ?? result.career_key}.`
        );
        }

        try {
        const updated = await mentorApi.conversations();
        setConversations(updated);
        } catch {
        // The successful message remains visible.
        }

    } catch (err) {
      setMessages(previousMessages);
      setDraft(question);

      setError(
        err instanceof Error
          ? err.message
          : 'The mentor could not respond.'
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
          disabled={sending || loadingThread}
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
              {sortedConversations.map((thread) => (
                <button
                  key={thread.id}
                  type="button"
                  disabled={sending || loadingThread}
                  className={
                    'cf-mentor-thread' +
                    (conversationId === thread.id
                      ? ' cf-mentor-thread-active'
                      : '')
                  }
                  onClick={() => openConversation(thread)}
                >
                  {thread.title?.trim() ||
                    `Conversation ${thread.id}`}
                </button>
              ))}
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
              <label htmlFor="mentor-career">Career context</label>

              <select
                id="mentor-career"
                value={careerKey}
                disabled={loading || loadingThread || sending}
                onChange={(event) =>
                  changeCareer(event.target.value)
                }
              >
                <option value="">Select a career</option>

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
            <p className="cf-mentor-career-notice" role="status">
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
