"""
시나리오 2: Replay 방지

이미 확정된 tx 또는 동일 nonce의 tx 재전파 시 거부
"""

import sys
import os
import copy

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from blockchain import Node, NetworkSimulator, Wallet, config


def test_replay_prevention():
    """Replay 공격 방지 테스트"""
    print("[TEST] 시나리오: Replay 공격 방지")

    network = NetworkSimulator()
    wallet_alice = Wallet("Alice")
    wallet_bob = Wallet("Bob")

    network.register_wallet(wallet_alice)
    network.register_wallet(wallet_bob)

    node = Node(wallet_alice.address, network.genesis_block)
    network.add_node(node)

    # 초기 채굴
    config.SIM_TIME = 1
    block1 = node.try_mine()
    node.receive_block(block1)

    # 트랜잭션 생성 및 채굴
    print("\n1. 정상 트랜잭션 생성 및 채굴")
    tx1 = wallet_alice.create_transaction(wallet_bob.address, 10, 1)
    node.add_transaction(tx1)

    config.SIM_TIME = 2
    block2 = node.try_mine()
    node.receive_block(block2)

    print(f"   Mempool 크기: {len(node.mempool)}")
    assert len(node.mempool) == 0, "Mempool should be empty"

    # Case A: 동일 txid 재전파
    print("\n2. Case A: 동일 트랜잭션 재전파")
    tx1_duplicate = copy.deepcopy(tx1)
    node.add_transaction(tx1_duplicate)

    print(f"   Mempool 크기: {len(node.mempool)}")

    # Mempool 정리 후 확인
    node.clean_mempool()
    print(f"   Mempool 정리 후 크기: {len(node.mempool)}")
    assert len(node.mempool) == 0, "Duplicate tx should be removed from mempool"

    # Case B: 동일 nonce의 다른 트랜잭션
    print("\n3. Case B: 동일 nonce로 다른 금액 전송 시도")
    tx1_double_spend = wallet_alice.create_transaction(wallet_bob.address, 20, 1)
    node.add_transaction(tx1_double_spend)

    node.clean_mempool()
    print(f"   Mempool 정리 후 크기: {len(node.mempool)}")

    alice_state = node.state.get(wallet_alice.address, {'balance': 0, 'nonce': 0})
    print(f"   Alice nonce: {alice_state['nonce']}")

    assert len(node.mempool) == 0, "Double spend with old nonce should be rejected"

    print("\n[OK] 시나리오 2 검증 완료")
    return True


if __name__ == "__main__":
    try:
        test_replay_prevention()
        print("\n[OK] Replay Prevention Test PASSED")
        sys.exit(0)
    except AssertionError as e:
        print(f"\n[FAIL] Test FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[FAIL] Test ERROR: {e}")
        sys.exit(1)
