// First, ensure we're using the React hooks from the global React object
const { useState, useEffect } = React;

// Constants for API endpoints
const API_ENDPOINTS = {
    ASSETS: '/api/assets',
    NPCS: '/api/npcs',
    PLAYERS: '/api/players',
    ASSET_THUMBNAIL: (id) => `/api/asset-thumbnail/${id}`,
    NPC: (id) => `/api/npcs/${id}`,
};

// NPCs Tab Component
const NPCsTab = ({ npcs, onEdit, onDelete }) => (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {npcs.map(npc => (
            <div key={npc.id} className="bg-white rounded-lg shadow p-4">
                <div className="flex items-start space-x-4">
                    {npc.thumbnailUrl ? (
                        <img
                            src={npc.thumbnailUrl}
                            alt={npc.displayName}
                            className="w-24 h-24 object-cover rounded"
                        />
                    ) : (
                        <div className="w-24 h-24 bg-gray-200 rounded flex items-center justify-center">
                            <span className="text-gray-400">No Image</span>
                        </div>
                    )}
                    <div className="flex-1">
                        <h3 className="font-bold">{npc.displayName}</h3>
                        <p className="text-sm text-gray-600 mb-2">ID: {npc.id}</p>
                        <p className="text-sm mb-4">{npc.system_prompt?.substring(0, 100)}...</p>
                        <div className="flex justify-end space-x-2">
                            <button
                                onClick={() => onEdit(npc)}
                                className="px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700"
                            >
                                Edit
                            </button>
                            <button
                                onClick={() => onDelete(npc.id)}
                                className="px-3 py-1 bg-red-600 text-white rounded hover:bg-red-700"
                            >
                                Delete
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        ))}
    </div>
);

// Assets Tab Component
const AssetsTab = ({ assets, onEdit, onDelete }) => (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {assets.map(asset => (
            <div key={asset.assetId} className="bg-white rounded-lg shadow p-4">
                <div className="flex items-start space-x-4">
                    {asset.imageUrl ? (
                        <img
                            src={asset.imageUrl}
                            alt={asset.name}
                            className="w-24 h-24 object-cover rounded"
                        />
                    ) : (
                        <div className="w-24 h-24 bg-gray-200 rounded flex items-center justify-center">
                            <span className="text-gray-400">No Image</span>
                        </div>
                    )}
                    <div className="flex-1">
                        <h3 className="font-bold">{asset.name}</h3>
                        <p className="text-sm text-gray-600 mb-2">ID: {asset.assetId}</p>
                        <p className="text-sm mb-4">{asset.description?.substring(0, 100)}...</p>
                        <div className="flex justify-end space-x-2">
                            <button
                                onClick={() => onEdit(asset)}
                                className="px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700"
                            >
                                Edit
                            </button>
                            <button
                                onClick={() => onDelete(asset.assetId)}
                                className="px-3 py-1 bg-red-600 text-white rounded hover:bg-red-700"
                            >
                                Delete
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        ))}
    </div>
);

// Players Tab Component
const PlayersTab = ({ players, onEdit, onDelete }) => (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {players.map(player => (
            <div key={player.playerID} className="bg-white rounded-lg shadow p-4">
                <div className="flex items-start space-x-4">
                    {player.imageURL ? (
                        <img
                            src={player.imageURL}
                            alt={player.displayName}
                            className="w-24 h-24 object-cover rounded"
                        />
                    ) : (
                        <div className="w-24 h-24 bg-gray-200 rounded flex items-center justify-center">
                            <span className="text-gray-400">No Image</span>
                        </div>
                    )}
                    <div className="flex-1">
                        <h3 className="font-bold">{player.displayName}</h3>
                        <p className="text-sm text-gray-600 mb-2">ID: {player.playerID}</p>
                        <p className="text-sm mb-4">{player.description?.substring(0, 100)}...</p>
                        <div className="flex justify-end space-x-2">
                            <button
                                onClick={() => onEdit(player)}
                                className="px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700"
                            >
                                Edit
                            </button>
                            <button
                                onClick={() => onDelete(player.playerID)}
                                className="px-3 py-1 bg-red-600 text-white rounded hover:bg-red-700"
                            >
                                Delete
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        ))}
    </div>
);

// Asset Edit Modal Component
const AssetEditModal = ({ asset, onClose, onSave }) => {
    const [formData, setFormData] = useState(asset);

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            const response = await fetch(`/api/assets/${asset.assetId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });

            if (!response.ok) throw new Error('Failed to update asset');
            onSave();
            onClose();
        } catch (e) {
            console.error('Error updating asset:', e);
            alert('Failed to update asset: ' + e.message);
        }
    };

    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4">
            <div className="bg-white rounded-lg p-6 max-w-2xl w-full max-h-90vh overflow-y-auto">
                <h2 className="text-2xl font-bold mb-4">Edit Asset: {asset.name}</h2>
                <form onSubmit={handleSubmit} className="space-y-4">
                    <div>
                        <label className="block text-sm font-medium mb-1">Name</label>
                        <input
                            type="text"
                            value={formData.name}
                            onChange={e => setFormData({ ...formData, name: e.target.value })}
                            className="w-full border rounded p-2"
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-medium mb-1">Description</label>
                        <textarea
                            value={formData.description}
                            onChange={e => setFormData({ ...formData, description: e.target.value })}
                            rows="6"
                            className="w-full border rounded p-2"
                        />
                    </div>
                    {formData.imageUrl && (
                        <div>
                            <label className="block text-sm font-medium mb-1">Current Image</label>
                            <img src={formData.imageUrl} alt={formData.name} className="h-32 w-32 object-cover rounded" />
                        </div>
                    )}
                    <div className="flex justify-end space-x-2">
                        <button
                            type="button"
                            onClick={onClose}
                            className="px-4 py-2 border rounded text-gray-600 hover:bg-gray-50"
                        >
                            Cancel
                        </button>
                        <button
                            type="submit"
                            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
                        >
                            Save Changes
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
};

// Modified NPC Edit Modal with Asset Selection
const NPCEditModal = ({ npc, assets, onClose, onSave }) => {
    const [formData, setFormData] = useState(npc);
    const [selectedAsset, setSelectedAsset] = useState(assets.find(a => a.assetId === npc.assetID) || null);

    const handleAssetChange = (assetId) => {
        const asset = assets.find(a => a.assetId === assetId);
        setSelectedAsset(asset);
        setFormData({
            ...formData,
            assetID: assetId,
            thumbnailUrl: asset?.imageUrl || null
        });
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            const response = await fetch(API_ENDPOINTS.NPC(npc.id), {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });

            if (!response.ok) throw new Error('Failed to update NPC');
            onSave();
            onClose();
        } catch (e) {
            console.error('Error updating NPC:', e);
            alert('Failed to update NPC: ' + e.message);
        }
    };

    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4">
            <div className="bg-white rounded-lg p-6 max-w-2xl w-full max-h-90vh overflow-y-auto">
                <h2 className="text-2xl font-bold mb-4">Edit NPC: {npc.displayName}</h2>
                <form onSubmit={handleSubmit} className="space-y-4">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {/* Basic Info */}
                        <div>
                            <label className="block text-sm font-medium mb-1">Display Name</label>
                            <input
                                type="text"
                                value={formData.displayName}
                                onChange={e => setFormData({ ...formData, displayName: e.target.value })}
                                className="w-full border rounded p-2"
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium mb-1">Model Name</label>
                            <input
                                type="text"
                                value={formData.model}
                                onChange={e => setFormData({ ...formData, model: e.target.value })}
                                className="w-full border rounded p-2"
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium mb-1">Asset</label>
                            <select
                                value={formData.assetID || ''}
                                onChange={e => handleAssetChange(e.target.value)}
                                className="w-full border rounded p-2"
                            >
                                <option value="">Select an asset</option>
                                {assets.map(asset => (
                                    <option key={asset.assetId} value={asset.assetId}>
                                        {asset.name} ({asset.assetId})
                                    </option>
                                ))}
                            </select>
                        </div>
                        <div>
                            <label className="block text-sm font-medium mb-1">Response Radius</label>
                            <input
                                type="number"
                                value={formData.responseRadius}
                                onChange={e => setFormData({ ...formData, responseRadius: parseInt(e.target.value) })}
                                className="w-full border rounded p-2"
                            />
                        </div>

                        {/* Spawn Position */}
                        <div>
                            <label className="block text-sm font-medium mb-1">Spawn Position X</label>
                            <input
                                type="number"
                                value={formData.spawnPosition.x}
                                onChange={e => setFormData({
                                    ...formData,
                                    spawnPosition: { ...formData.spawnPosition, x: parseFloat(e.target.value) }
                                })}
                                className="w-full border rounded p-2"
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium mb-1">Spawn Position Y</label>
                            <input
                                type="number"
                                value={formData.spawnPosition.y}
                                onChange={e => setFormData({
                                    ...formData,
                                    spawnPosition: { ...formData.spawnPosition, y: parseFloat(e.target.value) }
                                })}
                                className="w-full border rounded p-2"
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium mb-1">Spawn Position Z</label>
                            <input
                                type="number"
                                value={formData.spawnPosition.z}
                                onChange={e => setFormData({
                                    ...formData,
                                    spawnPosition: { ...formData.spawnPosition, z: parseFloat(e.target.value) }
                                })}
                                className="w-full border rounded p-2"
                            />
                        </div>
                    </div>

                    {/* System Prompt - Full Width */}
                    <div>
                        <label className="block text-sm font-medium mb-1">System Prompt</label>
                        <textarea
                            value={formData.system_prompt}
                            onChange={e => setFormData({ ...formData, system_prompt: e.target.value })}
                            rows="6"
                            className="w-full border rounded p-2"
                        />
                    </div>

                    {/* Thumbnail Preview */}
                    {selectedAsset && (
                        <div>
                            <label className="block text-sm font-medium mb-1">Asset Preview</label>
                            <img
                                src={selectedAsset.imageUrl}
                                alt={selectedAsset.name}
                                className="h-32 w-32 object-cover rounded"
                            />
                        </div>
                    )}

                    <div className="flex justify-end space-x-2">
                        <button
                            type="button"
                            onClick={onClose}
                            className="px-4 py-2 border rounded text-gray-600 hover:bg-gray-50"
                        >
                            Cancel
                        </button>
                        <button
                            type="submit"
                            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
                        >
                            Save Changes
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
};

// Main Dashboard Component
window.Dashboard = function Dashboard() {
    const [activeTab, setActiveTab] = useState('npcs');
    const [assets, setAssets] = useState([]);
    const [npcs, setNpcs] = useState([]);
    const [players, setPlayers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [editingNpc, setEditingNpc] = useState(null);
    const [editingAsset, setEditingAsset] = useState(null);

    useEffect(() => {
        fetchData();
    }, []);

    const fetchData = async () => {
        setLoading(true);
        try {
            console.log('Fetching data...');
            const [assetsRes, npcsRes, playersRes] = await Promise.all([
                fetch(API_ENDPOINTS.ASSETS),
                fetch(API_ENDPOINTS.NPCS),
                fetch(API_ENDPOINTS.PLAYERS)
            ]);

            console.log('Responses received:', {
                assets: assetsRes.status,
                npcs: npcsRes.status,
                players: playersRes.status
            });

            const [assetsData, npcsData, playersData] = await Promise.all([
                assetsRes.json(),
                npcsRes.json(),
                playersRes.json()
            ]);

            console.log('Data parsed:', {
                assets: assetsData?.assets?.length || 0,
                npcs: npcsData?.npcs?.length || 0,
                players: playersData?.players?.length || 0
            });

            setAssets(assetsData.assets || []);

            // In the fetchData function, modify the NPCs processing:
            const npcsWithThumbnails = await Promise.all(
                npcsData.npcs.map(async (npc) => {
                    if (npc.assetID) {
                        // Find the corresponding asset
                        const matchingAsset = assetsData.assets.find(asset => asset.assetId === npc.assetID);
                        if (matchingAsset) {
                            return { ...npc, thumbnailUrl: matchingAsset.imageUrl };
                        }
                    }
                    return { ...npc, thumbnailUrl: null };
                })
            );
            setNpcs(npcsWithThumbnails);
            setPlayers(playersData.players || []);

            console.log('State updated with:', {
                assets: assetsData.assets?.length || 0,
                npcs: npcsWithThumbnails.length,
                players: playersData.players?.length || 0
            });
        } catch (e) {
            console.error('Error fetching data:', e);
            setError(e.message);
        } finally {
            setLoading(false);
        }
    };

    const deleteItem = async (type, id) => {
        if (!confirm(`Are you sure you want to delete this ${type}?`)) return;

        try {
            const response = await fetch(`/api/${type}/${id}`, {
                method: 'DELETE'
            });
            if (!response.ok) throw new Error(`Failed to delete ${type}`);
            fetchData();
        } catch (e) {
            setError(e.message);
        }
    };

    return (
        <div className="container mx-auto px-4 py-8">
            <h1 className="text-3xl font-bold mb-8">Game Management Dashboard</h1>

            {error && (
                <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg">
                    Error: {error}
                    <button
                        onClick={() => setError(null)}
                        className="ml-2 text-red-600 hover:text-red-800"
                    >
                        Dismiss
                    </button>
                </div>
            )}

            {/* Navigation Tabs */}
            <div className="mb-6">
                <nav className="flex space-x-4">
                    <button
                        onClick={() => setActiveTab('npcs')}
                        className={`px-4 py-2 rounded-lg ${activeTab === 'npcs'
                            ? 'bg-blue-600 text-white'
                            : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                            }`}
                    >
                        NPCs
                    </button>
                    <button
                        onClick={() => setActiveTab('assets')}
                        className={`px-4 py-2 rounded-lg ${activeTab === 'assets'
                            ? 'bg-blue-600 text-white'
                            : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                            }`}
                    >
                        Assets
                    </button>
                    <button
                        onClick={() => setActiveTab('players')}
                        className={`px-4 py-2 rounded-lg ${activeTab === 'players'
                            ? 'bg-blue-600 text-white'
                            : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                            }`}
                    >
                        Players
                    </button>
                </nav>
            </div>

            {/* Content Area */}
            <div className="mb-8">
                {loading ? (
                    <div className="text-center py-8">
                        <div className="inline-block animate-spin rounded-full h-8 w-8 border-4 border-blue-600 border-t-transparent"></div>
                    </div>
                ) : (
                    <>
                        {activeTab === 'npcs' && (
                            <NPCsTab
                                npcs={npcs}
                                onEdit={setEditingNpc}
                                onDelete={id => deleteItem('npcs', id)}
                            />
                        )}
                        {activeTab === 'assets' && (
                            <AssetsTab
                                assets={assets}
                                onEdit={setEditingAsset}
                                onDelete={id => deleteItem('assets', id)}
                            />
                        )}
                        {activeTab === 'players' && (
                            <PlayersTab
                                players={players}
                                onEdit={(player) => { }} // TODO: Implement player editing
                                onDelete={id => deleteItem('players', id)}
                            />
                        )}
                    </>
                )}
            </div>

            {/* Edit Modal */}
            {editingNpc && (
                <NPCEditModal
                    npc={editingNpc}
                    assets={assets}
                    onClose={() => setEditingNpc(null)}
                    onSave={fetchData}
                />
            )}
            {editingAsset && (
                <AssetEditModal
                    asset={editingAsset}
                    onClose={() => setEditingAsset(null)}
                    onSave={fetchData}
                />
            )}
        </div>
    );
}

// Export to window
window.Dashboard = Dashboard;