#version 330
uniform sampler2D u_input;
uniform vec2 u_resolution;
uniform float u_time;
in vec2 v_uv;
out vec4 f_color;

// hero_1 — domain-warped fbm "liquid chrome": organic flowing metal.
// Real math: iterated value-noise fbm fed back into its own domain (warp of a
// warp), then turned into a surface via gradient -> normal -> anisotropic spec.

float hash(vec2 p) {
    p = fract(p * vec2(123.34, 456.21));
    p += dot(p, p + 45.32);
    return fract(p.x * p.y);
}

float vnoise(vec2 p) {
    vec2 i = floor(p);
    vec2 f = fract(p);
    f = f * f * (3.0 - 2.0 * f);              // smoothstep interp
    float a = hash(i + vec2(0.0, 0.0));
    float b = hash(i + vec2(1.0, 0.0));
    float c = hash(i + vec2(0.0, 1.0));
    float d = hash(i + vec2(1.0, 1.0));
    return mix(mix(a, b, f.x), mix(c, d, f.x), f.y);
}

float fbm(vec2 p) {
    float v = 0.0;
    float amp = 0.55;
    mat2 rot = mat2(0.80, 0.60, -0.60, 0.80); // rotate each octave -> less grid
    for (int i = 0; i < 6; i++) {
        v += amp * vnoise(p);
        p = rot * p * 2.02 + 11.3;
        amp *= 0.5;
    }
    return v;
}

// double domain warp: warp the domain, then warp again with the warped field.
float warped(vec2 p, float t, out vec2 q, out vec2 r) {
    q = vec2(fbm(p + vec2(0.0, 0.0) + 0.15 * t),
             fbm(p + vec2(5.2, 1.3) - 0.10 * t));
    r = vec2(fbm(p + 3.2 * q + vec2(1.7, 9.2) + 0.12 * t),
             fbm(p + 3.2 * q + vec2(8.3, 2.8) - 0.13 * t));
    return fbm(p + 3.6 * r);
}

void main() {
    vec2 uv = (v_uv - 0.5) * vec2(u_resolution.x / u_resolution.y, 1.0);
    float t = u_time * 0.35;

    vec2 p = uv * 2.6;
    vec2 q, r;
    float h = warped(p, t, q, r);

    // finite-difference gradient of the height field -> faux surface normal
    float e = 0.012;
    vec2 dq, dr;
    float hx = warped(p + vec2(e, 0.0), t, dq, dr);
    float hy = warped(p + vec2(0.0, e), t, dq, dr);
    vec3 n = normalize(vec3((h - hx) / e, (h - hy) / e, 1.0));

    // chrome lighting: a moving key + a sharp anisotropic highlight
    vec3 L = normalize(vec3(cos(t * 0.7), sin(t * 0.7), 0.85));
    vec3 V = vec3(0.0, 0.0, 1.0);
    vec3 H = normalize(L + V);
    float diff = clamp(dot(n, L) * 0.5 + 0.5, 0.0, 1.0);
    float spec = pow(clamp(dot(n, H), 0.0, 1.0), 64.0);
    float fres = pow(1.0 - clamp(dot(n, V), 0.0, 1.0), 3.0);

    // teal -> orange ramp driven by the warp magnitude (math-legible color)
    float ramp = clamp(h * 0.9 + length(r) * 0.4, 0.0, 1.0);
    vec3 teal   = vec3(0.04, 0.42, 0.55);
    vec3 deep   = vec3(0.02, 0.10, 0.18);
    vec3 orange = vec3(1.00, 0.55, 0.18);
    vec3 base = mix(deep, teal, smoothstep(0.15, 0.6, ramp));
    base = mix(base, orange, smoothstep(0.6, 0.95, ramp));

    vec3 col = base * (0.35 + 0.85 * diff);
    col += orange * spec * 1.3;            // hot specular streak
    col += vec3(0.5, 0.8, 1.0) * fres * 0.45; // cool rim = chrome edge
    // a single narrative-red vein riding the deepest warp valley
    float vein = smoothstep(0.05, 0.0, abs(r.y - 0.5)) * smoothstep(0.4, 0.0, h);
    col += vec3(0.9, 0.05, 0.12) * vein * 0.6;

    col = col / (col + 0.6);               // soft filmic shoulder
    col = pow(col, vec3(0.85));            // gamma lift
    f_color = vec4(col, 1.0);
}
