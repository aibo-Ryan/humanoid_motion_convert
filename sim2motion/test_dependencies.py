#!/usr/bin/env python3
"""
Test script to verify all dependencies for sim2sim_pm01.py
"""

import sys

def test_imports():
    """Test all required imports"""
    print("Testing dependencies for sim2sim_pm01.py...\n")

    # Test legged_gym imports FIRST (before torch)
    try:
        from legged_gym.envs import PM01Cfg
        print("✓ PM01Cfg              - OK")
    except ImportError as e:
        print(f"✗ PM01Cfg              - MISSING: {e}")
        return 1

    try:
        from legged_gym import LEGGED_GYM_ROOT_DIR
        print("✓ LEGGED_GYM_ROOT_DIR  - OK")
    except ImportError as e:
        print(f"✗ LEGGED_GYM_ROOT_DIR  - MISSING: {e}")
        return 1

    # List of required modules (test these AFTER legged_gym)
    modules = {
        'tkinter': 'tkinter',
        'numpy': 'numpy',
        'mujoco': 'mujoco',
        'mujoco_viewer': 'mujoco_viewer',
        'pickle': 'pickle',
        'pandas': 'pandas',
        'torch': 'torch',  # Test torch AFTER legged_gym
        'datetime': 'datetime',
        'collections': 'collections',
        'math': 'math',
        'scipy.spatial.transform': 'scipy (spatial)',
    }

    all_ok = True

    for module_name, display_name in modules.items():
        try:
            __import__(module_name)
            print(f"✓ {display_name:20} - OK")
        except ImportError as e:
            print(f"✗ {display_name:20} - MISSING: {e}")
            all_ok = False

    print("\n")

    # Check policy file
    policy_path = '/home/abo/git/zqsa01_legged_gym/logs/pm01_ppo/0_exported/policies/policy_1.pt'
    try:
        import os
        if os.path.exists(policy_path):
            print(f"✓ Policy file         - OK: {policy_path}")
        else:
            print(f"✗ Policy file         - MISSING: {policy_path}")
            all_ok = False
    except Exception as e:
        print(f"✗ Policy file check    - ERROR: {e}")
        all_ok = False

    print("\n")

    # Check Mujoco model file
    from legged_gym import LEGGED_GYM_ROOT_DIR
    model_path = f'{LEGGED_GYM_ROOT_DIR}/resources/robots/pm01_xml/pm_v2.xml'
    try:
        if os.path.exists(model_path):
            print(f"✓ Mujoco model file   - OK: {model_path}")
        else:
            print(f"✗ Mujoco model file   - MISSING: {model_path}")
            all_ok = False
    except Exception as e:
        print(f"✗ Mujoco model check   - ERROR: {e}")
        all_ok = False

    print("\n" + "="*50)

    if all_ok:
        print("\n✓ All dependencies are installed!")
        print("You can now run: python sim2sim_pm01.py")
        return 0
    else:
        print("\n✗ Some dependencies are missing.")
        print("Please install missing packages and try again.")
        return 1


if __name__ == '__main__':
    sys.exit(test_imports())
