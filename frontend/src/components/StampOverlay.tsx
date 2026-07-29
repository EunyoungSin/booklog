import { useEffect, useState } from "react";

/** `trigger()`가 호출될 때마다 한 번씩 "도장 찍기" 애니메이션을 실행한다. */
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
