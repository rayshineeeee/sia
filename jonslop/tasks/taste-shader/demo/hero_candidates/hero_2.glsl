#version 330
uniform sampler2D u_input;
uniform vec2 u_resolution;
uniform float u_time;
in vec2 v_uv;
out vec4 f_color;

// hero_2 — curl-noise flow field over a strange-attractor scaffold.
// Math-legible motion: we advect a dense ribbon of points through a divergence-
// free (curl of a scalar potential) velocity field warped by a de Jong-style
// attractor, and accumulate them analytically per-pixel (no real buffer needed).

float hash(vec2 p) {
    p = fract(p * vec2(127.1, 311.7));
    p += dot(p, p + 34.21);
    return fract(p.x * p.y);
}

float vnoise(vec2 p) {
    vec2 i = floor(p);
    vec2 f = fract(p);
    f = f * f * (3.0 - 2.0 * f);
    float a = hash(i);
    float b = hash(i + vec2(1.0, 0.0));
    float c = hash(i + vec2(0.0, 1.0));
    float d = hash(i + vec2(1.0, 1.0));
    return mix(mix(a, b, f.x), mix(c, d, f.x), f.y);
}

// scalar potential; its curl (perpendicular gradient) is divergence-free flow
float potential(vec2 p, float t) {
    return vnoise(p * 1.3 + vec2(0.0, t * 0.25))
         + 0.5 * vnoise(p * 2.7 - vec2(t * 0.18, 0.0));
}

vec2 curl(vec2 p, float t) {
    float e = 0.02;
    float n1 = potential(p + vec2(0.0, e), t);
    float n2 = potential(p - vec2(0.0, e), t);
    float n3 = potential(p + vec2(e, 0.0), t);
    float n4 = potential(p - vec2(e, 0.0), t);
    return vec2(n1 - n2, n4 - n3) / (2.0 * e);  // (d/dy, -d/dx)
}

void main() {
    vec2 uv = (v_uv - 0.5) * vec2(u_resolution.x / u_resolution.y, 1.0);
    float t = u_time * 0.6;

    vec3 col = vec3(0.0);
    float dens = 0.0;

    // 90 seed streamlines; integrate each a few RK1 steps through the curl field
    const int N = 90;
    for (int i = 0; i < N; i++) {
        float fi = float(i);
        // de Jong attractor seed -> structured (not random) emission points
        float a = 2.01, b = -2.53, c = 1.61, d = -0.33;
        float s = fi * 0.21 + t * 0.15;
        vec2 p = vec2(sin(a * s) - cos(b * s),
                      sin(c * s) - cos(d * s)) * 0.42;

        // advect the seed forward through curl noise (the "particle")
        for (int k = 0; k < 5; k++) {
            p += curl(p * 2.2, t) * 0.045;
        }
        p += 0.12 * vec2(cos(fi * 1.7 + t), sin(fi * 2.3 - t)); // gentle spread

        float r = length(uv - p);
        float glow = 0.0018 / (r * r + 0.0009);   // additive point glow (math)
        dens += glow;

        // teal->orange palette indexed by streamline id + local speed
        float spd = length(curl(p * 2.2, t));
        float hue = fract(fi * 0.012 + spd * 0.25 + t * 0.02);
        vec3 teal   = vec3(0.10, 0.65, 0.78);
        vec3 orange = vec3(1.00, 0.52, 0.16);
        vec3 c0 = mix(teal, orange, smoothstep(0.2, 0.8, hue));
        col += c0 * glow;
    }

    col /= max(dens, 0.001);     // normalize hue
    col *= clamp(dens * 0.9, 0.0, 1.6);

    // dark teal field (NOT pure black) so it reads as a medium, not a void
    vec3 bg = mix(vec3(0.015, 0.045, 0.07), vec3(0.02, 0.10, 0.14),
                  smoothstep(0.9, 0.0, length(uv)));
    col += bg;

    // one red thread tracing the densest ridge — narrative color
    float thread = smoothstep(0.55, 1.4, dens);
    col = mix(col, vec3(0.95, 0.08, 0.14), thread * 0.5);

    col = col / (col + 0.7);
    col = pow(col, vec3(0.9));
    f_color = vec4(col, 1.0);
}
