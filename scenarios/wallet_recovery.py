"""
시나리오 12: 지갑 백업 및 복구

개인키 내보내기/가져오기 기능 검증
- 개인키 백업 (export)
- 백업한 개인키로 지갑 복구 (import)
- 복구된 지갑의 주소와 서명 기능 검증
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from blockchain import Wallet, Node, NetworkSimulator, config
from blockchain.crypto import CryptoUtils


def test_wallet_recovery():
    """지갑 백업 및 복구 테스트"""
    print("[TEST] 시나리오: 지갑 백업 및 복구")

    # Case A: 원본 지갑 생성
    print("\n1. 원본 지갑 생성")
    original_wallet = Wallet("Alice")
    original_address = original_wallet.address
    original_public_key = original_wallet.get_public_key_hex()

    print(f"   원본 주소: {original_address}")
    print(f"   원본 공개키: {original_public_key[:32]}...")

    # Case B: 개인키 내보내기 (백업)
    print("\n2. 개인키 백업")
    exported_private_key = original_wallet.export_private_key()
    print(f"   백업된 개인키 크기: {len(exported_private_key)} bytes")
    print(f"   백업 형식: PEM (PKCS8)")
    assert exported_private_key is not None, "Private key should be exported"
    assert isinstance(exported_private_key, bytes), "Exported key should be bytes"

    # Case C: 백업한 개인키로 지갑 복구
    print("\n3. 백업한 개인키로 지갑 복구")
    recovered_wallet = Wallet.from_private_key(exported_private_key, "Alice_Recovered")
    recovered_address = recovered_wallet.address
    recovered_public_key = recovered_wallet.get_public_key_hex()

    print(f"   복구된 주소: {recovered_address}")
    print(f"   복구된 공개키: {recovered_public_key[:32]}...")

    # Case D: 주소 및 공개키 일치 확인
    print("\n4. 주소 및 공개키 일치 확인")
    assert recovered_address == original_address, "Recovered address should match original"
    assert recovered_public_key == original_public_key, "Recovered public key should match original"
    print(f"   주소 일치: {recovered_address == original_address}")
    print(f"   공개키 일치: {recovered_public_key == original_public_key}")

    # Case E: 복구된 지갑으로 트랜잭션 서명
    print("\n5. 복구된 지갑으로 트랜잭션 서명")
    bob_wallet = Wallet("Bob")
    tx = recovered_wallet.create_transaction(bob_wallet.address, 10, 1)

    print(f"   서명 길이: {len(tx['signature'])} chars")
    assert 'signature' in tx, "Transaction should have signature"
    assert 'public_key' in tx, "Transaction should have public key"

    # Case F: 서명 검증 (블록체인 노드에서)
    print("\n6. 복구된 지갑의 서명 검증")
    network = NetworkSimulator()
    network.register_wallet(recovered_wallet)
    network.register_wallet(bob_wallet)

    node = Node(recovered_wallet.address, network.genesis_block)

    # 서명 검증
    is_valid = node.verify_transaction_signature(tx)
    print(f"   서명 유효성: {is_valid}")
    assert is_valid, "Recovered wallet's signature should be valid"

    # Case G: 원본 지갑과 복구된 지갑의 서명이 다른지 확인 (nonce 기반)
    print("\n7. 원본 vs 복구 지갑 서명 비교")
    tx_original = original_wallet.create_transaction(bob_wallet.address, 10, 1)
    tx_recovered = recovered_wallet.create_transaction(bob_wallet.address, 10, 1)

    # 같은 내용이므로 txid는 동일해야 함
    txid_original = node.compute_txid(tx_original)
    txid_recovered = node.compute_txid(tx_recovered)

    print(f"   원본 TxID: {txid_original[:16]}...")
    print(f"   복구 TxID: {txid_recovered[:16]}...")
    assert txid_original == txid_recovered, "TxIDs should be same (same body)"

    # 서명은 달라질 수 있음 (ECDSA의 특성)
    print(f"   서명 동일 여부: {tx_original['signature'] == tx_recovered['signature']}")

    # Case H: 공개키 직렬화/역직렬화 테스트
    print("\n8. 공개키 직렬화/역직렬화 테스트")
    public_key_bytes = original_wallet.get_public_key_bytes()
    print(f"   직렬화된 공개키 크기: {len(public_key_bytes)} bytes")

    # 역직렬화
    deserialized_public_key = CryptoUtils.bytes_to_public_key(public_key_bytes)
    reconstructed_address = CryptoUtils.public_key_to_address(deserialized_public_key)

    print(f"   재구성된 주소: {reconstructed_address}")
    assert reconstructed_address == original_address, "Address should match after deserialization"

    print("\n[OK] 시나리오 12 검증 완료")
    return True


if __name__ == "__main__":
    try:
        test_wallet_recovery()
        print("\n[OK] Wallet Recovery Test PASSED")
        sys.exit(0)
    except AssertionError as e:
        print(f"\n[FAIL] Test FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[FAIL] Test ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
