"""
Blockchain Test Scenarios Package

This package contains comprehensive test scenarios for the blockchain simulator.
Each scenario file tests a specific aspect of the blockchain implementation.

Available scenarios:
1. sequential_nonce - Normal flow with sequential nonce handling
2. replay_prevention - Replay attack prevention
3. invalid_signature - Invalid signature detection
4. nonce_skip_reverse - Nonce skip and reverse order handling
5. double_spend_reorg - Double spend with reorg
6. deep_reorg - Deep reorganization
7. orphan_blocks - Orphan block handling
8. txid_stability - Transaction ID stability
9. tx_order_attack - Transaction order attack prevention
10. mempool_cleanup_reorg - Mempool cleanup after reorg
11. difficulty_adjustment - Difficulty adjustment algorithm
12. wallet_recovery - Wallet backup and recovery
13. wallet_manager - Multi-wallet management
14. network_broadcast - Network broadcasting
"""

from .sequential_nonce import test_sequential_nonce
from .replay_prevention import test_replay_prevention
from .invalid_signature import test_invalid_signature
from .nonce_skip_reverse import test_nonce_skip_reverse
from .double_spend_reorg import test_double_spend_reorg
from .deep_reorg import test_deep_reorg
from .orphan_blocks import test_orphan_blocks
from .txid_stability import test_txid_stability
from .tx_order_attack import test_block_tx_order_attack
from .mempool_cleanup_reorg import test_mempool_cleanup_after_reorg
from .difficulty_adjustment import test_difficulty_adjustment
from .wallet_recovery import test_wallet_recovery
from .wallet_manager import test_wallet_manager
from .network_broadcast import test_network_broadcast

__all__ = [
    'test_sequential_nonce',
    'test_replay_prevention',
    'test_invalid_signature',
    'test_nonce_skip_reverse',
    'test_double_spend_reorg',
    'test_deep_reorg',
    'test_orphan_blocks',
    'test_txid_stability',
    'test_block_tx_order_attack',
    'test_mempool_cleanup_after_reorg',
    'test_difficulty_adjustment',
    'test_wallet_recovery',
    'test_wallet_manager',
    'test_network_broadcast',
]
