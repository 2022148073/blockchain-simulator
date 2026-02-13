"""
블록체인 시뮬레이터 종합 테스트 스위트

10가지 핵심 시나리오를 검증:
1. 정상 흐름 (연속 nonce)
2. Replay 방지
3. 잘못된 서명
4. Nonce 건너뛰기/역순
5. 동일 nonce 이중지불 경쟁
6. Deep reorg
7. Orphan 블록
8. TxID 안정성
9. 블록 내 tx 순서 공격
10. Reorg 후 mempool 정리
"""

import copy
from tests import Node, NetworkSimulator, Wallet, Block, config, CryptoUtils


class TestScenarios:
    """블록체인 테스트 시나리오 클래스"""

    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.test_results = []

    def run_test(self, test_name, test_func):
        """테스트 실행 및 결과 기록"""
        print(f"\n{'=' * 70}")
        print(f"테스트: {test_name}")
        print('=' * 70)

        try:
            test_func()
            self.passed += 1
            self.test_results.append((test_name, "[OK] PASS"))
            print(f"\n[OK] {test_name} - PASS")
        except AssertionError as e:
            self.failed += 1
            self.test_results.append((test_name, f"[FAIL] FAIL: {e}"))
            print(f"\n[FAIL] {test_name} - FAIL")
            print(f"   오류: {e}")
        except Exception as e:
            self.failed += 1
            self.test_results.append((test_name, f"[FAIL] ERROR: {e}"))
            print(f"\n[FAIL] {test_name} - ERROR")
            print(f"   예외: {e}")

    def assert_equal(self, actual, expected, message=""):
        """값 비교 assert"""
        if actual != expected:
            raise AssertionError(f"{message}\n   Expected: {expected}\n   Actual: {actual}")

    def assert_true(self, condition, message=""):
        """조건 검증 assert"""
        if not condition:
            raise AssertionError(f"{message}")

    def print_summary(self):
        """테스트 결과 요약 출력"""
        print(f"\n\n{'=' * 70}")
        print("테스트 결과 요약")
        print('=' * 70)

        for test_name, result in self.test_results:
            print(f"{result[:2]} {test_name}")

        print(f"\n총 {len(self.test_results)}개 테스트")
        print(f"[OK] 통과: {self.passed}")
        print(f"[FAIL] 실패: {self.failed}")
        print('=' * 70)


def test_1_normal_sequential_nonce():
    """
    시나리오 1: 정상 흐름 - 연속 nonce 처리
    동일 계정의 연속 거래(nonce 1→2→3)가 블록에 포함될 때
    서명 검증, nonce 증가, 잔액 반영, mempool 정리가 정확히 동작
    """
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


def test_2_replay_prevention():
    """
    시나리오 2: Replay 방지
    이미 확정된 tx 또는 동일 nonce의 tx 재전파 시 거부
    """
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

    # Case B: 동일 nonce의 다른 트랜잭션 (이중지불 시도)
    print("\n3. Case B: 동일 nonce로 다른 금액 전송 시도")
    tx1_double_spend = wallet_alice.create_transaction(wallet_bob.address, 20, 1)  # nonce 1 재사용
    node.add_transaction(tx1_double_spend)

    node.clean_mempool()
    print(f"   Mempool 정리 후 크기: {len(node.mempool)}")

    alice_state = node.state.get(wallet_alice.address, {'balance': 0, 'nonce': 0})
    print(f"   Alice nonce: {alice_state['nonce']}")

    # Alice의 nonce는 1이므로, nonce 1인 거래는 expected_nonce (2)와 불일치
    assert len(node.mempool) == 0, "Double spend with old nonce should be rejected"

    print("\n[OK] 시나리오 2 검증 완료")


def test_3_invalid_signature():
    """
    시나리오 3: 잘못된 서명
    body는 동일하지만 signature가 변조된 경우 검증 실패
    """
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
    tx_tampered['signature'] = "00" * 64  # 잘못된 서명

    is_valid = node.verify_transaction_signature(tx_tampered)
    print(f"   서명 변조 tx 검증 결과: {is_valid}")
    assert not is_valid, "Tampered signature should fail verification"

    # Case B: body 변조 (금액 변경)
    print("\n3. Case B: body 변조 (금액 10→100)")
    tx_body_tampered = copy.deepcopy(tx_valid)
    tx_body_tampered['body']['amount'] = 100  # 서명은 그대로

    is_valid = node.verify_transaction_signature(tx_body_tampered)
    print(f"   Body 변조 tx 검증 결과: {is_valid}")
    assert not is_valid, "Body tampering should fail signature verification"

    # Case C: 다른 사람의 서명 도용
    print("\n4. Case C: Eve의 서명으로 Alice 주소 사칭")
    tx_impersonation = {
        "body": {
            "sender": wallet_alice.address,  # Alice인 척
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
        "public_key": wallet_eve.get_public_key_hex()  # Eve의 공개키
    }

    is_valid = node.verify_transaction_signature(tx_impersonation)
    print(f"   사칭 tx 검증 결과: {is_valid}")
    assert not is_valid, "Impersonation should fail (address mismatch)"

    print("\n[OK] 시나리오 3 검증 완료")


def test_4_nonce_skip_reverse():
    """
    시나리오 4: Nonce 건너뛰기/역순
    nonce=2 거래가 nonce=1 없이 먼저 블록에 포함되면 블록 무효 처리
    """
    print("[TEST] 시나리오: Nonce 건너뛰기 및 역순 처리")

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

    # Case A: Nonce 건너뛰기 (0 → 2, 1 건너뜀)
    print("\n1. Case A: Nonce 건너뛰기 (nonce 2, 1 없이)")
    tx_skip = wallet_alice.create_transaction(wallet_bob.address, 10, 2)  # nonce 1 건너뜀

    # 블록 수동 생성
    tip = node.get_tip_block()
    coinbase_tx = {"body": {"sender": "SYSTEM", "recipient": wallet_alice.address, "amount": 50, "nonce": 0}, "sig": None}

    bad_block = Block(
        index=tip.index + 1,
        timestamp=config.SIM_TIME + 1,
        transactions=[coinbase_tx, tx_skip],
        difficulty=tip.difficulty,
        previous_hash=tip.hash,
        miner_id=wallet_alice.address
    )
    bad_block.mine_block()

    # 블록 검증
    is_valid = node.validate_block(bad_block, tip)
    print(f"   Nonce 건너뛰기 블록 검증: {is_valid}")
    assert not is_valid, "Block with skipped nonce should be invalid"

    # Case B: Nonce 역순 (nonce 2, 1 순서로)
    print("\n2. Case B: Nonce 역순 (2→1)")
    tx1 = wallet_alice.create_transaction(wallet_bob.address, 5, 1)
    tx2 = wallet_alice.create_transaction(wallet_bob.address, 3, 2)

    # 역순으로 블록에 포함
    config.SIM_TIME = 2
    bad_block2 = Block(
        index=tip.index + 1,
        timestamp=config.SIM_TIME + 1,
        transactions=[coinbase_tx, tx2, tx1],  # 역순!
        difficulty=tip.difficulty,
        previous_hash=tip.hash,
        miner_id=wallet_alice.address
    )
    bad_block2.mine_block()

    is_valid = node.validate_block(bad_block2, tip)
    print(f"   Nonce 역순 블록 검증: {is_valid}")
    assert not is_valid, "Block with reversed nonce should be invalid"

    # Case C: 정상 순서 (1→2)
    print("\n3. Case C: 정상 순서 (1→2)")
    config.SIM_TIME = 3
    good_block = Block(
        index=tip.index + 1,
        timestamp=config.SIM_TIME + 1,
        transactions=[coinbase_tx, tx1, tx2],  # 정순!
        difficulty=tip.difficulty,
        previous_hash=tip.hash,
        miner_id=wallet_alice.address
    )
    good_block.mine_block()

    is_valid = node.validate_block(good_block, tip)
    print(f"   정상 순서 블록 검증: {is_valid}")
    assert is_valid, "Block with correct nonce order should be valid"

    print("\n[OK] 시나리오 4 검증 완료")


def test_5_double_spend_reorg():
    """
    시나리오 5: 동일 nonce 이중지불 경쟁
    같은 nonce의 두 거래가 포크된 체인에 각각 포함되었다가
    reorg 발생 시 패배 체인의 거래는 무효 처리
    """
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


def test_6_deep_reorg():
    """
    시나리오 6: Deep Reorg
    공통 조상 탐색 후 롤백+replay 과정에서
    balance와 nonce가 최종 체인 기준으로 정확히 재구성
    """
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


def test_7_orphan_blocks():
    """
    시나리오 7: Orphan 블록
    부모 없이 도착한 블록은 orphan_pool에 저장되었다가
    부모 수신 후 올바른 parent state 기준으로 재검증
    """
    print("[TEST] 시나리오: Orphan 블록 처리")

    network = NetworkSimulator()
    wallet_alice = Wallet("Alice")

    network.register_wallet(wallet_alice)

    node = Node(wallet_alice.address, network.genesis_block)

    # 블록 체인 생성 (node에서)
    print("\n1. 블록 체인 생성")
    config.SIM_TIME = 1
    block1 = node.try_mine()
    node.receive_block(block1)

    config.SIM_TIME = 2
    block2 = node.try_mine()
    # block2는 node에 전달하지 않음

    config.SIM_TIME = 3
    block3 = Block(
        index=block2.index + 1,
        timestamp=config.SIM_TIME,
        transactions=[{"body": {"sender": "SYSTEM", "recipient": wallet_alice.address, "amount": 50, "nonce": 0}, "sig": None}],
        difficulty=block2.difficulty,
        previous_hash=block2.hash,
        miner_id=wallet_alice.address
    )
    block3.total_work = block2.total_work + block3.block_work
    block3.mine_block()

    # block3을 먼저 수신 (부모 block2 없음)
    print("\n2. Orphan 블록 수신 (부모 미수신)")
    initial_tip = node.get_tip_block().hash
    node.receive_block(copy.deepcopy(block3))

    current_tip = node.get_tip_block().hash
    orphan_count = sum(len(v) for v in node.orphan_pool.values())

    print(f"   Tip 변경 여부: {initial_tip[:8]}... == {current_tip[:8]}... : {initial_tip == current_tip}")
    print(f"   Orphan pool 크기: {orphan_count}")

    assert initial_tip == current_tip, "Tip should not change (orphan)"
    assert orphan_count == 1, "block3 should be in orphan pool"
    assert block2.hash in node.orphan_pool, "Orphan should be indexed by parent hash"

    # 부모 블록(block2) 수신
    print("\n3. 부모 블록 수신")
    node.receive_block(copy.deepcopy(block2))

    new_tip = node.get_tip_block()
    orphan_count_after = sum(len(v) for v in node.orphan_pool.values())

    print(f"   새 Tip: Block #{new_tip.index} ({new_tip.hash[:8]}...)")
    print(f"   Orphan pool 크기: {orphan_count_after}")

    # 검증: block3이 자동으로 연결됨
    assert new_tip.hash == block3.hash, "block3 should be new tip"
    assert orphan_count_after == 0, "Orphan pool should be empty"
    assert new_tip.index == 3, "Chain height should be 3"

    # 상태도 올바르게 재구성되었는지 확인
    alice_state = node.state.get(wallet_alice.address, {'balance': 0, 'nonce': 0})
    expected_balance = 50 + 50 + 50  # 3번 채굴

    print(f"\n4. 최종 상태")
    print(f"   Alice 잔액: {alice_state['balance']}")
    print(f"   체인 높이: {new_tip.index}")

    assert alice_state['balance'] == expected_balance, f"Alice should have {expected_balance}"

    print("\n[OK] 시나리오 7 검증 완료")


def test_8_txid_stability():
    """
    시나리오 8: TxID 안정성
    txid는 body의 canonical serialization 기반 해시로
    signature 변경과 무관하게 동일해야 함
    """
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


def test_9_block_tx_order_attack():
    """
    시나리오 9: 블록 내 tx 순서 공격
    같은 계정의 거래를 nonce 역순으로 블록에 넣으면 validate_block에서 실패
    """
    print("[TEST] 시나리오: 블록 내 트랜잭션 순서 공격")

    network = NetworkSimulator()
    wallet_alice = Wallet("Alice")
    wallet_bob = Wallet("Bob")

    network.register_wallet(wallet_alice)
    network.register_wallet(wallet_bob)

    node = Node(wallet_alice.address, network.genesis_block)

    # 초기 채굴
    config.SIM_TIME = 1
    block1 = node.try_mine()
    node.receive_block(block1)

    # 순차 트랜잭션 생성
    print("\n1. 순차 트랜잭션 생성 (nonce 1, 2, 3)")
    tx1 = wallet_alice.create_transaction(wallet_bob.address, 10, 1)
    tx2 = wallet_alice.create_transaction(wallet_bob.address, 5, 2)
    tx3 = wallet_alice.create_transaction(wallet_bob.address, 3, 3)

    tip = node.get_tip_block()
    coinbase = {"body": {"sender": "SYSTEM", "recipient": wallet_alice.address, "amount": 50, "nonce": 0}, "sig": None}

    # Case A: 역순 (3→2→1)
    print("\n2. Case A: 역순 블록 (3→2→1)")
    config.SIM_TIME = 2
    bad_block1 = Block(
        index=tip.index + 1,
        timestamp=config.SIM_TIME,
        transactions=[coinbase, tx3, tx2, tx1],  # 역순!
        difficulty=tip.difficulty,
        previous_hash=tip.hash,
        miner_id=wallet_alice.address
    )
    bad_block1.mine_block()

    is_valid = node.validate_block(bad_block1, tip)
    print(f"   역순 블록 검증: {is_valid}")
    assert not is_valid, "Reverse order block should be invalid"

    # Case B: 중간 건너뛰기 (1→3, 2 빠짐)
    print("\n3. Case B: 중간 건너뛰기 (1→3)")
    config.SIM_TIME = 3
    bad_block2 = Block(
        index=tip.index + 1,
        timestamp=config.SIM_TIME,
        transactions=[coinbase, tx1, tx3],  # tx2 빠짐
        difficulty=tip.difficulty,
        previous_hash=tip.hash,
        miner_id=wallet_alice.address
    )
    bad_block2.mine_block()

    is_valid = node.validate_block(bad_block2, tip)
    print(f"   중간 건너뛰기 블록 검증: {is_valid}")
    assert not is_valid, "Block with skipped nonce should be invalid"

    # Case C: 정순 (1→2→3)
    print("\n4. Case C: 정순 블록 (1→2→3)")
    config.SIM_TIME = 4
    good_block = Block(
        index=tip.index + 1,
        timestamp=config.SIM_TIME,
        transactions=[coinbase, tx1, tx2, tx3],  # 정순!
        difficulty=tip.difficulty,
        previous_hash=tip.hash,
        miner_id=wallet_alice.address
    )
    good_block.mine_block()

    is_valid = node.validate_block(good_block, tip)
    print(f"   정순 블록 검증: {is_valid}")
    assert is_valid, "Block with correct order should be valid"

    print("\n[OK] 시나리오 9 검증 완료")


def test_10_mempool_cleanup_after_reorg():
    """
    시나리오 10: Reorg 후 mempool 정리
    체인 교체 이후 mempool의 모든 거래는 최신 state 기준으로
    nonce/잔액/서명을 재검증하여 유효한 것만 유지
    """
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


def run_all_tests():
    """모든 테스트 실행"""
    tester = TestScenarios()

    print("=" * 70)
    print("블록체인 시뮬레이터 종합 테스트 스위트")
    print("=" * 70)
    print("\n10가지 핵심 시나리오 검증:")
    print("1. 정상 흐름 (연속 nonce)")
    print("2. Replay 방지")
    print("3. 잘못된 서명")
    print("4. Nonce 건너뛰기/역순")
    print("5. 동일 nonce 이중지불 경쟁")
    print("6. Deep reorg")
    print("7. Orphan 블록")
    print("8. TxID 안정성")
    print("9. 블록 내 tx 순서 공격")
    print("10. Reorg 후 mempool 정리")

    # 테스트 실행
    tester.run_test("시나리오 1: 정상 흐름 (연속 nonce)", test_1_normal_sequential_nonce)
    tester.run_test("시나리오 2: Replay 방지", test_2_replay_prevention)
    tester.run_test("시나리오 3: 잘못된 서명", test_3_invalid_signature)
    tester.run_test("시나리오 4: Nonce 건너뛰기/역순", test_4_nonce_skip_reverse)
    tester.run_test("시나리오 5: 동일 nonce 이중지불 경쟁", test_5_double_spend_reorg)
    tester.run_test("시나리오 6: Deep Reorg", test_6_deep_reorg)
    tester.run_test("시나리오 7: Orphan 블록", test_7_orphan_blocks)
    tester.run_test("시나리오 8: TxID 안정성", test_8_txid_stability)
    tester.run_test("시나리오 9: 블록 내 tx 순서 공격", test_9_block_tx_order_attack)
    tester.run_test("시나리오 10: Reorg 후 mempool 정리", test_10_mempool_cleanup_after_reorg)

    # 결과 요약
    tester.print_summary()

    return tester.passed == len(tester.test_results)


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
