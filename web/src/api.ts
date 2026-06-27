export type SubType = "remote" | "local";
export type FetchStatus = "success" | "failed" | null;

export interface SubscriptionSource {
  subscription_key: string;
  name: string;
  type: SubType;
  url: string | null;
  created_at?: string;
  updated_at?: string;
  last_successful_fetch_at: string | null;
  last_fetch_status: FetchStatus;
}

export interface AddSubPayload {
  name: string;
  type: SubType;
  url?: string;
  content?: string;
}

export interface UpdateSubPayload {
  type: SubType;
  url?: string;
  content?: string;
}

async function httpJson<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });

  if (!res.ok) {
    // 尽量读后端的 {"error": "..."}
    let msg = `${res.status} ${res.statusText}`;
    try {
      const body = await res.json();
      if (body?.error) msg = body.error;
    } catch {
      // ignore
    }
    throw new Error(msg);
  }

  const text = await res.text();
  return (text ? JSON.parse(text) : ({} as T)) as T;
}

export async function listSubs(): Promise<SubscriptionSource[]> {
  const data = await httpJson<{ sub_list: SubscriptionSource[] }>("/sub/list");
  return data.sub_list ?? [];
}

export async function addSub(
  payload: AddSubPayload
): Promise<{ subscription_key: string; message?: string }> {
  return httpJson<{ subscription_key: string; message?: string }>("/sub/add", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function updateSub(
  subscriptionKey: string,
  payload: UpdateSubPayload
): Promise<{ message?: string }> {
  return httpJson<{ message?: string }>(`/sub/update/${encodeURIComponent(subscriptionKey)}`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function deleteSub(subscriptionKey: string): Promise<void> {
  const res = await fetch(`/sub/delete/${encodeURIComponent(subscriptionKey)}`, { method: "DELETE" });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `${res.status} ${res.statusText}`);
  }
}

export async function refreshSubCache(subscriptionKey: string): Promise<{ message?: string }> {
  return httpJson<{ message?: string }>(`/sub/refresh/${encodeURIComponent(subscriptionKey)}`, {
    method: "POST",
    body: JSON.stringify({}),
  });
}

export async function getSubContent(subscriptionKey: string): Promise<string> {
  const res = await fetch(`/sub/${encodeURIComponent(subscriptionKey)}`, { method: "GET" });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `${res.status} ${res.statusText}`);
  }
  return await res.text();
}
