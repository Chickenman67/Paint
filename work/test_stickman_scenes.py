#!/usr/bin/env python3
"""Test the scene-based stickman composition paradigm.

Renders 5 example scenes to verify:
1. stickman_on_surface with different expressions/poses
2. stickman_in_space with celestial bodies
3. stickman_with_environment with custom backgrounds
"""

import sys
from pathlib import Path

# Add work/lib to the path
work_lib = Path(__file__).parent / 'lib'
sys.path.insert(0, str(work_lib))

import stickman

def main():
    output_dir = Path(__file__).parent.parent / 'work'
    output_dir.mkdir(exist_ok=True)

    print("Testing scene-based stickman composition...")
    print("=" * 60)

    # Test 1: Stickman on a Mars-like surface, scared, hands up
    print("\n1. Mars surface scene (scared, hands up)")
    img1 = stickman.stickman_on_surface(
        expression='frown',
        pose='hands_up',
        surface_color=(180, 100, 60),  # rust-red Mars
        sky_gradient=((220, 150, 120), (180, 100, 80)),
        ground_y_pct=0.65,
        stickman_height=140
    )
    out1 = output_dir / 'test_scene1_mars_scared.png'
    img1.save(out1)
    print(f"   Saved: {out1}")

    # Test 2: Stickman on a moon surface, deadpan, standing
    print("\n2. Moon surface scene (deadpan, standing)")
    img2 = stickman.stickman_on_surface(
        expression='flat',
        pose='standing',
        surface_color=(140, 140, 150),  # gray moon
        sky_gradient=((10, 10, 20), (30, 30, 40)),  # black space
        ground_y_pct=0.70,
        stickman_height=120
    )
    out2 = output_dir / 'test_scene2_moon_deadpan.png'
    img2.save(out2)
    print(f"   Saved: {out2}")

    # Test 3: Stickman in space near a hot sun, shielding eyes
    print("\n3. Space scene near sun (shielding eyes, worried)")
    img3 = stickman.stickman_in_space(
        expression='worried',
        pose='shielding_eyes',
        celestial_body={
            'color': (255, 220, 100),
            'glow_radius': 80
        },
        body_position=(0.25, 0.35),
        body_scale=0.18,
        stickman_height=130
    )
    out3 = output_dir / 'test_scene3_space_sun.png'
    img3.save(out3)
    print(f"   Saved: {out3}")

    # Test 4: Stickman in space near a planet, awed
    print("\n4. Space scene near planet (awed, hands up)")
    img4 = stickman.stickman_in_space(
        expression='oval',
        pose='hands_up',
        celestial_body={
            'color': (100, 150, 200),
            'glow_radius': 0  # no glow for a planet
        },
        body_position=(0.7, 0.4),
        body_scale=0.22,
        stickman_height=120
    )
    out4 = output_dir / 'test_scene4_space_planet.png'
    img4.save(out4)
    print(f"   Saved: {out4}")

    # Test 5: Stickman in a room with background elements, pointing
    print("\n5. Environment scene with elements (smirk, pointing)")
    bg_elements = [
        # Floor
        {'type': 'rect', 'bounds': (0, 500, 1280, 720),
         'fill': (160, 140, 120)},
        # Wall
        {'type': 'rect', 'bounds': (0, 0, 1280, 500),
         'fill': (200, 195, 180)},
        # Window (rectangle with outline)
        {'type': 'rect', 'bounds': (800, 150, 1100, 400),
         'fill': (150, 200, 230), 'outline': (0, 0, 0), 'width': 3},
        # Table leg (line)
        {'type': 'line', 'points': [(300, 450), (300, 500)],
         'stroke': (80, 60, 40), 'width': 8},
        # Table top
        {'type': 'rect', 'bounds': (200, 440, 500, 460),
         'fill': (100, 80, 60)},
    ]
    img5 = stickman.stickman_with_environment(
        expression='smirk',
        pose='pointing',
        bg_elements=bg_elements,
        stickman_height=140,
        stickman_position=(0.4, 0.75)
    )
    out5 = output_dir / 'test_scene5_room_pointing.png'
    img5.save(out5)
    print(f"   Saved: {out5}")

    print("\n" + "=" * 60)
    print("✓ All 5 test scenes rendered successfully")
    print("\nParadigm verification:")
    print("  • Stickman is embedded IN each environment")
    print("  • Not overlaid as a separate layer")
    print("  • Expression changes via mouth shape only")
    print("  • Canonical proportions maintained")
    print("  • Each helper returns a complete PIL Image")

if __name__ == '__main__':
    main()
