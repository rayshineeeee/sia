#version 330
uniform sampler2D u_input;
uniform vec2 u_resolution;
uniform float u_time;
in vec2 v_uv;
out vec4 f_color;

// hero_3 — raymarched gyroid SDF: a dimensional, glossy triply-periodic surface.
// Real math: the gyroid implicit  sin x cos y + sin y cos z + sin z cos x = 0,
// sphere-traced with central-difference normals, lit with diffuse+spec+fresnel.

float gyroid(vec3 p) {
    return dot(sin(p), cos(p.yzx)); // sin x cos y + sin y cos z + sin z cos x
}

// signed distance to the thickened gyroid sheet (scaled to a metric estimate)
float map(vec3 p, float t) {
    p *= 1.6;
    float g = gyroid(p + vec3(0.0, t * 0.4, 0.0));
    float shell = abs(g) - 0.45;          // thickness of the sheet
    return shell * 0.55 / 1.6;            // Lipschitz fudge for stable stepping
}

vec3 calcNormal(vec3 p, float t) {
    vec2 e = vec2(0.002, 0.0);
    return normalize(vec3(
        map(p + e.xyy, t) - map(p - e.xyy, t),
        map(p + e.yxy, t) - map(p - e.yxy, t),
        map(p + e.yyx, t) - map(p - e.yyx, t)));
}

void main() {
    vec2 uv = (v_uv - 0.5) * vec2(u_resolution.x / u_resolution.y, 1.0);
    float t = u_time * 0.5;

    // slowly orbiting camera -> "depth that shouldn't be there"
    float ca = cos(t * 0.4), sa = sin(t * 0.4);
    vec3 ro = vec3(2.6 * sa, 0.8 * sin(t * 0.27), 2.6 * ca);
    vec3 fw = normalize(-ro);
    vec3 rt = normalize(cross(vec3(0.0, 1.0, 0.0), fw));
    vec3 up = cross(fw, rt);
    vec3 rd = normalize(uv.x * rt + uv.y * up + 1.5 * fw);

    float d = 0.0;
    float tmax = 9.0;
    bool hit = false;
    vec3 p = ro;
    for (int i = 0; i < 96; i++) {
        p = ro + rd * d;
        float s = map(p, t);
        if (s < 0.0008) { hit = true; break; }
        d += s;
        if (d > tmax) break;
    }

    vec3 col;
    if (hit) {
        vec3 n = calcNormal(p, t);
        vec3 V = -rd;
        vec3 L = normalize(vec3(0.7, 0.8, 0.4));
        vec3 H = normalize(L + V);
        float diff = clamp(dot(n, L) * 0.5 + 0.5, 0.0, 1.0);
        float spec = pow(clamp(dot(n, H), 0.0, 1.0), 80.0);
        float fres = pow(1.0 - clamp(dot(n, V), 0.0, 1.0), 4.0);

        // color by interior coordinate of the cell -> reveals the lattice (legible)
        float band = gyroid(p * 1.6 + vec3(0.0, t * 0.4, 0.0));
        float ramp = band * 0.5 + 0.5;
        vec3 teal   = vec3(0.05, 0.50, 0.62);
        vec3 deep   = vec3(0.02, 0.08, 0.14);
        vec3 orange = vec3(1.00, 0.50, 0.16);
        vec3 base = mix(deep, teal, smoothstep(0.2, 0.55, ramp));
        base = mix(base, orange, smoothstep(0.6, 0.95, ramp));

        float ao = clamp(d / tmax, 0.0, 1.0);   // cheap depth darkening
        col = base * (0.30 + 0.9 * diff) * (1.0 - 0.45 * ao);
        col += orange * spec * 1.4;             // glossy hotspot
        col += vec3(0.4, 0.75, 1.0) * fres * 0.5; // cool rim
        // narrative red where the surface is razor-thin (a seam of fate)
        float seam = smoothstep(0.06, 0.0, abs(band));
        col += vec3(0.9, 0.06, 0.12) * seam * 0.5;
    } else {
        // graded teal depth instead of flat black void
        float v = smoothstep(1.0, -0.4, uv.y);
        col = mix(vec3(0.01, 0.03, 0.05), vec3(0.03, 0.11, 0.15), v);
    }

    col = col / (col + 0.7);
    col = pow(col, vec3(0.88));
    f_color = vec4(col, 1.0);
}
