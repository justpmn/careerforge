
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
} from 'react';

import type { ReactNode } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from './AuthContext';
import { mentorApi } from '../lib/mentor';
import type { MentorJob, MentorJobAccepted } from '../lib/mentor';

type MentorJobsValue = {
  jobs: MentorJob[];
  sending: boolean;
  submitting: boolean;
  submit: (
    message: string,
    careerKey: string | null,
    conversationId: number | null
  ) => Promise<MentorJobAccepted>;
  refreshJobs: () => Promise<void>;
};

type Notice = {
  kind: 'success' | 'error';
  message: string;
  conversationId: number;
};

const MentorJobsContext = createContext<MentorJobsValue | null>(null);

function storageKey(userId: string) {
  return `careerforge:mentor:tracked:${userId}`;
}

function readTrackedJobs(userId: string): Set<number> {
  try {
    const saved = JSON.parse(
      localStorage.getItem(storageKey(userId)) || '[]'
    );

    if (!Array.isArray(saved)) return new Set();

    return new Set(
      saved.filter(
        (id): id is number =>
          Number.isSafeInteger(id) && id > 0
      )
    );
  } catch {
    return new Set();
  }
}

function saveTrackedJobs(userId: string, ids: Set<number>) {
  try {
    localStorage.setItem(
      storageKey(userId),
      JSON.stringify([...ids])
    );
  } catch {
    // Database-backed jobs remain available without local storage.
  }
}

export function MentorJobsProvider({
  children,
}: {
  children: ReactNode;
}) {
  const { user } = useAuth();
  const navigate = useNavigate();

  const userId = user?.id == null ? null : String(user.id);

  const [jobs, setJobs] = useState<MentorJob[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [notice, setNotice] = useState<Notice | null>(null);

  const trackedJobs = useRef<Set<number>>(new Set());
  const currentUser = useRef<string | null>(null);
  const polling = useRef(false);
  const submittingRef = useRef(false);

  const refreshJobs = useCallback(async () => {
    if (!userId || polling.current) return;

    polling.current = true;

    try {
      const results = await mentorApi.jobs();

      if (currentUser.current !== userId) return;

      setJobs(results);

      let nextNotice: Notice | null = null;
      let changed = false;

      for (const job of results) {
        if (
          job.status === 'queued' ||
          job.status === 'running'
        ) {
          if (!trackedJobs.current.has(job.id)) {
            trackedJobs.current.add(job.id);
            changed = true;
          }

          continue;
        }

        if (!trackedJobs.current.has(job.id)) continue;

        trackedJobs.current.delete(job.id);
        changed = true;

        if (nextNotice === null) {
          nextNotice = {
            kind:
              job.status === 'completed'
                ? 'success'
                : 'error',
            message:
              job.status === 'completed'
                ? 'Your response is ready.'
                : job.error ||
                  'Your AI Mentor could not respond.',
            conversationId: job.conversation_id,
          };
        }
      }

      if (changed) {
        saveTrackedJobs(userId, trackedJobs.current);
      }

      if (nextNotice) {
        setNotice(nextNotice);
      }
    } catch {
      // Retain the last known job state and retry.
    } finally {
      polling.current = false;
    }
  }, [userId]);

  useEffect(() => {
    currentUser.current = userId;
    trackedJobs.current = userId
      ? readTrackedJobs(userId)
      : new Set();

    setJobs([]);
    setNotice(null);
    setSubmitting(false);
    submittingRef.current = false;

    if (!userId) return;

    void refreshJobs();

    const interval = window.setInterval(() => {
      void refreshJobs();
    }, 3000);

    return () => {
      window.clearInterval(interval);
    };
  }, [userId, refreshJobs]);

  const sending =
    submitting ||
    jobs.some(
      (job) =>
        job.status === 'queued' ||
        job.status === 'running'
    );

  async function submit(
    message: string,
    careerKey: string | null,
    conversationId: number | null
  ): Promise<MentorJobAccepted> {
    if (!userId) {
      throw new Error('You must be signed in.');
    }

    if (submittingRef.current || sending) {
      throw new Error(
        'Your AI Mentor is already generating a response.'
      );
    }

    submittingRef.current = true;
    setSubmitting(true);

    try {
      const result = await mentorApi.queue(
        message,
        careerKey,
        conversationId
      );

      if (currentUser.current === userId) {
        trackedJobs.current.add(result.job_id);
        saveTrackedJobs(userId, trackedJobs.current);

        setJobs((previous) => [
          {
            id: result.job_id,
            conversation_id: result.conversation_id,
            status: 'queued',
            response_seconds: null,
            error: null,
          },
          ...previous.filter(
            (job) => job.id !== result.job_id
          ),
        ]);

        void refreshJobs();
      }

      return result;
    } finally {
      submittingRef.current = false;
      setSubmitting(false);
    }
  }

  function viewReply() {
    if (!notice) return;

    const id = notice.conversationId;
    setNotice(null);

    navigate(`/mentor?conversation=${id}`);
  }

  return (
    <MentorJobsContext.Provider
      value={{
        jobs,
        sending,
        submitting,
        submit,
        refreshJobs,
      }}
    >
      {children}

      {notice && (
        <div
          className="cf-global-notice"
          role="status"
          aria-live="polite"
        >
          <span
            className={
              notice.kind === 'success'
                ? 'cf-global-notice-dot'
                : 'cf-global-notice-dot cf-global-notice-error'
            }
            aria-hidden="true"
          />

          <div className="cf-global-notice-body">
            <strong>CareerForge AI Mentor</strong>
            <p>{notice.message}</p>

            <button type="button" onClick={viewReply}>
              View conversation →
            </button>
          </div>

          <button
            type="button"
            className="cf-global-notice-close"
            aria-label="Dismiss notification"
            onClick={() => setNotice(null)}
          >
            ×
          </button>
        </div>
      )}
    </MentorJobsContext.Provider>
  );
}

export function useMentorJobs(): MentorJobsValue {
  const context = useContext(MentorJobsContext);

  if (!context) {
    throw new Error(
      'useMentorJobs must be used within MentorJobsProvider'
    );
  }

  return context;
}
