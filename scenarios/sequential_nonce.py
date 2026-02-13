"""
시나리오 1: 정상 흐름 - 연속 nonce 처리

동일 계정의 연속 거래(nonce 1→2→3)가 블록에 포함될 때
서명 검증, nonce 증가, 잔액 반영, mempool 정리가 정확히 동작
"""

import sys
import os

# 상위 디렉토리의 blockchain 패키지를 import하기 위한 경로 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from blockchain import Node, NetworkSimulator, Wallet, config


def test_sequential_nonce():
    """정상 흐름: 연속 nonce 처리 테스트"""
    print("[TEST] 시나리오: 동일 계정의 연속 nonce 거래 처리")

    # 네트워크 설정
    network = NetworkSimulator()
    wallet_alice = Wallet("Alice")
    wallet_bob = Wallet("Bob")

    network.register_wallet(wallet_alice)
    network.register_wallet(wallet_bob)

    node = Node(wallet_alice.address, network.genesis_block)
    network.add_node(node)

    # 초기 채굴로 Alice에게 잔액 확보
    print("\n1. 초기 채굴 (Alice가 잔액 확보)")
    config.SIM_TIME = 1
    block1 = node.try_mine()
    node.receive_block(block1)

    alice_state = node.state.get(wallet_alice.address, {'balance': 0, 'nonce': 0})
    print(f"   Alice 초기 잔액: {alice_state['balance']}, nonce: {alice_state['nonce']}")
    assert alice_state['balance'] >= 50, "Alice should have mining reward"
    assert alice_state['nonce'] == 0, "Alice initial nonce should be 0"

    # 연속 트랜잭션 3개 생성 (nonce 1, 2, 3)
    print("\n2. 연속 트랜잭션 생성 (nonce 1→2→3)")
    tx1 = wallet_alice.create_transaction(wallet_bob.address, 10, 1)
    tx2 = wallet_alice.create_transaction(wallet_bob.address, 5, 2)
    tx3 = wallet_alice.create_transaction(wallet_bob.address, 3, 3)

    node.add_transaction(tx1)
    node.add_transaction(tx2)
    node.add_transaction(tx3)

    print(f"   Mempool 크기: {len(node.mempool)}")
    assert len(node.mempool) == 3, "3 transactions should be in mempool"

    # 블록 채굴 (모든 tx 포함)
    print("\n3. 블록 채굴 (모든 tx 포함)")
    config.SIM_TIME = 2
    block2 = node.try_mine()
    node.receive_block(block2)

    # 검증
    alice_state = node.state.get(wallet_alice.address, {'balance': 0, 'nonce': 0})
    bob_state = node.state.get(wallet_bob.address, {'balance': 0, 'nonce': 0})

    print(f"\n4. 최종 상태 검증")
    print(f"   Alice: balance={alice_state['balance']}, nonce={alice_state['nonce']}")
    print(f"   Bob: balance={bob_state['balance']}, nonce={bob_state['nonce']}")
    print(f"   Mempool 크기: {len(node.mempool)}")

    # Assert
    assert alice_state['nonce'] == 3, f"Alice nonce should be 3, got {alice_state['nonce']}"
    assert alice_state['balance'] == 50 + 50 - 10 - 5 - 3, "Alice balance incorrect"
    assert bob_state['balance'] == 10 + 5 + 3, "Bob balance incorrect"
    assert len(node.mempool) == 0, "Mempool should be empty after mining"

    print("\n[OK] 시나리오 1 검증 완료")
    return True


if __name__ == "__main__":
    try:
        test_sequential_nonce()
        print("\n[OK] Sequential Nonce Test PASSED")
        sys.exit(0)
    except AssertionError as e:
        print(f"\n[FAIL] Test FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[FAIL] Test ERROR: {e}")
        sys.exit(1)
