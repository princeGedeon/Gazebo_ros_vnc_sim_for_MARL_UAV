try:
    import utm
    import laspy
    print("SUCCESS: Modules found")
except ImportError as e:
    print(f"ERROR: Missing module {e}")
