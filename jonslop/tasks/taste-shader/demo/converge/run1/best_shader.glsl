#version 330

in vec2 v_uv;
uniform sampler2D u_input; // not used for procedural content
uniform vec2 u_resolution;
uniform float u_time;

out vec4 f_color;

// ---------- hash utilities ----------
float hash21(vec2 p) {
    p = fract(p * vec2(123.34, 45621.0));
    p += dot(p, p + 23.7);
    return fract(p.x * p.y);
}

// ---------- torus knot (p,q) = (2,3) ----------
vec3 torusKnot(float t) {
    float a = 2.0; // major radius
    float b = 3.0; // number of turns around the axis
    float c = 2.0; // number of turns around the tube
    return vec3((a + cos(c * t)) * cos(b * t),
                (a + cos(c * t)) * sin(b * t),
                sin(c * t));
}

// ---------- distance from point to ribbon (tube with soft radius) ----------
float ribbonDist(vec3 p, out float param) {
    // coarse search for nearest point on the curve
    float best = 1e9;
    float bestT = 0.0;
    const int SAMPLES = 128;
    for (int i = 0; i < SAMPLES; ++i) {
        float ti = float(i) / float(SAMPLES) * 6.2831853; // 0..2π
        vec3 kp = torusKnot(ti);
        float d = length(p - kp);
        if (d < best) { best = d; bestT = ti; }
    }
    // small refinement around the best sample
    for (int i = 0; i < 5; ++i) {
        float dt = 0.02 * pow(0.5, float(i));
        for (int s = -1; s <= 1; ++s) {
            float ti = bestT + float(s) * dt;
            vec3 kp = torusKnot(ti);
            float d = length(p - kp);
            if (d < best) { best = d; bestT = ti; }
        }
    }
    param = bestT;
    // thicker core radius for a visible ribbon
    float coreRadius = 0.1;
    return best - coreRadius;
}

// ---------- main ----------
void main() {
    // Normalized pixel coordinates (centered, y up, aspect corrected)
    vec2 uv = (gl_FragCoord.xy - 0.5 * u_resolution) / u_resolution.y;

    // Camera orbit around origin, with a slight tilt to expose the ribbon shape
    float camRadius = 5.0;
    float camAngle = u_time * 0.2;
    vec3 camPos = vec3(camRadius * sin(camAngle), 1.0, camRadius * cos(camAngle));
    vec3 target = vec3(0.0);
    vec3 forward = normalize(target - camPos);
    vec3 right = normalize(cross(vec3(0.0, 1.0, 0.0), forward));
    vec3 up = cross(forward, right);
    vec3 rd = normalize(forward + uv.x * right + uv.y * up);

    // Ray march – limited steps, early exit on hit
    float t = 0.0;
    const float tMax = 20.0;
    const float step = 0.04;
    float hitParam = 0.0;
    bool hit = false;
    vec3 hitPos = vec3(0.0);
    for (int i = 0; i < 250; ++i) {
        if (t > tMax) break;
        vec3 pos = camPos + rd * t;
        float d = ribbonDist(pos, hitParam);
        if (d < 0.0) {
            hit = true;
            hitPos = pos;
            break;
        }
        t += max(step, 0.5 * d);
    }

    // Glow intensity based on proximity to the ribbon
    float glow = 0.0;
    if (hit) {
        // Bright core – pure white, no fade
        float core = 1.0 - smoothstep(0.0, 0.1, length(hitPos - torusKnot(hitParam)));
        // Add a subtle pulsating along the curve for motion perception
        float flow = 0.5 + 0.5 * sin(10.0 * hitParam + u_time * 3.0);
        glow = core * flow;
    } else {
        // Halo for near misses – stronger exponential fall‑off
        float dNear = ribbonDist(camPos + rd * t, hitParam);
        glow = 0.4 * exp(-12.0 * max(dNear, 0.0));
    }

    // Strong bloom effect: amplify and add a soft radial glow
    float bloom = pow(glow, 0.5); // brightening
    float final = glow + 0.8 * bloom; // combine core and bloom
    // Clamp to [0,1] and ensure pure white output for bright parts
    final = clamp(final, 0.0, 1.0);
    vec3 col = vec3(final);
    f_color = vec4(col, 1.0);
}
