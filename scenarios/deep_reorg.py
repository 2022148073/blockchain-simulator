"""
시나리오 6: Deep Reorg

공통 조상 탐색 후 롤백+replay 과정에서
balance와 nonce가 최종 체인 기준으로 정확히 재구성
"""

import sys
import os
import copy

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from blockchain import Node, NetworkSimulator, Wallet, config


def test_deep_reorg():
    """Deep Reorg (다단계 롤백) 테스트"""
    print("[TEST] 시나리오: Deep Reorg (다단계 롤백)")

    network = NetworkSimulator()
    wallet_alice = Wallet("Alice")
    wallet_bob = Wallet("Bob")

    network.register_wallet(wallet_alice)
    network.register_wallet(wallet_bob)

    node = Node(wallet_alice.address, network.genesis_block)
    network.add_node(node)

    # 공통 조상까지 체인 구축
    print("\n1. 공통 조상 체인 구축 (블록 1-3)")
    config.SIM_TIME = 1
    block1 = node.try_mine()
    node.receive_block(block1)

    tx1 = wallet_alice.create_transaction(wallet_bob.address, 10, 1)
    node.add_transaction(tx1)
    config.SIM_TIME = 2
    block2 = node.try_mine()
    node.receive_block(block2)

    tx2 = wallet_alice.create_transaction(wallet_bob.address, 5, 2)
    node.add_transaction(tx2)
    config.SIM_TIME = 3
    block3 = node.try_mine()
    node.receive_block(block3)

    common_ancestor_hash = block2.hash
    print(f"   공통 조상: Block #{block2.index} ({common_ancestor_hash[:8]}...)")

    # 현재 상태 저장
    alice_state_old = node.state.get(wallet_alice.address, {'balance': 0, 'nonce': 0})
    bob_state_old = node.state.get(wallet_bob.address, {'balance': 0, 'nonce': 0})
    print(f"   Old chain - Alice: balance={alice_state_old['balance']}, nonce={alice_state_old['nonce']}")
    print(f"   Old chain - Bob: balance={bob_state_old['balance']}, nonce={bob_state_old['nonce']}")

    # 대체 체인 생성 (더 무거운 체인)
    print("\n2. 대체 체인 생성 (block2에서 분기)")

    # block2 시점의 상태로 새 노드 생성 (시뮬레이션)
    node2 = Node(wallet_bob.address, network.genesis_block)
    node2.receive_block(copy.deepcopy(block1))
    node2.receive_block(copy.deepcopy(block2))

    # 대체 체인: block2 → block3_alt → block4_alt (더 많은 작업량)
    tx3_alt = wallet_alice.create_transaction(wallet_bob.address, 20, 2)  # 다른 금액
    node2.add_transaction(tx3_alt)
    config.SIM_TIME = 4
    block3_alt = node2.try_mine()
    node2.receive_block(block3_alt)

    config.SIM_TIME = 5
    block4_alt = node2.try_mine()
    node2.receive_block(block4_alt)

    print(f"   Alt chain 총 작업량: {node2.get_tip_block().total_work}")
    print(f"   Old chain 총 작업량: {node.get_tip_block().total_work}")

    # Reorg 발생
    print("\n3. Deep Reorg 발생")
    old_tip_index = node.get_tip_block().index

    node.receive_block(copy.deepcopy(block3_alt))
    node.receive_block(copy.deepcopy(block4_alt))

    new_tip_index = node.get_tip_block().index
    print(f"   체인 높이: {old_tip_index} → {new_tip_index}")

    # 최종 상태 검증
    alice_state_new = node.state.get(wallet_alice.address, {'balance': 0, 'nonce': 0})
    bob_state_new = node.state.get(wallet_bob.address, {'balance': 0, 'nonce': 0})

    print(f"\n4. Reorg 후 상태")
    print(f"   Alice: balance={alice_state_new['balance']}, nonce={alice_state_new['nonce']}")
    print(f"   Bob: balance={bob_state_new['balance']}, nonce={bob_state_new['nonce']}")

    # 검증:
    # Block1: Alice 채굴 (+50)
    # Block2: Alice 채굴 (+50), tx1 (Alice→Bob 10, -10)
    # Block3_alt: Bob 채굴 (+50), tx3_alt (Alice→Bob 20, -20)
    # Block4_alt: Bob 채굴 (+50)
    # Alice 총: 50 + 50 - 10 - 20 = 70
    # Bob 총: 10 + 50 + 20 + 50 = 130
    expected_alice_balance = 50 + 50 - 10 - 20  # 2번 채굴 (block1, block2), 2번 송금
    expected_alice_nonce = 2
    expected_bob_balance = 10 + 50 + 20 + 50  # tx1 받음 + block3_alt 채굴 + tx3_alt 받음 + block4_alt 채굴

    assert alice_state_new['nonce'] == expected_alice_nonce, f"Alice nonce should be {expected_alice_nonce}, got {alice_state_new['nonce']}"
    assert alice_state_new['balance'] == expected_alice_balance, f"Alice balance should be {expected_alice_balance}, got {alice_state_new['balance']}"
    assert bob_state_new['balance'] == expected_bob_balance, f"Bob balance should be {expected_bob_balance}, got {bob_state_new['balance']}"

    print("\n[OK] 시나리오 6 검증 완료")
    return True


if __name__ == "__main__":
    try:
        test_deep_reorg()
        print("\n[OK] Deep Reorg Test PASSED")
        sys.exit(0)
    except AssertionError as e:
        print(f"\n[FAIL] Test FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[FAIL] Test ERROR: {e}")
        sys.exit(1)
