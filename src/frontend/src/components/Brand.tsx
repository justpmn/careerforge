import { Link } from 'react-router-dom';

export default function Brand() {
  return (
    <Link to="/" className="brand" aria-label="CareerForge home">
      <span className="brand-symbol" aria-hidden="true"><span></span><span></span><span></span><span></span></span>
      <span>career<span className="brand-accent">forge</span><span className="brand-period">.</span></span>
    </Link>
  );
}
