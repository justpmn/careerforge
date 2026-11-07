
import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

import { useAuth } from '../context/AuthContext';
import { getAdminIdentity } from '../lib/admin';

export default function AdminAccessLink() {
  const { user } = useAuth();
  const [authorized, setAuthorized] = useState(false);

  useEffect(() => {
    let active = true;

    setAuthorized(false);

    if (!user?.id) return;

    void getAdminIdentity()
      .then(() => {
        if (active) setAuthorized(true);
      })
      .catch(() => {
        if (active) setAuthorized(false);
      });

    return () => {
      active = false;
    };
  }, [user?.id]);

  if (!authorized) return null;

  return (
    <Link
      to="/admin"
      className="cf-profile-action"
    >
      Admin dashboard
    </Link>
  );
}
