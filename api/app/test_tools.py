from letta_templates.npc_tools import TOOL_REGISTRY, navigate_to

def test_navigation_tool():
    print("\nTesting navigation tool accepts any valid slug format...")
    
    # Test valid slug formats
    valid_slugs = [
        "test_location",
        "store_1",
        "north_building",
        "southpark",
        "zone123"
    ]
    
    print("\nTesting valid slugs:")
    for slug in valid_slugs:
        result = navigate_to(slug)
        print(f"\nInput: {slug}")
        print(f"Result: {result}")
        if result["status"] != "success":
            print("ERROR: Tool rejected valid slug format!")
    
    # Test invalid slug formats
    invalid_slugs = [
        "invalid@slug",
        "bad slug with spaces",
        "no$special%chars",
        "",
        "   "
    ]
    
    print("\nTesting invalid slugs:")
    for slug in invalid_slugs:
        result = navigate_to(slug)
        print(f"\nInput: {slug}")
        print(f"Result: {result}")
        if result["status"] == "success":
            print("ERROR: Tool accepted invalid slug format!")

if __name__ == "__main__":
    test_navigation_tool() 