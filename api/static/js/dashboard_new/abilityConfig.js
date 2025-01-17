const ABILITY_CONFIG = [
    {
        id: 'move',
        name: 'Movement',
        icon: 'fas fa-walking',
        description: 'Enables basic movement between locations'
    },
    {
        id: 'chat',
        name: 'Chat',
        icon: 'fas fa-comments',
        description: 'Enables responding to player conversations'
    },
    {
        id: 'initiate_chat',
        name: 'Initiate Chat',
        icon: 'fas fa-comment-dots',
        description: 'Allows NPC to start conversations with nearby players'
    },
    {
        id: 'follow',
        name: 'Follow',
        icon: 'fas fa-user-friends',
        description: 'Enables following players or other NPCs'
    },
    {
        id: 'unfollow',
        name: 'Unfollow',
        icon: 'fas fa-user-times',
        description: 'Allows NPC to stop following targets'
    },
    {
        id: 'run',
        name: 'Run',
        icon: 'fas fa-running',
        description: 'Enables faster movement speed'
    },
    {
        id: 'jump',
        name: 'Jump',
        icon: 'fas fa-arrow-up',
        description: 'Allows NPC to jump over obstacles'
    },
    {
        id: 'emote',
        name: 'Emote',
        icon: 'fas fa-smile',
        description: 'Enables playing animations and emotes'
    }
];

window.ABILITY_CONFIG = ABILITY_CONFIG;
