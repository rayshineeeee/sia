#version 330
in vec2 v_uv;
uniform sampler2D u_input;
uniform vec2 u_resolution;
uniform float u_time;
out vec4 f_color;

// Torus‑knot parameters (closed looping ribbon)
const float R = 0.5;          // major radius
const float r = 0.2;          // minor radius
const int   p = 2;            // longitudinal wraps
const int   q = 3;            // latitudinal wraps
const int   STEPS = 800;      // density of points along the knot
const float RADIUS = 0.015;   // visual thickness (in uv space)
const float EXPOSURE = 2.0;   // controls overall brightness

// Simple 2‑D rotation matrix (slow overall rotation)
mat2 rot(float a) {
    float c = cos(a);
    float s = sin(a);
    return mat2(c, -s, s, c);
}

void main() {
    // Normalised screen coordinates centred at (0,0) in range [-1,1]
    vec2 uv = v_uv * 2.0 - 1.0;

    float intensity = 0.0;
    float dt = 6.28318530718 / float(STEPS); // 2*PI / steps

    // Slow rotation of the whole knot
    float rotSpeed = 0.2; // radians per second
    mat2 globalRot = rot(u_time * rotSpeed);

    for (int i = 0; i < STEPS; ++i) {
        float t = float(i) * dt;
        // Torus‑knot parametric equation
        float ct = cos(t);
        float st = sin(t);
        float cp = cos(float(p) * t);
        float sp = sin(float(p) * t);
        float cq = cos(float(q) * t);
        float sq = sin(float(q) * t);
        vec3 p3 = vec3(
            (R + r * cq) * cp,
            (R + r * cq) * sp,
            r * sq
        );
        // Apply a gentle rotation around Z (adds visual variation)
        vec2 xy = globalRot * p3.xy;
        vec2 proj = xy * 0.5; // scale to fit inside [-1,1]
        // Accumulate contribution if pixel is near the projected point
        float d = length(uv - proj);
        intensity += exp(- (d * d) / (RADIUS * RADIUS));
    }

    // High‑contrast tone‑mapping (exponential fall‑off) and bloom‑like power curve
    float col = 1.0 - exp(-intensity * EXPOSURE);
    col = pow(col, 0.6); // keep bright core while allowing soft halo

    f_color = vec4(vec3(col), 1.0);
}
