export async function fetchSpaces() {
  const res = await fetch('/api/spaces');
  return res.json();
}

export async function matchSpaces(query: string) {
  const res = await fetch('/api/spaces/ai-match', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query })
  });
  return res.json();
}
