import { useEffect } from 'react';

type ShortcutAction = () => void;

interface Shortcuts {
  [key: string]: ShortcutAction;
}

/**
 * Hook to handle global keyboard shortcuts.
 * Pass an object where keys are string representations of combos (e.g., 'mod+k', 'mod+n')
 * and values are the actions to perform.
 * 'mod' automatically maps to Command on Mac and Ctrl on Windows/Linux.
 */
export const useKeyboardShortcuts = (shortcuts: Shortcuts) => {
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      const isMac = /Mac|iPod|iPhone|iPad/.test(navigator.platform);
      const modKey = isMac ? event.metaKey : event.ctrlKey;

      Object.entries(shortcuts).forEach(([combo, action]) => {
        const parts = combo.toLowerCase().split('+');
        const key = parts.pop();

        const needsMod = parts.includes('mod');
        const needsShift = parts.includes('shift');
        const needsAlt = parts.includes('alt');

        if (
          event.key.toLowerCase() === key &&
          modKey === needsMod &&
          event.shiftKey === needsShift &&
          event.altKey === needsAlt
        ) {
          event.preventDefault();
          action();
        }
      });
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [shortcuts]);
};
