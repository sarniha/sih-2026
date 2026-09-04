import type { EventResponse } from "../types/api";

export function groupAnprEvents(events: EventResponse[]): EventResponse[] {
  const groups = new Map<string, EventResponse>();

  for (const event of events) {
    const key = event.plate_text || event.object_id || event.id;
    const existing = groups.get(key);

    if (!existing) {
      groups.set(key, event);
    } else {
      const existingConf = existing.plate_confidence ?? existing.confidence;
      const currentConf = event.plate_confidence ?? event.confidence;

      if (currentConf > existingConf) {
        groups.set(key, event);
      }
    }
  }

  return Array.from(groups.values());
}
