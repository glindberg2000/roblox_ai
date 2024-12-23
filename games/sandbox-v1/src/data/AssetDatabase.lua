return {
    assets = {
        {
            assetId = "96144138651755",
            name = "Pete's Merch Stand",
            description = "Pete's Merch Stand is a wooden structure...",
            is_location = true,
            position = {
                x = -10.289,
                y = 21.512,
                z = -127.797
            },
            aliases = {
                "stand",
                "merchant stand",
                "pete's stand"
            },
            metadata = {
                area = "spawn_area",
                type = "shop",
                owner = "Pete",
                interactable = true
            }
        }
    },
    locations = {
        spawn_area = {
            center = { x = 0, y = 0, z = 0 },
            radius = 50,
            locations = { "petes_merch_stand" }
        }
    }
}