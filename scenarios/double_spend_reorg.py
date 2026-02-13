"""
시나리오 5: 동일 nonce 이중지불 경쟁

같은 nonce의 두 거래가 포크된 체인에 각각 포함되었다가
reorg 발생 시 패배 체인의 거래는 무효 처리
"""

import sys
import os
import copy

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from blockchain import Node, NetworkSimulator, Wallet, config


def test_double_spend_reorg():
    """이중지불 경쟁 및 Reorg 테스트"""
    print("[TEST] 시나리오: 이중지불 경쟁 및 Reorg")

    network = NetworkSimulator()
    wallet_alice = Wallet("Alice")
    wallet_bob = Wallet("Bob")
    wallet_charlie = Wallet("Charlie")

    network.register_wallet(wallet_alice)
    network.register_wallet(wallet_bob)
    network.register_wallet(wallet_charlie)

    node1 = Node(wallet_alice.address, network.genesis_block)
    node2 = Node(wallet_bob.address, network.genesis_block)

    # 초기 채굴
    config.SIM_TIME = 1
    block1 = node1.try_mine()
    node1.receive_block(block1)
    node2.receive_block(copy.deepcopy(block1))

    print("\n1. 동일 nonce로 두 개의 다른 트랜잭션 생성")
    # Alice가 동일 nonce로 Bob과 Charlie에게 각각 전송 (이중지불 시도)
    tx_to_bob = wallet_alice.create_transaction(wallet_bob.address, 10, 1)
    tx_to_charlie = wallet_alice.create_transaction(wallet_charlie.address, 15, 1)  # 같은 nonce!

    print(f"   TX1: Alice→Bob 10코인 (nonce 1)")
    print(f"   TX2: Alice→Charlie 15코인 (nonce 1)")

    # 포크 발생: node1은 tx_to_bob 채굴, node2는 tx_to_charlie 채굴
    print("\n2. 포크 발생 (각 노드가 다른 tx 채굴)")

    # Node1: tx_to_bob 포함
    node1.add_transaction(tx_to_bob)
    config.SIM_TIME = 2
    block2_node1 = node1.try_mine()
    node1.receive_block(block2_node1)
    print(f"   Node1 체인 높이: {node1.get_tip_block().index}")

    # Node2: tx_to_charlie 포함
    node2.add_transaction(tx_to_charlie)
    config.SIM_TIME = 2
    block2_node2 = node2.try_mine()
    node2.receive_block(block2_node2)
    print(f"   Node2 체인 높이: {node2.get_tip_block().index}")

    # Node2가 더 긴 체인 만들기 (reorg 유도)
    print("\n3. Node2가 추가 블록 채굴 (더 무거운 체인)")
    config.SIM_TIME = 3
    block3_node2 = node2.try_mine()
    node2.receive_block(block3_node2)
    print(f"   Node2 총 작업량: {node2.get_tip_block().total_work}")

    # Node1에 Node2의 블록들 전파 → Reorg 발생
    print("\n4. Reorg 발생 (Node1이 Node2 체인 수용)")
    old_tip = node1.get_tip_block().hash

    node1.receive_block(copy.deepcopy(block2_node2))
    node1.receive_block(copy.deepcopy(block3_node2))

    new_tip = node1.get_tip_block().hash
    print(f"   Tip 변경: {old_tip[:8]}... → {new_tip[:8]}...")

    # 검증: tx_to_bob은 mempool로 돌아왔지만, nonce가 이미 사용되어 무효
    print("\n5. Mempool 상태 검증")
    print(f"   Mempool 크기: {len(node1.mempool)}")

    # clean_mempool 호출 (자동으로 호출되지만 명시적으로)
    node1.clean_mempool()
    print(f"   Mempool 정리 후 크기: {len(node1.mempool)}")

    # Alice의 최종 nonce는 1 (tx_to_charlie 사용)
    alice_state = node1.state.get(wallet_alice.address, {'balance': 0, 'nonce': 0})
    bob_state = node1.state.get(wallet_bob.address, {'balance': 0, 'nonce': 0})
    charlie_state = node1.state.get(wallet_charlie.address, {'balance': 0, 'nonce': 0})

    print(f"\n6. 최종 상태")
    print(f"   Alice nonce: {alice_state['nonce']}")
    print(f"   Alice 잔액: {alice_state['balance']}")
    print(f"   Bob 잔액: {bob_state['balance']}")
    print(f"   Charlie 잔액: {charlie_state['balance']}")

    # 검증:
    # Block1: Alice 채굴 (+50)
    # Block2_node2: Bob 채굴 (+50), tx_to_charlie (Alice -15)
    # Block3_node2: Bob 채굴 (+50)
    # Alice 총: 50 - 15 = 35
    # Bob 총: 50 + 50 = 100
    # Charlie 총: 15

    assert alice_state['nonce'] == 1, "Alice nonce should be 1"
    assert alice_state['balance'] == 35, f"Alice should have 35, got {alice_state['balance']}"
    assert bob_state['balance'] == 100, f"Bob should have 100 (2 blocks mined), got {bob_state['balance']}"
    assert charlie_state['balance'] == 15, "Charlie should have 15 (tx_to_charlie confirmed)"
    assert len(node1.mempool) == 0, "tx_to_bob should be removed from mempool (nonce conflict)"

    print("\n[OK] 시나리오 5 검증 완료")
    return True


if __name__ == "__main__":
    try:
        test_double_spend_reorg()
        print("\n[OK] Double Spend Reorg Test PASSED")
        sys.exit(0)
    except AssertionError as e:
        print(f"\n[FAIL] Test FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[FAIL] Test ERROR: {e}")
        sys.exit(1)
