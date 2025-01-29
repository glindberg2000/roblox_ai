# Active Ticket Board

## Critical Path
| Ticket | Assignee | Title | Status | Dependencies |
|--------|----------|-------|--------|--------------|
| CLUSTER-01 | RD | Snapshot Migration | In Progress | - |
| BATCH-02 | RD+LD | Message Aggregation | Not Started | CLUSTER-01 |

## Core Systems
| MOD-04 | LD | Fast Moderator | Testing | BATCH-02 |

## Feature Development
| PRIO-03 | LD | Priority Flags | Code Review | - |

## QA & Testing
| TEST-05 | HD | Load Test Pipeline | Configuring | CLUSTER-01 |

## Optimization
| OPT-06 | LD | Cached Reactions | Backlog | BATCH-02 |

## Coordination
| COM-07 | HD | API Contracts | Ongoing | - |

## Backlog
1. WebSocket priority channel
2. Dynamic rate limiting
3. NPC state persistence 