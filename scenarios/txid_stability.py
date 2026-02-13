"""
시나리오 8: TxID 안정성

txid는 body의 canonical serialization 기반 해시로
signature 변경과 무관하게 동일해야 함
"""

import sys
import os
import copy

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from blockchain import Node, NetworkSimulator, Wallet, config


def test_txid_stability():
    """TxID 안정성 (서명 독립성) 테스트"""
    print("[TEST] 시나리오: TxID 안정성 (서명 독립성)")

    network = NetworkSimulator()
    wallet_alice = Wallet("Alice")
    wallet_bob = Wallet("Bob")

    network.register_wallet(wallet_alice)

    node = Node(wallet_alice.address, network.genesis_block)

    # 동일한 body의 트랜잭션 생성
    print("\n1. 트랜잭션 생성")
    tx1 = wallet_alice.create_transaction(wallet_bob.address, 10, 1)

    # TxID 계산 (body만 사용)
    txid1 = node.compute_txid(tx1)
    print(f"   Original TxID: {txid1[:16]}...")

    # 같은 body로 다시 서명 (서명은 매번 달라질 수 있음)
    print("\n2. 동일 body 재서명")
    tx2 = wallet_alice.create_transaction(wallet_bob.address, 10, 1)
    txid2 = node.compute_txid(tx2)

    print(f"   New TxID: {txid2[:16]}...")
    print(f"   서명 동일 여부: {tx1['signature'] == tx2['signature']}")

    # 서명은 다를 수 있지만 txid는 동일해야 함
    assert txid1 == txid2, "TxID should be same for same body"

    # body 변경 시 txid 달라지는지 확인
    print("\n3. Body 변경 (금액 10→20)")
    tx3 = wallet_alice.create_transaction(wallet_bob.address, 20, 1)
    txid3 = node.compute_txid(tx3)

    print(f"   Changed TxID: {txid3[:16]}...")
    assert txid1 != txid3, "TxID should be different for different body"

    # 서명 변조해도 txid는 동일
    print("\n4. 서명 변조 후 TxID")
    tx4 = copy.deepcopy(tx1)
    tx4['signature'] = "00" * 64  # 서명 변조
    txid4 = node.compute_txid(tx4)

    print(f"   Tampered TxID: {txid4[:16]}...")
    assert txid1 == txid4, "TxID should be same even with tampered signature"

    print("\n[OK] 시나리오 8 검증 완료")
    return True


if __name__ == "__main__":
    try:
        test_txid_stability()
        print("\n[OK] TxID Stability Test PASSED")
        sys.exit(0)
    except AssertionError as e:
        print(f"\n[FAIL] Test FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[FAIL] Test ERROR: {e}")
        sys.exit(1)
