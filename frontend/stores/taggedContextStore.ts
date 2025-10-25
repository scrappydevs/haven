import { create } from 'zustand';

export type ContextItemType = 'patient' | 'room' | 'alert' | 'protocol';

export interface ContextItem {
  id: string;
  name: string;
  type: ContextItemType;
  metadata?: any;
}

export interface TaggedContextState {
  contextItems: ContextItem[];
  maxItems: number;
}

export interface TaggedContextActions {
  addItem: (item: ContextItem) => void;
  removeItem: (itemId: string) => void;
  clearAll: () => void;
  hasItem: (itemId: string) => boolean;
  getItemsByType: (type: ContextItemType) => ContextItem[];
  getTaggedContext: () => ContextItem[] | null;
  popTaggedContext: () => ContextItem[] | null;
}

export type TaggedContextStore = TaggedContextState & TaggedContextActions;

const MAX_CONTEXT_ITEMS = 5;

export const useTaggedContextStore = create<TaggedContextStore>((set, get) => ({
  contextItems: [],
  maxItems: MAX_CONTEXT_ITEMS,

  addItem: (item: ContextItem) => {
    const { contextItems, maxItems } = get();

    // Don't add duplicates
    if (contextItems.some(existing => existing.id === item.id)) {
      return;
    }

    // Add new item, keep most recent up to maxItems
    const newItems =
      contextItems.length >= maxItems
        ? [item, ...contextItems.slice(0, maxItems - 1)]
        : [item, ...contextItems];

    set({ contextItems: newItems });
  },

  removeItem: (itemId: string) => {
    set(state => ({
      contextItems: state.contextItems.filter(item => item.id !== itemId),
    }));
  },

  clearAll: () => {
    set({ contextItems: [] });
  },

  hasItem: (itemId: string) => {
    return get().contextItems.some(item => item.id === itemId);
  },

  getItemsByType: (type: ContextItemType) => {
    return get().contextItems.filter(item => item.type === type);
  },

  getTaggedContext: () => {
    const { contextItems } = get();
    
    if (contextItems.length === 0) {
      return null;
    }

    return contextItems.map(item => ({
      id: item.id,
      name: item.name,
      type: item.type,
      metadata: item.metadata
    }));
  },

  popTaggedContext: () => {
    const { contextItems } = get();
    
    if (contextItems.length === 0) {
      return null;
    }

    const itemsToReturn = contextItems.map(item => ({
      id: item.id,
      name: item.name,
      type: item.type,
      metadata: item.metadata
    }));

    // Clear after popping
    set({ contextItems: [] });
    return itemsToReturn;
  },
}));

