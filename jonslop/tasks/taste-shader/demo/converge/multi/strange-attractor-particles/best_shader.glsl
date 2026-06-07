#version 330
in vec2 v_uv;
uniform sampler2D u_input;
uniform vec2 u_resolution;
uniform float u_time;
out vec4 f_color;

// 2‑D hash returning float in [0,1]
float hash21(vec2 p) {
    p = fract(p * vec2(123.34, 456.21));
    p += dot(p, p + 45.32);
    return fract(p.x * p.y);
}

mat3 rotY(float a) {
    float c = cos(a);
    float s = sin(a);
    return mat3(
        c, 0.0, s,
        0.0, 1.0, 0.0,
       -s, 0.0, c
    );
}

mat3 rotX(float a) {
    float c = cos(a);
    float s = sin(a);
    return mat3(
        1.0, 0.0, 0.0,
        0.0, c, -s,
        0.0, s,  c
    );
}

void main() {
    vec2 uv = v_uv;                     // [0,1] screen coordinates
    float accum = 0.0;
    const float dt = 0.0025;            // integration step
    const int steps = 1800;             // geometry density
    const float b = 0.208186;           // Thomas attractor parameter

    // Seed the attractor with a time‑varying pseudo‑random start point
    vec3 pos = vec3(0.1, 0.0, 0.0) + vec3(
        hash21(vec2(u_time, 0.0)),
        hash21(vec2(u_time, 1.0)),
        hash21(vec2(u_time, 2.0))
    ) * 0.4;

    // Global rotation for a pleasing view
    mat3 rot = rotY(u_time * 0.3) * rotX(u_time * 0.4);

    for (int i = 0; i < steps; ++i) {
        // Thomas attractor Euler step
        pos += dt * vec3(
            sin(pos.y) - b * pos.x,
            sin(pos.z) - b * pos.y,
            sin(pos.x) - b * pos.z
        );

        // Rotate the point into view space
        vec3 rp = rot * pos;

        // Depth‑based attenuation – far points are dimmer but keep a faint trace
        float depthAtt = exp(-abs(rp.z) * 0.4);

        // Simple perspective projection (centered, focal length 1)
        vec2 proj = rp.xy / (1.0 + rp.z * 0.35);
        vec2 screenUV = proj * 0.5 + 0.5; // map to [0,1]

        // Distance in pixel units
        vec2 dxy = (uv - screenUV) * u_resolution;
        float d = length(dxy);
        // Very tight Gaussian → ~1 px filament width, sharpened by depth
        float intensity = exp(-d * d * 0.20) * depthAtt;
        accum += intensity;
    }

    // Convert accumulated energy to a high‑contrast, white‑only bloom
    // Over‑expose the bright core, then clamp to keep pure black elsewhere
    float bright = 1.0 - exp(-accum * 800.0);
    // Slight gamma to keep the halo soft while preserving crisp peaks
    float col = pow(bright, 0.55);
    col = clamp(col, 0.0, 1.0);
    f_color = vec4(vec3(col), 1.0);
}