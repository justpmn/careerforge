import {
  createContext,
  useContext,
  useEffect,
  useRef,
  useState,
} from 'react';

import type { ReactNode } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';

import { useAuth } from './AuthContext';
import { mentorApi } from '../lib/mentor';
import type { MentorChatResponse } from '../lib/mentor';

type CompletedReply = MentorChatResponse & {
  responseSeconds: number;
};

type MentorJobsValue = {
  sending: boolean;
  submit: (
    message: string,
    careerKey: string | null,
    conversationId: number | null
  ) => Promise<CompletedReply>;
};

type Notice = {
  kind: 'success' | 'error';
  message: string;
  conversationId?: number;
};

const MentorJobsContext = createContext<MentorJobsValue | null>(
  null
);

export function MentorJobsProvider({
  children,
}: {
  children: ReactNode;
}) {
  const { user } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();

  const [sending, setSending] = useState(false);
  const [notice, setNotice] = useState<Notice | null>(null);

  const inFlight = useRef(false);
  const leftMentor = useRef(false);
  const currentUser = useRef(user?.id);
  const currentPath = useRef(location.pathname);

  useEffect(() => {
    currentUser.current = user?.id;
    setNotice(null);
  }, [user?.id]);

  useEffect(() => {
    currentPath.current = location.pathname;

    if (inFlight.current && location.pathname !== '/mentor') {
      leftMentor.current = true;
    }
  }, [location.pathname]);

  async function submit(
    message: string,
    careerKey: string | null,
    conversationId: number | null
  ): Promise<CompletedReply> {
    if (inFlight.current) {
      throw new Error('CareerForge is already generating a reply.');
    }

    inFlight.current = true;
    leftMentor.current = false;

    const requestingUser = currentUser.current;
    const startedAt = performance.now();

    setSending(true);
    setNotice(null);

    try {
      const result = await mentorApi.send(
        message,
        careerKey,
        conversationId
      );

      const completed: CompletedReply = {
        ...result,
        responseSeconds:
          (performance.now() - startedAt) / 1000,
      };

      if (
        currentUser.current === requestingUser &&
        (leftMentor.current || currentPath.current !== '/mentor')
      ) {
        setNotice({
          kind: 'success',
          message: 'Your AI Mentor response is ready.',
          conversationId: result.conversation_id,
        });
      }

      return completed;
    } catch (error) {
      if (
        currentUser.current === requestingUser &&
        (leftMentor.current || currentPath.current !== '/mentor')
      ) {
        setNotice({
          kind: 'error',
          message: 'Your AI Mentor could not respond.',
        });
      }

      throw error;
    } finally {
      inFlight.current = false;
      setSending(false);
    }
  }

  function viewReply() {
    if (!notice?.conversationId) return;

    const id = notice.conversationId;
    setNotice(null);
    navigate(`/mentor?conversation=${id}`);
  }

  return (
    <MentorJobsContext.Provider value={{ sending, submit }}>
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

            {notice.conversationId && (
              <button type="button" onClick={viewReply}>
                View response →
              </button>
            )}
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
