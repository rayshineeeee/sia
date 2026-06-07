#version 330
in vec2 v_uv;
uniform sampler2D u_input;
uniform vec2 u_resolution;
uniform float u_time;
out vec4 f_color;

// Refined thin glowing ribbons of a 3D Thomas attractor on pure black.
const int STEPS = 1200;          // integration steps for smooth curves
const float DT = 0.004;          // integration step size
const float B = 0.208;           // Thomas attractor parameter
const float SCALE = 0.055;       // screen‑space scale – keeps filaments ~1 px

mat2 rot2(float a){
    float c = cos(a);
    float s = sin(a);
    return mat2(c, -s, s, c);
}

float attractorContribution(vec2 uv){
    vec3 p = vec3(0.1, 0.0, 0.0);
    float coreSum = 0.0;
    float haloSum = 0.0;
    float t = u_time * 0.5;
    for(int i = 0; i < STEPS; ++i){
        // subtle rotation for animation
        p.xy = rot2(t * 0.3) * p.xy;
        p.xz = rot2(t * 0.2) * p.xz;
        // Thomas attractor ODE step
        vec3 dp = vec3(
            sin(p.y) - B * p.x,
            sin(p.z) - B * p.y,
            sin(p.x) - B * p.z
        );
        p += DT * dp;
        // project to screen space (centered)
        vec2 proj = p.xy * SCALE + 0.5;
        float d = length(uv - proj);
        // very sharp core (~1 px)
        float core = exp(-d * d * 60000.0);
        // soft halo – creates bloom where strands overlap
        float halo = exp(-d * d * 500.0) * 0.25;
        coreSum += core;
        haloSum += halo;
    }
    // Combine core and halo with a slight weighting favoring the halo for bloom
    float intensity = coreSum + haloSum * 0.8;
    // Exponential tone‑mapping for high contrast on black background
    float col = 1.0 - exp(-intensity * 4.0);
    return col;
}

void main(){
    vec2 uv = v_uv;
    float acc = attractorContribution(uv);
    // Clamp and apply a gentle gamma to keep the thinnest filaments visible
    float intensity = clamp(acc, 0.0, 1.0);
    float finalColor = pow(intensity, 0.45);
    f_color = vec4(vec3(finalColor), 1.0);
}