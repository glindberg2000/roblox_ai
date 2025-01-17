"""Asset Selector Response Structure Issue

Problem Description:
------------------
The asset selector appears to be receiving data but not populating correctly:
1. API returns successful response with 1 asset
2. Code reports "Populated model selector with 1 assets"
3. Selector remains empty
4. No JavaScript errors in console

Current Flow:
-----------
1. Game selected (id: 61)
2. NPCs loaded (empty array)
3. Assets fetched (1 asset found)
4. populateAssetSelector reports success
5. UI shows no options

Hypothesis:
----------
1. API response structure might not match what the frontend expects
2. Asset data might be nested differently than expected
3. The assetId/name fields might be named differently

Next Debug Steps:
---------------
1. Add console.log for the exact API response structure:
```javascript
console.log('Raw API response:', await response.text());
const data = await response.json();
console.log('Parsed API response:', JSON.stringify(data, null, 2));
```

2. Verify the asset data structure:
```javascript
if (data.assets && Array.isArray(data.assets)) {
    console.log('Asset array structure:', data.assets[0]);
    console.log('Asset fields:', Object.keys(data.assets[0]));
}
```

3. Check selector after population:
```javascript
console.log('Final selector state:', {
    options: assetSelect.options.length,
    html: assetSelect.innerHTML
});
```

Expected API Response:
-------------------
{
    "assets": [
        {
            "id": "123",
            "assetId": "14768974964",
            "name": "Asset Name"
        }
    ]
}

Would you like me to:
1. Add the debug logging
2. Check the API response structure
3. Verify the field names match
"""

def get_issue_description():
    """Return the issue documentation as a string."""
    return __doc__

if __name__ == "__main__":
    print(get_issue_description()) 