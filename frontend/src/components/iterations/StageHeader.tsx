import { TOTAL_ITERATIONS, iterations } from "./data";
import { generatedMeta } from "./iterations.generated";
import type { Iteration } from "./types";

export function StageHeader({
  activeIteration,
}: {
  activeIteration: Iteration;
}) {
  const real = iterations.filter((i) => typeof i.accuracy === "number");
  const baseline = real[0]?.accuracy;
  const best =
    generatedMeta?.bestAccuracy ||
    (real.length ? Math.max(...real.map((i) => i.accuracy ?? 0)) : undefined);
  const current = activeIteration.accuracy;

  return (
    <>
      <header className="app-bar">
        <div className="brand-lockup" style={{ display: "flex", alignItems: "center", gap: 8 }}>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src="/desiagn-mark.png"
            alt="deSIAgn"
            style={{ width: 28, height: 28, objectFit: "contain" }}
          />
          <span>deSIAgn</span>
        </div>
        <div className="active-readout" aria-live="polite">
          <span>{activeIteration.number}</span>
          <span>/ {TOTAL_ITERATIONS}</span>
        </div>
      </header>
      <div
        style={{
          position: "fixed",
          top: 68,
          left: 16,
          zIndex: 5000,
          display: "flex",
          gap: 12,
          alignItems: "center",
          pointerEvents: "none",
          background: "rgba(0,0,0,0.5)",
          padding: "10px 14px",
          borderRadius: 10,
          backdropFilter: "blur(6px)",
          color: "#fff",
          maxWidth: 470,
        }}
      >
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src="/reference.jpg"
          alt="taste reference"
          style={{
            width: 64,
            height: 64,
            objectFit: "cover",
            borderRadius: 8,
            border: "1px solid rgba(255,255,255,0.25)",
            flexShrink: 0,
          }}
        />
        <div style={{ lineHeight: 1.35, fontSize: 12 }}>
          <div
            style={{
              fontSize: 10,
              letterSpacing: "0.12em",
              textTransform: "uppercase",
              opacity: 0.65,
            }}
          >
            🎯 target = my taste
          </div>
          <div style={{ fontVariantNumeric: "tabular-nums" }}>
            taste match{" "}
            <strong style={{ fontSize: 15 }}>
              {typeof current === "number" ? `${current.toFixed(0)}%` : "—"}
            </strong>
            {typeof baseline === "number" && typeof best === "number" ? (
              <span style={{ opacity: 0.7 }}>
                {"  "}· baseline {baseline.toFixed(0)} → best {best.toFixed(0)}
              </span>
            ) : null}
          </div>
          <div style={{ fontSize: 10, opacity: 0.6, marginTop: 2 }}>
            human seeds, AI executes — swap the reference, the output changes
          </div>
        </div>
      </div>
      {(() => {
        const accs = iterations
          .filter((i) => typeof i.accuracy === "number")
          .map((i) => i.accuracy as number);
        if (accs.length < 2) return null;
        let rm = -Infinity;
        const rmax = accs.map((a) => (rm = Math.max(rm, a)));
        const W = 340;
        const H = 104;
        const pad = 10;
        const n = accs.length;
        const X = (i: number) => pad + (i / (n - 1)) * (W - 2 * pad);
        const Y = (a: number) => H - pad - (a / 100) * (H - 2 * pad);
        const toPath = (arr: number[]) =>
          arr.map((a, i) => `${i === 0 ? "M" : "L"} ${X(i).toFixed(1)} ${Y(a).toFixed(1)}`).join(" ");
        return (
          <div
            style={{
              position: "fixed",
              bottom: 16,
              left: 16,
              zIndex: 5000,
              pointerEvents: "none",
              background: "rgba(0,0,0,0.55)",
              padding: "10px 12px",
              borderRadius: 10,
              backdropFilter: "blur(6px)",
              color: "#fff",
            }}
          >
            <div
              style={{
                fontSize: 10,
                textTransform: "uppercase",
                letterSpacing: "0.12em",
                opacity: 0.65,
                marginBottom: 4,
              }}
            >
              improvement curve · {n} iterations · {accs[0].toFixed(0)} → {accs[n - 1].toFixed(0)} (best {rmax[n - 1].toFixed(0)})
            </div>
            <svg width={W} height={H} style={{ display: "block" }}>
              <line x1={pad} y1={H - pad} x2={W - pad} y2={H - pad} stroke="rgba(255,255,255,0.2)" />
              <line x1={pad} y1={Y(50)} x2={W - pad} y2={Y(50)} stroke="rgba(255,255,255,0.08)" />
              <path d={toPath(accs)} fill="none" stroke="rgba(255,255,255,0.35)" strokeWidth={1} />
              <path d={toPath(rmax)} fill="none" stroke="#eb6c36" strokeWidth={1.8} />
            </svg>
          </div>
        );
      })()}
    </>
  );
}
