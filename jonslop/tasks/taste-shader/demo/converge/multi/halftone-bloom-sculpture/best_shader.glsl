#version 330
in vec2 v_uv;
uniform sampler2D u_input;
uniform vec2 u_resolution;
uniform float u_time;
out vec4 f_color;

void main(){
    // Normalized screen coordinates with correct aspect ratio
    vec2 aspect = vec2(u_resolution.x/u_resolution.y, 1.0);
    vec2 uv = (v_uv - 0.5) * 2.0 * aspect;

    // Initial position of the attractor (centered)
    vec3 pos = vec3(0.0);
    // Subtle slow orbit to keep the pattern moving
    pos += 0.07 * vec3(sin(u_time*0.31), cos(u_time*0.27), sin(u_time*0.43));

    const int STEPS = 3000;       // enough for smooth ribbons, less heavy than before
    const float dt = 0.003;
    const float b = 0.208;

    float coreAcc = 0.0;   // ultra‑thin white core
    float haloAcc = 0.0;   // soft bloom around the core

    for(int i = 0; i < STEPS; ++i){
        // Thomas‑like attractor dynamics (sin‑based variant)
        vec3 dp = vec3(
            sin(pos.y) - b*pos.x,
            sin(pos.z) - b*pos.y,
            sin(pos.x) - b*pos.z
        );
        pos += dt * dp;

        // Simple perspective projection (camera looking towards +z)
        float perspective = 2.0 / (pos.z + 3.0);
        vec2 proj = pos.xy * perspective;

        float d = length(uv - proj);
        // Very thin core – high exponent makes it ~1‑pixel wide
        coreAcc += exp(-d * d * 80000.0);
        // Soft halo – lower exponent gives a gentle glow where strands cross
        haloAcc += exp(-d * d * 2000.0);
    }

    // Combine core and halo, keep values in [0,1]
    float acc = clamp(coreAcc + 0.15 * haloAcc, 0.0, 1.0);

    // Apply a strong gamma to keep the ribbons crisp on a pure black background
    float col = pow(acc, 0.22);
    // Light bloom boost that only affects the brighter parts
    col = col + 0.35 * col * col;

    f_color = vec4(vec3(col), 1.0);
}