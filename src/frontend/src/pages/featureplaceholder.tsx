
import { Link } from 'react-router-dom';

type Props = {
  category: string;
  title: string;
  description: string;
};

export default function FeaturePlaceholderPage({
  category,
  title,
  description,
}: Props) {
  return (
    <section className="cf-dashboard">
      <span className="stage-marker">{category}</span>

      <h1>{title}</h1>
      <p>{description}</p>

      <div className="cf-dashboard-card cf-feature-placeholder">
        <p>
          This section is being connected to CareerForge's
          existing backend functionality.
        </p>

        <Link
          to="/dashboard"
          className="cf-button cf-button-outline"
        >
          Return to dashboard
        </Link>
      </div>
    </section>
  );
}
