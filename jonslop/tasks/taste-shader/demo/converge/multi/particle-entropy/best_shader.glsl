#version 330
in vec2 v_uv;
uniform sampler2D u_input;
uniform vec2 u_resolution;
uniform float u_time;
out vec4 f_color;

// ---------------------------------------------------------------
// Simple hash utilities (deterministic pseudo‑random)
float hash(float n) { return fract(sin(n) * 43758.5453123); }
vec3 hash3(float n) { return vec3(hash(n + 1.0), hash(n + 2.0), hash(n + 3.0)); }

// ---------------------------------------------------------------
// Thomas attractor (double‑lobe chaotic flow)
vec3 attractor(vec3 p) {
    const float b = 0.208;
    return vec3(
        sin(p.y) - b * p.x,
        sin(p.z) - b * p.y,
        sin(p.x) - b * p.z
    );
}

void main() {
    // Normalised screen coordinates, centre at (0,0) with aspect correction
    vec2 uv = v_uv * 2.0 - 1.0;
    uv.x *= u_resolution.x / u_resolution.y;

    float coreAcc = 0.0; // bright filament core
    float haloAcc = 0.0; // soft bloom around the core

    const int PARTICLES = 1500;   // more seed strands for richer geometry
    const int STEPS    = 300;     // finer integration for smoother ribbons
    const float dt = 0.008;

    // pixel‑size based radii (≈1 px core, ≈3 px halo)
    float pixelSize = 1.0 / max(u_resolution.x, u_resolution.y);
    float coreRadius = pixelSize * 0.5;   // half‑pixel for crisp line
    float haloRadius = pixelSize * 3.0;   // few‑pixel halo
    const float coreFalloff = 15000.0;    // sharp core decay
    const float haloFalloff = 200.0;      // tighter halo decay

    for (int i = 0; i < PARTICLES; ++i) {
        // Seed positions wander slowly with time – creates animation
        vec3 pos = hash3(float(i) + u_time * 0.07) * 2.0 - 1.0;
        for (int s = 0; s < STEPS; ++s) {
            // Integrate the attractor flow (Euler)
            pos += attractor(pos) * dt;
            // Project to screen space (ignore depth)
            vec2 p2 = pos.xy;
            p2.x *= u_resolution.x / u_resolution.y;
            float d = length(p2 - uv);
            // Core contribution – very thin, high‑contrast filament
            if (d < coreRadius) {
                coreAcc += exp(-d * d * coreFalloff);
            }
            // Halo contribution – larger radius, lower weight
            if (d < haloRadius) {
                haloAcc += exp(-d * d * haloFalloff);
            }
        }
    }

    // Clamp and combine core and halo
    float core = clamp(coreAcc, 0.0, 1.0);
    float halo = clamp(haloAcc * 0.04, 0.0, 1.0); // reduced bloom weight
    float bright = core + halo;
    // Remove very low‑level background noise
    bright = max(bright - 0.02, 0.0);
    // Apply a modest contrast boost to keep the filaments crisp
    bright = pow(bright, 2.2);

    vec3 col = vec3(bright);
    f_color = vec4(col, 1.0);
}