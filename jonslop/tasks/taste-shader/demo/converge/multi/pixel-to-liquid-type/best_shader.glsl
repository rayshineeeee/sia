#version 330

in vec2 v_uv;
uniform sampler2D u_input;
uniform vec2 u_resolution;
uniform float u_time;

out vec4 f_color;

void main()
{
    // Normalized screen coordinates with correct aspect ratio
    float aspect = u_resolution.x / u_resolution.y;
    vec2 fragPos = (v_uv - 0.5) * 2.0;      // range [-1,1]
    fragPos.x *= aspect;

    // Parameters for the Thomas attractor (more steps for denser ribbons)
    const float b = 0.208;
    const float dt = 0.02;
    const int steps = 600; // increased density

    // Seed point – static, the animation comes from view rotation
    vec3 p = vec3(0.1, 0.0, 0.0);

    float col = 0.0;
    float t = u_time;

    for (int i = 0; i < steps; ++i)
    {
        // Thomas attractor derivative
        vec3 dP = vec3(
            sin(p.y) - b * p.x,
            sin(p.z) - b * p.y,
            sin(p.x) - b * p.z
        );
        // Euler integration
        p += dt * dP;

        // Slow rotating view to expose the 3‑D structure
        float angleY = t * 0.2;   // Y‑axis rotation speed
        float angleX = t * 0.3;   // X‑axis rotation speed
        float ca = cos(angleY);
        float sa = sin(angleY);
        float cb = cos(angleX);
        float sb = sin(angleX);

        // Y rotation
        vec3 pY;
        pY.x =  ca * p.x + sa * p.z;
        pY.y =  p.y;
        pY.z = -sa * p.x + ca * p.z;

        // X rotation
        vec3 rp;
        rp.x = pY.x;
        rp.y =  cb * pY.y - sb * pY.z;
        rp.z =  sb * pY.y + cb * pY.z;

        // Simple perspective projection
        float camDist = 3.0;
        vec2 proj = rp.xy / (rp.z + camDist);
        proj.x *= aspect;

        // Distance from fragment to projected point
        float d = length(fragPos - proj);
        // Thinner, brighter filaments
        float weight = exp(-d * d * 800.0);
        col += weight;
    }

    // Allow higher accumulation before tone‑mapping
    col = clamp(col, 0.0, 5.0);
    // Strong contrast, pure black background
    float bright = 1.0 - exp(-col * 2.0);
    // Soft glow where strands overlap
    float halo = bright * bright * 0.7;
    float final = clamp(bright + halo, 0.0, 1.0);

    f_color = vec4(vec3(final), 1.0);
}