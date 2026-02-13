"""
시나리오 3: 잘못된 서명

body는 동일하지만 signature가 변조된 경우 검증 실패
"""

import sys
import os
import copy

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from blockchain import Node, NetworkSimulator, Wallet, config


def test_invalid_signature():
    """서명 변조 감지 테스트"""
    print("[TEST] 시나리오: 서명 변조 감지")

    network = NetworkSimulator()
    wallet_alice = Wallet("Alice")
    wallet_bob = Wallet("Bob")
    wallet_eve = Wallet("Eve")  # 공격자

    network.register_wallet(wallet_alice)
    network.register_wallet(wallet_bob)

    node = Node(wallet_alice.address, network.genesis_block)
    network.add_node(node)

    # 초기 채굴
    config.SIM_TIME = 1
    block1 = node.try_mine()
    node.receive_block(block1)

    # 정상 트랜잭션 생성
    print("\n1. 정상 트랜잭션 생성")
    tx_valid = wallet_alice.create_transaction(wallet_bob.address, 10, 1)

    # Case A: 서명 변조
    print("\n2. Case A: 서명 변조")
    tx_tampered = copy.deepcopy(tx_valid)
    tx_tampered['signature'] = "00" * 64

    is_valid = node.verify_transaction_signature(tx_tampered)
    print(f"   서명 변조 tx 검증 결과: {is_valid}")
    assert not is_valid, "Tampered signature should fail verification"

    # Case B: body 변조
    print("\n3. Case B: body 변조 (금액 10→100)")
    tx_body_tampered = copy.deepcopy(tx_valid)
    tx_body_tampered['body']['amount'] = 100

    is_valid = node.verify_transaction_signature(tx_body_tampered)
    print(f"   Body 변조 tx 검증 결과: {is_valid}")
    assert not is_valid, "Body tampering should fail signature verification"

    # Case C: 다른 사람의 서명 도용
    print("\n4. Case C: Eve의 서명으로 Alice 주소 사칭")
    tx_impersonation = {
        "body": {
            "sender": wallet_alice.address,
            "recipient": wallet_bob.address,
            "amount": 10,
            "nonce": 1
        },
        "signature": wallet_eve.sign_transaction({
            "sender": wallet_alice.address,
            "recipient": wallet_bob.address,
            "amount": 10,
            "nonce": 1
        }),
        "public_key": wallet_eve.get_public_key_hex()
    }

    is_valid = node.verify_transaction_signature(tx_impersonation)
    print(f"   사칭 tx 검증 결과: {is_valid}")
    assert not is_valid, "Impersonation should fail (address mismatch)"

    print("\n[OK] 시나리오 3 검증 완료")
    return True


if __name__ == "__main__":
    try:
        test_invalid_signature()
        print("\n[OK] Invalid Signature Test PASSED")
        sys.exit(0)
    except AssertionError as e:
        print(f"\n[FAIL] Test FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[FAIL] Test ERROR: {e}")
        sys.exit(1)
