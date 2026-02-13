"""
시나리오 13: WalletManager 멀티 지갑 관리

WalletManager를 이용한 여러 지갑 생성 및 관리 기능 검증
- 지갑 생성 및 등록
- 이름으로 지갑 조회
- 주소 조회
- 중복 생성 방지
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from blockchain import Wallet, Node, NetworkSimulator, config
from blockchain.wallet import WalletManager


def test_wallet_manager():
    """WalletManager 멀티 지갑 관리 테스트"""
    print("[TEST] 시나리오: WalletManager 멀티 지갑 관리")

    # Case A: WalletManager 초기화
    print("\n1. WalletManager 초기화")
    manager = WalletManager()
    print(f"   초기 지갑 개수: {len(manager.wallets)}")
    assert len(manager.wallets) == 0, "Initial wallet count should be 0"

    # Case B: 여러 지갑 생성
    print("\n2. 여러 지갑 생성")
    wallet_alice = manager.create_wallet("Alice")
    wallet_bob = manager.create_wallet("Bob")
    wallet_charlie = manager.create_wallet("Charlie")

    print(f"   생성된 지갑 개수: {len(manager.wallets)}")
    assert len(manager.wallets) == 3, "Should have 3 wallets"
    assert wallet_alice is not None, "Alice wallet should be created"
    assert wallet_bob is not None, "Bob wallet should be created"
    assert wallet_charlie is not None, "Charlie wallet should be created"

    # Case C: 이름으로 지갑 조회
    print("\n3. 이름으로 지갑 조회")
    retrieved_alice = manager.get_wallet("Alice")
    print(f"   조회된 Alice 지갑: {retrieved_alice.owner_name}")
    assert retrieved_alice is not None, "Alice wallet should be found"
    assert retrieved_alice.address == wallet_alice.address, "Retrieved wallet should match original"

    # 존재하지 않는 지갑 조회
    non_existent = manager.get_wallet("David")
    print(f"   존재하지 않는 지갑 조회 결과: {non_existent}")
    assert non_existent is None, "Non-existent wallet should return None"

    # Case D: 주소 조회
    print("\n4. 주소 조회")
    alice_address = manager.get_address("Alice")
    bob_address = manager.get_address("Bob")

    print(f"   Alice 주소: {alice_address[:24]}...")
    print(f"   Bob 주소: {bob_address[:24]}...")
    assert alice_address == wallet_alice.address, "Alice address should match"
    assert bob_address == wallet_bob.address, "Bob address should match"

    # 존재하지 않는 지갑의 주소
    non_existent_address = manager.get_address("David")
    assert non_existent_address is None, "Non-existent wallet address should be None"

    # Case E: 중복 생성 방지
    print("\n5. 중복 생성 방지 테스트")
    original_alice = wallet_alice
    duplicate_alice = manager.create_wallet("Alice")  # 이미 존재하는 이름

    print(f"   중복 생성 시 반환된 지갑: {duplicate_alice.owner_name}")
    assert duplicate_alice is original_alice, "Should return existing wallet"
    assert len(manager.wallets) == 3, "Wallet count should remain 3"

    # Case F: 생성된 지갑으로 트랜잭션 생성 및 검증
    print("\n6. 생성된 지갑으로 트랜잭션 생성")
    network = NetworkSimulator()
    network.register_wallet(wallet_alice)
    network.register_wallet(wallet_bob)

    node = Node(wallet_alice.address, network.genesis_block)

    # Alice가 Bob에게 송금하는 트랜잭션
    tx = wallet_alice.create_transaction(wallet_bob.address, 10, 1)

    # 서명 검증
    is_valid = node.verify_transaction_signature(tx)
    print(f"   트랜잭션 서명 검증: {is_valid}")
    assert is_valid, "Transaction signature should be valid"

    # Case G: 여러 지갑 간 트랜잭션 시뮬레이션
    print("\n7. 여러 지갑 간 트랜잭션 시뮬레이션")
    network.register_wallet(wallet_charlie)

    # 초기 채굴 (Alice가 잔액 확보)
    config.SIM_TIME = 1
    block1 = node.try_mine()
    node.receive_block(block1)

    alice_state = node.state.get(wallet_alice.address, {'balance': 0, 'nonce': 0})
    print(f"   Alice 초기 잔액: {alice_state['balance']}")
    assert alice_state['balance'] >= 50, "Alice should have mining reward"

    # 트랜잭션 생성
    tx1 = wallet_alice.create_transaction(wallet_bob.address, 10, 1)
    tx2 = wallet_alice.create_transaction(wallet_charlie.address, 5, 2)

    node.add_transaction(tx1)
    node.add_transaction(tx2)

    # 블록 채굴
    config.SIM_TIME = 2
    block2 = node.try_mine()
    node.receive_block(block2)

    # 상태 확인
    alice_final = node.state.get(wallet_alice.address, {'balance': 0, 'nonce': 0})
    bob_final = node.state.get(wallet_bob.address, {'balance': 0, 'nonce': 0})
    charlie_final = node.state.get(wallet_charlie.address, {'balance': 0, 'nonce': 0})

    print(f"   Alice 최종 잔액: {alice_final['balance']}, nonce: {alice_final['nonce']}")
    print(f"   Bob 최종 잔액: {bob_final['balance']}")
    print(f"   Charlie 최종 잔액: {charlie_final['balance']}")

    assert alice_final['nonce'] == 2, "Alice nonce should be 2"
    assert bob_final['balance'] == 10, "Bob should have 10"
    assert charlie_final['balance'] == 5, "Charlie should have 5"

    # Case H: list_wallets 함수 호출 (출력 확인)
    print("\n8. 지갑 목록 출력")
    manager.list_wallets()  # 실제 출력

    print("\n[OK] 시나리오 13 검증 완료")
    return True


if __name__ == "__main__":
    try:
        test_wallet_manager()
        print("\n[OK] Wallet Manager Test PASSED")
        sys.exit(0)
    except AssertionError as e:
        print(f"\n[FAIL] Test FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[FAIL] Test ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
