export async function switchPersona(persona: string) {
  const res = await fetch('/api/persona/switch', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ persona })
  });
  return res.json();
}
