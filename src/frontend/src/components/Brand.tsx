
import { Link } from 'react-router-dom';

export default function Brand() {
  return (
    <Link to="/" className="brand" aria-label="CareerForge home">
      <span className="brand-symbol" aria-hidden="true">
        <span></span>
        <span></span>
        <span></span>
        <span></span>
      </span>

      <span className="brand-name">
        Career<span className="brand-accent">Forge</span>
        <span className="brand-period">.</span>
      </span>
    </Link>
  );
}
