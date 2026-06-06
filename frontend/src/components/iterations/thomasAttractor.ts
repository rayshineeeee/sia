export const THOMAS_ATTRACTOR = {
  b: 0.208186,
  dt: 0.005,
  skipTransient: 720,
};

export function computeThomasAttractor({
  b = THOMAS_ATTRACTOR.b,
  dt = THOMAS_ATTRACTOR.dt,
  scale = 2.25,
  seed = 1,
  skip = THOMAS_ATTRACTOR.skipTransient,
  total,
}: {
  b?: number;
  dt?: number;
  scale?: number;
  seed?: number;
  skip?: number;
  total: number;
}) {
  const positions = new Float32Array(total * 3);
  let x = 0.1 + Math.sin(seed) * 0.018;
  let y = Math.cos(seed * 0.7) * 0.018;
  let z = Math.sin(seed * 1.3) * 0.018;

  for (let i = 0; i < skip; i += 1) {
    const next = stepThomas(x, y, z, b, dt);
    x = next.x;
    y = next.y;
    z = next.z;
  }

  let minX = Infinity;
  let minY = Infinity;
  let minZ = Infinity;
  let maxX = -Infinity;
  let maxY = -Infinity;
  let maxZ = -Infinity;

  for (let i = 0; i < total; i += 1) {
    const next = stepThomas(x, y, z, b, dt);
    x = next.x;
    y = next.y;
    z = next.z;

    const cursor = i * 3;
    positions[cursor] = x;
    positions[cursor + 1] = y;
    positions[cursor + 2] = z;

    minX = Math.min(minX, x);
    minY = Math.min(minY, y);
    minZ = Math.min(minZ, z);
    maxX = Math.max(maxX, x);
    maxY = Math.max(maxY, y);
    maxZ = Math.max(maxZ, z);
  }

  const centerX = (minX + maxX) / 2;
  const centerY = (minY + maxY) / 2;
  const centerZ = (minZ + maxZ) / 2;
  const span = Math.max(maxX - minX, maxY - minY, maxZ - minZ, 1);
  const normalizedScale = scale / span;

  for (let i = 0; i < positions.length; i += 3) {
    positions[i] = (positions[i] - centerX) * normalizedScale;
    positions[i + 1] = (positions[i + 1] - centerY) * normalizedScale;
    positions[i + 2] = (positions[i + 2] - centerZ) * normalizedScale;
  }

  return positions;
}

function stepThomas(x: number, y: number, z: number, b: number, dt: number) {
  return {
    x: x + dt * (Math.sin(y) - b * x),
    y: y + dt * (Math.sin(z) - b * y),
    z: z + dt * (Math.sin(x) - b * z),
  };
}
