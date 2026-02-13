"""
시나리오 10: Reorg 후 mempool 정리

체인 교체 이후 mempool의 모든 거래는 최신 state 기준으로
nonce/잔액/서명을 재검증하여 유효한 것만 유지
"""

import sys
import os
import copy

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from blockchain import Node, NetworkSimulator, Wallet, config


def test_mempool_cleanup_after_reorg():
    """Reorg 후 Mempool 정리 테스트"""
    print("[TEST] 시나리오: Reorg 후 Mempool 정리")

    network = NetworkSimulator()
    wallet_alice = Wallet("Alice")
    wallet_bob = Wallet("Bob")

    network.register_wallet(wallet_alice)
    network.register_wallet(wallet_bob)

    node = Node(wallet_alice.address, network.genesis_block)

    # 초기 상태
    print("\n1. 초기 블록 채굴")
    config.SIM_TIME = 1
    block1 = node.try_mine()
    node.receive_block(block1)

    # 원본 체인: tx1, tx2 포함
    print("\n2. 원본 체인 구축 (tx1, tx2)")
    tx1 = wallet_alice.create_transaction(wallet_bob.address, 10, 1)
    tx2 = wallet_alice.create_transaction(wallet_bob.address, 5, 2)

    node.add_transaction(tx1)
    node.add_transaction(tx2)

    config.SIM_TIME = 2
    block2 = node.try_mine()
    node.receive_block(block2)

    print(f"   Alice nonce: {node.state[wallet_alice.address]['nonce']}")
    print(f"   Mempool 크기: {len(node.mempool)}")

    # Mempool에 추가 트랜잭션 (아직 미채굴)
    print("\n3. Mempool에 추가 트랜잭션 (nonce 3)")
    tx3 = wallet_alice.create_transaction(wallet_bob.address, 3, 3)
    node.add_transaction(tx3)
    print(f"   Mempool 크기: {len(node.mempool)}")

    # 대체 체인 생성 (block1에서 분기, tx1만 포함)
    print("\n4. 대체 체인 생성 (tx1만 포함)")
    node2 = Node(wallet_bob.address, network.genesis_block)
    node2.receive_block(copy.deepcopy(block1))

    node2.add_transaction(copy.deepcopy(tx1))
    config.SIM_TIME = 3
    block2_alt = node2.try_mine()
    node2.receive_block(block2_alt)

    # 더 무거운 체인 만들기
    config.SIM_TIME = 4
    block3_alt = node2.try_mine()
    node2.receive_block(block3_alt)

    print(f"   Alt chain 작업량: {node2.get_tip_block().total_work}")

    # Reorg 발생
    print("\n5. Reorg 발생")
    node.receive_block(copy.deepcopy(block2_alt))
    node.receive_block(copy.deepcopy(block3_alt))

    alice_state = node.state.get(wallet_alice.address, {'balance': 0, 'nonce': 0})
    print(f"   Reorg 후 Alice nonce: {alice_state['nonce']}")

    # Mempool 상태 확인 (자동 정리됨)
    print("\n6. Mempool 상태 확인")
    print(f"   Mempool 크기: {len(node.mempool)}")

    # 명시적 정리
    node.clean_mempool()
    print(f"   정리 후 Mempool 크기: {len(node.mempool)}")

    # 검증:
    # - tx1은 이미 block2_alt에 포함됨 (제거)
    # - tx2는 nonce 2인데 현재 Alice nonce는 1 → nonce 2 기대 → 유효
    # - tx3는 nonce 3인데 현재 Alice nonce는 1 → nonce 2 기대 → 무효

    valid_nonces = [tx['body']['nonce'] for tx in node.mempool]
    print(f"   유효한 mempool nonce: {valid_nonces}")

    # tx2만 남아야 함 (nonce 2)
    assert len(node.mempool) == 1, "Only tx2 should remain in mempool"
    assert node.mempool[0]['body']['nonce'] == 2, "Remaining tx should have nonce 2"

    # 추가 검증: 남은 tx의 서명도 유효한지
    for tx in node.mempool:
        is_valid = node.verify_transaction_signature(tx)
        assert is_valid, "Remaining tx should have valid signature"
        print(f"   Mempool tx (nonce {tx['body']['nonce']}) 서명 검증: [OK]")

    print("\n[OK] 시나리오 10 검증 완료")
    return True


if __name__ == "__main__":
    try:
        test_mempool_cleanup_after_reorg()
        print("\n[OK] Mempool Cleanup After Reorg Test PASSED")
        sys.exit(0)
    except AssertionError as e:
        print(f"\n[FAIL] Test FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[FAIL] Test ERROR: {e}")
        sys.exit(1)
