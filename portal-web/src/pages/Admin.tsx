import { useEffect, useState } from "react";

import { api } from "../api/client";
import { useAuth } from "../auth/AuthContext";

const ACTIONS = ["create", "read", "update", "delete"];

interface Feature {
  id: number;
  key: string;
  name: string;
}
interface Role {
  id: number;
  key: string;
  name: string;
  permissions: Record<string, string[]>;
}
interface AdminUser {
  id: number;
  email: string;
  roles: string[];
}

export default function Admin() {
  const { can, refresh } = useAuth();
  const [features, setFeatures] = useState<Feature[]>([]);
  const [roles, setRoles] = useState<Role[]>([]);
  const [users, setUsers] = useState<AdminUser[]>([]);

  async function load() {
    const [f, r, u] = await Promise.all([
      api("/api/admin/features"),
      api("/api/admin/roles"),
      api("/api/admin/users"),
    ]);
    if (f.ok) setFeatures(await f.json());
    if (r.ok) setRoles(await r.json());
    if (u.ok) setUsers(await u.json());
  }

  useEffect(() => {
    void load();
  }, []);

  async function togglePermission(role: Role, feature: string, action: string, on: boolean) {
    const next = new Set(role.permissions[feature] ?? []);
    on ? next.add(action) : next.delete(action);
    const resp = await api(`/api/admin/roles/${role.id}/permissions`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ permissions: { [feature]: Array.from(next) } }),
    });
    if (resp.ok) {
      await load();
      await refresh();
    }
  }

  async function toggleRole(user: AdminUser, roleKey: string, on: boolean) {
    const next = new Set(user.roles);
    on ? next.add(roleKey) : next.delete(roleKey);
    const resp = await api(`/api/admin/users/${user.id}/roles`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ roles: Array.from(next) }),
    });
    if (resp.ok) {
      await load();
      await refresh();
    }
  }

  if (!can("users", "read")) {
    return <p>You do not have access to administration.</p>;
  }
  const canUpdate = can("users", "update");

  return (
    <section>
      <h2>Administration</h2>

      <h3>Role permission matrix</h3>
      {roles.map((role) => (
        <fieldset key={role.id}>
          <legend>{role.name || role.key}</legend>
          <table>
            <thead>
              <tr>
                <th>Feature</th>
                {ACTIONS.map((a) => (
                  <th key={a}>{a}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {features.map((feat) => (
                <tr key={feat.id}>
                  <td>{feat.key}</td>
                  {ACTIONS.map((action) => (
                    <td key={action}>
                      <input
                        type="checkbox"
                        aria-label={`${role.key}-${feat.key}-${action}`}
                        checked={role.permissions[feat.key]?.includes(action) ?? false}
                        disabled={!canUpdate}
                        onChange={(e) =>
                          void togglePermission(role, feat.key, action, e.target.checked)
                        }
                      />
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </fieldset>
      ))}

      <h3>Users</h3>
      <table>
        <thead>
          <tr>
            <th>Email</th>
            {roles.map((r) => (
              <th key={r.id}>{r.key}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {users.map((u) => (
            <tr key={u.id}>
              <td>{u.email}</td>
              {roles.map((r) => (
                <td key={r.id}>
                  <input
                    type="checkbox"
                    aria-label={`user-${u.id}-${r.key}`}
                    checked={u.roles.includes(r.key)}
                    disabled={!canUpdate}
                    onChange={(e) => void toggleRole(u, r.key, e.target.checked)}
                  />
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
