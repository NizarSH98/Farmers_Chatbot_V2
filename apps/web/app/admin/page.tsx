"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";
import { supabaseBrowser } from "@/lib/supabase";

const LOCAL_AUTH = process.env.NEXT_PUBLIC_LOCAL_AUTH === "true";

type Release = {
  id: string;
  version: string;
  state: string;
  projection_state?: string;
  evidence_points?: number;
  entity_points?: number;
  active_scopes?: string[];
};

type Proposal = {
  id: string;
  base_release_id: string;
  record_type: string;
  record_id: string;
  operation: string;
  state: string;
  patch_json: Record<string, unknown>;
};

async function authToken(): Promise<string> {
  if (LOCAL_AUTH) return "local-development";
  const { data } = await supabaseBrowser().auth.getSession();
  if (!data.session?.access_token) throw new Error("Administrator sign-in is required.");
  return data.session.access_token;
}

export default function KnowledgeAdminPage() {
  const [releases, setReleases] = useState<Release[]>([]);
  const [proposals, setProposals] = useState<Proposal[]>([]);
  const [query, setQuery] = useState("");
  const [neighborhood, setNeighborhood] = useState<Record<string, unknown> | null>(null);
  const [recordType, setRecordType] = useState("claim");
  const [recordId, setRecordId] = useState("");
  const [operation, setOperation] = useState("update");
  const [patchText, setPatchText] = useState("{}");
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);

  const refresh = useCallback(async () => {
    setBusy(true);
    try {
      const token = await authToken();
      const [releaseResult, proposalResult] = await Promise.all([
        apiFetch<{ releases: Release[] }>("/v1/admin/knowledge/releases", token),
        apiFetch<{ proposals: Proposal[] }>("/v1/editor/knowledge/proposals", token)
      ]);
      setReleases(releaseResult.releases);
      setProposals(proposalResult.proposals);
      setMessage("");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Administration data could not be loaded.");
    } finally {
      setBusy(false);
    }
  }, []);

  useEffect(() => {
    const timer = window.setTimeout(() => void refresh(), 0);
    return () => window.clearTimeout(timer);
  }, [refresh]);

  const activeRelease = releases.find((release) => release.active_scopes?.includes("pilot"));

  const inspectGraph = async () => {
    if (!query.trim()) return;
    setBusy(true);
    try {
      const token = await authToken();
      setNeighborhood(
        await apiFetch<Record<string, unknown>>(
          `/v1/admin/knowledge/neighborhood?query=${encodeURIComponent(query)}&hops=2`,
          token
        )
      );
      setMessage("");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Graph lookup failed.");
    } finally {
      setBusy(false);
    }
  };

  const propose = async () => {
    if (!activeRelease || !recordId.trim()) return;
    setBusy(true);
    try {
      const patch = JSON.parse(patchText) as Record<string, unknown>;
      const token = await authToken();
      await apiFetch("/v1/editor/knowledge/proposals", token, {
        method: "POST",
        body: JSON.stringify({
          base_release_id: activeRelease.id,
          record_type: recordType,
          record_id: recordId.trim(),
          operation,
          patch
        })
      });
      setRecordId("");
      setPatchText("{}");
      setMessage("Proposal recorded. It will not mutate the active release.");
      await refresh();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Proposal could not be recorded.");
      setBusy(false);
    }
  };

  const reject = async (proposalId: string) => {
    if (!window.confirm("Reject this proposal?")) return;
    setBusy(true);
    try {
      const token = await authToken();
      await apiFetch(`/v1/admin/knowledge/proposals/${encodeURIComponent(proposalId)}/review`, token, {
        method: "POST",
        body: JSON.stringify({ state: "rejected", review_note: "Rejected in the RAISE editor UI." })
      });
      await refresh();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Proposal review failed.");
      setBusy(false);
    }
  };

  return (
    <main style={{ maxWidth: 1120, margin: "0 auto", padding: 24, direction: "ltr" }}>
      <p><Link href="/">← Farmer workspace</Link></p>
      <h1>Knowledge releases and editor review</h1>
      <p>This page is restricted by the API to administrators/editors. Proposals never edit an active release.</p>
      {message && <p role="status">{message}</p>}

      <section>
        <h2>Immutable releases</h2>
        <button type="button" disabled={busy} onClick={() => void refresh()}>Refresh</button>
        <div style={{ overflowX: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", marginTop: 12 }}>
            <thead><tr><th>Release</th><th>State</th><th>Projection</th><th>Points</th><th>Active</th></tr></thead>
            <tbody>{releases.map((release) => (
              <tr key={release.id}>
                <td><code>{release.id}</code></td>
                <td>{release.state}</td>
                <td>{release.projection_state || "—"}</td>
                <td>{release.evidence_points || 0} / {release.entity_points || 0}</td>
                <td>{release.active_scopes?.join(", ") || "—"}</td>
              </tr>
            ))}</tbody>
          </table>
        </div>
      </section>

      <section style={{ marginTop: 32 }}>
        <h2>Inspect a two-hop graph neighborhood</h2>
        <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="potato irrigation" />{" "}
        <button type="button" disabled={busy || !query.trim()} onClick={() => void inspectGraph()}>Inspect</button>
        {neighborhood && <pre style={{ whiteSpace: "pre-wrap", maxHeight: 420, overflow: "auto" }}>{JSON.stringify(neighborhood, null, 2)}</pre>}
      </section>

      <section style={{ marginTop: 32 }}>
        <h2>Propose an immutable-release change</h2>
        <p>Base: <code>{activeRelease?.id || "no active pilot release"}</code></p>
        <select value={recordType} onChange={(event) => setRecordType(event.target.value)}>
          <option value="document">Document</option><option value="claim">Claim</option>
          <option value="relation">Relation</option><option value="translation">Translation</option>
        </select>{" "}
        <select value={operation} onChange={(event) => setOperation(event.target.value)}>
          <option value="create">Create</option><option value="update">Update</option><option value="retire">Retire</option>
        </select>
        <p><input style={{ width: "100%" }} value={recordId} onChange={(event) => setRecordId(event.target.value)} placeholder="Stable record ID" /></p>
        <textarea style={{ width: "100%", minHeight: 120 }} value={patchText} onChange={(event) => setPatchText(event.target.value)} aria-label="JSON patch" />
        <p><button type="button" disabled={busy || !activeRelease || !recordId.trim()} onClick={() => void propose()}>Create proposal</button></p>
      </section>

      <section style={{ marginTop: 32 }}>
        <h2>Change proposals</h2>
        {proposals.map((proposal) => (
          <article key={proposal.id} style={{ border: "1px solid #ccd8d0", padding: 12, marginBottom: 10 }}>
            <strong>{proposal.record_type}:{proposal.record_id}</strong> — {proposal.operation} — {proposal.state}
            <pre style={{ whiteSpace: "pre-wrap" }}>{JSON.stringify(proposal.patch_json, null, 2)}</pre>
            {proposal.state === "proposed" && <button type="button" disabled={busy} onClick={() => void reject(proposal.id)}>Reject</button>}
          </article>
        ))}
      </section>
    </main>
  );
}
