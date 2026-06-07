#version 330
in vec2 v_uv;
uniform sampler2D u_input;
uniform vec2 u_resolution;
uniform float u_time;
out vec4 f_color;

//--- Utility functions -------------------------------------------------------
float hash(float n) { return fract(sin(n) * 43758.5453123); }

mat3 rotationY(float a) { float c = cos(a), s = sin(a); return mat3(c, 0.0, -s, 0.0, 1.0, 0.0, s, 0.0, c); }
mat3 rotationZ(float a) { float c = cos(a), s = sin(a); return mat3(c, -s, 0.0, s, c, 0.0, 0.0, 0.0, 1.0); }
mat3 rotationX(float a) { float c = cos(a), s = sin(a); return mat3(1.0, 0.0, 0.0, 0.0, c, -s, 0.0, s, c); }

//--- Attractor --------------------------------------------------------------
vec3 ribbonPos(float t) {
    float x = sin(t) + 2.0 * sin(2.0 * t);
    float y = cos(t) - 2.0 * cos(2.0 * t);
    float z = -sin(3.0 * t);
    return vec3(x, y, z) * 0.28;
}

float ribbonGrid(float t) {
    float a = fract(t * 12.3);
    float b = fract(t * 7.1);
    float lineA = step(0.48, fract(a * 20.0));
    float lineB = step(0.48, fract(b * 20.0));
    return max(lineA, lineB);
}

float segmentDist(vec2 p, vec2 a, vec2 b) {
    vec2 pa = p - a;
    vec2 ba = b - a;
    float h = clamp(dot(pa, ba) / dot(ba, ba), 0.0, 1.0);
    return length(pa - ba * h);
}

void main() {
    vec2 uv = v_uv;
    const int STEPS = 6000;          // keep high density but a bit cheaper
    const float dt = 0.004;
    float time = u_time * 0.35;

    // Camera rotation – slow, steady
    mat3 rot = rotationY(time * 0.18) * rotationZ(time * 0.13) * rotationX(0.25);
    float flow = time * 2.0;

    float intensity = 0.0;
    const vec3 lightDir = normalize(vec3(0.6, 0.8, 1.0));

    // Width & glow – sharpened for high contrast
    const float halfWidth   = 0.025;   // much wider ribbon (visual ribbon)
    const float coreRadius  = 0.0006; // sharper core
    const float haloRadius  = 0.004;  // tighter halo
    const float haloWeight  = 0.4;    // less bloom, crisper

    for (int i = 0; i < STEPS; ++i) {
        float t = flow + float(i) * dt;
        vec3 pos = rot * ribbonPos(t);
        // Add high‑frequency jitter to create a fibrous texture
        float jitter = (hash(t * 12.7) - 0.5) * 0.006;
        pos += vec3(jitter, jitter * 0.7, jitter * 0.3);

        // Tangent for ribbon framing
        vec3 posNext = rot * ribbonPos(t + dt);
        vec3 posPrev = rot * ribbonPos(t - dt);
        vec3 tangent = normalize(posNext - posPrev);
        vec3 up = vec3(0.0, 0.0, 1.0);
        vec3 binorm = normalize(cross(tangent, up));
        vec3 normal = normalize(cross(binorm, tangent));
        float lit = dot(normal, lightDir) * 0.5 + 0.5;

        // Two edge positions (ribbon extrusion)
        vec3 posL = pos - binorm * halfWidth;
        vec3 posR = pos + binorm * halfWidth;

        // Simple perspective projection
        float perspL = 1.0 / (posL.z * 0.5 + 1.0);
        float perspR = 1.0 / (posR.z * 0.5 + 1.0);
        vec2 projL = posL.xy * perspL * 0.5 + 0.5;
        vec2 projR = posR.xy * perspR * 0.5 + 0.5;

        // Distance from fragment to ribbon segment
        float d = segmentDist(uv, projL, projR);

        // Core and halo contributions – sharper now
        float core = exp(-pow(d / coreRadius, 2.0) * 6.0);
        float halo = exp(-pow(d / haloRadius, 2.0) * 1.5);

        // Wire‑frame like texture
        float grid = ribbonGrid(t);
        float texWeight = mix(0.6, 1.0, grid); // emphasise grid lines

        float weight = (core + haloWeight * halo) * texWeight * lit;

        // Depth fade (keep far parts visible but slightly dimmer)
        float depthFade = smoothstep(-0.2, 0.5, pos.z);
        weight *= depthFade;

        // Age fade – older points fade quickly to keep front dense
        float age = float(i) / float(STEPS);
        weight *= exp(-age * 6.0);

        // Small brightness variation using hash (adds speckle)
        float flowBright = 0.7 + 0.3 * hash(t * 7.3 + u_time * 0.5);
        intensity += weight * flowBright;
    }

    // High contrast tone mapping – aim for pure white where bright
    float exposure = 8.0;
    float col = 1.0 - exp(-intensity * exposure);
    col = clamp(col, 0.0, 1.0);

    // Remove any residual blur – gamma close to 1
    col = pow(col, 0.95);

    vec3 color = vec3(col);
    float alpha = col;
    f_color = vec4(color, alpha);
}
