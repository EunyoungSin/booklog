import { useEffect, useState } from "react";

/** Fires a one-shot "rubber stamp" animation each time `trigger()` is called. */
export function useStamp() {
  const [triggerKey, setTriggerKey] = useState(0);
  function trigger() {
    setTriggerKey((k) => k + 1);
  }
  return { triggerKey, trigger };
}

export function StampOverlay({ triggerKey, label = "SAVED" }: { triggerKey: number; label?: string }) {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    if (triggerKey === 0) return;
    setVisible(true);
    const timeout = setTimeout(() => setVisible(false), 950);
    return () => clearTimeout(timeout);
  }, [triggerKey]);

  if (!visible) return null;

  return (
    <div className="stamp" key={triggerKey} aria-hidden="true">
      {label}
    </div>
  );
}
