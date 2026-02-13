"""
블록체인 시뮬레이터 실행 스크립트 (암호화 버전)

기본 사용법:
    python -m blockchain.main

또는:
    python blockchain/main.py
"""

from blockchain import Node, NetworkSimulator, Wallet, config


def main():
    """메인 실행 함수 - 디지털 서명 포함"""
    print("=" * 60)
    print("블록체인 합의 알고리즘 시뮬레이터 v2.0")
    print("(ECDSA 디지털 서명 포함)")
    print("=" * 60)

    # 네트워크 시뮬레이터 생성
    network = NetworkSimulator()

    # 지갑 생성
    print("\n[WALLET] 지갑 생성 중...")
    wallet_alice = Wallet("Alice")
    wallet_bob = Wallet("Bob")
    wallet_charlie = Wallet("Charlie")

    # 지갑을 네트워크에 등록
    network.register_wallet(wallet_alice)
    network.register_wallet(wallet_bob)
    network.register_wallet(wallet_charlie)

    # 노드 생성 (지갑 주소를 노드 ID로 사용)
    print("\n[NODE] 노드 생성 중...")
    node_alice = Node(wallet_alice.address, network.genesis_block)
    node_bob = Node(wallet_bob.address, network.genesis_block)
    node_charlie = Node(wallet_charlie.address, network.genesis_block)

    network.add_node(node_alice)
    network.add_node(node_bob)
    network.add_node(node_charlie)

    print(f"[OK] 3개의 노드 생성 완료")
    print(f"   Alice: {wallet_alice.address[:24]}...")
    print(f"   Bob: {wallet_bob.address[:24]}...")
    print(f"   Charlie: {wallet_charlie.address[:24]}...")
    print(f"   Genesis Hash: {network.genesis_block.hash[:8]}...")

    # 시뮬레이션 설정 출력
    print(f"\n[CONFIG] 시뮬레이션 설정:")
    print(f"   - 난이도 조절 주기: {config.ADJUSTMENT_INTERVAL} 블록")
    print(f"   - 목표 블록 시간: {config.TARGET_BLOCK_TIME}초")
    print(f"   - 채굴 보상: {config.MINING_REWARD}")
    print(f"   - 초기 난이도: {config.DEFAULT_DIFFICULTY}")
    print(f"   - 채굴 확률: {config.MINING_PROBABILITY * 100}%")
    print(f"   - 서명 알고리즘: ECDSA (secp256k1)")

    # 시뮬레이션 실행
    print(f"\n{'=' * 60}")
    network.run_simulation(steps=20)

    # 최종 상태 출력
    print(f"\n{'=' * 60}")
    print("시뮬레이션 종료 - 최종 상태")
    print("=" * 60)

    wallets = {wallet_alice.address: "Alice", wallet_bob.address: "Bob", wallet_charlie.address: "Charlie"}

    for node in network.nodes:
        tip = node.get_tip_block()
        state = node.state.get(node.node_id, {'balance': 0, 'nonce': 0})
        node_name = wallets.get(node.node_id, node.node_id[:8])

        print(f"\n[{node_name}]")
        print(f"  - 주소: {node.node_id[:32]}...")
        print(f"  - 체인 높이: {tip.index}")
        print(f"  - Tip 해시: {tip.hash[:16]}...")
        print(f"  - 총 작업량: {tip.total_work}")
        print(f"  - 현재 난이도: {tip.difficulty}")
        print(f"  - 잔액: {state['balance']}")
        print(f"  - Nonce: {state['nonce']}")
        print(f"  - 멤풀 크기: {len(node.mempool)}")
        print(f"  - 블록 인덱스 크기: {len(node.block_index)}")
        print(f"  - 고아 풀 크기: {sum(len(v) for v in node.orphan_pool.values())}")


def demo_with_transactions():
    """트랜잭션 포함 데모 - 디지털 서명 검증"""
    print("=" * 60)
    print("블록체인 시뮬레이터 - 트랜잭션 데모 v2.0")
    print("(ECDSA 디지털 서명 검증 포함)")
    print("=" * 60)

    network = NetworkSimulator()

    # 지갑 생성
    print("\n🔐 지갑 생성...")
    wallet_alice = Wallet("Alice")
    wallet_bob = Wallet("Bob")

    network.register_wallet(wallet_alice)
    network.register_wallet(wallet_bob)

    # 노드 생성
    print("\n[NODE] 노드 생성...")
    node_alice = Node(wallet_alice.address, network.genesis_block)
    node_bob = Node(wallet_bob.address, network.genesis_block)

    network.add_node(node_alice)
    network.add_node(node_bob)

    print(f"[OK] 노드 생성 완료")
    print(f"   Alice: {wallet_alice.address[:32]}...")
    print(f"   Bob: {wallet_bob.address[:32]}...")

    # 초기 채굴 (잔액 확보)
    print(f"\n{'=' * 60}")
    print("초기 채굴 (5 스텝)")
    print("=" * 60)
    network.run_simulation(steps=5)

    # 트랜잭션 추가
    print(f"\n{'=' * 60}")
    print("서명된 트랜잭션 생성")
    print("=" * 60)

    # Alice가 잔액이 있는지 확인 후 트랜잭션 생성
    alice_balance = node_alice.state.get(wallet_alice.address, {'balance': 0})['balance']
    if alice_balance >= 10:
        print(f"\n[BALANCE] Alice 잔액: {alice_balance}")
        network.add_transaction_to_network(wallet_alice.address, wallet_bob.address, 10)

    bob_balance = node_bob.state.get(wallet_bob.address, {'balance': 0})['balance']
    if bob_balance >= 5:
        print(f"[BALANCE] Bob 잔액: {bob_balance}")
        network.add_transaction_to_network(wallet_bob.address, wallet_alice.address, 5)

    # 추가 채굴 (트랜잭션 포함)
    print(f"\n{'=' * 60}")
    print("트랜잭션 포함 채굴 (10 스텝)")
    print("=" * 60)
    network.run_simulation(steps=10)

    # 최종 상태
    print(f"\n{'=' * 60}")
    print("최종 잔액")
    print("=" * 60)

    alice_state = node_alice.state.get(wallet_alice.address, {'balance': 0, 'nonce': 0})
    bob_state = node_bob.state.get(wallet_bob.address, {'balance': 0, 'nonce': 0})

    print(f"  Alice: {alice_state['balance']} (nonce: {alice_state['nonce']})")
    print(f"  Bob: {bob_state['balance']} (nonce: {bob_state['nonce']})")


def demo_signature_validation():
    """디지털 서명 검증 데모"""
    print("=" * 60)
    print("디지털 서명 검증 데모")
    print("=" * 60)

    from blockchain import CryptoUtils

    # 지갑 생성
    alice_wallet = Wallet("Alice")
    bob_wallet = Wallet("Bob")

    print(f"\n[OK] Alice 지갑 생성")
    print(f"   주소: {alice_wallet.address}")
    print(f"\n[OK] Bob 지갑 생성")
    print(f"   주소: {bob_wallet.address}")

    # Alice가 Bob에게 트랜잭션 생성
    print(f"\n[TX] Alice가 Bob에게 10 코인 전송 트랜잭션 생성...")
    tx = alice_wallet.create_transaction(bob_wallet.address, 10, 1)

    print(f"\n트랜잭션 내용:")
    print(f"  - 송신자: {tx['body']['sender'][:32]}...")
    print(f"  - 수신자: {tx['body']['recipient'][:32]}...")
    print(f"  - 금액: {tx['body']['amount']}")
    print(f"  - Nonce: {tx['body']['nonce']}")
    print(f"  - 서명: {tx['signature'][:64]}...")

    # 서명 검증
    print(f"\n[VERIFY] 서명 검증 중...")
    public_key_bytes = bytes.fromhex(tx['public_key'])
    public_key = CryptoUtils.bytes_to_public_key(public_key_bytes)
    signature = CryptoUtils.hex_to_signature(tx['signature'])

    is_valid = CryptoUtils.verify_signature(public_key, tx['body'], signature)
    print(f"   검증 결과: {'[OK] 유효한 서명' if is_valid else '[FAIL] 무효한 서명'}")

    # 공개키로부터 주소 복원
    calculated_address = CryptoUtils.public_key_to_address(public_key)
    address_match = calculated_address == alice_wallet.address
    print(f"   주소 일치: {'[OK] 일치' if address_match else '[FAIL] 불일치'}")

    # 변조 시도
    print(f"\n[WARN] 트랜잭션 변조 시도 (금액을 10 -> 1000으로 변경)...")
    tampered_body = tx['body'].copy()
    tampered_body['amount'] = 1000

    is_valid_tampered = CryptoUtils.verify_signature(public_key, tampered_body, signature)
    print(f"   검증 결과: {'[OK] 유효한 서명 (이상함!)' if is_valid_tampered else '[FAIL] 무효한 서명 (정상)'}")

    # 다른 사람의 공개키로 검증 시도
    print(f"\n[WARN] Bob의 공개키로 검증 시도...")
    is_valid_wrong_key = CryptoUtils.verify_signature(bob_wallet.public_key, tx['body'], signature)
    print(f"   검증 결과: {'[OK] 유효한 서명 (이상함!)' if is_valid_wrong_key else '[FAIL] 무효한 서명 (정상)'}")


if __name__ == "__main__":
    # 기본 시뮬레이션 실행
    main()

    # 트랜잭션 데모를 실행하려면 아래 주석 해제
    # print("\n\n")
    # demo_with_transactions()

    # 서명 검증 데모를 실행하려면 아래 주석 해제
    # print("\n\n")
    # demo_signature_validation()
