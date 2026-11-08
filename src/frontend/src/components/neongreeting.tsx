
import { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import '../neon-greeting.css';

const GREETING = 'Welcome back, ';
const TYPE_SPEED = 75;

export default function NeonGreeting() {
  const { user } = useAuth();
  const firstName = user?.name?.trim().split(/\s+/)[0] || 'there';
  const name = `${firstName}.`;
  const fullText = GREETING + name;

  const [reducedMotion, setReducedMotion] = useState(
    () => window.matchMedia('(prefers-reduced-motion: reduce)').matches
  );

  const [count, setCount] = useState(0);

  useEffect(() => {
    const media = window.matchMedia('(prefers-reduced-motion: reduce)');
    const update = () => setReducedMotion(media.matches);

    media.addEventListener('change', update);
    return () => media.removeEventListener('change', update);
  }, []);

  useEffect(() => {
    if (reducedMotion) {
      setCount(fullText.length);
      return;
    }

    setCount(0);
    let index = 0;

    const timer = window.setInterval(() => {
      index += 1;
      setCount(index);

      if (index >= fullText.length) {
        window.clearInterval(timer);
      }
    }, TYPE_SPEED);

    return () => window.clearInterval(timer);
  }, [fullText, reducedMotion]);

  const greetingCount = Math.min(count, GREETING.length);
  const nameCount = Math.max(0, count - GREETING.length);
  const complete = count >= fullText.length;

  return (
    <h1
      className="cf-neon-greeting"
      aria-label={fullText}
    >
      <span aria-hidden="true">
        {GREETING.slice(0, greetingCount)}
      </span>

      <span
        className={`cf-neon-name ${complete ? 'is-complete' : ''}`}
        data-text={complete ? name : ''}
        aria-hidden="true"
      >
        {name.slice(0, nameCount)}
      </span>

      <span className="cf-neon-cursor" aria-hidden="true">
        _
      </span>
    </h1>
  );
}
