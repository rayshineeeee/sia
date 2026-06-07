#version 330

in vec2 v_uv;
uniform sampler2D u_input; // not used for procedural content
uniform vec2 u_resolution;
uniform float u_time;

out vec4 f_color;

// ---------- hash utilities ----------
float hash21(vec2 p) {
    p = fract(p * vec2(123.34, 456.21));
    p += dot(p, p + 23.7);
    return fract(p.x * p.y);
}

// ---------- 3D Thomas attractor (double‑lobe) ----------
vec3 attractorStep(vec3 p) {
    const float b = 0.208;
    return vec3(sin(p.y) - b * p.x,
                sin(p.z) - b * p.y,
                sin(p.x) - b * p.z);
}

// Generate a point on the attractor using a time parameter (t)
vec3 attractorPos(float t) {
    vec3 p = vec3(sin(t), cos(t), sin(t * 0.7));
    const int ITER = 40;   // more iterations → tighter filament
    const float dt = 0.02;
    for (int i = 0; i < ITER; ++i) {
        p += attractorStep(p) * dt;
    }
    return p;
}

// Slow rotation matrix (Y axis) – matrix on left side
mat3 rotationY(float a) {
    float c = cos(a), s = sin(a);
    return mat3( c, 0.0,  s,
                0.0, 1.0, 0.0,
               -s, 0.0,  c);
}

// ---------- distance to nearest filament point (brute‑force sampling) ----------
float filamentDensity(vec3 ro, vec3 rd) {
    float t = 0.0;
    float acc = 0.0;
    const int steps = 140;          // more ray steps for higher density
    const float dtRay = 0.015;      // smaller ray step size
    const float dtCurve = 0.008;    // finer spacing between curve samples
    const int curveSamples = 300;   // more samples per ray step
    for (int i = 0; i < steps; ++i) {
        vec3 pos = ro + rd * t;
        for (int j = 0; j < curveSamples; ++j) {
            float ti = u_time * 0.25 + float(j) * dtCurve; // slow animation
            vec3 p = attractorPos(ti);
            p = rotationY(u_time * 0.2) * p; // gentle spin
            float d = length(pos - p);
            // Very narrow kernel – bright when extremely close
            float w = exp(-d * d * 1200.0);
            // Increase contribution per sample for higher density
            acc += w * 0.0035;
        }
        t += dtRay;
    }
    return acc;
}

void main() {
    // Normalized pixel coordinates (centered, y up)
    vec2 uv = (gl_FragCoord.xy - 0.5 * u_resolution) / u_resolution.y;

    // Camera orbit around the origin – slow motion
    float camAngle = u_time * 0.07;
    vec3 camPos = vec3(3.0 * sin(camAngle), 0.6, 3.0 * cos(camAngle));
    vec3 target = vec3(0.0);
    vec3 forward = normalize(target - camPos);
    vec3 right = normalize(cross(vec3(0.0, 1.0, 0.0), forward));
    vec3 up = cross(forward, right);
    vec3 rd = normalize(forward + uv.x * right + uv.y * up);

    // Accumulate filament brightness
    float raw = filamentDensity(camPos, rd);

    // High‑contrast tone‑mapping: push values into bright white
    float bright = 1.0 - exp(-raw * 45.0);
    // Sharpen overlapping filaments while keeping fine lines crisp
    bright = pow(bright, 0.55);

    // Final color: pure white on black background
    f_color = vec4(vec3(bright), 1.0);
}