"use client";
import { Html, Line, OrbitControls } from "@react-three/drei";
import { Canvas, useFrame, useThree, type ThreeEvent } from "@react-three/fiber";
import { useInView } from "framer-motion";
import { useEffect, useLayoutEffect, useMemo, useRef, useState, type ReactNode } from "react";
import * as THREE from "three";
import type { Chip, Run } from "@/lib/data";

const GENUINE = "#2a78d6";
const GENUINE_HI = "#5aa0f2";
const FORGED = "#eb6834";
const GOLD = "#c9a24a";

const reduced = () => typeof window !== "undefined" && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

/** Mounts its 3D scene only while near the viewport, so off-screen canvases cost nothing. */
export function Scene({ children, camera, className = "canvas3d", label }: {
  children: ReactNode; camera: [number, number, number]; className?: string; label: string;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const near = useInView(ref, { margin: "200px 0px" });
  return (
    <div ref={ref} className={className} role="img" aria-label={label}>
      {near && (
        <Canvas camera={{ position: camera, fov: 40 }} dpr={[1, 2]} gl={{ antialias: true, alpha: true }}>
          {children}
        </Canvas>
      )}
    </div>
  );
}

const lerp = (a: number, b: number, t: number) => a + (b - a) * t;

function chipPositions(chip: Chip, spread = 0.62) {
  return chip.qubits.map((q) => new THREE.Vector3((q.x - 7.5) * spread, 0, (q.y - 7.5) * spread));
}

function Lattice({ chip, placements, ghost = false, onHover }: {
  chip: Chip; placements: [number, number][]; ghost?: boolean; onHover?: (q: number | null) => void;
}) {
  const mesh = useRef<THREE.InstancedMesh>(null);
  const pos = useMemo(() => chipPositions(chip), [chip]);
  const placed = useMemo(() => new Set(placements.flat()), [placements]);

  useLayoutEffect(() => {
    const m = mesh.current!;
    const t1s = chip.qubits.map((q) => q.T1 ?? 0).sort((a, b) => a - b);
    const dummy = new THREE.Object3D();
    const cold = new THREE.Color("#334055");
    const warm = new THREE.Color("#dfe8f2");
    chip.qubits.forEach((q, i) => {
      dummy.position.copy(pos[i]);
      dummy.scale.setScalar((placed.has(i) ? 1.5 : 1) * (ghost ? 0.7 : 1));
      dummy.updateMatrix();
      m.setMatrixAt(i, dummy.matrix);
      const rank = t1s.indexOf(q.T1 ?? 0) / t1s.length; // brighter = longer T1
      m.setColorAt(i, placed.has(i) && !ghost ? new THREE.Color(GOLD) : cold.clone().lerp(warm, rank));
    });
    m.instanceMatrix.needsUpdate = true;
    if (m.instanceColor) m.instanceColor.needsUpdate = true;
  }, [chip, pos, placed, ghost]);

  const edges = useMemo(() => {
    const g = new THREE.BufferGeometry();
    const p: number[] = [];
    const c: number[] = [];
    const good = new THREE.Color(ghost ? FORGED : GOLD).multiplyScalar(ghost ? 0.5 : 0.55);
    const bad = new THREE.Color("#ff3b3b");
    chip.edges.forEach(([a, b, e]) => {
      p.push(...pos[a].toArray(), ...pos[b].toArray());
      const t = Math.min(1, ((e ?? 0.01) - 0.002) / 0.03);
      const col = ghost ? good : good.clone().lerp(bad, t);
      c.push(col.r, col.g, col.b, col.r, col.g, col.b);
    });
    g.setAttribute("position", new THREE.Float32BufferAttribute(p, 3));
    g.setAttribute("color", new THREE.Float32BufferAttribute(c, 3));
    return g;
  }, [chip, pos, ghost]);

  return (
    <group>
      <lineSegments geometry={edges}>
        <lineBasicMaterial vertexColors transparent opacity={ghost ? 0.22 : 0.8} />
      </lineSegments>
      <instancedMesh ref={mesh} args={[undefined, undefined, chip.qubits.length]}
        onPointerMove={onHover ? (e: ThreeEvent<PointerEvent>) => { e.stopPropagation(); onHover(e.instanceId ?? null); } : undefined}
        onPointerOut={onHover ? () => onHover(null) : undefined}>
        <sphereGeometry args={[0.11, 16, 16]} />
        {ghost
          ? <meshBasicMaterial color={FORGED} wireframe transparent opacity={0.28} />
          : <meshBasicMaterial toneMapped={false} />}
      </instancedMesh>
      {!ghost && placements.map(([t, n]) => (
        <group key={t}>
          <Halo at={pos[t]} />
          <Halo at={pos[n]} small />
        </group>
      ))}
    </group>
  );
}

function Halo({ at, small = false }: { at: THREE.Vector3; small?: boolean }) {
  const ref = useRef<THREE.Mesh>(null);
  const phase = useMemo(() => Math.random() * 6, []);
  useFrame(({ clock }) => {
    if (!ref.current) return;
    const s = (small ? 0.28 : 0.4) * (1 + 0.25 * Math.sin(clock.elapsedTime * 2.4 + phase));
    ref.current.scale.setScalar(s);
  });
  return (
    <mesh ref={ref} position={at}>
      <sphereGeometry args={[1, 24, 24]} />
      <meshBasicMaterial color={GOLD} transparent opacity={0.18} depthWrite={false} blending={THREE.AdditiveBlending} />
    </mesh>
  );
}

/** Hero: the real ibm_marrakesh coupling map, with the Forger's translucent copy hovering above it. */
export function ChipScene({ chip, placements }: { chip: Chip; placements: [number, number][] }) {
  const root = useRef<THREE.Group>(null);
  const ghost = useRef<THREE.Group>(null);
  const [hover, setHover] = useState<number | null>(null);
  const still = useMemo(reduced, []);
  const pos = useMemo(() => chipPositions(chip), [chip]);
  const { camera, size } = useThree();
  const wide = size.width / size.height > 1.25;

  useEffect(() => {
    // Fit the ~10-unit lattice to the viewport; on wide screens it sits right of the headline.
    const aspect = size.width / size.height;
    const d = wide ? 14 : Math.min(30, 13 / Math.max(aspect, 0.45));
    camera.position.set(0, d * 0.7, d * 0.72);
    camera.lookAt(0, wide ? 0.6 : -1.2, 0);
  }, [camera, size, wide]);

  useFrame(({ clock, pointer }) => {
    const t = still ? 0 : clock.elapsedTime;
    if (root.current) {
      root.current.rotation.y = lerp(root.current.rotation.y, t * 0.05 + pointer.x * 0.35, 0.05);
      root.current.rotation.x = lerp(root.current.rotation.x, -pointer.y * 0.12, 0.05);
    }
    if (ghost.current) {
      ghost.current.position.y = 2.7 + Math.sin(t * 0.8) * 0.18;
      ghost.current.position.x = Math.sin(t * 0.37) * 0.12;
      ghost.current.rotation.y = Math.sin(t * 0.3) * 0.03;
    }
  });

  const q = hover !== null ? chip.qubits[hover] : null;
  return (
    <group ref={root} position={[wide ? 4.6 : 0, 0, 0]}>
      <Lattice chip={chip} placements={placements} onHover={setHover} />
      <group ref={ghost}>
        <Lattice chip={chip} placements={placements} ghost />
      </group>
      {q && hover !== null && (
        <Html position={pos[hover]} center style={{ pointerEvents: "none", transform: "translateY(-48px)" }}>
          <div className="mono" style={{ background: "#0b0e14ee", border: `1px solid ${GOLD}`, borderRadius: 8, padding: "8px 10px", fontSize: 11, whiteSpace: "nowrap", color: "#e4eaf0" }}>
            <b style={{ color: GOLD }}>Q{hover}</b>{placements.flat().includes(hover) ? "  · canary placement" : ""}<br />
            T1 {q.T1?.toFixed(0)} µs · T2 {q.T2?.toFixed(0)} µs<br />
            readout error {(q.readout_error * 100).toFixed(2)}%
          </div>
        </Html>
      )}
    </group>
  );
}

const NS = [0, 4, 8, 16, 32, 64, 128];

/** P(1) after N X gates, every placement as its own ribbon: Genuine bends upward, the Twin stays flat. */
export function CoherentScene({ genuine, twin, sandwich }: { genuine: Run; twin?: Run; sandwich: boolean }) {
  const sx = (i: number) => (i - 3) * 1.1;
  const sz = (k: number) => (k - 1.5) * 1.3;
  const sy = (p: number) => p * 12;
  const series = (run: Run, color: string, dz: number) =>
    run.per_placement.map((pl, k) => {
      const pts = NS.map((n, i) => {
        const hit = pl.coherent.find((c) => c[0] === n && c[1] === sandwich);
        return new THREE.Vector3(sx(i), sy(hit ? hit[2] : 0), sz(k) + dz);
      });
      return { pts, color, key: `${run.id}-${k}`, label: pl.placement.join("-") };
    });
  const all = [...series(genuine, GENUINE_HI, -0.18), ...(twin ? series(twin, FORGED, 0.18) : [])];
  return (
    <>
      <OrbitControls enableZoom={false} enablePan={false} autoRotate={!reduced()} autoRotateSpeed={0.5} maxPolarAngle={Math.PI / 2.1} />
      <gridHelper args={[10, 20, "#2b3546", "#1a2130"]} position={[0, 0, 0]} />
      {all.map((s) => (
        <group key={s.key}>
          <Line points={s.pts} color={s.color} lineWidth={3} />
          {s.pts.map((p, i) => (
            <group key={i}>
              <mesh position={p}><sphereGeometry args={[0.07, 12, 12]} /><meshBasicMaterial color={s.color} toneMapped={false} /></mesh>
              <Line points={[p, new THREE.Vector3(p.x, 0, p.z)]} color={s.color} lineWidth={0.6} transparent opacity={0.3} />
            </group>
          ))}
        </group>
      ))}
      {NS.map((n, i) => (
        <Html key={n} position={[sx(i), -0.05, sz(3) + 1.1]} center>
          <span className="mono" style={{ fontSize: 11, color: "#8791a3" }}>N={n}</span>
        </Html>
      ))}
      {genuine.per_placement.map((pl, k) => (
        <Html key={k} position={[sx(6) + 1.2, 0, sz(k)]} center>
          <span className="mono" style={{ fontSize: 10, color: GOLD, whiteSpace: "nowrap" }}>Q{pl.placement[0]}</span>
        </Html>
      ))}
      {[0.1, 0.2, 0.3, 0.4].map((p) => (
        <Html key={p} position={[sx(0) - 0.8, sy(p), sz(0) - 0.6]} center>
          <span className="mono" style={{ fontSize: 10, color: "#8791a3" }}>{p.toFixed(1)}</span>
        </Html>
      ))}
    </>
  );
}

/** Every time chunk of every Run as a point in three Signature features. */
export function SignatureScene({ points, axes }: {
  points: { x: number; y: number; z: number; origin: string; fresh: boolean; label: string }[]; axes: [string, string, string];
}) {
  const [hover, setHover] = useState<number | null>(null);
  const S = 4;
  const p = (v: { x: number; y: number; z: number }) => new THREE.Vector3((v.x - 0.5) * S, v.y * S, (v.z - 0.5) * S);
  const box = useMemo(() => new THREE.EdgesGeometry(new THREE.BoxGeometry(S, S, S)), []);
  return (
    <>
      <OrbitControls enableZoom={false} enablePan={false} autoRotate={!reduced()} autoRotateSpeed={0.6} />
      <lineSegments geometry={box} position={[0, S / 2, 0]}><lineBasicMaterial color="#2b3546" /></lineSegments>
      {points.map((v, i) => (
        <mesh key={i} position={p(v)} onPointerOver={(e) => { e.stopPropagation(); setHover(i); }} onPointerOut={() => setHover(null)}>
          {v.fresh ? <octahedronGeometry args={[0.13]} /> : <sphereGeometry args={[0.09, 14, 14]} />}
          <meshBasicMaterial color={v.origin === "genuine" ? GENUINE_HI : FORGED} toneMapped={false} wireframe={v.fresh} />
        </mesh>
      ))}
      {hover !== null && (
        <Html position={p(points[hover])} center style={{ pointerEvents: "none", transform: "translateY(-30px)" }}>
          <div className="mono" style={{ background: "#0b0e14ee", border: "1px solid #c9a24a", borderRadius: 6, padding: "4px 8px", fontSize: 11, whiteSpace: "nowrap" }}>
            {points[hover].label}
          </div>
        </Html>
      )}
      <Html position={[0, -0.25, S / 2 + 0.4]} center><span className="mono" style={{ fontSize: 11, color: GOLD, whiteSpace: "nowrap" }}>{axes[0]} →</span></Html>
      <Html position={[-S / 2 - 0.3, S + 0.3, -S / 2]} center><span className="mono" style={{ fontSize: 11, color: GOLD, whiteSpace: "nowrap" }}>↑ {axes[1]}</span></Html>
      <Html position={[S / 2 + 0.4, -0.25, 0]} center><span className="mono" style={{ fontSize: 11, color: GOLD, whiteSpace: "nowrap" }}>{axes[2]} →</span></Html>
    </>
  );
}
