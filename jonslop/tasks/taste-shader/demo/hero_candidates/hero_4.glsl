#version 330
uniform sampler2D u_input;
uniform vec2 u_resolution;
uniform float u_time;
in vec2 v_uv;
out vec4 f_color;

// hero_4 — kaleidoscopic IFS (iterated function system) with a reaction-diffusion
// -style threshold pass. Real math: fold space into a wedge (dihedral symmetry),
// then iterate an affine contraction (scale+rotate+translate) — a deterministic
// IFS whose orbit density we read as an emergent organic pattern, then posterize
// it with smooth thresholds (the gooey "RD" look) and color teal->orange->red.

mat2 rot(float a) { return mat2(cos(a), -sin(a), sin(a), cos(a)); }

// fold p into one wedge of an n-fold kaleidoscope (mirror dihedral symmetry)
vec2 kaleido(vec2 p, float n) {
    float ang = 3.14159265 / n;
    float a = atan(p.y, p.x);
    float r = length(p);
    a = mod(a, 2.0 * ang) - ang;        // wrap into wedge
    a = abs(a);                          // mirror -> dihedral
    return vec2(cos(a), sin(a)) * r;
}

void main() {
    vec2 uv = (v_uv - 0.5) * vec2(u_resolution.x / u_resolution.y, 1.0);
    float t = u_time * 0.4;

    vec2 p = uv * 1.4;
    float sym = 6.0 + 2.0 * sin(t * 0.2);   // breathing fold count
    p = kaleido(p, sym);

    // IFS orbit: iterate an affine contraction, accumulate proximity to attractor
    float acc = 0.0;
    float dmin = 1e9;
    vec2 z = p;
    mat2 R = rot(0.5 + 0.25 * sin(t * 0.5));
    for (int i = 0; i < 14; i++) {
        z = R * z * 1.32;                  // scale + rotate (contraction inverse)
        z = abs(z) - vec2(0.55, 0.42);     // fold (box-fold style nonlinearity)
        z += 0.18 * vec2(sin(t + float(i)), cos(t * 0.7 - float(i)));
        float d = length(z);
        dmin = min(dmin, d);
        acc += exp(-3.0 * d) * (0.6 + 0.4 * sin(float(i) + t)); // orbit density
    }

    // reaction-diffusion-style smooth threshold (gooey posterize / SDF cutoff)
    float field = acc * 0.5 + (1.0 - dmin);
    float a = smoothstep(0.35, 0.55, fract(field * 1.5));
    float b = smoothstep(0.55, 0.75, fract(field * 1.5 + 0.33));
    float pattern = clamp(a + 0.6 * b, 0.0, 1.0);

    // teal -> orange palette by field, with the emergent threshold as structure
    float ramp = clamp(field * 0.45, 0.0, 1.0);
    vec3 deep   = vec3(0.02, 0.07, 0.12);
    vec3 teal   = vec3(0.06, 0.55, 0.66);
    vec3 orange = vec3(1.00, 0.52, 0.16);
    vec3 base = mix(deep, teal, smoothstep(0.1, 0.55, ramp));
    base = mix(base, orange, smoothstep(0.55, 0.95, ramp));

    vec3 col = mix(base * 0.35, base, pattern);
    // crisp emergent rims where the threshold flips -> additive-emissive from math
    float edge = smoothstep(0.45, 0.5, pattern) * (1.0 - smoothstep(0.5, 0.6, pattern));
    col += orange * edge * 1.2;

    // narrative red riding the IFS attractor core (the string of fate, literal)
    float core = smoothstep(0.18, 0.0, dmin);
    col = mix(col, vec3(0.95, 0.07, 0.13), core * 0.7);

    // subtle radial vignette in teal (depth, not a black void)
    col *= mix(1.0, 0.55, smoothstep(0.4, 1.1, length(uv)));

    col = col / (col + 0.7);
    col = pow(col, vec3(0.88));
    f_color = vec4(col, 1.0);
}
