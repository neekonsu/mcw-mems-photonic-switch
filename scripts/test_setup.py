#!/usr/bin/env python3
"""
Test script to verify GDSFactory installation and basic functionality.
"""

import sys

def test_imports():
    """Test that all required packages can be imported."""
    print("Testing package imports...")

    try:
        import gdsfactory as gf
        print(f"✓ GDSFactory {gf.__version__}")
    except ImportError as e:
        print(f"✗ GDSFactory import failed: {e}")
        return False

    try:
        import numpy as np
        print(f"✓ NumPy {np.__version__}")
    except ImportError as e:
        print(f"✗ NumPy import failed: {e}")
        return False

    try:
        import matplotlib
        print(f"✓ Matplotlib {matplotlib.__version__}")
    except ImportError as e:
        print(f"✗ Matplotlib import failed: {e}")
        return False

    return True

def test_basic_component():
    """Test creating a simple GDSFactory component."""
    print("\nTesting basic component creation...")

    try:
        import gdsfactory as gf

        # Create a simple rectangle
        c = gf.Component("test_rect")
        c.add_polygon([(0, 0), (10, 0), (10, 5), (0, 5)], layer=(1, 0))

        # Check that component was created
        print(f"✓ Created component '{c.name}'")

        # Test using a built-in component
        waveguide = gf.components.rectangle(size=(10, 0.5), layer=(1, 0))
        print(f"✓ Created built-in rectangle component")
        return True
    except Exception as e:
        print(f"✗ Component creation failed: {e}")
        return False

def main():
    """Run all tests."""
    print("=" * 50)
    print("GDSFactory Setup Verification")
    print("=" * 50)

    all_passed = True

    if not test_imports():
        all_passed = False

    if not test_basic_component():
        all_passed = False

    print("\n" + "=" * 50)
    if all_passed:
        print("✓ All tests passed! Setup is complete.")
        print("=" * 50)
        return 0
    else:
        print("✗ Some tests failed. Check the errors above.")
        print("=" * 50)
        return 1

if __name__ == "__main__":
    sys.exit(main())
