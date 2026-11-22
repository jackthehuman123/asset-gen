# Game style

Modern-day New York City. The pipeline is dynamic: a building that follows an existing style reuses that STYLE.md (and saves tokens); a new style gets a new STYLE.md. This is the new style for present-day Manhattan: real streets, lived-in and maintained, with an overcast city light. Buildings keep their historic masonry while the street level is modern: glass storefronts, awnings, window AC units, concrete sidewalks.

```json style
{
  "intent": "Modern-day New York City: historic masonry buildings in a lived-in, maintained present-day street scene, seen in first person at street level.",
  "camera": "first_person",
  "lighting": {"preset": "overcast_exterior"},
  "budgets": {"max_tris_per_mesh": 20000, "texture_big": 1024, "texture_small": 512}
}
```
